#!/usr/bin/env python3
"""
Add signal routing segments and vias to voice_car_controller.kicad_pcb.
Routing strategy:
  - I2S signals  : F.Cu (short, below ESP32 bottom pads → INMP441)
  - Motor ctrl   : B.Cu with vias (long run under ESP32 module)
  - Motor outputs: F.Cu (short, DRV8833 → JST connectors)
  - Power (VBAT, 3V3): F.Cu medium runs
  - GND plane    : zone on B.Cu (already in file)
"""

import re

PCB_PATH = "/Users/crzhacko/projects/maker_lab/voice_car_esp32s3/electronics/voice_car_controller/voice_car_controller.kicad_pcb"

# ── net numbers (from (net N "name") declarations) ────────────────────────────
GND        = 1
V3V3       = 2
USB_5V     = 3
VBAT       = 4
LEFT_IN1   = 11
LEFT_IN2   = 12
RIGHT_IN1  = 13
RIGHT_IN2  = 14
DRV_SLEEP  = 15
AOUT1      = 16
AOUT2      = 17
BOUT1      = 18
BOUT2      = 19
I2S_WS     = 22
I2S_SCK    = 23
I2S_SD     = 24

# ── absolute pad positions (component_pos + relative_pad_pos) ─────────────────
# U1 ESP32-S3-WROOM-1 @ (30, 25) — left-side pads (x=-8.75 rel)
U1 = {
    2:  (21.25, 21.01),   # 3V3
    3:  (21.25, 22.28),   # EN
    4:  (21.25, 23.55),   # IO1  LEFT_IN1
    5:  (21.25, 24.82),   # IO2  LEFT_IN2
    6:  (21.25, 26.09),   # IO3  RIGHT_IN1
    7:  (21.25, 27.36),   # IO4  RIGHT_IN2
    8:  (21.25, 28.63),   # IO5  DRV_SLEEP
   13:  (21.25, 34.98),   # USB_D-
   14:  (21.25, 36.25),   # USB_D+
   # bottom pads (y=+12.5 rel)
   15: (23.015, 37.5),   # IO15 I2S_WS
   16: (24.285, 37.5),   # IO16 I2S_SCK
   17: (25.555, 37.5),   # IO17 I2S_SD
}

# U2 DRV8833 @ (50, 35) — TSSOP-16, 0.65mm pitch
# Left  pads (x=-2.862): pins 1-8  top→bottom
# Right pads (x=+2.862): pins 9-16 bottom→top
U2 = {
    1:  (47.138, 32.725),  # DRV_SLEEP (nSLEEP)
    2:  (47.138, 33.375),  # AOUT1
    3:  (47.138, 34.025),  # GND
    4:  (47.138, 34.675),  # AOUT2
    5:  (47.138, 35.325),  # BOUT2
    6:  (47.138, 35.975),  # GND
    7:  (47.138, 36.625),  # BOUT1
    8:  (47.138, 37.275),  # GND
    9:  (52.862, 37.275),  # RIGHT_IN1
   10:  (52.862, 36.625),  # RIGHT_IN2
   11:  (52.862, 35.975),  # VBAT (VM)
   12:  (52.862, 35.325),  # VBAT (VM)
   13:  (52.862, 34.675),  # GND
   14:  (52.862, 34.025),  # 3V3 (VCC)
   15:  (52.862, 33.375),  # LEFT_IN2
   16:  (52.862, 32.725),  # LEFT_IN1
}

# U3 XC6220 LDO @ (8, 35) — SOT-23-5
U3 = {
    1:  (6.862,  34.050),  # VIN (VBAT)
    3:  (6.862,  35.950),  # VIN (VBAT)
    5:  (9.137,  34.050),  # VOUT (3V3)
}

# U4 TP4056 @ (8, 28) — SOP-8, pins 1-4 left, 5-8 right
U4 = {
    1: (5.545,  29.905),   # TEMP  → GND via R7
    2: (5.545,  28.635),   # PROG  → GND via R6
    3: (5.545,  27.365),   # GND
    4: (5.545,  26.095),   # VCC   ← USB_5V
    5: (10.455, 26.095),   # BAT   → VBAT
    6: (10.455, 27.365),   # CHRG
    7: (10.455, 28.635),   # STDBY
    8: (10.455, 29.905),   # CE    ← USB_5V
}

# MK1 INMP441 @ (30, 47) — LGA-6
MK1 = {
    1: (28.950, 45.400),   # GND  (L/R select - tied GND)
    2: (31.050, 48.600),   # I2S_SD
    3: (31.050, 47.000),   # GND
    4: (28.950, 47.000),   # 3V3  (VDD)
    5: (28.950, 48.600),   # I2S_WS
    6: (31.050, 45.400),   # I2S_SCK
}

