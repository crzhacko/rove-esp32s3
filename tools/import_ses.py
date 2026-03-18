#!/usr/bin/env python3
"""
Specctra SES → KiCad PCB 트랙 임포터 (순수 Python, pcbnew 불필요)

Usage:
    python3 import_ses.py
"""

import re, os, uuid, shutil
from datetime import datetime

PCB_FILE = os.path.normpath(os.path.join(
    os.path.dirname(__file__), '..', 'electronics', 'rove_v', 'rove_v.kicad_pcb'))
SES_FILE = os.path.normpath(os.path.join(
    os.path.dirname(__file__), '..', 'electronics', 'rove_v', 'rove_v_pcbnew.ses'))

# ── 좌표 변환 ──────────────────────────────────────────────────────────────────
# SES resolution mm 1000: 1 unit = 0.001 mm
# SES Y축은 반전: y_kicad = -y_ses / 1000
def ses2mm(v):
    return v / 1000.0

def ses_y2kicad(y_ses):
    return -y_ses / 1000.0

# ── KiCad 넷 이름 → 번호 매핑 ─────────────────────────────────────────────────
def build_net_map(pcb_content):
    """PCB 파일에서 넷 번호 맵 구성"""
    net_map = {}
    for m in re.finditer(r'\(net (\d+) "([^"]*)"\)', pcb_content):
        n, name = int(m.group(1)), m.group(2)
        net_map[name] = n
        # "/" 접두사 없는 버전도 등록
        if name.startswith('/'):
            net_map[name[1:]] = n
    return net_map

# ── SES 파일 파싱 ──────────────────────────────────────────────────────────────
def parse_ses(content):
    """SES 파일에서 wire 경로와 via를 추출"""
    segments = []  # list of (net_name, layer, width_mm, x1, y1, x2, y2)
    vias = []      # list of (net_name, x, y, drill_mm, annular_mm)

    # 현재 net 이름 추적
    current_net = None

    lines = content.split('\n')
    i = 0
    in_routes = False

    while i < len(lines):
        line = lines[i].strip()

        if '(routes' in line:
            in_routes = True

        if not in_routes:
            i += 1
            continue

        # net 블록 시작
        m = re.match(r'\(net\s+(.+)', line)
        if m:
            net_raw = m.group(1).strip().rstrip(')')
            current_net = net_raw.strip('"')
            i += 1
            continue

        # wire 블록: (wire (path LAYER WIDTH x1 y1 x2 y2 ...))
        if line == '(wire':
            # 다음 줄: (path LAYER WIDTH ...)
            i += 1
            path_line = lines[i].strip()
            pm = re.match(r'\(path\s+(\S+)\s+(\d+)', path_line)
            if pm:
                layer_raw = pm.group(1)
                width_ses = int(pm.group(2))
                width_mm = ses2mm(width_ses)

                # 레이어 이름 정규화
                layer = layer_raw.replace('_', '.')
                if layer == 'F.Cu': layer = 'F.Cu'
                elif layer == 'B.Cu': layer = 'B.Cu'

                # 좌표 수집
                coords = []
                i += 1
                while i < len(lines):
                    l2 = lines[i].strip()
                    if l2 == ')':
                        i += 1
                        break
                    # 숫자 쌍 파싱
                    nums = re.findall(r'-?\d+', l2)
                    for j in range(0, len(nums) - 1, 2):
                        x = ses2mm(int(nums[j]))
                        y = ses_y2kicad(int(nums[j+1]))
                        coords.append((x, y))
                    i += 1

                # 연속 점 쌍을 세그먼트로 변환
                for j in range(len(coords) - 1):
                    x1, y1 = coords[j]
                    x2, y2 = coords[j+1]
                    if (x1, y1) != (x2, y2):
                        segments.append((current_net, layer, width_mm, x1, y1, x2, y2))

                # 닫는 ')' (wire 블록)
                while i < len(lines) and lines[i].strip() != ')':
                    i += 1
                i += 1
            continue

        # via 블록: (via "PADSTACK_NAME" x y (net "NET"))
        m = re.match(r'\(via\s+"([^"]+)"\s+(-?\d+)\s+(-?\d+)', line)
        if m:
            padstack = m.group(1)
            x = ses2mm(int(m.group(2)))
            y = ses_y2kicad(int(m.group(3)))
            # net 이름 추출
            net_m = re.search(r'\(net\s+"([^"]+)"\)', line)
            via_net = net_m.group(1) if net_m else current_net
            # Via[0-1]_800:400_um: drill=400um=0.4mm, annular=800um=0.8mm
            drill_m = re.search(r'_(\d+):(\d+)_um', padstack)
            if drill_m:
                annular_um = int(drill_m.group(1))
                drill_um = int(drill_m.group(2))
                vias.append((via_net, x, y, drill_um/1000.0, annular_um/1000.0))
            else:
                vias.append((via_net, x, y, 0.4, 0.8))

        i += 1

    return segments, vias


