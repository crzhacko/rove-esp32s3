#!/usr/bin/env python3
"""
ROVE-V: Add battery protection circuit to PCB (text-file approach)
Adds:
  U5  DW01A    SOT-23-6  at (12, 58)
  Q1  FS8205A  SOT-23-6  at (22, 58)
  R6  100k     0402      at (30, 52)  — VBAT divider high
  R7  47k      0402      at (30, 58)  — VBAT divider low
New nets:
  /BATT_NEG  (32)  — J2 pin2, FS8205A.D1
  /DW01_OD   (31)  — DW01A.OD, FS8205A.G1
  /DW01_OC   (33)  — DW01A.OC, FS8205A.G2
  /PROT_CS   (34)  — DW01A.CS, FS8205A.S/B
  /VBAT_MON  (35)  — R6–R7 junction → ESP32 ADC
Updates:
  J2 pad 2: GND → /BATT_NEG  (battery – through protection FETs)
  Remove stale TP4056 net entries (25-30)
"""
import os, re, uuid, shutil

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__),
                       "../electronics/rove_v/rove_v.kicad_pcb"))

def uid(): return str(uuid.uuid4())

# ── net definitions to add ────────────────────────────────────────────────────
NEW_NETS = {
    31: "/DW01_OD",
    32: "/BATT_NEG",
    33: "/DW01_OC",
    34: "/PROT_CS",
    35: "/VBAT_MON",
}

# ── SOT-23-6 pad template ─────────────────────────────────────────────────────
# Pin layout (KiCad Y-down):
#   Left col  x=-0.95:  pad1(y=+1.30), pad2(y=0.00), pad3(y=-1.30)
#   Right col x=+0.95:  pad4(y=-1.30), pad5(y=0.00), pad6(y=+1.30)

def sot23_6_fp(ref, value, x, y, pad_nets):
    """
    pad_nets: dict {pad_str: (net_num, net_name)} or {pad_str: None} for NC
    """
    pad_positions = {
        "1": (-0.95,  1.30),
        "2": (-0.95,  0.00),
        "3": (-0.95, -1.30),
        "4": ( 0.95, -1.30),
        "5": ( 0.95,  0.00),
        "6": ( 0.95,  1.30),
    }
    pad_size = (0.60, 1.10)
    pads = ""
    for p, (px, py) in pad_positions.items():
        net_part = ""
        if pad_nets.get(p):
            nn, nm = pad_nets[p]
            net_part = f'\n\t\t\t(net {nn} "{nm}")'
        pads += f"""\t\t(pad "{p}" smd rect
\t\t\t(at {px} {py})
\t\t\t(size {pad_size[0]} {pad_size[1]})
\t\t\t(layers "F.Cu" "F.Paste" "F.Mask"){net_part}
\t\t\t(uuid "{uid()}")
\t\t)\n"""

    return f"""\t(footprint "Package_TO_SOT_SMD:SOT-23-6"
\t\t(layer "F.Cu")
\t\t(uuid "{uid()}")
\t\t(at {x} {y})
\t\t(descr "Battery protection SOT-23-6")
\t\t(property "Reference" "{ref}"
\t\t\t(at 0 -2.5 0)
\t\t\t(layer "F.SilkS")
\t\t\t(uuid "{uid()}")
\t\t\t(effects (font (size 1 1) (thickness 0.15)))
\t\t)
\t\t(property "Value" "{value}"
\t\t\t(at 0 2.5 0)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{uid()}")
\t\t\t(effects (font (size 1 1) (thickness 0.15)))
\t\t)
\t\t(fp_rect
\t\t\t(start -1.6 -1.9)
\t\t\t(end 1.6 1.9)
\t\t\t(stroke (width 0.05) (type default))
\t\t\t(layer "F.CrtYd")
\t\t\t(uuid "{uid()}")
\t\t)
{pads}\t)\n"""

# ── 0402 pad template ─────────────────────────────────────────────────────────

