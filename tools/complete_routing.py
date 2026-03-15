#!/usr/bin/env python3
"""
Complete all unrouted nets + inject zone fill polygons for voice_car_controller.kicad_pcb.

Strategy:
  - All SMD pads on F.Cu
  - GND / 3V3 handled by copper pours (zone fill added below)
  - USB D+/D-  : F.Cu, routed left of board edge (differential pair style)
  - CC1 / CC2  : F.Cu, route north of USB connector then south
  - EN          : B.Cu with vias (avoids motor-signal vias at x=19.5)
  - IO0 (BOOT) : F.Cu, route south & west around ESP32 bottom
  - STATUS_LED  : F.Cu, route around DRV_SLEEP trace
  - TP4056 sigs : F.Cu, short local runs
  - VBAT / 3V3 : F.Cu power traces, route around TP4056 body
  - Diode spurs : Short stubs to VBAT / USB_5V rail
"""

import re, math

PCB_PATH = ("/Users/crzhacko/projects/maker_lab/voice_car_esp32s3"
            "/electronics/voice_car_controller/voice_car_controller.kicad_pcb")

# ── net ids ───────────────────────────────────────────────────────────────────
GND=1; V3V3=2; USB_5V=3; VBAT=4
USB_DP=5; USB_DM=6; CC1=7; CC2=8; EN=9; IO0=10
STATUS_LED=20; LED_ANODE=21
TP_PROG=25; TP_TEMP=26; TP_CHRG=27; TP_STDBY=28
CHRG_LED=29; STDBY_LED=30

# ── absolute pad coords (component_pos + relative_pad) ───────────────────────
J1   = {                       # USB-C @ (8,12)
    "A5":(6.75,7.96),  "B5":(9.75,7.96),   # CC1 / CC2
    "A6":(7.75,7.96),  "B6":(8.75,7.96),   # D+
    "A7":(8.25,7.96),  "B7":(7.25,7.96),   # D-
    "A4":(5.55,7.96),                       # VBUS (USB_5V) -- already in net 3
}
U1   = {                       # ESP32-S3 @ (30,25)
    3 :(21.25,22.28),           # EN
    12:(21.25,33.71),           # USB_D-  (U1 has two D- pads)
    13:(21.25,34.98),           # USB_D-
    14:(21.25,36.25),           # USB_D+
    18:(26.82,37.50),           # STATUS_LED (IO48)
    26:(36.98,37.50),           # IO0 (bottom pad)
    27:(38.75,36.25),           # IO0 (right-side pad)
}
R1   = {1:(17.09,45.00), 2:(18.91,45.00)}  # EN pull-up  @ (18,45)
R2   = {1:(21.09,45.00), 2:(22.91,45.00)}  # IO0 pull-up @ (22,45)
R3   = {1:(21.09,42.00), 2:(22.91,42.00)}  # LED resistor@ (22,42)
R4   = {1:(7.09,20.00),  2:(8.91,20.00)}   # CC1          @ (8,20)
R5   = {1:(11.09,20.00), 2:(12.91,20.00)}  # CC2          @ (12,20)
R6   = {1:(14.09,28.00), 2:(15.91,28.00)}  # TP PROG      @ (15,28)
R7   = {1:(14.09,32.00), 2:(15.91,32.00)}  # TP TEMP      @ (15,32)
R8   = {1:(17.09,28.00), 2:(18.91,28.00)}  # CHRG pull-up @ (18,28)
R9   = {1:(21.09,28.00), 2:(22.91,28.00)}  # STDBY pull-up@ (22,28)
R10  = {1:(17.09,32.00), 2:(18.91,32.00)}  # CHRG LED R   @ (18,32)
R11  = {1:(21.09,32.00), 2:(22.91,32.00)}  # STDBY LED R  @ (22,32)
D1   = {"A":(18.94,42.00), "K":(17.06,42.00)}
D2   = {1:(13.35,35.00),   2:(16.65,35.00)}  # Schottky VBAT/USB_5V
D3   = {1:(16.35,35.00),   2:(19.65,35.00)}  # Schottky VBAT/USB_5V
D4   = {"A":(18.94,36.00), "K":(17.06,36.00)}
D5   = {"A":(22.94,36.00), "K":(21.06,36.00)}
U4   = {                       # TP4056 @ (8,28)
    1:(5.545,29.905),           # TEMP
    2:(5.545,28.635),           # PROG
    4:(5.545,26.095),           # VCC
    5:(10.455,26.095),          # BAT
    6:(10.455,27.365),          # CHRG
    7:(10.455,28.635),          # STDBY
    8:(10.455,29.905),          # CE
}
U3   = {5:(9.137,34.050)}      # LDO 3V3 output

