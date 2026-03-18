#!/usr/bin/env python3
"""
Fixes ROVE-SV PCB net assignments and prepares for routing:
1. Repositions J5 (50,42)->(50,38) and J6 (50,47)->(50,43) to safe positions
2. Adds SERVO1 (net 30) and SERVO2 (net 31) to net table
3. Fixes J5/J6 pad net assignments
4. Updates ESP32 pad 12 (IO8/GPIO12) -> SERVO1, pad 11 (IO18/GPIO11) -> SERVO2
   NOTE: pad 17 (GPIO17) = I2S_SD (used by microphone, NOT touched)
5. Exports DSN, runs freerouting, imports session
"""

import re
import os
import sys
import subprocess
import shutil
import tempfile

PCB_IN  = '/Users/crzhacko/projects/maker_lab/rove_esp32s3/electronics/rove_sv/rove_sv.kicad_pcb'
PCB_OUT = PCB_IN
DSN_OUT = '/Users/crzhacko/projects/maker_lab/rove_esp32s3/electronics/rove_sv/rove_sv.dsn'
SES_OUT = '/Users/crzhacko/projects/maker_lab/rove_esp32s3/electronics/rove_sv/rove_sv.ses'
EXPORT_DSN = '/Users/crzhacko/projects/maker_lab/rove_esp32s3/tools/export_dsn.py'
FREEROUTING = '/Users/crzhacko/bin/freerouting-1.9.0.jar'

# New safe positions for servo connectors (J6 was too close to board edge y=50)
J5_OLD_STR = '50.00 42.00'
J5_NEW_STR = '50.00 38.00'
J6_OLD_STR = '50.00 47.00'
J6_NEW_STR = '50.00 43.00'

NET_SERVO1 = 30
NET_SERVO2 = 31

def load(path):
    with open(path, 'r') as f:
        return f.read()

def save(path, content):
    with open(path, 'w') as f:
        f.write(content)
    print(f'Saved {path}')

def reposition_connector(content, ref, old_str, new_str):
    """Move a connector footprint to new position.
    old_str/new_str are exact 'X Y' coordinate strings matching the file.
    """
    ref_pattern = f'(property "Reference" "{ref}"'
    idx = content.find(ref_pattern)
    if idx == -1:
        print(f'ERROR: Could not find reference {ref}')
        return content

    block_start = content.rfind('(footprint', 0, idx)
    fp_block = content[block_start:idx]

    old_at = f'(at {old_str})'
    new_at = f'(at {new_str})'

    if old_at not in fp_block:
        print(f'ERROR: Could not find {old_at!r} in {ref} footprint block')
        print(f'Block snippet: {fp_block[:300]}')
        return content

    new_fp_block = fp_block.replace(old_at, new_at, 1)
    content = content[:block_start] + new_fp_block + content[block_start+len(fp_block):]
    print(f'Moved {ref}: (at {old_str}) -> (at {new_str})')
    return content

def add_nets_to_table(content):
    """Add SERVO1 and SERVO2 to the net table at top of file."""
    # Check if already added
    if '/SERVO1' in content[:5000]:
        print('SERVO1/SERVO2 nets already in table')
        return content

    # Find last net declaration in the top section (before footprints)
    # Net table is at the top, before first (footprint
    first_fp = content.find('(footprint ')
    top_section = content[:first_fp]

    # Find the last (net N "...") in top section
    net_matches = list(re.finditer(r'\(net \d+ "[^"]*"\)', top_section))
    if not net_matches:
        print('ERROR: Could not find net table')
        return content

    last_net = net_matches[-1]
    insert_pos = last_net.end()

    new_nets = f'\n\t(net {NET_SERVO1} "/SERVO1")\n\t(net {NET_SERVO2} "/SERVO2")'
    content = content[:insert_pos] + new_nets + content[insert_pos:]
    print(f'Added net {NET_SERVO1} "/SERVO1" and net {NET_SERVO2} "/SERVO2" to table')
    return content