def r0402_fp(ref, value, x, y, net1, net2):
    """
    net1: (num, name) for pad "1" (left at -0.925, 0)
    net2: (num, name) for pad "2" (right at +0.925, 0)
    """
    def net_str(n): return f'\n\t\t\t(net {n[0]} "{n[1]}")' if n else ""
    return f"""\t(footprint "Resistor_SMD:R_0402_1005Metric"
\t\t(layer "F.Cu")
\t\t(uuid "{uid()}")
\t\t(at {x} {y})
\t\t(descr "Resistor 0402")
\t\t(property "Reference" "{ref}"
\t\t\t(at 0 -1.2 0)
\t\t\t(layer "F.SilkS")
\t\t\t(uuid "{uid()}")
\t\t\t(effects (font (size 0.6 0.6) (thickness 0.1)))
\t\t)
\t\t(property "Value" "{value}"
\t\t\t(at 0 1.2 0)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{uid()}")
\t\t\t(effects (font (size 0.6 0.6) (thickness 0.1)))
\t\t)
\t\t(fp_rect
\t\t\t(start -1.0 -0.65)
\t\t\t(end 1.0 0.65)
\t\t\t(stroke (width 0.05) (type default))
\t\t\t(layer "F.CrtYd")
\t\t\t(uuid "{uid()}")
\t\t)
\t\t(pad "1" smd rect
\t\t\t(at -0.925 0)
\t\t\t(size 0.6 0.5){net_str(net1)}
\t\t\t(layers "F.Cu" "F.Paste" "F.Mask")
\t\t\t(uuid "{uid()}")
\t\t)
\t\t(pad "2" smd rect
\t\t\t(at 0.925 0)
\t\t\t(size 0.6 0.5){net_str(net2)}
\t\t\t(layers "F.Cu" "F.Paste" "F.Mask")
\t\t\t(uuid "{uid()}")
\t\t)
\t)\n"""

# ── build new footprints ──────────────────────────────────────────────────────

# Protection circuit topology:
# BATT_NEG (J2-) → FS8205A.D1 → FS8205A.S/B (PROT_CS) → FS8205A.D2 → GND
# DW01A.OD → FS8205A.G1 (overdischarge FET gate)
# DW01A.OC → FS8205A.G2 (overcharge FET gate)
# DW01A.CS = PROT_CS
# DW01A.VDD = VBAT, DW01A.GND = GND

DW01A_NETS = {
    "1": (31, "/DW01_OD"),   # OD output
    "2": (34, "/PROT_CS"),   # CS (current sense)
    "3": (33, "/DW01_OC"),   # OC output
    "4": (4,  "/VBAT"),      # VDD → VBAT
    "5": (1,  "GND"),        # GND
    "6": None,               # TM → no connect
}

FS8205A_NETS = {
    "1": (31, "/DW01_OD"),   # G1 (discharge gate)
    "2": (34, "/PROT_CS"),   # S/B (common source = CS node)
    "3": (33, "/DW01_OC"),   # G2 (charge gate)
    "4": (32, "/BATT_NEG"),  # D1 (battery negative input)
    "5": (1,  "GND"),        # D2 (system ground output)
    "6": (34, "/PROT_CS"),   # S/B (same as pad 2, common source)
}

U5_FP  = sot23_6_fp("U5", "DW01A",   12, 58, DW01A_NETS)
Q1_FP  = sot23_6_fp("Q1", "FS8205A", 22, 58, FS8205A_NETS)
# R6: VBAT (pad1 left) → VBAT_MON (pad2 right)
R6_FP  = r0402_fp("R6", "100k", 30, 52,
                  net1=(4, "/VBAT"), net2=(35, "/VBAT_MON"))
# R7: VBAT_MON (pad1 left) → GND (pad2 right)
R7_FP  = r0402_fp("R7", "47k",  30, 58,
                  net1=(35, "/VBAT_MON"), net2=(1, "GND"))

NEW_FOOTPRINTS = U5_FP + Q1_FP + R6_FP + R7_FP

# ── main ─────────────────────────────────────────────────────────────────────