# ── helpers ───────────────────────────────────────────────────────────────────
_uid = [9000]
def _uuid():
    _uid[0] += 1; n = _uid[0]
    return f"dd{n:06d}-{n:04d}-{n:04d}-{n:04d}-{n:012d}"

def seg(x1,y1, x2,y2, net, layer="F.Cu", w=0.2):
    if abs(x1-x2)<0.001 and abs(y1-y2)<0.001: return ""
    return (f'\n\t(segment\n\t\t(start {x1:.3f} {y1:.3f})\n'
            f'\t\t(end {x2:.3f} {y2:.3f})\n\t\t(width {w})\n'
            f'\t\t(layer "{layer}")\n\t\t(net {net})\n'
            f'\t\t(uuid "{_uuid()}")\n\t)')

def via(x,y,net):
    return (f'\n\t(via\n\t\t(at {x:.3f} {y:.3f})\n\t\t(size 0.6)\n'
            f'\t\t(drill 0.3)\n\t\t(layers "F.Cu" "B.Cu")\n'
            f'\t\t(net {net})\n\t\t(uuid "{_uuid()}")\n\t)')

def L(x1,y1, x2,y2, net, layer="F.Cu", w=0.2, h_first=True):
    if h_first:
        return seg(x1,y1,x2,y1,net,layer,w) + seg(x2,y1,x2,y2,net,layer,w)
    return seg(x1,y1,x1,y2,net,layer,w) + seg(x1,y2,x2,y2,net,layer,w)

def Z(x1,y1, xm,ym, x2,y2, net, layer="F.Cu", w=0.2):
    """3-segment Z-route: (x1,y1)→(xm,y1)→(xm,ym)→(x2,ym)→(x2,y2) optional."""
    return (seg(x1,y1,xm,y1,net,layer,w) + seg(xm,y1,xm,ym,net,layer,w)
            + seg(xm,ym,x2,ym,net,layer,w) + seg(x2,ym,x2,y2,net,layer,w))

def via_bridge(x1,y1, x2,y2, net, vx1,vy1, vx2,vy2, w=0.2):
    """F.Cu stub → via → B.Cu route → via → F.Cu stub."""
    return (seg(x1,y1,vx1,vy1,net,"F.Cu",w) + via(vx1,vy1,net)
            + seg(vx1,vy1,vx2,vy2,net,"B.Cu",w) + via(vx2,vy2,net)
            + seg(vx2,vy2,x2,y2,net,"F.Cu",w))

# ── build new routing ─────────────────────────────────────────────────────────
R = []

# ━━ USB D+ (net 5) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# J1.A6 ↔ J1.B6 short tie, then route left-edge of board south to ESP32
R.append(seg(*J1["A6"],*J1["B6"], USB_DP))
# Route around USB connector body (go north to y=4, then left, then south)
R.append(L(*J1["A6"], 2.0, 4.0, USB_DP, h_first=False))   # west at y=4
R.append(L(2.0, 4.0, *U1[14], USB_DP, h_first=False))      # south then east

# ━━ USB D- (net 6) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# J1.A7 ↔ J1.B7, then left edge → ESP32 pads 12+13
R.append(seg(*J1["A7"],*J1["B7"], USB_DM))
# Merge U1 pads 12+13 (both D-)
R.append(seg(*U1[12],*U1[13], USB_DM))
# Route: J1 → north to y=4.5 at x=2.5, south to y=34.35 (midpoint), then to U1
R.append(L(*J1["B7"], 2.5, 4.5, USB_DM, h_first=False))
R.append(seg(2.5, 4.5, 2.5, 34.35, USB_DM))
R.append(seg(2.5, 34.35, *U1[12], USB_DM))                 # to pad 12