def fix_connector_pad_nets(content, ref, pad_nets):
    """Fix pad net assignments in a connector footprint.

    pad_nets: dict {pad_num_str: (net_idx, net_name)}
    """
    ref_pattern = f'(property "Reference" "{ref}"'
    idx = content.find(ref_pattern)
    if idx == -1:
        print(f'ERROR: Could not find reference {ref}')
        return content

    block_start = content.rfind('(footprint', 0, idx)
    # Find end of footprint block
    depth = 0
    end = block_start
    for i in range(block_start, len(content)):
        if content[i] == '(':
            depth += 1
        elif content[i] == ')':
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    fp_block = content[block_start:end]

    for pad_num, (net_idx, net_name) in pad_nets.items():
        # Find (pad "N" ...) and replace its (net 0 "...") with correct net
        # Old patterns: (net 0 "GND"), (net 0 "VBAT"), (net 0 "SERVO1"), (net 0 "SERVO2")
        # Also handle old incorrect format
        old_patterns = [
            f'(net 0 "GND")',
            f'(net 0 "VBAT")',
            f'(net 0 "/VBAT")',
            f'(net 0 "SERVO1")',
            f'(net 0 "SERVO2")',
            f'(net 0 "/SERVO1")',
            f'(net 0 "/SERVO2")',
        ]
        new_net_str = f'(net {net_idx} "{net_name}")'

        # Find the specific pad block
        pad_pattern = f'(pad "{pad_num}"'
        pad_idx = fp_block.find(pad_pattern)
        if pad_idx == -1:
            print(f'ERROR: Could not find pad {pad_num} in {ref}')
            continue

        # Find end of this pad block
        pad_depth = 0
        pad_end = pad_idx
        for i in range(pad_idx, len(fp_block)):
            if fp_block[i] == '(':
                pad_depth += 1
            elif fp_block[i] == ')':
                pad_depth -= 1
                if pad_depth == 0:
                    pad_end = i + 1
                    break

        pad_block = fp_block[pad_idx:pad_end]
        new_pad_block = pad_block

        for old in old_patterns:
            if old in pad_block:
                new_pad_block = pad_block.replace(old, new_net_str, 1)
                print(f'Fixed {ref} pad {pad_num}: {old} -> {new_net_str}')
                break

        fp_block = fp_block[:pad_idx] + new_pad_block + fp_block[pad_end:]

    content = content[:block_start] + fp_block + content[end:]
    return content

def fix_esp32_pad_net(content, pad_num_str, net_idx, net_name):
    """Update ESP32 pad net assignment."""
    # Find ESP32 footprint
    esp32_start = content.find('footprint "ESP32-S3-WROOM')
    if esp32_start == -1:
        print('ERROR: Could not find ESP32 footprint')
        return content

    # Find start of footprint (opening paren)
    fp_open = content.rfind('(footprint', 0, esp32_start + 10)

    # Find end
    depth = 0
    end = fp_open
    for i in range(fp_open, len(content)):
        if content[i] == '(':
            depth += 1
        elif content[i] == ')':
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    fp_block = content[fp_open:end]

    # Find pad block
    pad_pattern = f'(pad "{pad_num_str}"'
    pad_idx = fp_block.find(pad_pattern)
    if pad_idx == -1:
        print(f'ERROR: Could not find ESP32 pad {pad_num_str}')
        return content

    pad_depth = 0
    pad_end = pad_idx
    for i in range(pad_idx, len(fp_block)):
        if fp_block[i] == '(':
            pad_depth += 1
        elif fp_block[i] == ')':
            pad_depth -= 1
            if pad_depth == 0:
                pad_end = i + 1
                break

    pad_block = fp_block[pad_idx:pad_end]

    # Replace existing net or add net
    new_net_str = f'(net {net_idx} "{net_name}")'
    old_net_match = re.search(r'\(net \d+ "[^"]*"\)', pad_block)
    if old_net_match:
        old_net_str = old_net_match.group(0)
        if old_net_str != new_net_str:
            new_pad_block = pad_block.replace(old_net_str, new_net_str, 1)
            print(f'Updated ESP32 pad {pad_num_str}: {old_net_str} -> {new_net_str}')
        else:
            print(f'ESP32 pad {pad_num_str} already has correct net')
            new_pad_block = pad_block
    else:
        # Insert net before closing paren of pad
        insert_at = pad_block.rfind(')')
        new_pad_block = pad_block[:insert_at] + f'\n\t\t\t{new_net_str}\n\t\t' + pad_block[insert_at:]
        print(f'Added net to ESP32 pad {pad_num_str}: {new_net_str}')

    fp_block = fp_block[:pad_idx] + new_pad_block + fp_block[pad_end:]
    content = content[:fp_open] + fp_block + content[end:]
    return content

