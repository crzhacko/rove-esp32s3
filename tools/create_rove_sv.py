#!/usr/bin/env python3
"""
ROVE-SV: Create schematic and PCB from ROVE-V by adding servo support.

Changes from ROVE-V:
- Remove no_connect on IO8 (y=112.54) and IO9 (y=115.08) ESP32 pins
- Add SERVO1/SERVO2 net labels at those pin positions
- Add J5 (Servo1) and J6 (Servo2) 3-pin connectors
  Pin 1: GND, Pin 2: VBAT (servo power), Pin 3: SERVO signal
- PCB: copy rove_v.kicad_pcb and add J5/J6 footprints at suitable positions
"""

import os
import re
import shutil
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCH_SRC = os.path.join(ROOT, "electronics/rove_v/rove_v.kicad_sch")
PCB_SRC = os.path.join(ROOT, "electronics/rove_v/rove_v.kicad_pcb")
SCH_DST = os.path.join(ROOT, "electronics/rove_sv/rove_sv.kicad_sch")
PCB_DST = os.path.join(ROOT, "electronics/rove_sv/rove_sv.kicad_pcb")
PRO_SRC = os.path.join(ROOT, "electronics/rove_v/rove_v.kicad_pro")
PRO_DST = os.path.join(ROOT, "electronics/rove_sv/rove_sv.kicad_pro")

def new_uuid():
    return str(uuid.uuid4())

# ── Schematic ──────────────────────────────────────────────────────────────────

print(f"Reading: {SCH_SRC}")
with open(SCH_SRC) as f:
    sch = f.read()

# 1. Remove no_connect markers on IO8 (139.76, 112.54) and IO9 (139.76, 115.08)
NO_CONNECT_IO8 = '(139.76, 112.54)'
NO_CONNECT_IO9 = '(139.76, 115.08)'

def remove_no_connect(content, x, y):
    """Remove a no_connect block at given coordinates."""
    pattern = rf'\(no_connect\s*\(at {re.escape(str(x))} {re.escape(str(y))}\)\s*\(uuid "[^"]+"\)\s*\)'
    matches = re.findall(pattern, content)
    if matches:
        print(f"  Removing {len(matches)} no_connect at ({x}, {y})")
        content = re.sub(pattern, '', content)
    else:
        print(f"  WARNING: no_connect at ({x}, {y}) not found — checking nearby...")
        # Try without strict spacing
        pattern2 = rf'\(no_connect\s*\n\s*\(at {re.escape(str(x))} {re.escape(str(y))}\)\s*\n\s*\(uuid "[^"]+"\)\s*\)'
        matches2 = re.findall(pattern2, content)
        if matches2:
            print(f"  Removing {len(matches2)} no_connect (multiline) at ({x}, {y})")
            content = re.sub(pattern2, '', content)
        else:
            print(f"  ERROR: Could not find no_connect at ({x}, {y})")
    return content

sch = remove_no_connect(sch, 139.76, 112.54)
sch = remove_no_connect(sch, 139.76, 115.08)

# 2. Add SERVO1 and SERVO2 net labels at the ESP32 pin positions
# Pattern from existing labels: (label "LEFT_IN1" (at 137.22 102.38 0) ...)
SERVO_LABELS = f"""
\t(label "SERVO1"
\t\t(at 137.22 112.54 0)
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.27 1.27)
\t\t\t)
\t\t\t(justify right bottom)
\t\t)
\t\t(uuid "{new_uuid()}")
\t)

\t(label "SERVO2"
\t\t(at 137.22 115.08 0)
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.27 1.27)
\t\t\t)
\t\t\t(justify right bottom)
\t\t)
\t\t(uuid "{new_uuid()}")
\t)
"""

# 3. Add J5 and J6 connector instances + wiring in an empty area of the schematic
# Place them below/near the battery protection circuit area (around x=50-90, y=145-175)
# Connector pinout: 1=GND, 2=VBAT(servo power), 3=SERVO signal
# Using Connector_Generic:Conn_01x03 with PinHeader_1x03_P2.54mm_Vertical footprint

