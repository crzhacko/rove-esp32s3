#!/usr/bin/env python3
"""
ROVE-V PCB Redesign — R2  (text-file approach, no pcbnew dependency)
Changes:
  - Board: 80×55 → 100×80 mm  (generous; optimize later)
  - J1 USB-C: moved to LEFT EDGE (X≈4.5) — cable plugs in from the side
  - Removed: U4 TP4056 + R6..R11 + D2..D5 (charging/TP4056 indicators)
  - Placeholder comments for U5 (DW01A) + Q1 (FS8205A) + R6/R7 divider
    → Add those manually via KiCad "Update PCB from Schematic" after schematic update
  - All segment/via tracks cleared — re-route in KiCad
  - Board title updated to ROVE-V R2
"""
import os, re, shutil, uuid

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__),
                       "../electronics/rove_v/rove_v.kicad_pcb"))

# ── helpers ───────────────────────────────────────────────────────────────────

def block_end(lines, start):
    """Return the line index of the closing paren of the S-expr block at 'start'."""
    depth = 0
    for i in range(start, len(lines)):
        depth += lines[i].count('(') - lines[i].count(')')
        if i > start and depth <= 0:
            return i
    return len(lines) - 1

def find_footprint(lines, ref):
    """Return (block_start, block_end) for the footprint with given Reference."""
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith('(footprint '):
            fp_start = i
            fp_end   = block_end(lines, i)
            block    = ''.join(lines[fp_start:fp_end + 1])
            if f'"Reference" "{ref}"' in block:
                return fp_start, fp_end
            i = fp_end + 1
        else:
            i += 1
    return None, None

def remove_footprint(lines, ref):
    """Remove the footprint block for 'ref'. Returns modified lines."""
    start, end = find_footprint(lines, ref)
    if start is None:
        print(f"  WARNING (remove): '{ref}' not found")
        return lines
    print(f"  Removed footprint: {ref}  (lines {start+1}–{end+1})")
    return lines[:start] + lines[end + 1:]

def move_footprint(lines, ref, new_x, new_y, new_rot=None):
    """Update the top-level (at X Y [rot]) of a footprint block."""
    start, end = find_footprint(lines, ref)
    if start is None:
        print(f"  WARNING (move): '{ref}' not found")
        return lines
    # The top-level (at ...) is typically within the first ~6 lines of the block
    for i in range(start, min(start + 8, end + 1)):
        m = re.match(r'^(\t+)\(at\s+([\d.+-]+)\s+([\d.+-]+)(.*)\)$', lines[i])
        if m:
            indent = m.group(1)
            old_rot_str = m.group(4).strip()
            if new_rot is not None:
                rot_part = f' {new_rot}' if new_rot != 0 else ''
            elif old_rot_str:
                # preserve existing rotation
                rot_part = f' {old_rot_str}'
            else:
                rot_part = ''
            lines[i] = f'{indent}(at {new_x} {new_y}{rot_part})\n'
            print(f"  Moved {ref} → ({new_x}, {new_y}){' rot='+str(new_rot)+'°' if new_rot else ''}")
            return lines
    print(f"  WARNING (move): could not find (at ...) in '{ref}' block")
    return lines

# ── Components to remove (TP4056 charging circuit) ────────────────────────────
REMOVE = [
    'U4',                              # TP4056 charger IC
    'R6', 'R7', 'R8', 'R9', 'R10', 'R11',  # TP4056 signal chain resistors
    'D2', 'D3',                        # USB_5V/VBAT ORing diodes (not needed)
    'D4', 'D5',                        # CHRG / STDBY indicator LEDs
]

# ── New positions (100×80 mm board, origin top-left) ─────────────────────────
#
#  USB-C (J1) at X=4.5 → left edge; connector face at X≈0
#
#  LEFT  (X 0–35):  power + protection + USB-C
#  CENTER(X 35–65): ESP32-S3 + INMP441
#  RIGHT (X 65–100): DRV8833 + JST connectors
#
POSITIONS = {
    #  ref     x       y    rot
    'J1':  ( 4.5,  40.0,   0),   # USB-C  ← LEFT EDGE
    'U3':  (15.0,  32.0,   0),   # XC6220 LDO 3.3V
    'C1':  ( 8.0,  24.0,   0),   # 100µF VBAT bulk
    'C2':  (22.0,  32.0,   0),   # 10µF 3V3 bulk
    'C3':  (15.0,  37.0,   0),   # 100nF LDO bypass
    'D1':  (10.0,  14.0,   0),   # green status LED
    'R3':  (16.0,  14.0,  90),   # 330Ω LED resistor
    'R1':  (18.0,  43.0,  90),   # 10kΩ EN pull-up
    'R2':  (18.0,  47.0,  90),   # 10kΩ IO0 pull-up
    'R4':  ( 5.0,  27.0,  90),   # 5.1kΩ CC1
    'R5':  ( 9.0,  27.0,  90),   # 5.1kΩ CC2
    'SW1': ( 8.0,  72.0,   0),   # boot button
    'U1':  (50.0,  35.0,   0),   # ESP32-S3-WROOM-1
    'MK1': (50.0,  58.0,   0),   # INMP441 I2S mic
    'C5':  (44.0,  57.0,  90),   # 100nF INMP441 VDD bypass
    'C6':  (76.0,  38.0,  90),   # 100nF DRV8833 3V3 bypass
    'C7':  (76.0,  43.0,  90),   # 100nF 3V3 bypass
    'C8':  (36.0,  22.0,  90),   # 100nF ESP32 3V3 bypass
    'U2':  (83.0,  45.0,   0),   # DRV8833PW motor driver
    'J2':  (96.0,  14.0,   0),   # LiPo battery JST  ← RIGHT EDGE
    'J3':  (96.0,  35.0,   0),   # left motor JST    ← RIGHT EDGE
    'J4':  (96.0,  50.0,   0),   # right motor JST   ← RIGHT EDGE
}