# ━━ CC1 (net 7) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# J1.A5(6.75,7.96) → R4.1(7.09,20.00) — go north, then route south of connector
R.append(L(*J1["A5"], *R4[1], CC1, h_first=False))

# ━━ CC2 (net 8) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# J1.B5(9.75,7.96) → R5.1(11.09,20.00) — north tip then south
R.append(L(*J1["B5"], *R5[1], CC2, h_first=False))

# ━━ EN (net 9): U1.3 → R1.2 — use B.Cu to avoid motor vias at x=19.5 ━━━━━━━━
# F.Cu stub right → via → B.Cu left past x=19.5, south, via → F.Cu to R1.2
R.append(via_bridge(
    *U1[3], *R1[2], EN,
    vx1=21.25, vy1=22.28-0.5,   # via just above pad on F.Cu
    vx2=18.0,  vy2=45.50,       # via near R1.2 on left side
    w=0.2
))
# The B.Cu path: (21.25, 21.78) → (18.0, 21.78) → (18.0, 45.50)
# Override with explicit segments for the B.Cu leg
R_en = []
R_en.append(seg(*U1[3], 21.25, 21.50, EN,"F.Cu"))           # short south on F.Cu
R_en.append(via(21.25, 21.50, EN))
R_en.append(seg(21.25, 21.50, 17.5, 21.50, EN,"B.Cu"))      # left on B.Cu (clear of x=19.5 vias)
R_en.append(seg(17.5, 21.50, 17.5, 45.50, EN,"B.Cu"))       # south on B.Cu
R_en.append(via(17.5, 45.50, EN))
R_en.append(seg(17.5, 45.50, *R1[2], EN,"F.Cu"))            # east to R1.2
R.append("".join(R_en))

# ━━ IO0 (net 10): U1.26 + U1.27 → R2.2 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Merge U1.26 and U1.27 with short stub
R.append(L(*U1[26], *U1[27], IO0))
# Route south then west to R2.2(22.91,45.00)
# Avoid DRV_SLEEP trace at y=40 (x=21.25 to x=47.14)
# Go to y=46 (below DRV_SLEEP) then left
R.append(L(*U1[27], 22.91, 46.0, IO0, h_first=False))
R.append(seg(22.91, 46.0, *R2[2], IO0))

# ━━ STATUS_LED (net 20): U1.18 → R3.1 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Route around DRV_SLEEP trace at y=40 (x=21.25→47.14)
# Go south to y=39 (above DRV_SLEEP), then west to x=20, south to y=42, east to R3.1
R.append(seg(*U1[18], 26.82, 39.0, STATUS_LED))
R.append(seg(26.82, 39.0, 20.0, 39.0, STATUS_LED))
R.append(L(20.0, 39.0, *R3[1], STATUS_LED, h_first=False))

# ━━ LED_ANODE (net 21): R3.2 → D1.A ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
R.append(seg(*R3[2], *D1["A"], LED_ANODE))

# ━━ TP PROG (net 25): U4.2 → R6.1 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
R.append(L(*U4[2], *R6[1], TP_PROG, h_first=False))

# ━━ TP TEMP (net 26): U4.1 → R7.1 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
R.append(L(*U4[1], *R7[1], TP_TEMP, h_first=False))

# ━━ TP_CHRG (net 27): U4.6 → R8.2 and R8.2 → R10.1 ━━━━━━━━━━━━━━━━━━━━━━━━
# U4.6(10.455,27.365) → (go east at y=27.365 to R8.2 x=18.91) → then up to R8.1
R.append(seg(*U4[6], R8[2][0], U4[6][1], TP_CHRG))  # east at same y
R.append(seg(R8[2][0], U4[6][1], *R8[2], TP_CHRG))  # south to R8.2
# R8.2(18.91,28) → R10.1(17.09,32): go left then south
R.append(L(*R8[2], *R10[1], TP_CHRG, h_first=True))

