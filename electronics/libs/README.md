# ROVE Shared KiCad Libraries

## Custom Symbols (`rove.kicad_sym`)
현재 ROVE-V 회로도에 임베드된 커스텀 심볼:

| Symbol | Package | 설명 |
|--------|---------|------|
| `Custom:TP4056` | SOP-8 | 1A Li-Po 충전 IC |
| `Custom:INMP441` | LGA-6 | I2S MEMS 마이크 |

> **TODO**: `rove_v.kicad_sch` 의 `lib_symbols` 섹션에서 위 두 심볼을
> `rove.kicad_sym` 파일로 추출하면 모든 variant가 공유 가능.
> KiCad → Tools → Edit Symbol Library → Export 로 추출.

## Custom Footprints (`rove.pretty/`)
현재 ROVE-V PCB에 인라인 정의된 커스텀 풋프린트:

| Footprint | 설명 |
|-----------|------|
| `SOP-8_3.9x4.9mm_P1.27mm` | TP4056 전용 |
| `INMP441_LGA-6` | INMP441 전용 |

> **TODO**: PCB에서 추출하여 `rove.pretty/` 디렉토리에 `.kicad_mod` 파일로 저장.

## 사용 방법 (KiCad 7+)
각 variant의 `fp-lib-table`, `sym-lib-table` 에 아래 경로 추가:
```
${KIPRJMOD}/../../libs/rove.kicad_sym
${KIPRJMOD}/../../libs/rove.pretty
```
