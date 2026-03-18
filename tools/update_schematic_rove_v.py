#!/usr/bin/env python3
"""
ROVE-V Schematic Update — R2
Changes:
  - Remove TP4056 (U4) charging circuit and its lib symbol
  - Remove all USB_5V net labels (no longer used for power)
  - Add DW01A battery protection IC (U5)
  - Add FS8205A dual N-MOSFET (Q1) for DW01A switch pair
  - Add VBAT voltage divider resistors R6 (100kΩ) / R7 (47kΩ) → GPIO10 (ADC)
  - Rename VBAT net upstream of protection to BATT_RAW
Input / Output: electronics/rove_v/rove_v.kicad_sch  (overwritten in-place)
Backup written to rove_v.kicad_sch.bak_pre_r2
"""
import os, re, shutil, uuid

SCH = os.path.abspath(
    os.path.join(os.path.dirname(__file__),
                 "../electronics/rove_v/rove_v.kicad_sch"))

# ── helpers ──────────────────────────────────────────────────────────────────

def uid():
    return str(uuid.uuid4())

def block_end(lines, start):
    """Return the index of the last line of the S-expression block starting at 'start'."""
    depth = 0
    for i in range(start, len(lines)):
        depth += lines[i].count('(') - lines[i].count(')')
        if i > start and depth <= 0:
            return i
    return len(lines) - 1

def find_block_start(lines, pattern, start=0):
    for i in range(start, len(lines)):
        if re.search(pattern, lines[i]):
            return i
    return None

def remove_block(lines, start):
    end = block_end(lines, start)
    return lines[:start] + lines[end + 1:]

# ── lib symbol definitions to inject ─────────────────────────────────────────

DW01A_LIB = '''\
\t\t(symbol "Custom:DW01A"
\t\t\t(pin_numbers hide)
\t\t\t(pin_names (offset 0))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "U"
\t\t\t\t(at 2.54 0 90)
\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t)
\t\t\t(property "Value" "DW01A"
\t\t\t\t(at 0 0 90)
\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t)
\t\t\t(property "Footprint" "Package_TO_SOT_SMD:SOT-23-6"
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Datasheet" "http://www.celltech.com.tw/pdf/DW01A.pdf"
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Description" "Li-Ion/LiPo Battery Protection IC"
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(symbol "DW01A_0_1"
\t\t\t\t(rectangle (start -5.08 -6.35) (end 5.08 6.35)
\t\t\t\t\t(stroke (width 0.254) (type default))
\t\t\t\t\t(fill (type background))
\t\t\t\t)
\t\t\t)
\t\t\t(symbol "DW01A_1_1"
\t\t\t\t(pin output line (at -7.62 5.08 0) (length 2.54)
\t\t\t\t\t(name "OD" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "1" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t\t(pin input line (at -7.62 2.54 0) (length 2.54)
\t\t\t\t\t(name "CS" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "2" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t\t(pin output line (at -7.62 0 0) (length 2.54)
\t\t\t\t\t(name "OC" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "3" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t\t(pin power_in line (at 7.62 2.54 180) (length 2.54)
\t\t\t\t\t(name "VDD" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "4" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t\t(pin power_in line (at 7.62 0 180) (length 2.54)
\t\t\t\t\t(name "GND" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "5" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t\t(pin no_connect line (at 7.62 -2.54 180) (length 2.54)
\t\t\t\t\t(name "TM" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "6" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t)
\t\t)
'''

FS8205A_LIB = '''\
\t\t(symbol "Custom:FS8205A"
\t\t\t(pin_numbers hide)
\t\t\t(pin_names (offset 0))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "Q"
\t\t\t\t(at 2.54 0 90)
\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t)
\t\t\t(property "Value" "FS8205A"
\t\t\t\t(at 0 0 90)
\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t)
\t\t\t(property "Footprint" "Package_TO_SOT_SMD:SOT-23-6"
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Datasheet" "https://datasheet.lcsc.com/szlcsc/Fortune-Semiconductor-FS8205A_C32254.pdf"
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Description" "Dual N-Channel MOSFET for Li-Ion battery protection"
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(symbol "FS8205A_0_1"
\t\t\t\t(rectangle (start -5.08 -7.62) (end 5.08 7.62)
\t\t\t\t\t(stroke (width 0.254) (type default))
\t\t\t\t\t(fill (type background))
\t\t\t\t)
\t\t\t)
\t\t\t(symbol "FS8205A_1_1"
\t\t\t\t(pin input line (at -7.62 5.08 0) (length 2.54)
\t\t\t\t\t(name "G1" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "1" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t\t(pin bidirectional line (at -7.62 2.54 0) (length 2.54)
\t\t\t\t\t(name "S/B" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "2" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t\t(pin input line (at -7.62 0 0) (length 2.54)
\t\t\t\t\t(name "G2" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "3" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t\t(pin passive line (at 7.62 5.08 180) (length 2.54)
\t\t\t\t\t(name "D1" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "4" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t\t(pin passive line (at 7.62 2.54 180) (length 2.54)
\t\t\t\t\t(name "D2" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "5" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t\t(pin bidirectional line (at 7.62 0 180) (length 2.54)
\t\t\t\t\t(name "S/B" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "6" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t)
\t\t)
'''

