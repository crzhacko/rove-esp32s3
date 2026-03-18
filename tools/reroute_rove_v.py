#!/usr/bin/env python3
"""Complete re-routing of ROVE-V PCB — v5.
Board expanded 60×50 → 80×55mm.
Motor section (U2,J2,J3,J4,C5,C6,C7) shifted east +18mm.
R9/R11/D5 moved west of U1 ESP32 module.
D4 moved south to clear D3 courtyard.
"""
import sys, os

KICAD_SITE = os.path.expanduser(
    "~/Applications/KiCad/KiCad.app/Contents/Frameworks/"
    "Python.framework/Versions/3.9/lib/python3.9/site-packages"
)
sys.path.insert(0, KICAD_SITE)
import pcbnew

PCB_IN  = os.path.abspath(os.path.join(os.path.dirname(__file__),
                           "../electronics/rove_v/rove_v.kicad_pcb"))
PCB_OUT = PCB_IN

F_CU = pcbnew.F_Cu
B_CU = pcbnew.B_Cu

def mm(v):
    return int(pcbnew.FromMM(v))

# ── Phase 1: component moves + board outline (save/reload to avoid SWIG invalidation) ──
board = pcbnew.LoadBoard(PCB_IN)

# ── Move components (BEFORE removing tracks — footprint refs stay valid) ──────
def move_fp(ref, new_x, new_y):
    for fp in board.GetFootprints():
        if fp.GetReference() == ref:
            fp.SetPosition(pcbnew.VECTOR2I(mm(new_x), mm(new_y)))
            return
    print(f"WARNING: footprint {ref} not found")

# Motor section: shift east +18mm
move_fp('U2',  68.0, 35.0)   # DRV8833  (was 50,35)
move_fp('J2',  70.0, 12.0)   # LiPo     (was 52,12)
move_fp('J3',  70.0, 20.0)   # Left motor (was 52,20)
move_fp('J4',  70.0, 28.0)   # Right motor (was 52,28)
move_fp('C5',  70.0, 42.0)   # VBAT decoupling (was 68,42; moved east so pad1=(67.05,42) clears C7.pad2)
move_fp('C6',  63.0, 38.0)   # 3V3 decoupling  (was 45,38)
move_fp('C7',  63.0, 42.0)   # 3V3 decoupling  (was 45,42; pad1=(62.05,42) lands on 3V3 B.Cu via ✓)
move_fp('R8',  18.0, 28.0)   # TP_CHRG/3V3 junction (pad1=(17.087,28)/3V3  pad2=(18.913,28)/TP_CHRG)

# TP4056 indicator resistors/LEDs: move west of U1 (ESP32 left pads at x=21.25)
move_fp('R9',   16.0, 24.0)  # was (22,28) inside U1
move_fp('R10',  18.0, 32.0)  # TP_CHRG/CHRG_LED: moved west to clear U1 copper (pad1=(17.087,32) pad2=(18.913,32))
move_fp('R11',  16.0, 30.0)  # TP_STDBY/STDBY_LED: y=30 clears TP_TEMP (R7.pad1 at y=32)
move_fp('D5',   14.5, 40.0)  # STDBY_LED/GND: x=14.5 avoids D1.padK short (D1 at 18,41)
move_fp('D1',   18.0, 41.0)  # status LED: moved north of D2 row to clear D2.pad2 at y=43
move_fp('D4',   18.0, 38.5)  # was (18,36)
move_fp('D2',   17.0, 43.0)  # moved south/east away from dense y=35 routing
move_fp('D3',   17.0, 47.0)  # same

print("Moved components")

print("Board outline: 80×55mm (4 edges already in PCB file)")

# Save phase 1 and reload fresh
board.Save(PCB_OUT)
board = pcbnew.LoadBoard(PCB_IN)
print("Reloaded board after layout changes")

def net(name):
    ni = board.FindNet(name)
    if ni is None:
        raise ValueError(f"net not found: {name}")
    return ni

