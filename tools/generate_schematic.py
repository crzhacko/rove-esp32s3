#!/usr/bin/env python3
"""
generate_schematic.py
Generates the KiCad schematic for the voice-controlled car project
by transforming the existing excavator schematic.

Steps:
  1. Read the existing schematic file
  2. Extract the lib_symbols section using a paren-matching parser
  3. Append TP4056 and INMP441 symbol definitions inside lib_symbols
  4. Remove servo-related symbol instances (J5, J6, J7) and their net labels
  5. Add TP4056, INMP441, and related passives as new symbol instances
  6. Add I2S net labels
  7. Write the new schematic
"""

import re
import sys

SRC = (
    "/Users/crzhacko/projects/maker_lab/excavator_esp32_project/"
    "electronics/vehicle_controller_drv8833/vehicle_controller_drv8833.kicad_sch"
)
DST = (
    "/Users/crzhacko/projects/maker_lab/voice_car_esp32s3/"
    "electronics/voice_car_controller/voice_car_controller.kicad_sch"
)

# ---------------------------------------------------------------------------
# Additional lib_symbol definitions to inject
# ---------------------------------------------------------------------------

TP4056_SYMBOL = """
\t(symbol "Custom:TP4056"
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(property "Reference" "U"
\t\t\t(at 0 4.572 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Value" "TP4056"
\t\t\t(at 0 3.048 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Footprint" "Package_SO:SOP-8_3.9x4.9mm_P1.27mm"
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Datasheet" "https://dlnmh9ip6v2uc.cloudfront.net/datasheets/Prototyping/TP4056.pdf"
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Description" "1A Standalone Linear Li-Ion Battery Charger"
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(symbol "TP4056_0_1"
\t\t\t(rectangle
\t\t\t\t(start -5.08 -7.62)
\t\t\t\t(end 5.08 2.54)
\t\t\t\t(stroke (width 0.254) (type default))
\t\t\t\t(fill (type background))
\t\t\t)
\t\t)
\t\t(symbol "TP4056_1_1"
\t\t\t(pin input line
\t\t\t\t(at -7.62 1.27 0)
\t\t\t\t(length 2.54)
\t\t\t\t(name "TEMP" (effects (font (size 1.27 1.27))))
\t\t\t\t(number "1" (effects (font (size 1.27 1.27))))
\t\t\t)
\t\t\t(pin input line
\t\t\t\t(at -7.62 -1.27 0)
\t\t\t\t(length 2.54)
\t\t\t\t(name "PROG" (effects (font (size 1.27 1.27))))
\t\t\t\t(number "2" (effects (font (size 1.27 1.27))))
\t\t\t)
\t\t\t(pin power_in line
\t\t\t\t(at 0 -10.16 90)
\t\t\t\t(length 2.54)
\t\t\t\t(name "GND" (effects (font (size 1.27 1.27))))
\t\t\t\t(number "3" (effects (font (size 1.27 1.27))))
\t\t\t)
\t\t\t(pin power_in line
\t\t\t\t(at -7.62 -3.81 0)
\t\t\t\t(length 2.54)
\t\t\t\t(name "VCC" (effects (font (size 1.27 1.27))))
\t\t\t\t(number "4" (effects (font (size 1.27 1.27))))
\t\t\t)
\t\t\t(pin power_out line
\t\t\t\t(at 7.62 -3.81 180)
\t\t\t\t(length 2.54)
\t\t\t\t(name "BAT" (effects (font (size 1.27 1.27))))
\t\t\t\t(number "5" (effects (font (size 1.27 1.27))))
\t\t\t)
\t\t\t(pin open_collector line
\t\t\t\t(at 7.62 -1.27 180)
\t\t\t\t(length 2.54)
\t\t\t\t(name "CHRG" (effects (font (size 1.27 1.27))))
\t\t\t\t(number "6" (effects (font (size 1.27 1.27))))
\t\t\t)
\t\t\t(pin open_collector line
\t\t\t\t(at 7.62 1.27 180)
\t\t\t\t(length 2.54)
\t\t\t\t(name "STDBY" (effects (font (size 1.27 1.27))))
\t\t\t\t(number "7" (effects (font (size 1.27 1.27))))
\t\t\t)
\t\t\t(pin input line
\t\t\t\t(at -7.62 -6.35 0)
\t\t\t\t(length 2.54)
\t\t\t\t(name "CE" (effects (font (size 1.27 1.27))))
\t\t\t\t(number "8" (effects (font (size 1.27 1.27))))
\t\t\t)
\t\t)
\t)"""

