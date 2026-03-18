#!/usr/bin/env python3
"""
ROVE-V PCB Board Resize: 100×80mm → 60×50mm
컴포넌트 재배치 + 보드 외곽 축소 + 기존 트랙 제거 후 재라우팅 준비

Usage:
    python3 resize_board_60x50.py
"""

import re
import os
import shutil
from datetime import datetime

PCB_FILE = os.path.join(os.path.dirname(__file__), '..', 'electronics', 'rove_v', 'rove_v.kicad_pcb')
PCB_FILE = os.path.normpath(PCB_FILE)

NEW_W = 60.0
NEW_H = 50.0

# ─────────────────────────────────────────────────────────────────────────────
# 새 컴포넌트 위치 정의  (ref: (x, y, rotation))
#
# 레이아웃 (60×50mm):
#   좌측: USB-C + 충전/전원관리 (U3 LDO, C1, R4/R5 CC 저항)
#   중앙: ESP32-S3-WROOM-1 모듈 (18×25.5mm)
#   우측: DRV8833 모터드라이버 + JST 커넥터 3개
#   하단: INMP441 마이크 + 배터리보호 IC + 대용량 캡
# ─────────────────────────────────────────────────────────────────────────────
NEW_POSITIONS = {
    # ── 주요 IC ─────────────────────────────────────────────────
    'U1':  (30.0,  21.0,   0),   # ESP32-S3-WROOM-1  center, 가로 (18×25.5mm CrtYd ±9.75/±13.45)
    'U2':  (50.0,  28.0,   0),   # DRV8833PW  TSSOP-16  (CrtYd ±3.85/±2.75)
    'U3':  (13.0,  16.0,   0),   # XC6220 LDO SOT-23-5
    'U5':  ( 7.0,  36.0,   0),   # DW01A  SOT-23-6  배터리 보호
    'Q1':  (13.0,  36.0,   0),   # FS8205A  SOT-23-6  보호 FET

    # ── 커넥터 ──────────────────────────────────────────────────
    'J1':  ( 4.5,  25.0,   0),   # USB-C (좌측 보드 에지, 중간 높이)
    'J2':  (57.0,   9.0, 270),   # 배터리 JST PH 2pin (rot=270: pad1 at (57,9), pad2 at (57,11))
    'J3':  (57.0,  22.0, 270),   # 좌 모터 JST PH 2pin (rot=270: pad1 at (57,22), pad2 at (57,24))
    'J4':  (57.0,  33.0, 270),   # 우 모터 JST PH 2pin (rot=270: pad1 at (57,33), pad2 at (57,35))

    # ── 스위치 ──────────────────────────────────────────────────
    'SW1': ( 5.0,  44.0,   0),   # BOOT 택트 스위치 (좌하단)

    # ── 마이크 ──────────────────────────────────────────────────
    'MK1': (34.0,  43.0,   0),   # INMP441 LGA-6 (ESP32 하단, CrtYd ±2.38/±2.86)

    # ── LED ─────────────────────────────────────────────────────
    'D1':  ( 6.0,   8.0,   0),   # 상태 LED 0805

    # ── 저항 (0805/0402) ────────────────────────────────────────
    'R1':  (11.0,  27.0,   0),   # 10kΩ EN 풀업 (rot=0: pads in X dir)
    'R2':  (11.0,  31.0,   0),   # 10kΩ IO0 풀업 (rot=0: pads in X dir)
    'R3':  (10.0,   9.0,   0),   # 330Ω LED 직렬 (rot=0: pads in X dir)
    'R4':  ( 3.0,  17.0,   0),   # 5.1kΩ CC1 (rot=0: pads in X dir)
    'R5':  ( 6.5,  17.0,   0),   # 5.1kΩ CC2 (rot=0: pads in X dir)
    'R6':  (12.0,  39.5,   0),   # 100kΩ VBAT 분배
    'R7':  (19.0,  39.5,   0),   # 저항 (배터리 보호 회로)

    # ── 캐패시터 ────────────────────────────────────────────────
    'C1':  ( 5.0,  14.0,   0),   # 10µF 전해 6.3×5.8mm (VBAT)
    'C2':  (13.0,  22.0,   0),   # 0.1µF 0805 (3V3 디커플링)
    'C5':  (26.0,  42.0,   0),   # 100µF 전해 6.3×5.8mm (VBAT 벌크, rot=0: pads in X dir)
    'C6':  (54.0,  20.0,   0),   # 10nF 0805 (DRV8833 디커플링, rot=0: pads in X dir)
    'C7':  (54.0,  24.0,   0),   # 0.1µF 0805 (DRV8833 디커플링, rot=0: pads in X dir)
    'C8':  (34.0,  40.0,   0),   # 100nF 0805 (INMP441 디커플링, MK1 근처)
}