J5_UUID    = new_uuid()
J5_P1_UUID = new_uuid()
J5_P2_UUID = new_uuid()
J5_P3_UUID = new_uuid()

J6_UUID    = new_uuid()
J6_P1_UUID = new_uuid()
J6_P2_UUID = new_uuid()
J6_P3_UUID = new_uuid()

# Power symbols
PWR_GND_J5  = new_uuid()
PWR_GND_J6  = new_uuid()
PWR_VBAT_J5 = new_uuid()
PWR_VBAT_J6 = new_uuid()

# Wire UUIDs
WIRE_J5_SIG  = new_uuid()
WIRE_J6_SIG  = new_uuid()
WIRE_J5_PWR  = new_uuid()
WIRE_J6_PWR  = new_uuid()
WIRE_J5_GND  = new_uuid()
WIRE_J6_GND  = new_uuid()

# Positions:
# J5 at (70, 148): pins at x=65.24 (left stub ends)
# J6 at (70, 163): same pattern
# Conn_01x03 pin stubs extend left: each pin at local x=-5.08
# So pin 1 local (−5.08, 2.54) = sch (64.92, 145.46) for J5 at (70,148)
# Pin positions in Conn_01x03 symbol (Y-up library convention):
#   pin1: at (-5.08, 2.54) → sch (70-5.08, 148-2.54) = (64.92, 145.46)
#   pin2: at (-5.08, 0.00) → sch (64.92, 148.00)
#   pin3: at (-5.08, -2.54) → sch (64.92, 150.54)
# BUT we need to check this. Looking at Conn_01x02 symbol definition:
# pin1: at (-5.08, 0)  and pin2: at (-5.08, -2.54)
# For Conn_01x03: pin1 top, pin2 middle, pin3 bottom
# Standard KiCad Conn_01x03: pin1 at (-5.08, 2.54), pin2 at (-5.08, 0), pin3 at (-5.08, -2.54)

# We'll use a simple wire approach: put the connectors at positions with
# GND on pin1, VBAT on pin2, SERVO signal on pin3
# J5 placed at (70, 148), J6 at (70, 163)