INMP441_SYMBOL = """
\t(symbol "Custom:INMP441"
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(property "Reference" "MK"
\t\t\t(at 0 4.572 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Value" "INMP441"
\t\t\t(at 0 3.048 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Footprint" "Microphone:Knowles_LGA-6_3.76x4.72mm"
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Datasheet" "https://invensense.tdk.com/wp-content/uploads/2015/02/INMP441.pdf"
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Description" "I2S MEMS Microphone with Bottom Port and High SNR"
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(symbol "INMP441_0_1"
\t\t\t(rectangle
\t\t\t\t(start -5.08 -5.08)
\t\t\t\t(end 5.08 2.54)
\t\t\t\t(stroke (width 0.254) (type default))
\t\t\t\t(fill (type background))
\t\t\t)
\t\t)
\t\t(symbol "INMP441_1_1"
\t\t\t(pin power_in line
\t\t\t\t(at -7.62 1.27 0)
\t\t\t\t(length 2.54)
\t\t\t\t(name "VDD" (effects (font (size 1.27 1.27))))
\t\t\t\t(number "1" (effects (font (size 1.27 1.27))))
\t\t\t)
\t\t\t(pin power_in line
\t\t\t\t(at 0 -7.62 90)
\t\t\t\t(length 2.54)
\t\t\t\t(name "GND" (effects (font (size 1.27 1.27))))
\t\t\t\t(number "2" (effects (font (size 1.27 1.27))))
\t\t\t)
\t\t\t(pin output line
\t\t\t\t(at 7.62 -1.27 180)
\t\t\t\t(length 2.54)
\t\t\t\t(name "SD" (effects (font (size 1.27 1.27))))
\t\t\t\t(number "3" (effects (font (size 1.27 1.27))))
\t\t\t)
\t\t\t(pin input line
\t\t\t\t(at -7.62 -1.27 0)
\t\t\t\t(length 2.54)
\t\t\t\t(name "WS" (effects (font (size 1.27 1.27))))
\t\t\t\t(number "4" (effects (font (size 1.27 1.27))))
\t\t\t)
\t\t\t(pin input line
\t\t\t\t(at -7.62 -3.81 0)
\t\t\t\t(length 2.54)
\t\t\t\t(name "SCK" (effects (font (size 1.27 1.27))))
\t\t\t\t(number "5" (effects (font (size 1.27 1.27))))
\t\t\t)
\t\t\t(pin input line
\t\t\t\t(at 7.62 1.27 180)
\t\t\t\t(length 2.54)
\t\t\t\t(name "L/R" (effects (font (size 1.27 1.27))))
\t\t\t\t(number "6" (effects (font (size 1.27 1.27))))
\t\t\t)
\t\t)
\t)"""

# ---------------------------------------------------------------------------
# New component instances to insert
# ---------------------------------------------------------------------------