# J3 Left motor @ (52, 20)  pad1=AOUT1, pad2=AOUT2
J3 = {1: (52.0, 20.0), 2: (54.0, 20.0)}
# J4 Right motor @ (52, 28) pad1=BOUT1, pad2=BOUT2
J4 = {1: (52.0, 28.0), 2: (54.0, 28.0)}
# J2 Battery @ (52, 12) pad1=VBAT, pad2=GND
J2 = {1: (52.0, 12.0), 2: (54.0, 12.0)}

# ── helpers ───────────────────────────────────────────────────────────────────
_uid = [5000]

def _uuid():
    _uid[0] += 1
    n = _uid[0]
    return f"cc{n:06d}-{n:04d}-{n:04d}-{n:04d}-{n:012d}"

def seg(x1, y1, x2, y2, net, layer="F.Cu", w=0.2):
    if abs(x1-x2) < 0.001 and abs(y1-y2) < 0.001:
        return ""
    return (
        f'\n\t(segment\n'
        f'\t\t(start {x1:.3f} {y1:.3f})\n'
        f'\t\t(end {x2:.3f} {y2:.3f})\n'
        f'\t\t(width {w})\n'
        f'\t\t(layer "{layer}")\n'
        f'\t\t(net {net})\n'
        f'\t\t(uuid "{_uuid()}")\n'
        f'\t)'
    )

def via(x, y, net, size=0.6, drill=0.3):
    return (
        f'\n\t(via\n'
        f'\t\t(at {x:.3f} {y:.3f})\n'
        f'\t\t(size {size})\n'
        f'\t\t(drill {drill})\n'
        f'\t\t(layers "F.Cu" "B.Cu")\n'
        f'\t\t(net {net})\n'
        f'\t\t(uuid "{_uuid()}")\n'
        f'\t)'
    )

def L(x1, y1, x2, y2, net, layer="F.Cu", w=0.2, go_h_first=True):
    """L-shaped route: horizontal then vertical (or vice-versa)."""
    out = []
    if go_h_first:
        out.append(seg(x1, y1, x2, y1, net, layer, w))
        out.append(seg(x2, y1, x2, y2, net, layer, w))
    else:
        out.append(seg(x1, y1, x1, y2, net, layer, w))
        out.append(seg(x1, y2, x2, y2, net, layer, w))
    return "".join(out)

def via_bridge(x1, y1, x2, y2, net, via_x1=None, via_x2=None, via_y=None, w_sig=0.2):
    """
    Route a net through B.Cu with vias.
    F.Cu stub → via → B.Cu trace → via → F.Cu stub
    """
    out = []
    # Default via positions: just outside the pads
    vx1 = via_x1 if via_x1 is not None else x1 - 1.0
    vx2 = via_x2 if via_x2 is not None else x2 + 1.0
    vy  = via_y  if via_y  is not None else y1

    out.append(seg(x1, y1, vx1, y1, net, "F.Cu", w_sig))
    out.append(via(vx1, y1, net))
    out.append(seg(vx1, y1, vx2, vy, net, "B.Cu", w_sig))
    if abs(vy - y2) > 0.01:
        out.append(seg(vx2, vy, vx2, y2, net, "B.Cu", w_sig))
    out.append(via(vx2, y2, net))
    out.append(seg(vx2, y2, x2, y2, net, "F.Cu", w_sig))
    return "".join(out)

# ── build routing ──────────────────────────────────────────────────────────────
routing = []

# ━━ 1. I2S signals: F.Cu, short traces, ESP32 bottom → INMP441 ━━━━━━━━━━━━━━━
# I2S_WS  (22): U1p15 (23.015, 37.5) → MK1p5 (28.95, 48.6)
routing.append(L(*U1[15], *MK1[5], I2S_WS, go_h_first=False))

# I2S_SCK (23): U1p16 (24.285, 37.5) → MK1p6 (31.05, 45.4)
routing.append(L(*U1[16], *MK1[6], I2S_SCK, go_h_first=False))

# I2S_SD  (24): U1p17 (25.555, 37.5) → MK1p2 (31.05, 48.6)
routing.append(L(*U1[17], *MK1[2], I2S_SD, go_h_first=False))

# ━━ 2. Motor control signals: B.Cu via-bridge under ESP32 ━━━━━━━━━━━━━━━━━━━━
# LEFT_IN1  (11): U1p4  → U2p16 — via route at y=23.55 across board
routing.append(via_bridge(*U1[4], *U2[16], LEFT_IN1,
    via_x1=19.5, via_x2=54.0, via_y=23.55))

# LEFT_IN2  (12): U1p5  → U2p15 — y=24.82
routing.append(via_bridge(*U1[5], *U2[15], LEFT_IN2,
    via_x1=19.5, via_x2=54.0, via_y=24.82))

# RIGHT_IN1 (13): U1p6  → U2p9  — y=26.09
routing.append(via_bridge(*U1[6], *U2[9], RIGHT_IN1,
    via_x1=19.5, via_x2=54.0, via_y=26.09))