# ── Board outline replacement ─────────────────────────────────────────────────
NEW_W, NEW_H = 100, 80

NEW_OUTLINE = """\
\t(gr_line
\t\t(start 0 0)
\t\t(end {w} 0)
\t\t(stroke (width 0.05) (type default))
\t\t(layer "Edge.Cuts")
\t\t(uuid "{u1}")
\t)
\t(gr_line
\t\t(start {w} 0)
\t\t(end {w} {h})
\t\t(stroke (width 0.05) (type default))
\t\t(layer "Edge.Cuts")
\t\t(uuid "{u2}")
\t)
\t(gr_line
\t\t(start {w} {h})
\t\t(end 0 {h})
\t\t(stroke (width 0.05) (type default))
\t\t(layer "Edge.Cuts")
\t\t(uuid "{u3}")
\t)
\t(gr_line
\t\t(start 0 {h})
\t\t(end 0 0)
\t\t(stroke (width 0.05) (type default))
\t\t(layer "Edge.Cuts")
\t\t(uuid "{u4}")
\t)
""".format(w=NEW_W, h=NEW_H,
           u1=str(uuid.uuid4()), u2=str(uuid.uuid4()),
           u3=str(uuid.uuid4()), u4=str(uuid.uuid4()))

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    bak = PCB + ".bak_pre_r2"
    if not os.path.exists(bak):
        shutil.copy2(PCB, bak)
        print(f"Backup: {bak}")

    with open(PCB, 'r') as f:
        lines = f.readlines()
    print(f"Loaded: {len(lines)} lines from {PCB}")

    # ── 1. Remove TP4056 footprints ────────────────────────────────────────
    print("\n[1] Removing TP4056 charging circuit footprints...")
    for ref in REMOVE:
        lines = remove_footprint(lines, ref)

    # ── 2. Reposition remaining footprints ────────────────────────────────
    print("\n[2] Repositioning components (100×80 mm layout)...")
    for ref, (x, y, rot) in POSITIONS.items():
        lines = move_footprint(lines, ref, x, y, rot)

    # ── 3. Replace board outline ───────────────────────────────────────────
    print(f"\n[3] Updating board outline: 80×55 → {NEW_W}×{NEW_H} mm...")
    # Remove all existing Edge.Cuts gr_line blocks
    i = 0
    removed_edges = 0
    while i < len(lines):
        if lines[i].strip() == '(gr_line':
            blk_end = block_end(lines, i)
            blk = ''.join(lines[i:blk_end + 1])
            if '"Edge.Cuts"' in blk:
                lines = lines[:i] + lines[blk_end + 1:]
                removed_edges += 1
                continue
        i += 1
    print(f"  Removed {removed_edges} Edge.Cuts lines")

    # Insert new outline just before the first (segment or (via or closing )
    for i, l in enumerate(lines):
        if l.strip().startswith('(segment') or l.strip().startswith('(via'):
            lines.insert(i, NEW_OUTLINE)
            print(f"  Inserted {NEW_W}×{NEW_H} mm outline at line {i+1}")
            break
    else:
        # fallback: insert before final closing paren
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == ')':
                lines.insert(i, NEW_OUTLINE)
                print(f"  Inserted outline at line {i+1} (fallback)")
                break

    # ── 4. Update board title ──────────────────────────────────────────────
    for i, l in enumerate(lines):
        if '"Voice Car Controller"' in l:
            lines[i] = l.replace('Voice Car Controller', 'ROVE-V R2')
            print(f'\n[4] Updated title → "ROVE-V R2"')
            break

    # ── 5. Remove all routed tracks and vias ──────────────────────────────
    print("\n[5] Clearing all segment/via tracks...")
    seg_count = via_count = 0
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith('(segment'):
            end = block_end(lines, i)
            lines = lines[:i] + lines[end + 1:]
            seg_count += 1
            continue
        if stripped.startswith('(via'):
            end = block_end(lines, i)
            lines = lines[:i] + lines[end + 1:]
            via_count += 1
            continue
        i += 1
    print(f"  Removed {seg_count} segments + {via_count} vias")

    # ── Write ──────────────────────────────────────────────────────────────
    with open(PCB, 'w') as f:
        f.writelines(lines)
    print(f"\nSaved: {PCB}  ({len(lines)} lines)")

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  ROVE-V R2 PCB Layout — Done                                    ║
╠══════════════════════════════════════════════════════════════════╣
║  Board    : {NEW_W}×{NEW_H} mm  (generous — optimize after routing)     ║
║  USB-C J1 : X=4.5 mm  LEFT EDGE — cable accessible from side   ║
║  Removed  : U4 TP4056, R6-R11, D2-D5                           ║
║  Routing  : CLEARED — open KiCad to route                       ║
╠══════════════════════════════════════════════════════════════════╣
║  Next steps in KiCad:                                           ║
║  1. Open rove_v.kicad_sch → run update_schematic_rove_v.py     ║
║  2. Open rove_v.kicad_pcb                                       ║
║  3. Tools → Update PCB from Schematic                           ║
║     → places U5 (DW01A), Q1 (FS8205A), R6 (100k), R7 (47k)    ║
║  4. Arrange new components in left section (X 10-30, Y 55-70)  ║
║  5. Route: Inspect → Board Statistics to confirm 100×80mm      ║
║  6. Route all signals (Interactive Router or FreeRouter)        ║
║  7. DRC → target 0 violations → export Gerbers                  ║
╚══════════════════════════════════════════════════════════════════╝
""")

if __name__ == "__main__":
    main()