def T(x1, y1, x2, y2, layer, net_name, width=0.2):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(   pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetLayer(layer)
    t.SetNet(net(net_name))
    t.SetWidth(mm(width))
    board.Add(t)

def V(x, y, net_name, drill=0.3, size=0.6):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetNet(net(net_name))
    v.SetDrill(mm(drill))
    v.SetWidth(mm(size))
    board.Add(v)

# ── Phase 2: remove old tracks, add new routing ───────────────────────────────
for t in list(board.GetTracks()):
    board.Remove(t)
print("Removed all tracks/vias")

# New pad positions after moves:
# U2 left pads:  x=65.138  (DRV_SLEEP=32.725, AOUT1=33.375, pad3GND=34.025,
#                            AOUT2=34.675, BOUT2=35.325, pad6GND=35.975,
#                            BOUT1=36.625, pad8GND=37.275)
# U2 right pads: x=70.862  (RIGHT_IN1=37.275, RIGHT_IN2=36.625, VBAT=35.975,
#                            VBAT=35.325, pad13GND=34.675, 3V3=34.025,
#                            LEFT_IN2=33.375, LEFT_IN1=32.725)
# J2: pad1=(70,12)/VBAT  pad2=(72,12)/GND
# J3: pad1=(70,20)/AOUT1 pad2=(72,20)/AOUT2
# J4: pad1=(70,28)/BOUT1 pad2=(72,28)/BOUT2
# C5: pad1=(67.05,42)/VBAT  pad2=(72.95,42)/GND  [C5 moved to x=70]
# C6: pad1=(62.05,38)/3V3  pad2=(63.95,38)/GND
# C7: pad1=(62.05,42)/3V3  pad2=(63.95,42)/GND
# R9:  pad1=(15.087,24)/3V3  pad2=(16.913,24)/TP_STDBY
# R8:  pad1=(17.087,28)/3V3  pad2=(18.913,28)/TP_CHRG  [x=18.0]
# R10: pad1=(17.087,32)/TP_CHRG  pad2=(18.913,32)/CHRG_LED  [x=18.0]
# R11: pad1=(15.087,30)/TP_STDBY  pad2=(16.913,30)/STDBY_LED  [y=30]
# D5:  padK=(13.587,40.0)/GND  padA=(15.413,40.0)/STDBY_LED  [x=14.5,y=40.0]
# D1:  padK=(17.062,41)/GND  padA=(18.938,41)/LED_ANODE  [y=41]
# D4:  padK=(17.062,38.5)/GND  padA=(18.938,38.5)/CHRG_LED
# D2:  pad1=(15.35,43)/VBAT  pad2=(18.65,43)/USB_5V  [moved south]
# D3:  pad1=(15.35,47)/VBAT  pad2=(18.65,47)/USB_5V  [moved south]

# ── Widths ────────────────────────────────────────────────────────────────────
W  = 0.2   # signal
WP = 0.5   # power (VBAT / USB_5V)
W3 = 0.3   # 3V3 distribution
WM = 1.0   # motor output

# =============================================================================
# VBAT
# Source: J2.pad1 (70,12)  →  north jog to y=10, east to x=76
# x=76 south column: y=10→18 (bridge level), y=18→42 (U2/C5 feeds)
# B.Cu bridge at y=18: x=76→12  (carries VBAT west to LDO/C1/D2/D3)
# Western bus F.Cu y=26.095 x=6.862→16.35 (same as before)
# U2.pad12 at (70.862,35.325) and pad11 at (70.862,35.975)
# C5.pad1 at (65.3,42)
# =============================================================================
# J2 exit: north jog then east to x=76 column
T(70, 12, 70, 10, F_CU, "/VBAT", WP)
T(70, 10, 76, 10, F_CU, "/VBAT", WP)
V(76, 10, "/VBAT")
T(76, 10, 76, 18, B_CU, "/VBAT", WP)        # south to bridge level

# East↔west bridge at y=18
V(76, 18, "/VBAT")
T(76, 18, 12.0, 18, B_CU, "/VBAT", WP)
V(12.0, 18, "/VBAT")
T(12.0, 18, 14.0, 18, F_CU, "/VBAT", WP)       # F.Cu east jog
V(14.0, 18, "/VBAT")
T(14.0, 18, 14.0, 26.095, B_CU, "/VBAT", WP)   # B.Cu south (avoids TP_CHRG F.Cu east at y=25.2 ✓)
V(14.0, 26.095, "/VBAT")

# Western bus (x=6.862→16.35)
T(6.862, 26.095, 16.35, 26.095, F_CU, "/VBAT", WP)

# South column for U2 and C5
T(76, 18, 76, 42, B_CU, "/VBAT", WP)           # continue south from bridge

# U2.pad12 (70.862,35.325) and pad11 (70.862,35.975)
V(76, 35.325, "/VBAT")
T(76, 35.325, 70.862, 35.325, F_CU, "/VBAT", WP)   # → U2.pad12
V(76, 35.975, "/VBAT")
T(76, 35.975, 70.862, 35.975, F_CU, "/VBAT", WP)   # → U2.pad11

# C5.pad1 (65.3,42): detour around AOUT2 B.Cu col (x=74.5, WM=1.0mm, edge at x=75.0)
# B.Cu hop would short AOUT2 (via(75,42) copper edge 74.7 < AOUT2 edge 75.0).
# Use F.Cu directly from via(76,42): south past motor buses, west, north to C5.pad1.
V(76, 42, "/VBAT")
T(76, 42, 76.0, 47.8, F_CU, "/VBAT", WP)           # F.Cu south (avoids AOUT2 B.Cu at x=74.5)
T(76.0, 47.8, 67.3, 47.8, F_CU, "/VBAT", WP)       # F.Cu west (C5.pad1=(67.3,42) from inspect_pcb ✓)
T(67.3, 47.8, 67.3, 42.0, F_CU, "/VBAT", WP)      # F.Cu north → C5.pad1

# LDO U3 + C1 + D2 + D3: B.Cu south column at x=6.862, extended to y=47
V(6.862, 26.095, "/VBAT")
T(6.862, 26.095, 6.862, 47.0, B_CU, "/VBAT", WP)   # extended south to D3
V(6.862, 34.050, "/VBAT")   # tap → U3.pad1
V(6.862, 35.950, "/VBAT")   # tap → U3.pad3
V(6.862, 40.0,   "/VBAT")
T(6.862, 40.0, 5.3, 40.0, F_CU, "/VBAT", WP)       # → C1.pad1

# D2.pad1 (new: 15.35,43) and D3.pad1 (new: 15.35,47)
# Use B.Cu to avoid SW1 mechanical pads at (11.1,43.15) and (11.1,46.85) on F.Cu
V(6.862, 43.0, "/VBAT")
T(6.862, 43.0, 15.35, 43.0, B_CU, "/VBAT", WP)    # B.Cu → D2.pad1 (avoids SW1 F.Cu pads)
V(15.35, 43.0, "/VBAT")
V(6.862, 47.0, "/VBAT")
T(6.862, 47.0, 15.35, 47.0, B_CU, "/VBAT", WP)    # B.Cu → D3.pad1
V(15.35, 47.0, "/VBAT")

# =============================================================================
# USB_5V
# B.Cu bridge (5.55→7.0, y=30) crossed VBAT B.Cu col at x=6.862 → removed.
# New: tap F.Cu column at y=21 (above VBAT bus at y=26.095, clear of CC1/CC2
# which end at y=20), go east to x=16.8, via to B.Cu south col at x=16.8.
# x=16.8 clears: TP_STDBY B.Cu at x=16.0 (gap=0.35mm), VBAT D2/D3 at x≤15.6,
# 3V3 B.Cu at x=17.7 (gap=0.5mm).
# U4.pad8 still fed from J1 second VBUS via at (10.45,7.955) on B.Cu south.
# TP_STDBY via at (10.455,29.0) removed in new TP_STDBY routing → no conflict.
# =============================================================================
# J1 → U4.pad4: via on J1 pad, B.Cu east jog to x=5.90 (clears NPTH at (5.11,9.4) right≈5.30;
# B.Cu left edge 5.65; gap 0.35mm ✓). J1 pads are SMD on F.Cu → B.Cu jog unaffected ✓.
V(5.55, 7.955, "/USB_5V")                            # via on J1 VBUS pad
T(5.55, 7.955, 6.0, 7.955, B_CU, "/USB_5V", WP)    # B.Cu east jog (NPTH at (5.11,9.4) right≈5.435; track left=5.75; gap=0.315mm ✓)
T(6.0, 7.955, 6.0, 26.095, B_CU, "/USB_5V", WP)   # B.Cu south (NPTH gap 0.415mm ✓)
V(6.0, 26.095, "/USB_5V")
T(6.0, 26.095, 5.545, 26.095, F_CU, "/USB_5V", WP) # F.Cu west → U4.pad4 (VBAT starts x=6.862 ✓)
# B.Cu south for D2/D3: continue from same via
T(6.0, 26.095, 6.0, 48.5, B_CU, "/USB_5V", WP)    # B.Cu south (VBAT col at x=6.862 → gap 0.56mm ✓)
T(6.0, 48.5, 16.6, 48.5, B_CU, "/USB_5V", WP)     # east to x=16.6 (stops west of 3V3 B.Cu x=17.7 ✓)
# D3: via at (16.6,48.5), F.Cu east to x=18.65, north to D3.pad2 at y=47
V(16.6, 48.5, "/USB_5V")
T(16.6, 48.5, 18.65, 48.5, F_CU, "/USB_5V", WP)    # F.Cu east (3V3 B.Cu at x=17.7 on B.Cu only ✓)
T(18.65, 48.5, 18.65, 47.0, F_CU, "/USB_5V", WP)   # F.Cu north → D3.pad2
# D2: B.Cu north col at x=16.6 (avoids IO0 F.Cu at y=46)
T(16.6, 48.5, 16.6, 43.0, B_CU, "/USB_5V", WP)     # B.Cu north
V(16.6, 43.0, "/USB_5V")
T(16.6, 43.0, 18.65, 43.0, F_CU, "/USB_5V", WP)    # F.Cu east → D2.pad2
# U4.pad8 (10.455,29.905): via on J1 pad, B.Cu west, south to y=31, F.Cu north → pad8.
# The two VBUS branches are bridged on F.Cu at y=37 (below USB_D+ end y=36.25 — different y ✓,
# below USB_D- end y=34.98 — different y ✓, different layer for any B.Cu conflicts ✓).
V(10.45, 7.955, "/USB_5V")
T(10.45, 7.955, 9.2, 7.955, B_CU, "/USB_5V", WP)   # B.Cu west (clear of USB_D- via at x=8.5; gap=0.45mm ✓)
T(9.2, 7.955, 9.2, 31.0, B_CU, "/USB_5V", WP)      # B.Cu south at x=9.2
V(9.2, 31.0, "/USB_5V")
T(9.2, 31.0, 9.2, 29.905, F_CU, "/USB_5V", WP)     # F.Cu north stub
T(9.2, 29.905, 10.455, 29.905, F_CU, "/USB_5V", WP) # east → U4.pad8
# Bridge branch 1 (x=5.90) to branch 2 (x=9.2) at y=37 on F.Cu (USB_D+ B.Cu ends y=36.25, USB_D- B.Cu ends y=34.98 — both below y=37 on B.Cu ✓)
T(9.2, 31.0, 9.2, 37.0, B_CU, "/USB_5V", WP)       # B.Cu south extension
V(9.2, 37.0, "/USB_5V")
V(6.0, 37.0, "/USB_5V")
T(6.0, 37.0, 9.2, 37.0, F_CU, "/USB_5V", WP)       # F.Cu bridge (USB_D+ F.Cu east at y=36.25 ≠ y=37 ✓)

# =============================================================================
# 3V3
# Main bus F.Cu y=34.05 from U3.pad5 east to x=62.05 (stops before U2 body)
# Jog north at x=62.05 to y=32.0, east to x=69.5, south to U2.pad14 (70.862,34.025)
# C6/C7 south stubs at x=62.05
# R8.pad1 tap, R1/R2 pullup bridge, ESP32 VCC (all unchanged from v4)
# R9.pad1 tap: west branch at y=19.5 from via (17.7,19.5), south to (15.087,24)
# =============================================================================
# Main bus (shortened to x=60.0 to clear AOUT2 via area)
T(9.137, 34.05, 60.0, 34.05, F_CU, "/3V3", W3)

# C6 and C7 stubs: tap from y=30 north bus at x=62.05 (avoids motor via area at y=34.05)
V(62.05, 30.0, "/3V3")
T(62.05, 30.0, 62.05, 38.0, B_CU, "/3V3", W3)   # B.Cu south → C6.pad1
V(62.05, 38.0, "/3V3")
T(62.05, 38.0, 62.05, 42.0, B_CU, "/3V3", W3)   # through y=42
V(62.05, 42.0, "/3V3")
# V(62.05,42) via already lands on C7.pad1 at (62.05,42) — no west track needed

# Detour to U2.pad14 (70.862,34.025): north at x=54, east at y=30, south at x=73.5, west to pad14.
# Avoids U2.pad3 GND at (65.138,34.025) which sits on the direct F.Cu east path.
# x=54 is 1mm west of DRV_SLEEP col x=55; y=30 is clear of USB_5V bus (ends x=20.5).
T(54.0, 34.05, 54.0, 30.0, F_CU, "/3V3", W3)
T(54.0, 30.0, 73.5, 30.0, F_CU, "/3V3", W3)
T(73.5, 30.0, 73.5, 34.025, F_CU, "/3V3", W3)
T(73.5, 34.025, 70.862, 34.025, F_CU, "/3V3", W3)  # → U2.pad14

# C2 bypass (C2.pad1 at (11.05,35.0))
# B.Cu to avoid crossing USB_D- F.Cu east at y=33.0 (x=10.0→21.25)
V(11.05, 34.05, "/3V3")
T(11.05, 34.05, 11.05, 35.0, B_CU, "/3V3", W3)     # B.Cu direct (hole-to-hole: 0.95mm > 0.25mm min ✓)
V(11.05, 35.0, "/3V3")                              # via on C2.pad1

# MK1 VDD (MK1.pad4 at (28.95,47.0))
# Use x=17.7 B.Cu col (already present) — eliminates V(18.0,34.05) via too close to V(17.7,34.05).
# Extend B.Cu south from y=44 to y=52, east to x=32.5, F.Cu north to y=46.5
# (above MK1.pad3 GND at y=47.0 — pad3 top edge ≈46.65; y=46.5 track top 46.35 → gap 0.3mm ✓)
# x=32.5 clears I2S_SD F.Cu stub at x=31.05 right edge 31.15 (gap 1.2mm ✓)
# x=32.5 clears MK1.pad3 right edge ≈31.55 (gap 0.8mm ✓)

# ESP32 VCC: B.Cu bridge at x=17.7 north to y=19.5, F.Cu east to U1.pad2
T(17.7, 19.5, 20.0, 19.5, F_CU, "/3V3", W3)
T(20.0, 19.5, 20.0, 21.01, F_CU, "/3V3", W3)
T(20.0, 21.01, 21.25, 21.01, F_CU, "/3V3", W3)   # → U1.pad2

# R9.pad1 (15.087,24): west branch from via (17.7,19.5)
T(17.7, 19.5, 15.087, 19.5, F_CU, "/3V3", W3)    # west
T(15.087, 19.5, 15.087, 24.0, F_CU, "/3V3", W3)  # south → R9.pad1

# R8.pad1 (17.087,28): R8 at x=18.0; tap via on 3V3 B.Cu col at (17.7,28), F.Cu west to pad1
V(17.7, 28.0, "/3V3")
T(17.7, 28.0, 17.087, 28.0, F_CU, "/3V3", W3)     # F.Cu west → R8.pad1 center

# R1.pad1 (17.087,45) and R2.pad1 (21.087,45): B.Cu bridge at x=17.7 south
# Tap at y=42 to avoid R1.pad2(EN) at (18.913,45) — gap at y=44 was 0.15mm < 0.2mm
V(17.7, 34.05, "/3V3")
T(17.7, 34.05, 17.7, 19.5, B_CU, "/3V3", W3)     # north bridge
V(17.7, 19.5, "/3V3")
T(17.7, 34.05, 17.7, 52.0, B_CU, "/3V3", W3)     # south (single segment; tap via at y=42 below)
V(17.7, 42.0, "/3V3")                             # tap at y=42
# R1.pad1 (17.087,45): B.Cu south to avoid crossing USB_5V F.Cu at y=43 (x=16.6-18.65)
V(17.087, 42.0, "/3V3")                           # via at x=17.087 (hole-to-hole: 0.613mm > 0.549mm ✓)
T(17.087, 42.0, 17.087, 45.0, B_CU, "/3V3", W3)  # B.Cu south (avoids USB_5V F.Cu east at y=43 ✓)
V(17.087, 45.0, "/3V3")                           # via on R1.pad1
T(17.7, 42.0, 20.0, 42.0, F_CU, "/3V3", W3)      # F.Cu east to x=20
T(20.0, 42.0, 20.0, 45.0, F_CU, "/3V3", W3)      # south at x=20 (EN at 18.913 → gap=0.54mm ✓)
T(20.0, 45.0, 21.087, 45.0, F_CU, "/3V3", W3)    # east → R2.pad1
# MK1 VDD: B.Cu south in T above (y=34.05→52), tap at y=47 (below)
# MK1 VDD: B.Cu east at y=47 (clear of I2S_WS at y=48.6, I2S_SCK at y=45.4, STATUS_LED at x=31.7 ✓)
V(17.7, 47.0, "/3V3")
T(17.7, 47.0, 28.95, 47.0, B_CU, "/3V3", W3)     # B.Cu east → MK1.pad4
V(28.95, 47.0, "/3V3")                            # via on MK1.pad4

# =============================================================================
# Motor control signals: U1 left pads → B.Cu east → U2 right pads
# Column x in REVERSE order vs U1 pad y → zero B.Cu crossings.
# 0.8mm col spacing avoids via-to-track clearance violations (via r=0.3mm).
# Cols: LEFT_IN1=68.9, LEFT_IN2=68.1, RIGHT_IN1=67.3, RIGHT_IN2=66.5
# All ≤69.1mm (J4.pad1 copper edge at 69.4mm; gap at x=68.9: 0.4mm ✓)
# =============================================================================
# LEFT_IN1: U1.pad4 (21.25,23.55) → U2.pad16 (70.862,32.725)
T(21.25, 23.55, 20.0, 23.55, F_CU, "/LEFT_IN1", W)
V(20.0, 23.55, "/LEFT_IN1")
T(20.0, 23.55, 68.9, 23.55, B_CU, "/LEFT_IN1", W)
T(68.9, 23.55, 68.9, 32.725, B_CU, "/LEFT_IN1", W)
V(68.9, 32.725, "/LEFT_IN1")
T(68.9, 32.725, 70.862, 32.725, F_CU, "/LEFT_IN1", W)  # → pad16

# LEFT_IN2: U1.pad5 (21.25,24.82) → U2.pad15 (70.862,33.375)
T(21.25, 24.82, 20.0, 24.82, F_CU, "/LEFT_IN2", W)
V(20.0, 24.82, "/LEFT_IN2")
T(20.0, 24.82, 68.1, 24.82, B_CU, "/LEFT_IN2", W)
T(68.1, 24.82, 68.1, 33.375, B_CU, "/LEFT_IN2", W)
V(68.1, 33.375, "/LEFT_IN2")
T(68.1, 33.375, 70.862, 33.375, F_CU, "/LEFT_IN2", W)  # → pad15

# RIGHT_IN1: U1.pad6 (21.25,26.09) → U2.pad9 (70.862,37.275)
T(21.25, 26.09, 20.0, 26.09, F_CU, "/RIGHT_IN1", W)
V(20.0, 26.09, "/RIGHT_IN1")
T(20.0, 26.09, 67.3, 26.09, B_CU, "/RIGHT_IN1", W)
T(67.3, 26.09, 67.3, 37.275, B_CU, "/RIGHT_IN1", W)
V(67.3, 37.275, "/RIGHT_IN1")
T(67.3, 37.275, 70.862, 37.275, F_CU, "/RIGHT_IN1", W)  # → pad9

# RIGHT_IN2: U1.pad7 (21.25,27.36) → U2.pad10 (70.862,36.625)
# Via moved to x=21.5 (R8.pad2 at 19.913,28 → dist=1.71mm, gap=0.91mm ✓; DRV_SLEEP via at 21.5,28.63 → gap=0.67mm ✓)
T(21.25, 27.36, 21.5, 27.36, F_CU, "/RIGHT_IN2", W)
V(21.5, 27.36, "/RIGHT_IN2")
T(21.5, 27.36, 66.5, 27.36, B_CU, "/RIGHT_IN2", W)
T(66.5, 27.36, 66.5, 36.625, B_CU, "/RIGHT_IN2", W)
V(66.5, 36.625, "/RIGHT_IN2")
T(66.5, 36.625, 70.862, 36.625, F_CU, "/RIGHT_IN2", W)  # → pad10

# DRV_SLEEP: U1.pad8 (21.25,28.63) → U2.pad1 (65.138,32.725)
# B.Cu south to y=50 (below I2S_WS/SCK, IO0, STATUS_LED verticals),
# east to x=55, north to y=31.5, via, F.Cu east at y=31.5, south stub to pad1.
# x=55 avoids motor output south columns (BOUT1 at x=57, AOUT2 at x=60, AOUT1 at x=61.5, BOUT2 at x=67)
T(21.25, 28.63, 21.5, 28.63, F_CU, "/DRV_SLEEP", W)
V(21.5, 28.63, "/DRV_SLEEP")
T(21.5, 28.63, 21.5, 50.0, B_CU, "/DRV_SLEEP", W)    # south (clear of I2S/IO0 which go to y≤48.6)
T(21.5, 50.0, 55.0, 50.0, B_CU, "/DRV_SLEEP", W)     # east to x=55
T(55.0, 50.0, 55.0, 31.5, B_CU, "/DRV_SLEEP", W)     # north (x=55 west of all motor south columns)
V(55.0, 31.5, "/DRV_SLEEP")
T(55.0, 31.5, 65.138, 31.5, F_CU, "/DRV_SLEEP", W)   # east at y=31.5 (above 3V3 bus at y=34.05)
T(65.138, 31.5, 65.138, 32.725, F_CU, "/DRV_SLEEP", W)  # south stub → U2.pad1

# =============================================================================
# Motor outputs — south-east-north detour
# All east buses at y≥44 to clear: motor control cols (end y≤37.3), C6/C7 B.Cu (end y=42),
#   VBAT B.Cu col (y=18→42), I2S/IO0 verticals (x=23-39, all west of south columns x≥57)
# Column x: AOUT1=73, AOUT2=74.5, BOUT2=77.5, BOUT1=79 (VBAT B.Cu at x=76 between BOUT2/BOUT1)
# F.Cu approaches: AOUT1 y=21, AOUT2 y=19 (different y to avoid crossing)
# BOUT2 exits west to x=58.5 so its B.Cu south col doesn't cross AOUT1 east at y=44
# =============================================================================
# AOUT1: U2.pad2 (65.138,33.375) → J3.pad1 (70,20)
# Via at x=64 (stub stays x>62.05 so no overlap with 3V3 F.Cu bus).
# B.Cu south col x=64 clears 3V3 B.Cu at x=62.05 by 1.95mm.
# F.Cu approach at y=23 separates from AOUT2 at y=19 (4mm gap).
T(65.138, 33.375, 64.0, 33.375, F_CU, "/AOUT1", W)    # short W stub (x≥62.05 ✓)
V(64.0, 33.375, "/AOUT1", drill=0.4, size=0.8)
T(64.0, 33.375, 64.0, 44.0, B_CU, "/AOUT1", WM)      # south to y=44
T(64.0, 44.0, 73.5, 44.0, B_CU, "/AOUT1", WM)        # east at y=44 to x=73.5
T(73.5, 44.0, 73.5, 23.0, B_CU, "/AOUT1", WM)        # north col x=73.5 (J4.pad2 copper edge=72.6; gap=73.0-72.6=0.4mm ✓)
V(73.5, 23.0, "/AOUT1", drill=0.4, size=0.8)
T(73.5, 23.0, 70.0, 23.0, F_CU, "/AOUT1", WM)        # west at y=23
T(70.0, 23.0, 70.0, 20.0, F_CU, "/AOUT1", WM)        # south → J3.pad1

# AOUT2: U2.pad4 (65.138,34.675) → J3.pad2 (72,20)
# Via at x=62.0 (3V3 bus ends x=60.0 → dist=2.1mm, gap=1.55mm ✓; BOUT2 via at (58.5,35.325) → gap=2.76mm ✓)
T(65.138, 34.675, 62.0, 34.675, F_CU, "/AOUT2", W)   # W stub (BOUT2 via at y=35.325: gap=0.45mm ✓)
V(62.0, 34.675, "/AOUT2", drill=0.4, size=0.8)
T(62.0, 34.675, 62.0, 45.2, B_CU, "/AOUT2", WM)     # south (AOUT1 at x=64: gap=1.0mm ✓)
T(62.0, 45.2, 75.0, 45.2, B_CU, "/AOUT2", WM)       # east at y=45.2
T(75.0, 45.2, 75.0, 19.0, B_CU, "/AOUT2", WM)       # north to y=19 (stops above VBAT y=18)
V(75.0, 19.0, "/AOUT2", drill=0.4, size=0.8)
T(75.0, 19.0, 72.0, 19.0, F_CU, "/AOUT2", WM)       # west at y=19 (≠ AOUT1 y=21 ✓)
T(72.0, 19.0, 72.0, 20.0, F_CU, "/AOUT2", WM)       # → J3.pad2

# BOUT2: U2.pad5 (65.138,35.325) → J4.pad2 (72,28)
# Via at x=58.5 (AOUT2 via now at (62.0,34.675) → dist=3.56mm, gap=2.76mm ✓)
T(65.138, 35.325, 58.5, 35.325, F_CU, "/BOUT2", W)   # W stub to x=58.5
V(58.5, 35.325, "/BOUT2", drill=0.4, size=0.8)
T(58.5, 35.325, 58.5, 46.5, B_CU, "/BOUT2", WM)     # south to y=46.5
T(58.5, 46.5, 77.5, 46.5, B_CU, "/BOUT2", WM)       # east at y=46.5
T(77.5, 46.5, 77.5, 27.0, B_CU, "/BOUT2", WM)       # north to y=27 (x=77.5 east of VBAT x=76)
V(77.5, 27.0, "/BOUT2", drill=0.4, size=0.8)
T(77.5, 27.0, 72.0, 27.0, F_CU, "/BOUT2", WM)       # west at y=27
T(72.0, 27.0, 72.0, 28.0, F_CU, "/BOUT2", WM)       # → J4.pad2

# BOUT1: U2.pad7 (65.138,36.625) → J4.pad1 (70,28)
T(65.138, 36.625, 57.0, 36.625, F_CU, "/BOUT1", W)   # W stub to x=57 (2mm east of DRV_SLEEP col x=55)
V(57.0, 36.625, "/BOUT1", drill=0.4, size=0.8)
T(57.0, 36.625, 57.0, 47.7, B_CU, "/BOUT1", WM)    # south to y=47.7
T(57.0, 47.7, 79.0, 47.7, B_CU, "/BOUT1", WM)      # east at y=47.7 (board edge x=80 ✓)
T(79.0, 47.7, 79.0, 25.5, B_CU, "/BOUT1", WM)      # north to y=25.5
V(79.0, 25.5, "/BOUT1", drill=0.4, size=0.8)
T(79.0, 25.5, 70.0, 25.5, F_CU, "/BOUT1", WM)      # west at y=25.5
T(70.0, 25.5, 70.0, 28.0, F_CU, "/BOUT1", WM)      # → J4.pad1

# =============================================================================
# I2S signals (unchanged)
# =============================================================================
V(23.015, 37.5, "/I2S_WS")
T(23.015, 37.5, 23.015, 48.6, B_CU, "/I2S_WS", W)
T(23.015, 48.6, 28.95, 48.6, B_CU, "/I2S_WS", W)
V(28.95, 48.6, "/I2S_WS")

V(24.285, 37.5, "/I2S_SCK")
T(24.285, 37.5, 24.285, 45.4, B_CU, "/I2S_SCK", W)
T(24.285, 45.4, 31.05, 45.4, B_CU, "/I2S_SCK", W)
V(31.05, 45.4, "/I2S_SCK")

T(25.555, 37.5, 25.555, 49.5, F_CU, "/I2S_SD", W)
T(25.555, 49.5, 31.05, 49.5, F_CU, "/I2S_SD", W)
T(31.05, 49.5, 31.05, 48.6, F_CU, "/I2S_SD", W)

# =============================================================================
# USB D+/D-
# J1.A6(USB_D+)=(7.75,7.955), J1.A7(USB_D-)=(8.25,7.955)
# D+: F.Cu south to y=14, B.Cu south at x=7.75 to y=40 (below U3 bottom ~y=36.4),
#     via at (7.75,40), F.Cu east to x=10.4, F.Cu north to y=36.25, F.Cu east → U1.pad14
# D-: F.Cu south to y=15, east jog to x=10.0, via, B.Cu south to y=33.0,
#     via, F.Cu east to (21.25,33.0), F.Cu south → U1.pad13
# J1.B6↔A6 and J1.B7↔A7 not bridged (0.5mm pitch prevents direct short)
# =============================================================================
# USB_D+
T(7.75, 7.955, 7.75, 14.0, F_CU, "/USB_D+", W)      # F.Cu south stub
V(7.75, 14.0, "/USB_D+", drill=0.3, size=0.5)
T(7.75, 14.0, 7.75, 40.0, B_CU, "/USB_D+", W)       # B.Cu south (clears U3 bottom ≈36.4, USB_5V bridge at y=37 ✓)
V(7.75, 40.0, "/USB_D+", drill=0.3, size=0.5)        # transition via (VBAT B.Cu x=6.862 → gap=0.34mm ✓)
T(7.75, 40.0, 10.4, 40.0, F_CU, "/USB_D+", W)        # F.Cu east (U3 right=9.587 → gap=0.71mm ✓)
T(10.4, 40.0, 10.4, 36.25, F_CU, "/USB_D+", W)       # F.Cu north (C2 via x=11.05 → gap=0.25mm ✓)
T(10.4, 36.25, 21.25, 36.25, F_CU, "/USB_D+", W)     # F.Cu east → U1.pad14

# USB_D-
T(8.25, 7.955, 8.25, 15.0, F_CU, "/USB_D-", W)       # F.Cu south stub
T(8.25, 15.0, 10.0, 15.0, F_CU, "/USB_D-", W)        # F.Cu east jog (B.Cu later at x=10.0 clears USB_5V B.Cu at x=9.2 ✓)
V(10.0, 15.0, "/USB_D-", drill=0.3, size=0.5)
T(10.0, 15.0, 10.0, 33.0, B_CU, "/USB_D-", W)        # B.Cu south (USB_5V x=9.2 → gap=0.45mm ✓; U3 clears ✓)
V(10.0, 33.0, "/USB_D-", drill=0.3, size=0.5)         # transition via (U3.pad5 gap=0.62mm ✓)
T(10.0, 33.0, 21.25, 33.0, F_CU, "/USB_D-", W)        # F.Cu east (3V3 via at (17.7,34.05): gap=0.65mm ✓)
T(21.25, 33.0, 21.25, 34.98, F_CU, "/USB_D-", W)      # F.Cu south → U1.pad13

# =============================================================================
# CC1 / CC2 (unchanged)
# =============================================================================
T(6.75, 7.955, 6.75, 20.0, F_CU, "/CC1", W)
T(6.75, 20.0, 7.088, 20.0, F_CU, "/CC1", W)
T(9.75, 7.955, 9.75, 20.0, F_CU, "/CC2", W)
T(9.75, 20.0, 11.088, 20.0, F_CU, "/CC2", W)

# =============================================================================
# EN: U1.pad3 (21.25,22.28) → R1.pad2 (18.913,45)
# =============================================================================
T(21.25, 22.28, 21.5, 22.28, F_CU, "/EN", W)
V(21.5, 22.28, "/EN")
T(21.5, 22.28, 18.913, 22.28, B_CU, "/EN", W)
T(18.913, 22.28, 18.913, 45.0, B_CU, "/EN", W)
V(18.913, 45.0, "/EN")

# =============================================================================
# IO0: U1.pad27 (38.75,36.25) → R2.pad2 (22.913,45) + SW1.pad1 (4.9,43.15)
# =============================================================================
V(38.75, 36.25, "/IO0")
T(38.75, 36.25, 38.75, 46.0, B_CU, "/IO0", W)
T(38.75, 46.0, 23.7, 46.0, B_CU, "/IO0", W)
V(23.7, 46.0, "/IO0")
T(23.7, 46.0, 22.913, 46.0, F_CU, "/IO0", W)
T(22.913, 46.0, 22.913, 45.0, F_CU, "/IO0", W)   # → R2.pad2
T(23.7, 46.0, 4.9, 46.0, F_CU, "/IO0", W)
T(4.9, 46.0, 4.9, 43.15, F_CU, "/IO0", W)        # → SW1.pad1

# =============================================================================
# STATUS_LED: U1.pad18 (26.825,37.5) → R3.pad1 (21.087,42)
# Cannot use x=21.087 for the north col: 3V3 east ends at (21.087,44) and
# IO0 west spans x=4.9→23.7 at y=46, both crossing a north col at x=21.087.
# Fix: F.Cu south stub to y=38.5, east to x=32, south to y=53, west to x=24,
# north at x=24 to y=43 (x=24 > IO0 west end x=23.7 → no IO0 crossing ✓,
# 3V3 east ends x=21.087 << 24 → no 3V3 crossing ✓),
# west at y=43 to x=21.087, short south to y=42 → R3.pad1.
# =============================================================================
T(26.825, 37.5, 26.825, 39.0, F_CU, "/STATUS_LED", W)   # south stub
T(26.825, 39.0, 31.7, 39.0, F_CU, "/STATUS_LED", W)     # east to x=31.7 (I2S_SCK via at 31.05 → gap=0.25mm ✓)
T(31.7, 39.0, 31.7, 53.0, F_CU, "/STATUS_LED", W)       # south at x=31.7
T(31.7, 53.0, 24.9, 53.0, F_CU, "/STATUS_LED", W)       # west to x=24.9
T(24.9, 53.0, 24.9, 43.0, F_CU, "/STATUS_LED", W)       # north at x=24.9 (IO0 via right edge=24.0 → gap 0.8mm ✓;
                                                          #   I2S_SCK via at y=37.5 is above north col range y=43-53 ✓)
T(24.9, 43.0, 21.087, 43.0, F_CU, "/STATUS_LED", W)     # west at y=43
T(21.087, 43.0, 21.087, 42.0, F_CU, "/STATUS_LED", W)   # south stub → R3.pad1 (SMD on F.Cu; no via needed)

# LED_ANODE: R3.pad2 (22.913,42) → D1.padA (18.938,41)  [D1 moved to y=41]
# Route at y=41: jog north from R3.pad2, then west to D1.padA.
# Avoids STATUS_LED via at (21.087,42) — via top edge at y=41.7, track bottom at y=40.9 ✓
T(22.913, 42.0, 22.913, 41.0, F_CU, "/LED_ANODE", W)   # north to y=41
T(22.913, 41.0, 18.938, 41.0, F_CU, "/LED_ANODE", W)   # west → D1.padA

# =============================================================================
# TP4056 indicator signals
# R6/R7 unchanged. R8/R10 unchanged. R9 now at (16,24), R11 at (16,30).
# D4 now at (18,38.5): padA=(18.938,38.5)
# D5 now at (16,33):   padA=(16.913,33)
# =============================================================================
# TP_PROG: U4.pad2 (5.545,28.635) → R6.pad1 (14.088,28) — F.Cu direct
T(5.545, 28.635, 5.545, 28.0, F_CU, "/TP_PROG", W)
T(5.545, 28.0, 14.088, 28.0, F_CU, "/TP_PROG", W)

# TP_TEMP: U4.pad1 (5.545,29.905) → R7.pad1 (14.088,32)
T(5.545, 29.905, 5.545, 32.0, F_CU, "/TP_TEMP", W)
T(5.545, 32.0, 14.088, 32.0, F_CU, "/TP_TEMP", W)

# TP_CHRG: U4.pad6 (10.455,27.365) → R8.pad2 (18.913,28) → R10.pad1 (17.087,32)
# R8 at x=18.0: pad1=(17.087,28), pad2=(18.913,28). R10 at x=18.0: pad1=(17.087,32).
T(10.455, 27.365, 12.8, 27.365, F_CU, "/TP_CHRG", W)
T(12.8, 27.365, 12.8, 27.0, F_CU, "/TP_CHRG", W)
V(12.8, 27.0, "/TP_CHRG")
T(12.8, 27.0, 12.8, 25.2, B_CU, "/TP_CHRG", W)
V(12.8, 25.2, "/TP_CHRG")
T(12.8, 25.2, 19.0, 25.2, F_CU, "/TP_CHRG", W)     # east to x=19.0 (inside R8 pads 17.087-18.913 ✓)
T(19.0, 25.2, 19.0, 28.0, F_CU, "/TP_CHRG", W)     # south to R8.pad row
T(19.0, 28.0, 18.913, 28.0, F_CU, "/TP_CHRG", W)   # west → R8.pad2 (now at x=18.913)
# South to R10.pad1: via x=18.913 south, west to R10.pad1 at (17.087,32)
# EN B.Cu at x=18.913 is B.Cu layer — F.Cu south at same x has no conflict ✓
T(18.913, 28.0, 18.913, 30.5, F_CU, "/TP_CHRG", W) # south
T(18.913, 30.5, 17.087, 30.5, F_CU, "/TP_CHRG", W) # west (3V3 via at (17.7,28): gap=2.05mm ✓)
T(17.087, 30.5, 17.087, 32.0, F_CU, "/TP_CHRG", W) # south → R10.pad1

# TP_STDBY: U4.pad7 (10.455,28.635) → R9.pad2 (16.913,24) → R11.pad1 (15.087,30)
# Exit east on F.Cu to x=11.5 (avoids USB_5V B.Cu at x=10.45), via to B.Cu.
# B.Cu east at y=28.635 to x=16, north to y=24, via, F.Cu → R9.pad2.
# Then B.Cu south at x=16 to y=30, west to x=14.6 (clears R11.pad2 at 16.913), via, F.Cu → R11.pad1.
# TP_STDBY: single B.Cu col at x=16.913 (eliminates hole_to_hole violation)
T(10.455, 28.635, 11.5, 28.635, F_CU, "/TP_STDBY", W)  # F.Cu east
V(11.5, 28.635, "/TP_STDBY")
T(11.5, 28.635, 16.913, 28.635, B_CU, "/TP_STDBY", W)  # B.Cu east (3V3 via at 17.7,28: y-dist only ✓)
T(16.913, 28.635, 16.913, 24.0, B_CU, "/TP_STDBY", W)  # B.Cu north (R9.pad1 at 15.087,24 → gap=0.98mm ✓)
V(16.913, 24.0, "/TP_STDBY")                            # single via on R9.pad2 (no hole_to_hole issue ✓)
T(16.913, 24.0, 16.913, 29.0, B_CU, "/TP_STDBY", W)    # B.Cu south (stops before R11.pad2 at y=30 ✓)
T(16.913, 29.0, 14.6, 29.0, B_CU, "/TP_STDBY", W)      # west (STDBY_LED B.Cu at x=16.913 starts y=30.5 → gap ✓)
V(14.6, 29.0, "/TP_STDBY")
T(14.6, 29.0, 15.087, 29.0, F_CU, "/TP_STDBY", W)      # east
T(15.087, 29.0, 15.087, 30.0, F_CU, "/TP_STDBY", W)    # south → R11.pad1

# CHRG_LED: R10.pad2 (18.913,32) → D4.padA (18.938,38.5)
# Exit F.Cu east from R10.pad2 to x=19.6 (EN B.Cu at x=18.913: gap=0.487mm ✓)
# via at (19.6,32), B.Cu south to y=38.5, via, F.Cu west → D4.padA
T(18.913, 32.0, 19.6, 32.0, F_CU, "/CHRG_LED", W)    # F.Cu east stub (EN is B.Cu only ✓)
V(19.6, 32.0, "/CHRG_LED")
T(19.6, 32.0, 19.6, 38.5, B_CU, "/CHRG_LED", W)     # B.Cu south (EN B.Cu x=18.913 → gap=0.487mm ✓)
V(19.6, 38.5, "/CHRG_LED")
T(19.6, 38.5, 18.938, 38.5, F_CU, "/CHRG_LED", W)   # F.Cu west → D4.padA

# STDBY_LED: R11.pad2 (16.913,30) → D5.padA (15.413,40.0) [D5 at x=14.5]
# B.Cu south at x=16.913 (avoids all F.Cu crossings, USB_D- F.Cu at y=33 etc.)
T(16.913, 30.0, 16.913, 30.5, F_CU, "/STDBY_LED", W)  # short F.Cu south stub
V(16.913, 30.5, "/STDBY_LED")
T(16.913, 30.5, 16.913, 40.0, B_CU, "/STDBY_LED", W)  # B.Cu south (TP_STDBY B.Cu ends y=29.0; gap=1.3mm ✓)
V(16.913, 40.0, "/STDBY_LED")
T(16.913, 40.0, 15.413, 40.0, F_CU, "/STDBY_LED", W)  # F.Cu west → D5.padA

# =============================================================================
# Zone fill (GND zones already defined in the board file)
# =============================================================================
print("Running zone fill...")
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())

board.Save(PCB_OUT)
print(f"Saved: {PCB_OUT}")
print("Done — run kicad-cli pcb drc to verify")