# 기존 보드 Edge.Cuts 좌표 → 새 좌표 매핑
EDGE_CUTS_MAP = [
    # (old_start, old_end) -> (new_start, new_end)
    ((100, 80, 0, 80),   (NEW_W, NEW_H, 0, NEW_H)),   # top edge
    ((0, 80, 0, 0),      (0, NEW_H, 0, 0)),             # left edge
    ((0, 0, 100, 0),     (0, 0, NEW_W, 0)),              # bottom edge
    ((100, 0, 100, 80),  (NEW_W, 0, NEW_W, NEW_H)),     # right edge
]


def fmt_coord(v):
    """소수점 후행 0 제거"""
    s = f'{v:.6f}'.rstrip('0').rstrip('.')
    return s


def replace_edge_cuts(content):
    """Edge.Cuts 보드 외곽 좌표를 새 사이즈로 교체"""
    replacements = [
        # 각 방향 라인의 (start X Y) (end X Y) 패턴 교체
        ('(start 100 80)\n\t\t(end 0 80)', f'(start {NEW_W} {NEW_H})\n\t\t(end 0 {NEW_H})'),
        ('(start 0 80)\n\t\t(end 0 0)',    f'(start 0 {NEW_H})\n\t\t(end 0 0)'),
        ('(start 0 0)\n\t\t(end 100 0)',   f'(start 0 0)\n\t\t(end {NEW_W} 0)'),
        ('(start 100 0)\n\t\t(end 100 80)', f'(start {NEW_W} 0)\n\t\t(end {NEW_W} {NEW_H})'),
    ]
    for old, new in replacements:
        content = content.replace(old, new)
    return content


def update_silkscreen_text(content):
    """실크스크린 보드명 위치를 새 보드 안으로 이동"""
    # "ROVE-V R2" 텍스트를 (30, 2) → (20, 2) 로 이동
    content = re.sub(
        r'\(gr_text "ROVE-V R2"\s*\(at [0-9.]+ [0-9.]+',
        '(gr_text "ROVE-V R2"\n\t\t(at 15 2',
        content
    )
    return content


def remove_tracks(content):
    """모든 세그먼트(트랙)와 via를 제거. 재라우팅 필요."""
    # segment 블록 제거
    content = re.sub(r'\t\(segment\s*\([^)]*\)[^)]*\([^)]*\)[^)]*\([^)]*\)[^)]*\([^)]*\)[^)]*\([^)]*\)\s*\)', '', content)
    content = re.sub(r'\t\(segment[^)]*(?:\([^()]*(?:\([^()]*\))*[^()]*\))*[^)]*\)', '', content)

    # via 블록 제거
    content = re.sub(r'\t\(via[^)]*(?:\([^()]*(?:\([^()]*\))*[^()]*\))*[^)]*\)', '', content)

    return content


def remove_tracks_v2(lines):
    """라인 단위로 segment / via / zone fill 블록 제거"""
    result = []
    i = 0
    removed = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip('\t')
        # segment, via, filled_polygon 블록만 제거
        if stripped.startswith('(segment') or stripped.startswith('(via'):
            # 괄호 깊이 추적하며 블록 끝까지 건너뜀
            depth = stripped.count('(') - stripped.count(')')
            if depth <= 0:
                # 한 줄짜리
                i += 1
                removed += 1
                continue
            i += 1
            while i < len(lines) and depth > 0:
                depth += lines[i].count('(') - lines[i].count(')')
                i += 1
            removed += 1
            continue
        result.append(line)
        i += 1
    print(f'  트랙/via {removed}개 제거')
    return result