SERVO_CIRCUIT = f"""
\t(symbol
\t\t(lib_id "Connector_Generic:Conn_01x03")
\t\t(at 70 148 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{J5_UUID}")
\t\t(property "Reference" "J5"
\t\t\t(at 72.39 143.51 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Value" "Servo1"
\t\t\t(at 72.39 146.05 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
\t\t\t(at 70 148 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Datasheet" "~"
\t\t\t(at 70 148 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Description" "Servo 1 connector: 1=GND 2=VBAT 3=SERVO1"
\t\t\t(at 70 148 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(pin "1" (uuid "{J5_P1_UUID}"))
\t\t(pin "2" (uuid "{J5_P2_UUID}"))
\t\t(pin "3" (uuid "{J5_P3_UUID}"))
\t\t(instances
\t\t\t(project ""
\t\t\t\t(path "/voice-car-001"
\t\t\t\t\t(reference "J5")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)

\t(symbol
\t\t(lib_id "Connector_Generic:Conn_01x03")
\t\t(at 70 163 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{J6_UUID}")
\t\t(property "Reference" "J6"
\t\t\t(at 72.39 158.51 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Value" "Servo2"
\t\t\t(at 72.39 161.05 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
\t\t\t(at 70 163 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Datasheet" "~"
\t\t\t(at 70 163 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Description" "Servo 2 connector: 1=GND 2=VBAT 3=SERVO2"
\t\t\t(at 70 163 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(pin "1" (uuid "{J6_P1_UUID}"))
\t\t(pin "2" (uuid "{J6_P2_UUID}"))
\t\t(pin "3" (uuid "{J6_P3_UUID}"))
\t\t(instances
\t\t\t(project ""
\t\t\t\t(path "/voice-car-001"
\t\t\t\t\t(reference "J6")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)

\t(label "GND"
\t\t(at 62.38 145.46 0)
\t\t(effects
\t\t\t(font (size 1.27 1.27))
\t\t\t(justify right bottom)
\t\t)
\t\t(uuid "{PWR_GND_J5}")
\t)
\t(label "VBAT"
\t\t(at 62.38 148.00 0)
\t\t(effects
\t\t\t(font (size 1.27 1.27))
\t\t\t(justify right bottom)
\t\t)
\t\t(uuid "{PWR_VBAT_J5}")
\t)
\t(label "SERVO1"
\t\t(at 62.38 150.54 0)
\t\t(effects
\t\t\t(font (size 1.27 1.27))
\t\t\t(justify right bottom)
\t\t)
\t\t(uuid "{WIRE_J5_SIG}")
\t)

\t(label "GND"
\t\t(at 62.38 160.46 0)
\t\t(effects
\t\t\t(font (size 1.27 1.27))
\t\t\t(justify right bottom)
\t\t)
\t\t(uuid "{PWR_GND_J6}")
\t)
\t(label "VBAT"
\t\t(at 62.38 163.00 0)
\t\t(effects
\t\t\t(font (size 1.27 1.27))
\t\t\t(justify right bottom)
\t\t)
\t\t(uuid "{PWR_VBAT_J6}")
\t)
\t(label "SERVO2"
\t\t(at 62.38 165.54 0)
\t\t(effects
\t\t\t(font (size 1.27 1.27))
\t\t\t(justify right bottom)
\t\t)
\t\t(uuid "{WIRE_J6_SIG}")
\t)

\t(text
\t\t(at 50 142 0)
\t\t(effects
\t\t\t(font (size 1.5 1.5))
\t\t\t(justify left)
\t\t)
\t\t(uuid "{new_uuid()}")
\t\t"Servo connectors (J5=Servo1, J6=Servo2)\\nPin 1=GND  Pin 2=VBAT (servo power)  Pin 3=PWM signal\\nIO8→SERVO1 (ESP32 left side, y=112.54)\\nIO9→SERVO2 (ESP32 left side, y=115.08)"
\t)
"""

# 4. Insert everything before the final closing paren of the schematic
# Find the last line (should end with closing paren)
# We insert before the last ) in the file

# Insert servo labels at the end of the labels/symbols section
# Find (sheet_instances) which is the last major block before )
sheet_instances_pos = sch.rfind("(sheet_instances")
if sheet_instances_pos == -1:
    # Fallback: insert before last )
    insert_pos = sch.rfind(")")
    print("  WARNING: (sheet_instances) not found, inserting before last )")
else:
    insert_pos = sheet_instances_pos

sch = sch[:insert_pos] + SERVO_LABELS + "\n" + SERVO_CIRCUIT + "\n\t" + sch[insert_pos:]

# 5. Update schematic metadata: change rove_v references to rove_sv in title/description
# Update generator comment if any
sch = sch.replace('"ROVE-V', '"ROVE-SV')
sch = sch.replace('"rove_v', '"rove_sv')
# Keep the lib_id references as-is (they use KiCad library IDs, not project names)

# 6. Update sheet instances path UUID (make it unique for rove_sv)
# Actually, keep the same UUIDs for reuse - no need to change

print(f"Writing: {SCH_DST}")
with open(SCH_DST, 'w') as f:
    f.write(sch)

print(f"  Schematic written: {len(sch)} chars")

# ── PCB ────────────────────────────────────────────────────────────────────────

print(f"\nReading: {PCB_SRC}")
with open(PCB_SRC) as f:
    pcb = f.read()

# Copy PCB with new project name
pcb_new = pcb.replace('"rove_v"', '"rove_sv"')
pcb_new = pcb_new.replace('"rove_v.kicad_pcb"', '"rove_sv.kicad_pcb"')
pcb_new = pcb_new.replace('"ROVE-V R2"', '"ROVE-SV R1"')
pcb_new = pcb_new.replace('"ROVE-V"', '"ROVE-SV"')