# ━━ TP_STDBY (net 28): U4.7 → R9.2, R9.2 → R11.1 ━━━━━━━━━━━━━━━━━━━━━━━━━━
# U4.7(10.455,28.635) → east below CHRG line → R9.2(22.91,28.0)
R.append(seg(*U4[7], R9[2][0], U4[7][1], TP_STDBY))  # east at y=28.635
R.append(seg(R9[2][0], U4[7][1], *R9[2], TP_STDBY))  # north to R9.2
# R9.2(22.91,28) → R11.1(21.09,32): left then south
R.append(L(*R9[2], *R11[1], TP_STDBY, h_first=True))

# ━━ CHRG_LED (net 29): R10.2 → D4.A ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
R.append(L(*R10[2], *D4["A"], CHRG_LED, h_first=False))

# ━━ STDBY_LED (net 30): R11.2 → D5.A ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
R.append(L(*R11[2], *D5["A"], STDBY_LED, h_first=False))

# ━━ VBAT fixes: connect remaining VBAT pads ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# D2.1(13.35,35.0) and D3.1(16.35,35.0) → VBAT rail (connect to U3.1 area via y=34.05)
R.append(L(*D2[1], 13.35, 34.05, VBAT, w=0.5, h_first=False))  # north to VBAT rail
R.append(L(*D3[1], 16.35, 34.05, VBAT, w=0.5, h_first=False))  # north
# U3.3 duplicate VIN spur
R.append(seg(6.862, 34.050, 6.862, 35.950, VBAT, w=0.5))       # U3.1→U3.3 vertical
# Fix VBAT→LDO: go RIGHT of TP4056 body (x=12) to avoid crossing TP4056 pads
R.append(seg(10.455, 26.095, 12.0, 26.095, VBAT, w=0.5))       # east
R.append(seg(12.0, 26.095, 12.0, 34.050, VBAT, w=0.5))         # south
R.append(seg(12.0, 34.050, 6.862, 34.050, VBAT, w=0.5))        # west to U3.1
# Also connect both DRV8833 VM pins
R.append(seg(52.862, 35.975, 52.862, 35.325, VBAT, w=0.5))     # U2.11↔U2.12

# ━━ USB_5V fixes: connect D2.2 / D3.2 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# D2.2(16.65,35.0) and D3.2(19.65,35.0) are USB_5V (diode output → USB_5V rail)
# Route them up to the horizontal USB_5V trace (y≈26 area)
# The existing USB_5V trace runs at y=12 and y=26.095
# Spur: D2.2 → north to y=26.095 → west to existing USB_5V segment
R.append(L(*D2[2], D2[2][0], 26.095, USB_5V, w=0.5, h_first=False))
R.append(L(*D3[2], D3[2][0], 26.095, USB_5V, w=0.5, h_first=False))
# Extend USB_5V trace to cover D2.2 and D3.2 spurs on y=26.095
# Existing trace ends at U4.4(5.545,26.095), go east to cover diode spurs
R.append(seg(5.545, 26.095, 19.65, 26.095, USB_5V, w=0.5))

# ━━ 3V3 supplemental connections ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Connect U2.14 (DRV8833 VCC) to 3V3 (near U2 on right, at y=34.02)
# U3.5(9.137,34.05) → east along y=34.05 to U2.14(52.862,34.025)
R.append(seg(9.137, 34.050, 52.862, 34.025, V3V3, w=0.5))
# R1.1(17.09,45.0) → connect to 3V3; route north to 3V3 rail at y=20 via B.Cu
R_3v3_r1 = []
R_3v3_r1.append(seg(*R1[1], 17.09, 45.50, V3V3, "F.Cu", 0.3))
R_3v3_r1.append(via(17.09, 45.50, V3V3))
R_3v3_r1.append(seg(17.09, 45.50, 17.09, 19.50, V3V3, "B.Cu", 0.3))
R_3v3_r1.append(via(17.09, 19.50, V3V3))
R_3v3_r1.append(seg(17.09, 19.50, 21.25, 19.50, V3V3, "F.Cu", 0.3))
R_3v3_r1.append(seg(21.25, 19.50, 21.25, 21.01, V3V3, "F.Cu", 0.3))
R.append("".join(R_3v3_r1))
# R2.1(21.09,45.0) → tie to R1.1 via horizontal at y=45
R.append(seg(*R2[1], *R1[1], V3V3, "F.Cu", 0.3))
# R8.1(17.09,28.0) → 3V3 short spur north to y=26 then to U3.5 x-rail
R.append(L(*R8[1], 17.09, 26.0, V3V3, "F.Cu", 0.3, h_first=False))
R.append(seg(17.09, 26.0, 9.137, 26.0, V3V3, "F.Cu", 0.3))
R.append(L(9.137, 26.0, *U3[5], V3V3, "F.Cu", 0.3, h_first=False))
# R9.1(21.09,28.0) → connect to 3V3 rail at y=26
R.append(L(*R9[1], 21.09, 26.0, V3V3, "F.Cu", 0.3, h_first=False))
R.append(seg(21.09, 26.0, 17.09, 26.0, V3V3, "F.Cu", 0.3))

