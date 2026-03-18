#!/usr/bin/env python3
"""Inspect ROVE-V PCB footprint positions and nets using pcbnew API."""
import sys, os

KICAD_SITE = os.path.expanduser(
    "~/Applications/KiCad/KiCad.app/Contents/Frameworks/"
    "Python.framework/Versions/3.9/lib/python3.9/site-packages"
)
sys.path.insert(0, KICAD_SITE)

import pcbnew

PCB = os.path.join(os.path.dirname(__file__),
                   "../electronics/rove_v/rove_v.kicad_pcb")

board = pcbnew.LoadBoard(os.path.abspath(PCB))

print("=== NETS ===")
nets_by_code = board.GetNetInfo().NetsByNetcode()
for code in sorted(nets_by_code.keys()):
    ni = nets_by_code[code]
    print(f"  {code:3d}  {ni.GetNetname()}")

print("\n=== FOOTPRINTS ===")
for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
    pos = fp.GetPosition()
    x = pcbnew.ToMM(pos.x)
    y = pcbnew.ToMM(pos.y)
    print(f"  {fp.GetReference():10s}  ({x:7.3f}, {y:7.3f})  layer={fp.GetLayerName()}")
    for pad in fp.Pads():
        ppos = pad.GetPosition()
        px = pcbnew.ToMM(ppos.x)
        py = pcbnew.ToMM(ppos.y)
        net = pad.GetNetname()
        print(f"    pad {pad.GetNumber():3s} ({px:7.3f},{py:7.3f}) net={net}")

print("\n=== TRACKS ===")
for t in board.GetTracks():
    if t.GetClass() == "PCB_TRACK":
        s = t.GetStart(); e = t.GetEnd()
        print(f"  TRACK  ({pcbnew.ToMM(s.x):.3f},{pcbnew.ToMM(s.y):.3f})"
              f" -> ({pcbnew.ToMM(e.x):.3f},{pcbnew.ToMM(e.y):.3f})"
              f"  w={pcbnew.ToMM(t.GetWidth()):.3f}  layer={t.GetLayerName()}"
              f"  net={t.GetNetname()}")
    elif t.GetClass() == "PCB_VIA":
        c = t.GetPosition()
        print(f"  VIA    ({pcbnew.ToMM(c.x):.3f},{pcbnew.ToMM(c.y):.3f})"
              f"  d={pcbnew.ToMM(t.GetDrillValue()):.3f}  net={t.GetNetname()}")