def relocate_footprints(lines):
    """
    각 footprint 블록을 찾아 Reference를 읽고,
    NEW_POSITIONS에 있으면 (at X Y [rot]) 라인을 교체.
    """
    result = []
    i = 0
    moved = 0
    skipped = []

    while i < len(lines):
        line = lines[i]

        # footprint 블록 시작 감지 (탭 1개)
        if line.startswith('\t(footprint ') and not line.startswith('\t\t'):
            fp_start = i
            fp_block = [line]
            depth = line.count('(') - line.count(')')
            i += 1

            while i < len(lines) and depth > 0:
                fp_block.append(lines[i])
                depth += lines[i].count('(') - lines[i].count(')')
                i += 1

            # footprint 블록 전체에서 Reference 값 추출
            fp_text = '\n'.join(fp_block)
            ref_match = re.search(r'\(property "Reference" "([^"]+)"', fp_text)
            ref = ref_match.group(1) if ref_match else None

            if ref and ref in NEW_POSITIONS:
                nx, ny, nr = NEW_POSITIONS[ref]
                new_at = f'\t\t(at {fmt_coord(nx)} {fmt_coord(ny)})' if nr == 0 else \
                         f'\t\t(at {fmt_coord(nx)} {fmt_coord(ny)} {nr})'

                new_block = []
                for j, fl in enumerate(fp_block):
                    # 탭 2개로 시작하는 (at ...) 라인 교체
                    if fl.startswith('\t\t(at ') and not fl.startswith('\t\t\t'):
                        new_block.append(new_at)
                    else:
                        new_block.append(fl)

                result.extend(new_block)
                moved += 1
            else:
                if ref:
                    skipped.append(ref)
                result.extend(fp_block)

            continue

        result.append(line)
        i += 1

    print(f'  컴포넌트 {moved}개 재배치')
    if skipped:
        print(f'  위치 미지정 컴포넌트: {skipped}')
    return result


def main():
    print(f'ROVE-V 보드 리사이징: 100×80mm → {NEW_W}×{NEW_H}mm')
    print(f'입력: {PCB_FILE}')

    with open(PCB_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # 백업
    backup = PCB_FILE + f'.bak_pre_resize_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    shutil.copy2(PCB_FILE, backup)
    print(f'백업: {os.path.basename(backup)}')

    # 라인 분할
    lines = content.split('\n')
    print(f'  총 {len(lines)}줄')

    # 1. 컴포넌트 재배치
    print('\n[1] 컴포넌트 재배치...')
    lines = relocate_footprints(lines)

    # 2. 트랙/via 제거
    print('\n[2] 트랙 및 via 제거...')
    lines = remove_tracks_v2(lines)

    # 3. Edge.Cuts 교체 (문자열 조작)
    print('\n[3] 보드 외곽(Edge.Cuts) 교체...')
    content = '\n'.join(lines)
    old_content = content

    content = replace_edge_cuts(content)

    if content == old_content:
        print('  ⚠ Edge.Cuts 패턴을 찾지 못했습니다. 수동 확인 필요.')
    else:
        print(f'  보드 크기: {NEW_W}×{NEW_H}mm 로 변경')

    # 4. 실크스크린 텍스트 위치 조정
    print('\n[4] 실크스크린 텍스트 조정...')
    content = update_silkscreen_text(content)

    # 5. 저장
    with open(PCB_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'\n✓ 완료: {PCB_FILE}')
    print(f'  → 보드 크기: {NEW_W}×{NEW_H}mm (원본 대비 {(1 - NEW_W*NEW_H/8000)*100:.0f}% 면적 감소)')
    print('\n다음 단계:')
    print('  1. KiCad PCB Editor에서 파일 열어 레이아웃 확인')
    print('  2. DRC 실행하여 오류 확인')
    print('  3. freerouting 또는 KiCad autorouter로 배선 재라우팅')
    print('  4. 수동으로 중요 신호(USB D+/D-, I2S) 배선 검토')


if __name__ == '__main__':
    main()