def fix_pcb():
    print('=== Fixing ROVE-SV PCB ===')
    content = load(PCB_IN)

    # 1. Reposition J5 and J6 (J6 was too close to bottom board edge y=50)
    content = reposition_connector(content, 'J5', J5_OLD_STR, J5_NEW_STR)
    content = reposition_connector(content, 'J6', J6_OLD_STR, J6_NEW_STR)

    # 2. Add SERVO1/SERVO2 to net table
    content = add_nets_to_table(content)

    # 3. Fix J5 pad nets: pad1=GND(1), pad2=/VBAT(4), pad3=/SERVO1(30)
    content = fix_connector_pad_nets(content, 'J5', {
        '1': (1, 'GND'),
        '2': (4, '/VBAT'),
        '3': (NET_SERVO1, '/SERVO1'),
    })

    # 4. Fix J6 pad nets: pad1=GND(1), pad2=/VBAT(4), pad3=/SERVO2(31)
    content = fix_connector_pad_nets(content, 'J6', {
        '1': (1, 'GND'),
        '2': (4, '/VBAT'),
        '3': (NET_SERVO2, '/SERVO2'),
    })

    # 5. Update ESP32 pad 12 (GPIO12, left side, free in ROVE-V) -> SERVO1
    content = fix_esp32_pad_net(content, '12', NET_SERVO1, '/SERVO1')

    # 6. Update ESP32 pad 11 (GPIO11, left side, free in ROVE-V) -> SERVO2
    #    NOTE: pad 17 = GPIO17 = /I2S_SD (microphone) - do NOT touch it
    content = fix_esp32_pad_net(content, '11', NET_SERVO2, '/SERVO2')

    save(PCB_OUT, content)
    print('PCB fixes applied successfully')

def export_dsn():
    print('\n=== Exporting DSN ===')
    result = subprocess.run(
        ['python3', EXPORT_DSN, PCB_IN, DSN_OUT],
        capture_output=True, text=True
    )
    print(result.stdout[-2000:] if result.stdout else '')
    if result.returncode != 0:
        print('STDERR:', result.stderr[-500:])
        return False
    print(f'DSN exported: {DSN_OUT}')
    return True

def run_freerouting():
    print('\n=== Running freerouting ===')
    cmd = [
        'java', '-jar', FREEROUTING,
        '-de', DSN_OUT,
        '-do', SES_OUT,
        '-mp', '100',
        '-l', '1',
        '-dr', '/Users/crzhacko/projects/maker_lab/rove_esp32s3/electronics/rove_sv/rove_sv.kicad_dru',
    ]
    # Note: freerouting may not accept .kicad_dru directly
    cmd_simple = [
        'java', '-jar', FREEROUTING,
        '-de', DSN_OUT,
        '-do', SES_OUT,
        '-mp', '100',
        '-l', '1',
    ]
    print('CMD:', ' '.join(cmd_simple))
    result = subprocess.run(cmd_simple, capture_output=True, text=True, timeout=300)
    print(result.stdout[-3000:] if result.stdout else '')
    if result.returncode != 0:
        print('STDERR:', result.stderr[-500:])
        return False
    if os.path.exists(SES_OUT):
        print(f'Session file generated: {SES_OUT}')
        return True
    print('ERROR: No session file generated')
    return False

def import_session():
    print('\n=== Importing session ===')
    # Use kicad-cli pcb import-specctra
    result = subprocess.run(
        ['kicad-cli', 'pcb', 'import-specctra',
         '--input', SES_OUT,
         '--output', PCB_OUT,
         PCB_IN],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print('STDERR:', result.stderr[-500:])
        # Try alternate import via Python
        return import_session_python()
    print('Session imported successfully via kicad-cli')
    return True

def import_session_python():
    """Import .ses back into PCB using the existing import logic."""
    import_script = '/Users/crzhacko/projects/maker_lab/rove_esp32s3/tools/import_ses.py'
    if not os.path.exists(import_script):
        print('No import_ses.py found — manual import needed')
        return False
    result = subprocess.run(['python3', import_script, SES_OUT, PCB_IN, PCB_OUT],
                            capture_output=True, text=True)
    print(result.stdout)
    return result.returncode == 0

def run_drc():
    print('\n=== Running DRC ===')
    drc_out = '/Users/crzhacko/projects/maker_lab/rove_esp32s3/electronics/rove_sv/drc/drc_sv_routed.txt'
    os.makedirs(os.path.dirname(drc_out), exist_ok=True)
    result = subprocess.run(
        ['kicad-cli', 'pcb', 'drc',
         '--output', drc_out,
         '--format', 'text',
         '--schematic-parity',
         '--units', 'mm',
         PCB_IN],
        capture_output=True, text=True, timeout=120
    )
    print(result.stdout[-2000:] if result.stdout else '')
    if os.path.exists(drc_out):
        with open(drc_out) as f:
            lines = f.readlines()
        # Show summary
        for line in lines[-20:]:
            print(line, end='')
    return result.returncode == 0

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--fix-only', action='store_true', help='Only fix PCB nets, no routing')
    parser.add_argument('--route-only', action='store_true', help='Only run routing (PCB already fixed)')
    parser.add_argument('--drc', action='store_true', help='Run DRC after routing')
    args = parser.parse_args()

    if not args.route_only:
        fix_pcb()

    if not args.fix_only:
        if export_dsn():
            if run_freerouting():
                import_session()

    if args.drc:
        run_drc()

    print('\nDone.')
