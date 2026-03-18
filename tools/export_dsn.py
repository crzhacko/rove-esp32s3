#!/usr/bin/env python3
"""
ROVE-V: Export KiCad PCB → Specctra DSN for FreeRouter.
Pure Python parser — no pcbnew dependency.
"""
import os, re, sys, math
from collections import defaultdict

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__),
                       "../electronics/rove_v/rove_v.kicad_pcb"))
DSN = PCB.replace(".kicad_pcb", ".dsn")

# ── S-expression tokeniser ────────────────────────────────────────────────────

def tokenize(text):
    tokens = []
    i = 0
    while i < len(text):
        c = text[i]
        if c in ' \t\n\r':
            i += 1
        elif c == '(':
            tokens.append('('); i += 1
        elif c == ')':
            tokens.append(')'); i += 1
        elif c == '"':
            j = i + 1
            while j < len(text) and text[j] != '"':
                if text[j] == '\\': j += 1
                j += 1
            tokens.append(text[i:j+1]); i = j + 1
        else:
            j = i
            while j < len(text) and text[j] not in ' \t\n\r()':
                j += 1
            tokens.append(text[i:j]); i = j
    return tokens

def parse(tokens, pos=0):
    if tokens[pos] != '(':
        val = tokens[pos].strip('"')
        return val, pos + 1
    pos += 1  # consume '('
    result = []
    while tokens[pos] != ')':
        node, pos = parse(tokens, pos)
        result.append(node)
    return result, pos + 1  # consume ')'

def get(node, key):
    if not isinstance(node, list): return None
    for child in node:
        if isinstance(child, list) and child and child[0] == key:
            return child
    return None

def gets(node, key):
    if not isinstance(node, list): return []
    return [c for c in node if isinstance(c, list) and c and c[0] == key]

# ── parse PCB ─────────────────────────────────────────────────────────────────

print(f"Parsing: {PCB}")
with open(PCB) as f:
    raw = f.read()

tokens = tokenize(raw)
board, _ = parse(tokens)

# Board outline (Edge.Cuts)
outline_pts = []
for gl in gets(board, 'gr_line'):
    layer = get(gl, 'layer')
    if layer and layer[1] == 'Edge.Cuts':
        s = get(gl, 'start'); e = get(gl, 'end')
        if s and e:
            outline_pts.append(((float(s[1]), float(s[2])),
                                (float(e[1]), float(e[2]))))

# Compute board bounds
all_x = [p[0] for seg in outline_pts for p in seg]
all_y = [p[1] for seg in outline_pts for p in seg]
bx0, bx1 = min(all_x), max(all_x)
by0, by1 = min(all_y), max(all_y)
print(f"  Board: ({bx0},{by0}) → ({bx1},{by1})  = {bx1-bx0}×{by1-by0} mm")

# Net table (top-level)
net_table = {}   # num → name
for n in gets(board, 'net'):
    if len(n) >= 3:
        net_table[int(n[1])] = n[2]

# Footprints → pads
class Pad:
    __slots__ = ['ref', 'num', 'x', 'y', 'sx', 'sy', 'layers', 'net_name',
                 'shape', 'ptype', 'drill_d', 'rx', 'ry', 'bsx', 'bsy']
    def __init__(self, ref, num, x, y, sx, sy, layers, net_name, shape, ptype,
                 drill_d, rx, ry, bsx, bsy):
        self.ref=ref; self.num=num; self.x=x; self.y=y
        self.sx=sx; self.sy=sy; self.layers=layers
        self.net_name=net_name; self.shape=shape; self.ptype=ptype
        self.drill_d=drill_d
        self.rx=rx; self.ry=ry   # relative position within footprint
        self.bsx=bsx; self.bsy=bsy  # board-oriented pad extents (rotation applied)

fp_data = {}   # ref → (cx, cy, frot)
pads = []