# RIGHT_IN2 (14): U1p7  → U2p10 — y=27.36
routing.append(via_bridge(*U1[7], *U2[10], RIGHT_IN2,
    via_x1=19.5, via_x2=54.0, via_y=27.36))

# DRV_SLEEP (15): U1p8 → U2p1
# Route: go south past ESP32 bottom, then east to DRV8833 left pad
x1, y1 = U1[8]   # 21.25, 28.63
x2, y2 = U2[1]   # 47.138, 32.725
routing.append(seg(x1, y1, x1, 40.0, DRV_SLEEP))             # south to clear ESP32
routing.append(seg(x1, 40.0, x2, 40.0, DRV_SLEEP))           # east
routing.append(seg(x2, 40.0, x2, y2, DRV_SLEEP))             # north to pad

# ━━ 3. Motor output traces: F.Cu, DRV8833 → connectors ━━━━━━━━━━━━━━━━━━━━━━
# AOUT1 (16): U2p2 (47.138, 33.375) → J3p1 (52.0, 20.0)  1mm wide (current)
routing.append(L(*U2[2], *J3[1], AOUT1, w=1.0, go_h_first=False))

# AOUT2 (17): U2p4 (47.138, 34.675) → J3p2 (54.0, 20.0)
routing.append(L(*U2[4], *J3[2], AOUT2, w=1.0, go_h_first=False))

# BOUT1 (18): U2p7 (47.138, 36.625) → J4p1 (52.0, 28.0)
routing.append(L(*U2[7], *J4[1], BOUT1, w=1.0))

# BOUT2 (19): U2p5 (47.138, 35.325) → J4p2 (54.0, 28.0)
routing.append(L(*U2[5], *J4[2], BOUT2, w=1.0))

# ━━ 4. Power traces: VBAT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VBAT: TP4056.BAT → LDO.VIN  (U4p5 → U3p1)
# U4p5 (10.455, 26.095) → U3p1 (6.862, 34.050)
routing.append(L(*U4[5], *U3[1], VBAT, w=0.5, go_h_first=False))

# VBAT: LDO.VIN (U3p3 at 6.862, 35.95) → local bypass already nearby
# VBAT: U4p5 → DRV8833 VM (U2p11 52.862,35.975) via horizontal
routing.append(L(U4[5][0], U4[5][1], U2[11][0], U2[11][1], VBAT, w=0.5, go_h_first=True))

# VBAT: J2p1 battery → U4p5 TP4056 BAT
routing.append(L(*J2[1], *U4[5], VBAT, w=0.5, go_h_first=False))

# ━━ 5. Power traces: 3V3 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# U3p5 (9.137, 34.05) → U1p2 (21.25, 21.01)
routing.append(seg(U3[5][0], U3[5][1], U3[5][0], 20.0, V3V3, w=0.5))
routing.append(seg(U3[5][0], 20.0, U1[2][0], 20.0, V3V3, w=0.5))
routing.append(seg(U1[2][0], 20.0, *U1[2], V3V3, w=0.5))

# 3V3 → MK1 VDD (U1 3V3 zone handles this; add a short spur)
routing.append(L(U1[2][0], U1[2][1], MK1[4][0], MK1[4][1], V3V3, w=0.5, go_h_first=False))

# ━━ 6. USB_5V: J1 → TP4056 VCC ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# J1 USB-C VBUS pads are near (8, 12), TP4056 VCC at (5.545, 26.095)
# USB_5V trace: (8.0, 12.0) → (5.545, 12.0) → (5.545, 26.095)
routing.append(seg(8.0, 12.0, 5.545, 12.0, USB_5V, w=0.5))
routing.append(seg(5.545, 12.0, *U4[4], USB_5V, w=0.5))
# Also connect CE pin 8
routing.append(seg(*U4[4], *U4[8], USB_5V, w=0.5))

# ━━ 7. Board outline (Edge.Cuts) 60×50mm ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# (outline is already in the file as gr_line from the original generation)

# ── inject into PCB file ───────────────────────────────────────────────────────
content = open(PCB_PATH).read()

# Remove trailing ')'
content = content.rstrip()
if content.endswith(')'):
    content = content[:-1]

injection = "\n\t; --- auto-routed signal traces ---" + "".join(routing)

content = content + injection + "\n)\n"

with open(PCB_PATH, 'w') as f:
    f.write(content)

# Verify
depth = 0
for ch in content:
    if ch == '(': depth += 1
    elif ch == ')': depth -= 1

import re
segs  = len(re.findall(r'\(segment\b', content))
vias  = len(re.findall(r'\(via\b', content))
print(f"Paren depth: {depth}")
print(f"Segments (traces): {segs}")
print(f"Vias: {vias}")
print("Done → voice_car_controller.kicad_pcb updated.")