def main():
    bak = PCB + ".bak_pre_prot"
    if not os.path.exists(bak):
        shutil.copy2(PCB, bak)

    with open(PCB) as f:
        content = f.read()
        lines = content.splitlines(keepends=True)

    # 1. Remove stale TP4056 nets (25–30)
    stale = {25, 26, 27, 28, 29, 30}
    new_lines = []
    i = 0
    removed = 0
    while i < len(lines):
        m = re.match(r'\s+\(net (\d+) "([^"]+)"\)', lines[i])
        if m and int(m.group(1)) in stale:
            new_lines.append(f'\t(net {m.group(1)} "")\n')  # blank name = unused
            removed += 1
            i += 1
            continue
        new_lines.append(lines[i])
        i += 1
    print(f"[1] Blanked {removed} stale TP4056 net names")
    lines = new_lines

    # 2. Inject new net entries into net_settings / net table
    # KiCad PCB has individual (net N "name") entries inside footprint pads
    # The top-level net table is separate. Find last net entry and insert after.
    last_net_idx = None
    for i, l in enumerate(lines):
        if re.match(r'\s+\(net \d+ "[^"]*"\)\s*$', l):
            if not any(keyword in l for keyword in ['(pad', '(zone', '(segment', '(via']):
                last_net_idx = i
    if last_net_idx is not None:
        net_entries = [f'\t(net {n} "{nm}")\n' for n, nm in sorted(NEW_NETS.items())]
        lines = lines[:last_net_idx+1] + net_entries + lines[last_net_idx+1:]
        print(f"[2] Added {len(NEW_NETS)} new nets after line {last_net_idx+1}")
    else:
        print("[2] WARNING: Could not find net table insertion point")

    # 3. Update J2 pad 2: GND → /BATT_NEG
    # Find J2 footprint block and change pad "2" net
    content2 = ''.join(lines)
    # Locate J2 footprint block
    j2_match = None
    idx = 0
    fp_starts = [i for i, l in enumerate(lines) if l.strip().startswith('(footprint ')]
    for fp_start in fp_starts:
        depth = 0
        fp_end = fp_start
        for j in range(fp_start, len(lines)):
            depth += lines[j].count('(') - lines[j].count(')')
            if j > fp_start and depth <= 0:
                fp_end = j; break
        block_lines = lines[fp_start:fp_end+1]
        block = ''.join(block_lines)
        if '"Reference" "J2"' in block:
            # Find pad "2" within this block and change its net
            for k in range(fp_start, fp_end+1):
                if '(pad "2"' in lines[k] or ("pad" in lines[k] and '"2"' in lines[k]):
                    # scan ahead for (net N "GND")
                    for m in range(k, min(k+10, fp_end+1)):
                        if re.search(r'\(net \d+ "GND"\)', lines[m]):
                            lines[m] = re.sub(r'\(net \d+ "GND"\)',
                                              '(net 32 "/BATT_NEG")', lines[m])
                            print(f"[3] Updated J2 pad 2: GND → /BATT_NEG at line {m+1}")
                            break
                    break
            break

    # 4. Inject new footprints before closing ')' of board
    for i in range(len(lines)-1, -1, -1):
        if lines[i].strip() == ')':
            lines = lines[:i] + [NEW_FOOTPRINTS] + lines[i:]
            print(f"[4] Injected U5/Q1/R6/R7 footprints before line {i+1}")
            break

    with open(PCB, 'w') as f:
        f.writelines(lines)
    print(f"\nSaved: {PCB}")
    print("""
Protection circuit added to PCB:
  U5  DW01A    (12, 58) — overdischarge/overcurrent IC
  Q1  FS8205A  (22, 58) — dual N-MOSFET switch
  R6  100k     (30, 52) — VBAT divider high → /VBAT_MON
  R7  47k      (30, 58) — VBAT divider low → GND
  J2 pad 2     → /BATT_NEG (battery negative, through FETs)

Next: run export_dsn.py → FreeRouter → import_ses.py
""")

if __name__ == "__main__":
    main()