for fp in gets(board, 'footprint'):
    at = get(fp, 'at')
    if not at: continue
    fx, fy = float(at[1]), float(at[2])
    frot = float(at[3]) if len(at) > 3 else 0.0

    ref_node = None
    for prop in gets(fp, 'property'):
        if len(prop) >= 3 and prop[1] == 'Reference':
            ref_node = prop[2]
    if ref_node is None:
        for ft in gets(fp, 'fp_text'):
            if len(ft) >= 3 and ft[1] == 'reference':
                ref_node = ft[2]
    ref = ref_node or '?'

    for pad in gets(fp, 'pad'):
        if len(pad) < 4: continue
        pnum  = pad[1]
        ptype = pad[2]   # smd / thru_hole / np_thru_hole
        if ptype == 'np_thru_hole': continue

        pat = get(pad, 'at')
        if not pat: continue
        px_loc, py_loc = float(pat[1]), float(pat[2])

        # transform to board coords
        # KiCad uses CW-positive rotation in Y-down coordinate system:
        #   px = fx + loc_x * cos(a) + loc_y * sin(a)
        #   py = fy - loc_x * sin(a) + loc_y * cos(a)
        angle = math.radians(frot)
        px = fx + px_loc * math.cos(angle) + py_loc * math.sin(angle)
        py = fy - px_loc * math.sin(angle) + py_loc * math.cos(angle)

        psz = get(pad, 'size')
        sx = float(psz[1]) if psz else 0.6
        sy = float(psz[2]) if psz else 0.6

        # Board-oriented pad extents after footprint rotation:
        # For a rectangle with local size (sx, sy) at rotation angle a,
        # the board-aligned bounding box is:
        #   bsx = sx*|cos(a)| + sy*|sin(a)|
        #   bsy = sx*|sin(a)| + sy*|cos(a)|
        bsx = sx * abs(math.cos(angle)) + sy * abs(math.sin(angle))
        bsy = sx * abs(math.sin(angle)) + sy * abs(math.cos(angle))

        # drill diameter (thru-hole)
        drill_d = 0.0
        drill_node = get(pad, 'drill')
        if drill_node and len(drill_node) >= 2:
            try:
                drill_d = float(drill_node[1])
            except ValueError:
                pass

        pnet = get(pad, 'net')
        net_name = pnet[2] if pnet and len(pnet) >= 3 else ''

        layers_node = get(pad, 'layers')
        layers_list = layers_node[1:] if layers_node else ['F.Cu']

        shape_str = pad[3] if len(pad) > 3 else 'rect'

        pads.append(Pad(ref, pnum, px, py, sx, sy, layers_list, net_name,
                        shape_str, ptype, drill_d, px_loc, py_loc, bsx, bsy))

    fp_data[ref] = (fx, fy, frot)

print(f"  Pads: {len(pads)}")
print(f"  Nets: {len(net_table)}")

# Group pads by footprint
fp_pads = defaultdict(list)
for p in pads:
    fp_pads[p.ref].append(p)

# ── Build padstack registry ────────────────────────────────────────────────────

def padstack_name(p):
    """Generate a unique padstack name based on board-oriented dimensions."""
    if p.ptype == 'thru_hole':
        return f"th_d{p.drill_d:.3f}_s{p.bsx:.3f}x{p.bsy:.3f}"
    # smd — use board-oriented extents so rotated footprints get correct padstacks
    layer = 'F' if any('F.Cu' in l for l in p.layers) else 'B'
    return f"smd_{layer}_{p.bsx:.3f}x{p.bsy:.3f}"

padstacks = {}   # name → Pad (first occurrence)
for p in pads:
    name = padstack_name(p)
    if name not in padstacks:
        padstacks[name] = p

# ── Write DSN ─────────────────────────────────────────────────────────────────

def f4(v):
    return f"{v:.4f}"

print(f"Writing DSN: {DSN}")
lines = []
W = lines.append

W('(pcb rove_v_r2.dsn')
W('  (parser')
W('    (string_quote ")')
W('    (space_in_quoted_tokens on)')
W('    (host_cad "KiCad")')
W('    (host_version "text-exporter")')
W('  )')
W('  (resolution mm 1000)')
W('  (unit mm)')
W('')