NEW_COMPONENTS = """
\t(symbol
\t\t(lib_id "Custom:TP4056")
\t\t(at 55 45 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
\t\t(property "Reference" "U4"
\t\t\t(at 55 37.5 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Value" "TP4056"
\t\t\t(at 55 39.0 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Footprint" "Package_SO:SOP-8_3.9x4.9mm_P1.27mm"
\t\t\t(at 55 45 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Datasheet" "~"
\t\t\t(at 55 45 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Description" ""
\t\t\t(at 55 45 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(pin "1" (uuid "b2c3d4e5-f6a7-8901-bcde-f12345678901"))
\t\t(pin "2" (uuid "c3d4e5f6-a7b8-9012-cdef-123456789012"))
\t\t(pin "3" (uuid "d4e5f6a7-b8c9-0123-def0-234567890123"))
\t\t(pin "4" (uuid "e5f6a7b8-c9d0-1234-ef01-345678901234"))
\t\t(pin "5" (uuid "f6a7b8c9-d0e1-2345-f012-456789012345"))
\t\t(pin "6" (uuid "a7b8c9d0-e1f2-3456-0123-567890123456"))
\t\t(pin "7" (uuid "b8c9d0e1-f2a3-4567-1234-678901234567"))
\t\t(pin "8" (uuid "c9d0e1f2-a3b4-5678-2345-789012345678"))
\t\t(instances
\t\t\t(project ""
\t\t\t\t(path "/voice-car-001"
\t\t\t\t\t(reference "U4")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)

\t(symbol
\t\t(lib_id "Custom:INMP441")
\t\t(at 155 175 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "d0e1f2a3-b4c5-6789-3456-890123456789")
\t\t(property "Reference" "MK1"
\t\t\t(at 155 167.5 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Value" "INMP441"
\t\t\t(at 155 169.0 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Footprint" "Microphone:Knowles_LGA-6_3.76x4.72mm"
\t\t\t(at 155 175 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Datasheet" "~"
\t\t\t(at 155 175 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Description" ""
\t\t\t(at 155 175 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(pin "1" (uuid "e1f2a3b4-c5d6-7890-4567-901234567890"))
\t\t(pin "2" (uuid "f2a3b4c5-d6e7-8901-5678-012345678901"))
\t\t(pin "3" (uuid "a3b4c5d6-e7f8-9012-6789-123456789012"))
\t\t(pin "4" (uuid "b4c5d6e7-f8a9-0123-7890-234567890123"))
\t\t(pin "5" (uuid "c5d6e7f8-a9b0-1234-8901-345678901234"))
\t\t(pin "6" (uuid "d6e7f8a9-b0c1-2345-9012-456789012345"))
\t\t(instances
\t\t\t(project ""
\t\t\t\t(path "/voice-car-001"
\t\t\t\t\t(reference "MK1")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)

\t(symbol
\t\t(lib_id "power:+3.3V")
\t\t(at 155 172.46 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(uuid "e3f4a5b6-c7d8-9012-6789-123456789012")
\t\t(property "Reference" "#PWR050"
\t\t\t(at 155 176.53 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Value" "+3.3V"
\t\t\t(at 155 170.18 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Footprint" ""
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Datasheet" ""
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Description" ""
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(pin "1" (uuid "f4a5b6c7-d8e9-0123-7890-234567890123"))
\t\t(instances
\t\t\t(project ""
\t\t\t\t(path "/voice-car-001"
\t\t\t\t\t(reference "#PWR050")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)
"""

# ---------------------------------------------------------------------------
# I2S net labels near ESP32-S3 GPIO pins (replacing no_connect marks)
# and near INMP441
# ---------------------------------------------------------------------------

NEW_LABELS = """
\t(label "I2S_WS"
\t\t(at 170.24 115.08 0)
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "e7f8a9b0-c1d2-3456-0123-567890123456")
\t)

\t(label "I2S_SCK"
\t\t(at 170.24 117.62 0)
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "f8a9b0c1-d2e3-4567-1234-678901234567")
\t)

\t(label "I2S_SD"
\t\t(at 170.24 120.16 0)
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "a9b0c1d2-e3f4-5678-2345-789012345678")
\t)

\t(label "I2S_SD"
\t\t(at 162.62 173.73 0)
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "b0c1d2e3-f4a5-6789-3456-890123456789")
\t)

\t(label "I2S_WS"
\t\t(at 147.38 173.73 0)
\t\t(effects (font (size 1.27 1.27)) (justify right bottom))
\t\t(uuid "c1d2e3f4-a5b6-7890-4567-901234567890")
\t)

\t(label "I2S_SCK"
\t\t(at 147.38 171.19 0)
\t\t(effects (font (size 1.27 1.27)) (justify right bottom))
\t\t(uuid "d2e3f4a5-b6c7-8901-5678-012345678901")
\t)

\t(text "NOTE: TP4056 and INMP441 connections - see docs/schematic_notes.md"
\t\t(at 55 60 0)
\t\t(effects (font (size 1.27 1.27)))
\t\t(uuid "99887766-5544-3322-1100-aabbccddeeff")
\t)
"""