# Add J5 and J6 footprints to the PCB
# Position them at the edge of the board where space allows
# Board is 60×50mm, origin at bx0/by0.
# Looking at the ROVE-V PCB, the board spans roughly (5, 5) to (65, 55) in mm
# Let's place them near J3/J4 motor connectors (which are on the edge)
# J3/J4 are through-hole JST PH 2-pin — let's find their positions in the PCB

# Extract J3/J4 positions from PCB to know the area
j3_match = re.search(r'\(footprint[^(]*\(at ([\d.]+) ([\d.]+)[^)]*\)[^(]*\(property "Reference" "J3"', pcb, re.DOTALL)
j4_match = re.search(r'\(footprint[^(]*\(at ([\d.]+) ([\d.]+)[^)]*\)[^(]*\(property "Reference" "J4"', pcb, re.DOTALL)

if j3_match:
    j3x, j3y = float(j3_match.group(1)), float(j3_match.group(2))
    print(f"  J3 at ({j3x}, {j3y})")
else:
    j3x, j3y = 57.0, 22.0  # fallback (known from PCB)
    print(f"  J3 not found, using known position ({j3x}, {j3y})")

if j4_match:
    j4x, j4y = float(j4_match.group(1)), float(j4_match.group(2))
    print(f"  J4 at ({j4x}, {j4y})")
else:
    j4x, j4y = 57.0, 33.0  # known from PCB
    print(f"  J4 not found, using known position ({j4x}, {j4y})")

# Board is 60×50mm (0,0)→(60,50)
# J3 at (57,22), J4 at (57,33) on right edge
# Place J5/J6 below J4 on right side, within board bounds
# 3-pin header needs ~8mm height; with courtyard, about ±4mm from center
# J5 at y=42 → extends y=38-46 ✓  J6 at y=47.5 → extends y=43.5-51.5 (too close to edge)
# Better: place at x=50 (more inward) below J4
j5x = 50.0
j5y = 42.0
j6x = 50.0
j6y = 47.0

print(f"  Placing J5 at ({j5x:.2f}, {j5y:.2f})")
print(f"  Placing J6 at ({j6x:.2f}, {j6y:.2f})")

# Build J5 footprint block
# Using Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical
# Net assignments will be done by netlist — for now add with empty nets (to be routed)
# Pad 1 = GND, Pad 2 = VBAT, Pad 3 = SERVO1/SERVO2

def make_servo_footprint(ref, value, x, y, net_sig, uuid_fp, uuid_p1, uuid_p2, uuid_p3):
    """Generate a PinHeader_1x03 footprint block in KiCad PCB S-expression format."""
    # Through-hole pin header: pads at 0, +2.54, +5.08 from center along y axis
    # We'll orient vertically (pins in a column)
    pad_size = 1.7
    drill = 1.0
    return f"""
\t(footprint "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
\t\t(layer "F.Cu")
\t\t(uuid "{uuid_fp}")
\t\t(at {x:.2f} {y:.2f})
\t\t(property "Reference" "{ref}"
\t\t\t(at 0 -4.5 0)
\t\t\t(layer "F.SilkS")
\t\t\t(uuid "{new_uuid()}")
\t\t\t(effects (font (size 1 1) (thickness 0.15)))
\t\t)
\t\t(property "Value" "{value}"
\t\t\t(at 0 4.5 0)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{new_uuid()}")
\t\t\t(effects (font (size 1 1) (thickness 0.15)))
\t\t)
\t\t(property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
\t\t\t(at 0 0 0)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{new_uuid()}")
\t\t\t(effects (font (size 1 1) (thickness 0.15)) (hide yes))
\t\t)
\t\t(fp_line
\t\t\t(start -1.33 -4.08) (end 1.33 -4.08)
\t\t\t(layer "F.SilkS") (uuid "{new_uuid()}")
\t\t\t(stroke (width 0.12) (type solid))
\t\t)
\t\t(fp_line
\t\t\t(start -1.33 4.08) (end 1.33 4.08)
\t\t\t(layer "F.SilkS") (uuid "{new_uuid()}")
\t\t\t(stroke (width 0.12) (type solid))
\t\t)
\t\t(fp_line
\t\t\t(start -1.33 -4.08) (end -1.33 4.08)
\t\t\t(layer "F.SilkS") (uuid "{new_uuid()}")
\t\t\t(stroke (width 0.12) (type solid))
\t\t)
\t\t(fp_line
\t\t\t(start 1.33 -4.08) (end 1.33 4.08)
\t\t\t(layer "F.SilkS") (uuid "{new_uuid()}")
\t\t\t(stroke (width 0.12) (type solid))
\t\t)
\t\t(fp_rect
\t\t\t(start -2.33 -5.08) (end 2.33 5.08)
\t\t\t(layer "F.CrtYd") (uuid "{new_uuid()}")
\t\t\t(stroke (width 0.05) (type solid)) (fill none)
\t\t)
\t\t(pad "1" thru_hole rect
\t\t\t(at 0 -2.54)
\t\t\t(size {pad_size} {pad_size})
\t\t\t(drill {drill})
\t\t\t(layers "*.Cu" "*.Mask")
\t\t\t(net 0 "GND")
\t\t\t(uuid "{uuid_p1}")
\t\t)
\t\t(pad "2" thru_hole circle
\t\t\t(at 0 0)
\t\t\t(size {pad_size} {pad_size})
\t\t\t(drill {drill})
\t\t\t(layers "*.Cu" "*.Mask")
\t\t\t(net 0 "VBAT")
\t\t\t(uuid "{uuid_p2}")
\t\t)
\t\t(pad "3" thru_hole circle
\t\t\t(at 0 2.54)
\t\t\t(size {pad_size} {pad_size})
\t\t\t(drill {drill})
\t\t\t(layers "*.Cu" "*.Mask")
\t\t\t(net 0 "{net_sig}")
\t\t\t(uuid "{uuid_p3}")
\t\t)
\t)
"""