# ── KiCad 세그먼트/via 생성 ────────────────────────────────────────────────────
def fmt(v):
    s = f'{v:.6f}'.rstrip('0').rstrip('.')
    return s

def make_segment(x1, y1, x2, y2, width, layer, net_num):
    uid = str(uuid.uuid4())
    return (
        f'\t(segment\n'
        f'\t\t(start {fmt(x1)} {fmt(y1)})\n'
        f'\t\t(end {fmt(x2)} {fmt(y2)})\n'
        f'\t\t(width {fmt(width)})\n'
        f'\t\t(layer "{layer}")\n'
        f'\t\t(net {net_num})\n'
        f'\t\t(uuid "{uid}")\n'
        f'\t)'
    )

def make_via(x, y, drill, size, net_num):
    uid = str(uuid.uuid4())
    return (
        f'\t(via\n'
        f'\t\t(at {fmt(x)} {fmt(y)})\n'
        f'\t\t(size {fmt(size)})\n'
        f'\t\t(drill {fmt(drill)})\n'
        f'\t\t(layers "F.Cu" "B.Cu")\n'
        f'\t\t(net {net_num})\n'
        f'\t\t(uuid "{uid}")\n'
        f'\t)'
    )


def main():
    print(f'SES 임포트: {os.path.basename(SES_FILE)} → {os.path.basename(PCB_FILE)}')

    with open(PCB_FILE, 'r') as f:
        pcb_content = f.read()
    with open(SES_FILE, 'r') as f:
        ses_content = f.read()

    # 백업
    bak = PCB_FILE + f'.bak_pre_ses2_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    shutil.copy2(PCB_FILE, bak)
    print(f'백업: {os.path.basename(bak)}')

    # 넷 맵 구성
    net_map = build_net_map(pcb_content)
    print(f'  넷 {len(net_map)}개 인식')

    # SES 파싱
    segments, vias = parse_ses(ses_content)
    print(f'  세그먼트 {len(segments)}개, via {len(vias)}개 파싱')

    # KiCad 형식 생성
    seg_strs = []
    unknown_nets = set()
    for net_name, layer, width, x1, y1, x2, y2 in segments:
        # 넷 번호 조회 (여러 이름 형식 시도)
        net_num = None
        for key in [net_name, '/' + net_name, net_name.lstrip('/')]:
            if key in net_map:
                net_num = net_map[key]
                break
        if net_num is None:
            unknown_nets.add(net_name)
            net_num = 0  # 미할당 net
        seg_strs.append(make_segment(x1, y1, x2, y2, width, layer, net_num))

    via_strs = []
    for net_name, x, y, drill, size in vias:
        net_num = net_map.get(net_name, net_map.get('/' + net_name, 0))
        via_strs.append(make_via(x, y, drill, size, net_num))

    if unknown_nets:
        print(f'  ⚠ 넷 번호 미발견: {unknown_nets}')

    # PCB 파일 맨 끝의 ')' 직전에 삽입
    all_new = '\n'.join(seg_strs + via_strs)
    # PCB 파일 마지막 ')' 앞에 삽입
    last_paren = pcb_content.rfind('\n)')
    if last_paren == -1:
        print('ERROR: PCB 파일 끝 패턴을 찾을 수 없습니다')
        return

    new_pcb = pcb_content[:last_paren] + '\n' + all_new + pcb_content[last_paren:]

    with open(PCB_FILE, 'w') as f:
        f.write(new_pcb)

    print(f'✓ 세그먼트 {len(seg_strs)}개, via {len(via_strs)}개 삽입 완료')
    print(f'  → {PCB_FILE}')


if __name__ == '__main__':
    main()