# ---------------------------------------------------------------------------
# UUIDs of no_connect markers that conflict with new I2S labels
# (at 170.24 115.08, 117.62, 120.16)
# ---------------------------------------------------------------------------

NO_CONNECT_UUIDS_TO_REMOVE = {
    "60b76996-cd14-4464-a3e8-b703e3b5a728",  # 170.24 115.08
    "d759f2ae-4057-41b6-b697-8acdae382aa2",  # 170.24 115.08
    "5928023d-33ae-43b7-8931-e458482740a3",  # 170.24 117.62
    "1ec1333e-d9bc-4922-84a9-01366bce6e7d",  # 170.24 117.62
    "b4b15d7d-1118-4d82-afc3-88401cab94ae",  # 170.24 120.16
    "29d2d93f-7231-400f-93cd-6501bef526b1",  # 170.24 120.16
}

# UUIDs of servo-related net labels to remove
SERVO_LABEL_UUIDS = {
    "8b3dbae8-8e36-4189-afed-fee23162c21a",  # BOOM_SERVO at ESP32 side
    "ee109987-c2f6-4343-a861-657ad3aff9fa",  # BUCKET_SERVO at ESP32 side
    "f2aa88cd-aba1-4e5c-ada8-346f0159d7d1",  # SERVO_5V at J5
    "7189193c-a217-49fe-a01f-b23b413ffa80",  # BOOM_SERVO at J5
    "4b38eeef-98ee-495a-846e-aa9006b5ca18",  # SERVO_5V at J6
    "7e138c2d-ee00-4e06-998e-6fcec8792167",  # BUCKET_SERVO at J6
    "ab7ec0a5-cdd0-4572-9665-9104116eec35",  # VBAT_MOTOR at J7
    "437f36e0-1ae3-4e53-93ec-a6c10788a672",  # SERVO_5V at J7
}

# UUIDs of symbol instances to remove (J5, J6, J7)
SERVO_SYMBOL_UUIDS = {
    "83fe2d42-3baa-407a-9de2-09e0e147ed70",  # J5 BoomServo
    "818f3832-dea6-4c5e-b18c-df4bb7956cf5",  # J6 BucketServo
    "bb2e817e-64e6-44e6-873b-e3c6df0e51fe",  # J7 5V Buck
}


def find_matching_paren(text, start):
    """
    Given text and an index `start` pointing at '(',
    return the index of the matching ')'.
    """
    assert text[start] == '(', f"Expected '(' at {start}, got {text[start]!r}"
    depth = 0
    i = start
    while i < len(text):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError(f"No matching ')' found starting from position {start}")


def extract_lib_symbols_section(content):
    """
    Returns (start_idx, end_idx) of the entire (lib_symbols ...) block,
    inclusive of both parentheses.
    """
    start = content.find('\t(lib_symbols')
    if start == -1:
        start = content.find('(lib_symbols')
    assert start != -1, "Could not find (lib_symbols in source file"
    end = find_matching_paren(content, start + content[start:].index('('))
    return start, end


def remove_symbol_block_by_uuid(content, uuid):
    """
    Locate a top-level (symbol ...) block whose uuid matches and remove it,
    including any leading whitespace/newline.
    """
    pattern = f'(uuid "{uuid}")'
    idx = content.find(pattern)
    if idx == -1:
        print(f"  WARNING: uuid {uuid} not found - skipping removal", file=sys.stderr)
        return content
    # Walk back to find the opening '(' of the enclosing (symbol ...) block.
    # We need to find the (symbol or (power or (label that owns this uuid.
    # Strategy: scan backwards for a line starting with \t( at depth 0.
    block_start = content.rfind('\n\t(', 0, idx)
    if block_start == -1:
        print(f"  WARNING: could not find block start for uuid {uuid}", file=sys.stderr)
        return content
    # block_start points to the \n before \t(
    open_paren = content.index('(', block_start)
    close_paren = find_matching_paren(content, open_paren)
    # Remove from the newline before the block to (inclusive) the close paren
    # and any trailing newline
    end = close_paren + 1
    if end < len(content) and content[end] == '\n':
        end += 1
    removed_text = content[block_start:end]
    print(f"  Removing block uuid={uuid}: {removed_text[:80].strip()!r}...")
    return content[:block_start] + content[end:]