j5_block = make_servo_footprint(
    "J5", "Servo1", j5x, j5y, "SERVO1",
    new_uuid(), new_uuid(), new_uuid(), new_uuid()
)
j6_block = make_servo_footprint(
    "J6", "Servo2", j6x, j6y, "SERVO2",
    new_uuid(), new_uuid(), new_uuid(), new_uuid()
)

# Insert footprints before the closing ) of the PCB file
pcb_close_pos = pcb_new.rfind(")")
pcb_new = pcb_new[:pcb_close_pos] + j5_block + j6_block + "\n)"

print(f"Writing: {PCB_DST}")
with open(PCB_DST, 'w') as f:
    f.write(pcb_new)
print(f"  PCB written: {len(pcb_new)} chars")

# ── Project file ────────────────────────────────────────────────────────────────
print(f"\nCopying project file: {PRO_SRC} → {PRO_DST}")
with open(PRO_SRC) as f:
    pro = f.read()
# Update any project-specific references
pro = pro.replace('"rove_v"', '"rove_sv"')
pro = pro.replace('"rove_v.kicad_pcb"', '"rove_sv.kicad_pcb"')
pro = pro.replace('"rove_v.kicad_sch"', '"rove_sv.kicad_sch"')
with open(PRO_DST, 'w') as f:
    f.write(pro)

print("\n=== ROVE-SV generation complete ===")
print(f"  Schematic: {SCH_DST}")
print(f"  PCB:       {PCB_DST}")
print(f"  Project:   {PRO_DST}")
print()
print("Changes from ROVE-V:")
print("  - IO8 (y=112.54) no_connect removed → SERVO1 label added")
print("  - IO9 (y=115.08) no_connect removed → SERVO2 label added")
print("  - J5 (Servo1) 3-pin header added at schematic")
print("  - J6 (Servo2) 3-pin header added at schematic")
print("  - J5/J6 footprints added to PCB (need routing)")
print()
print("Next steps:")
print("  1. Open rove_sv.kicad_sch in KiCad and verify the schematic")
print("  2. Run ERC to check for errors")
print("  3. Update PCB from schematic (sync netlist)")
print("  4. Route J5/J6 connections (GND, VBAT, SERVO1, SERVO2)")
print("  5. Run DRC and generate Gerbers")