# ── symbol instances to inject (placed on schematic sheet) ───────────────────
#  Protection block at schematic coordinates (~55, 100):
#  DW01A (U5): (55, 100)
#  FS8205A (Q1): (75, 100)
#  R6 100kΩ divider-high: (55, 120)
#  R7  47kΩ divider-low:  (55, 127)

DW01A_INST = f'''\
\t(symbol
\t\t(lib_id "Custom:DW01A")
\t\t(at 55 100 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{uid()}")
\t\t(property "Reference" "U5"
\t\t\t(at 55 91 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Value" "DW01A"
\t\t\t(at 55 93 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Footprint" "Package_TO_SOT_SMD:SOT-23-6"
\t\t\t(at 55 100 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Datasheet" "~"
\t\t\t(at 55 100 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Description" ""
\t\t\t(at 55 100 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(pin "1" (uuid "{uid()}"))
\t\t(pin "2" (uuid "{uid()}"))
\t\t(pin "3" (uuid "{uid()}"))
\t\t(pin "4" (uuid "{uid()}"))
\t\t(pin "5" (uuid "{uid()}"))
\t\t(pin "6" (uuid "{uid()}"))
\t\t(instances
\t\t\t(project ""
\t\t\t\t(path "/voice-car-001"
\t\t\t\t\t(reference "U5")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)
'''

FS8205A_INST = f'''\
\t(symbol
\t\t(lib_id "Custom:FS8205A")
\t\t(at 75 100 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{uid()}")
\t\t(property "Reference" "Q1"
\t\t\t(at 75 91 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Value" "FS8205A"
\t\t\t(at 75 93 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Footprint" "Package_TO_SOT_SMD:SOT-23-6"
\t\t\t(at 75 100 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Datasheet" "~"
\t\t\t(at 75 100 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Description" ""
\t\t\t(at 75 100 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(pin "1" (uuid "{uid()}"))
\t\t(pin "2" (uuid "{uid()}"))
\t\t(pin "3" (uuid "{uid()}"))
\t\t(pin "4" (uuid "{uid()}"))
\t\t(pin "5" (uuid "{uid()}"))
\t\t(pin "6" (uuid "{uid()}"))
\t\t(instances
\t\t\t(project ""
\t\t\t\t(path "/voice-car-001"
\t\t\t\t\t(reference "Q1")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)
'''

R6_INST = f'''\
\t(symbol
\t\t(lib_id "Device:R")
\t\t(at 55 120 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{uid()}")
\t\t(property "Reference" "R6"
\t\t\t(at 57.28 120 90)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Value" "100k"
\t\t\t(at 55 120 90)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Footprint" "Resistor_SMD:R_0402_1005Metric"
\t\t\t(at 55 120 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Datasheet" "~"
\t\t\t(at 55 120 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Description" "VBAT ADC divider high (VBAT → ADC)"
\t\t\t(at 55 120 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(pin "1" (uuid "{uid()}"))
\t\t(pin "2" (uuid "{uid()}"))
\t\t(instances
\t\t\t(project ""
\t\t\t\t(path "/voice-car-001"
\t\t\t\t\t(reference "R6")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)
'''

R7_INST = f'''\
\t(symbol
\t\t(lib_id "Device:R")
\t\t(at 55 127 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{uid()}")
\t\t(property "Reference" "R7"
\t\t\t(at 57.28 127 90)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Value" "47k"
\t\t\t(at 55 127 90)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Footprint" "Resistor_SMD:R_0402_1005Metric"
\t\t\t(at 55 127 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Datasheet" "~"
\t\t\t(at 55 127 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Description" "VBAT ADC divider low (ADC → GND)"
\t\t\t(at 55 127 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(pin "1" (uuid "{uid()}"))
\t\t(pin "2" (uuid "{uid()}"))
\t\t(instances
\t\t\t(project ""
\t\t\t\t(path "/voice-car-001"
\t\t\t\t\t(reference "R7")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)
'''