def remove_no_connect_by_uuid(content, uuid):
    """Remove a (no_connect ...) block by its uuid."""
    pattern = f'(uuid "{uuid}")'
    idx = content.find(pattern)
    if idx == -1:
        print(f"  WARNING: no_connect uuid {uuid} not found", file=sys.stderr)
        return content
    block_start = content.rfind('\n\t(', 0, idx)
    if block_start == -1:
        print(f"  WARNING: cannot find block start for no_connect {uuid}", file=sys.stderr)
        return content
    open_paren = content.index('(', block_start)
    close_paren = find_matching_paren(content, open_paren)
    end = close_paren + 1
    if end < len(content) and content[end] == '\n':
        end += 1
    return content[:block_start] + content[end:]


def main():
    print(f"Reading source: {SRC}")
    with open(SRC, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"  Read {len(content)} chars, {content.count(chr(10))} lines")

    # ------------------------------------------------------------------
    # Step 1: Inject new lib_symbol definitions into lib_symbols section
    # ------------------------------------------------------------------
    print("Injecting TP4056 and INMP441 lib_symbols...")
    lib_start, lib_end = extract_lib_symbols_section(content)
    print(f"  lib_symbols: chars {lib_start}–{lib_end}")
    # Insert before the closing ')' of lib_symbols
    injection = TP4056_SYMBOL + "\n" + INMP441_SYMBOL + "\n"
    content = content[:lib_end] + injection + content[lib_end:]
    print(f"  After injection: {len(content)} chars")

    # ------------------------------------------------------------------
    # Step 2: Remove J5, J6, J7 symbol instances
    # ------------------------------------------------------------------
    print("Removing servo symbol instances (J5, J6, J7)...")
    for uuid in SERVO_SYMBOL_UUIDS:
        content = remove_symbol_block_by_uuid(content, uuid)

    # ------------------------------------------------------------------
    # Step 3: Remove servo-related net labels
    # ------------------------------------------------------------------
    print("Removing servo net labels...")
    for uuid in SERVO_LABEL_UUIDS:
        content = remove_symbol_block_by_uuid(content, uuid)

    # ------------------------------------------------------------------
    # Step 4: Remove no_connect markers that will be replaced by I2S labels
    # ------------------------------------------------------------------
    print("Removing no_connect markers at I2S GPIO positions...")
    for uuid in NO_CONNECT_UUIDS_TO_REMOVE:
        content = remove_no_connect_by_uuid(content, uuid)

    # ------------------------------------------------------------------
    # Step 5: Update schematic UUID (generator comment only)
    # ------------------------------------------------------------------
    content = content.replace(
        '(generator "codex")',
        '(generator "voice_car_generator")'
    )
    content = content.replace(
        '(uuid "f7ce4dbf-1f1d-4458-9b54-257a1aa085fb")',
        '(uuid "vc001111-2222-3333-4444-555566667777")'
    )

    # ------------------------------------------------------------------
    # Step 6: Insert new components and labels before (sheet_instances ...)
    # ------------------------------------------------------------------
    print("Inserting new component instances and I2S labels...")
    sheet_marker = '\n\t(sheet_instances'
    idx = content.find(sheet_marker)
    if idx == -1:
        # fallback: insert before the final closing paren
        idx = content.rfind('\n)')
    insertion = "\n" + NEW_COMPONENTS + "\n" + NEW_LABELS
    content = content[:idx] + insertion + content[idx:]

    # ------------------------------------------------------------------
    # Step 7: Write output
    # ------------------------------------------------------------------
    print(f"Writing output: {DST}")
    with open(DST, 'w', encoding='utf-8') as f:
        f.write(content)
    final_lines = content.count('\n')
    print(f"  Done. Written {len(content)} chars, ~{final_lines} lines")


if __name__ == "__main__":
    main()