# ── read PCB and inject routing ───────────────────────────────────────────────
content = open(PCB_PATH).read()
content = content.rstrip().rstrip(')')  # remove closing ')'
content += "\n" + "".join(R)

# ── zone fill: add filled_polygon to GND and 3V3 zones ───────────────────────
# Approximate fill = board outline minus 0.3mm margin
# Format: (filled_polygon (layer "B.Cu") (pts (xy ...) ...))
# We inject this into each zone block
def inject_fill(content, net_id, layer, pts_str):
    """Insert filled_polygon into the first matching zone(net_id)(layer)."""
    zone_pat = re.compile(
        r'(\(zone\n\t+\(net ' + str(net_id) + r'\)\n\t+\(net_name[^\n]+\)\n'
        r'\t+\(layer "' + re.escape(layer) + r'"\).*?'
        r'\(polygon\n\t+\(pts\n\t+[^\)]+\)\n\t+\)\n\t+\))',
        re.DOTALL
    )
    fill_block = (
        f'\n\t\t(filled_polygon\n'
        f'\t\t\t(layer "{layer}")\n'
        f'\t\t\t(pts\n\t\t\t\t{pts_str}\n\t\t\t)\n'
        f'\t\t)'
    )
    def replacer(m):
        zone_text = m.group(1)
        # insert before last ')' of zone
        return zone_text[:-1] + fill_block + '\n\t)'
    new_content, n = zone_pat.subn(replacer, content, count=1)
    if n == 0:
        print(f"  WARNING: zone fill injection failed for net {net_id} {layer}")
    return new_content

# Build fill polygon: board is 60×50, margin 0.5mm from edge
margin = 0.5
corners = [
    (margin, margin), (60-margin, margin),
    (60-margin, 50-margin), (margin, 50-margin)
]
pts = " ".join(f"(xy {x} {y})" for x,y in corners)

content = inject_fill(content, GND,  "B.Cu", pts)
content = inject_fill(content, V3V3, "F.Cu", pts)

# Close the file
content = content.rstrip() + "\n)\n"

with open(PCB_PATH, 'w') as f:
    f.write(content)

# ── verify ────────────────────────────────────────────────────────────────────
depth = sum(1 if c=='(' else -1 if c==')' else 0 for c in content)
segs  = len(re.findall(r'\(segment\b', content))
vias  = len(re.findall(r'\(via\b',     content))
zones = len(re.findall(r'\(zone\b',    content))
fills = len(re.findall(r'\(filled_polygon\b', content))
print(f"Paren depth   : {depth}")
print(f"Segments      : {segs}")
print(f"Vias          : {vias}")
print(f"Zones         : {zones}")
print(f"Filled polygons: {fills}")

# Net coverage check
net_names = dict(re.findall(r'\(net (\d+) "([^"]+)"\)', content))
seg_nets = set(int(n) for n in re.findall(r'\(net (\d+)\)\n\t\t\(uuid', content))
all_nets = set(int(k) for k in net_names)
print(f"\nRouted nets   : {sorted(seg_nets)}")
print(f"Missing nets  : {sorted(all_nets - seg_nets - {0})}")