# Structure
W('  (structure')
W('    (layer "F.Cu"')
W('      (type signal)')
W('      (property (index 0))')
W('    )')
W('    (layer "B.Cu"')
W('      (type signal)')
W('      (property (index 1))')
W('    )')
W('    (boundary')
W(f'      (rect pcb {f4(bx0)} {f4(-by1)} {f4(bx1)} {f4(-by0)})')
W('    )')
W('    (via "Via[0-1]_600:300_um")')
W('    (rule')
W('      (width 0.2)')
W('      (clearance 0.2)')
W('      (clearance 0.2 (type default_smd))')
W('      (clearance 0.2 (type smd_smd))')
W('    )')
W('  )')
W('')

# Placement
W('  (placement')
for ref, pp in fp_pads.items():
    if not pp: continue
    cx = sum(p.x for p in pp) / len(pp)
    cy = sum(p.y for p in pp) / len(pp)
    side = 'front' if any('F.Cu' in l for lp in pp for l in lp.layers) else 'back'
    W(f'  (component "{ref}"')
    W(f'    (place "{ref}" {f4(cx)} {f4(-cy)} {side} 0)')
    W('  )')
W('  )')
W('')

# Library
W('  (library')

# Define standard via padstack first
W('  (padstack "Via[0-1]_600:300_um"')
W('    (shape (circle "F.Cu" 0.3000))')
W('    (shape (circle "B.Cu" 0.3000))')
W('    (drill 0.3000)')
W('    (attach off)')
W('  )')
W('')

# Define component padstacks
for ps_name, p in padstacks.items():
    W(f'  (padstack "{ps_name}"')
    if p.ptype == 'thru_hole':
        # thru-hole: appear on all copper layers — use board-oriented extents
        half_x, half_y = p.bsx / 2, p.bsy / 2
        W(f'    (shape (rect "F.Cu" {f4(-half_x)} {f4(-half_y)} {f4(half_x)} {f4(half_y)}))')
        W(f'    (shape (rect "B.Cu" {f4(-half_x)} {f4(-half_y)} {f4(half_x)} {f4(half_y)}))')
        if p.drill_d > 0:
            W(f'    (drill {f4(p.drill_d)})')
    else:
        # SMD — use board-oriented extents (accounts for footprint rotation)
        layer = '"F.Cu"' if any('F.Cu' in l for l in p.layers) else '"B.Cu"'
        half_x, half_y = p.bsx / 2, p.bsy / 2
        W(f'    (shape (rect {layer} {f4(-half_x)} {f4(-half_y)} {f4(half_x)} {f4(half_y)}))')
    W('    (attach off)')
    W('  )')

W('')

# Component images (pins relative to component centroid)
for ref, pp in fp_pads.items():
    if not pp: continue
    cx = sum(p.x for p in pp) / len(pp)
    cy = sum(p.y for p in pp) / len(pp)
    W(f'  (image "{ref}"')
    for p in pp:
        rx = p.x - cx
        ry = -(p.y - cy)   # DSN Y-axis is inverted vs KiCad
        ps = padstack_name(p)
        W(f'    (pin "{ps}" "{p.num}" {f4(rx)} {f4(ry)})')
    W('  )')

W('  )')
W('')

# Network
W('  (network')

net_pads = defaultdict(list)
for p in pads:
    if p.net_name:
        net_pads[p.net_name].append(p)

for net_name in sorted(net_pads.keys()):
    if not net_name: continue
    dsn_net = net_name.lstrip('/')
    W(f'  (net "{dsn_net}"')
    W(f'    (pins')
    for p in net_pads[net_name]:
        W(f'      {p.ref}-{p.num}')
    W(f'    )')
    W(f'  )')

W('  )')
W('')
W('  (wiring')
W('  )')
W(')')

with open(DSN, 'w') as f:
    f.write('\n'.join(lines))

print(f"DSN written: {DSN}")
print(f"  {len(net_pads)} nets, {len(fp_pads)} components, {len(pads)} pads, {len(padstacks)} padstacks")