NET_LABELS = f'''\
\t(label "BATT_RAW"
\t\t(at 62.5 99.76 0)
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "{uid()}")
\t)
\t(label "BATT_RAW"
\t\t(at 68.0 97.5 0)
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "{uid()}")
\t)
\t(label "VBAT_MON"
\t\t(at 55.0 122.0 0)
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "{uid()}")
\t)
\t(label "VBAT_MON"
\t\t(at 140.0 27.46 0)
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "{uid()}")
\t)
\t(text "Battery protection: DW01A + FS8205A\\nBATT_RAW: unprotected battery input\\nVBAT: protected output to rest of circuit\\nVBAT_MON → ESP32 GPIO10 (ADC1_CH9)\\nVBAT_MON = VBAT × 47/(100+47) ≈ VBAT × 0.32\\nLow battery threshold: VBAT_MON < 1.06V → VBAT < 3.3V"
\t\t(at 55 135 0)
\t\t(effects (font (size 1.27 1.27)) (justify left))
\t\t(uuid "{uid()}")
\t)
'''

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    # Backup
    bak = SCH + ".bak_pre_r2"
    if not os.path.exists(bak):
        shutil.copy2(SCH, bak)
        print(f"Backup: {bak}")

    with open(SCH, 'r') as f:
        lines = f.readlines()

    print(f"Loaded: {len(lines)} lines")

    # ── 1. Remove TP4056 lib symbol definition ─────────────────────────────
    idx = find_block_start(lines, r'\(symbol "Custom:TP4056"')
    if idx is not None:
        lines = remove_block(lines, idx)
        print(f"Removed TP4056 lib symbol at line {idx+1}")
    else:
        print("WARNING: TP4056 lib symbol not found")

    # ── 2. Remove U4 (TP4056) instance ────────────────────────────────────
    idx = find_block_start(lines, r'\(lib_id "Custom:TP4056"\)')
    if idx is not None:
        # Walk back to find the enclosing (symbol ...) block
        for j in range(idx, max(0, idx - 5), -1):
            if lines[j].strip().startswith('(symbol'):
                idx = j
                break
        lines = remove_block(lines, idx)
        print(f"Removed U4 TP4056 instance at line {idx+1}")
    else:
        print("WARNING: U4 TP4056 instance not found")

    # ── 3. Remove duplicate USB_5V labels (TP4056 VBUS labels) ────────────
    # These 4-5 labels at (52.78, 99.76) were for TP4056 VCC
    # J1 USB-C power labels at different coordinates are preserved
    removed_usb5v = 0
    i = 0
    while i < len(lines):
        if '"USB_5V"' in lines[i] and i + 1 < len(lines):
            # Check if this label block is at TP4056-area coordinate (y≈99)
            block_txt = ''.join(lines[i:i+8])
            if '99.76' in block_txt or '99.7' in block_txt:
                end = block_end(lines, i)
                lines = lines[:i] + lines[end + 1:]
                removed_usb5v += 1
                continue
        i += 1
    print(f"Removed {removed_usb5v} USB_5V label(s) from TP4056 area")

    # ── 4. Inject DW01A + FS8205A lib symbols (before end of lib_symbols) ─
    # Find the closing paren of lib_symbols section
    lib_sym_start = find_block_start(lines, r'^\s*\(lib_symbols\s*$')
    if lib_sym_start is None:
        lib_sym_start = find_block_start(lines, r'\(lib_symbols')
    if lib_sym_start is not None:
        end = block_end(lines, lib_sym_start)
        # Insert just before the closing paren of lib_symbols
        insert_pos = end  # lines[end] is the closing ')'
        lines = (lines[:insert_pos]
                 + [DW01A_LIB, FS8205A_LIB]
                 + lines[insert_pos:])
        print(f"Injected DW01A + FS8205A lib symbols before line {insert_pos+1}")
    else:
        print("WARNING: lib_symbols section not found — lib symbols NOT injected")

    # ── 5. Inject instances + net labels before closing paren of kicad_sch ─
    # Find the very last ')' line
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == ')':
            insert_pos = i
            break
    else:
        insert_pos = len(lines)

    lines = (lines[:insert_pos]
             + [DW01A_INST, FS8205A_INST, R6_INST, R7_INST, NET_LABELS]
             + lines[insert_pos:])
    print(f"Injected DW01A/FS8205A instances + net labels at line {insert_pos+1}")

    # ── 6. Update generator tag ────────────────────────────────────────────
    for i, l in enumerate(lines):
        if '(generator "voice_car_generator")' in l:
            lines[i] = l.replace('voice_car_generator', 'rove_v_r2')
        if '(generator_version "1.0")' in l:
            lines[i] = l.replace('"1.0"', '"2.0"')

    # ── Write ──────────────────────────────────────────────────────────────
    with open(SCH, 'w') as f:
        f.writelines(lines)

    print(f"\nDone. Saved: {SCH}")
    print("""
Next steps in KiCad Schematic Editor:
  1. Open rove_v.kicad_sch
  2. Find DW01A (U5) and FS8205A (Q1) blocks — they appear at coordinates ~(55,100) and ~(75,100)
  3. Wire protection circuit:
       BATT_RAW (J2 +) → Q1.D1/D2 → Q1.S/B → VBAT
       DW01A.OD → Q1.G1   (overdischarge control)
       DW01A.OC → Q1.G2   (overcharge control)
       DW01A.CS → BATT_RAW- (current sense — 0Ω or direct)
       DW01A.VDD → VBAT
       DW01A.GND / DW01A.TM → GND
  4. Wire voltage divider:
       VBAT → R6(100kΩ) → VBAT_MON → R7(47kΩ) → GND
       VBAT_MON → ESP32 GPIO10
  5. Run ERC to check for errors
""")

if __name__ == "__main__":
    main()
