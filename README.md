# ROVE — ESP32-S3 RC/Voice Car Platform

Offline voice-controlled toy car platform based on the **ESP32-S3-WROOM-1**.
No internet required — all speech recognition runs on-device via
[ESP-SR](https://github.com/espressif/esp-sr).

## Variants

| Variant  | Motors | Servos | Voice | PCB            |
|----------|:------:|:------:|:-----:|----------------|
| ROVE     | ✓      |        |       | placeholder    |
| ROVE-S   | ✓      | ✓      |       | placeholder    |
| ROVE-V   | ✓      |        | ✓     | **routed** ✓   |
| ROVE-SV  | ✓      | ✓      | ✓     | placeholder    |
| ROVE-SVX | ✓      | ✓      | ✓+    | placeholder    |

See [`docs/rove_variants.md`](docs/rove_variants.md) for full pin assignment,
build instructions, and BOM.

## Repository layout

```
rove_esp32s3/
├── electronics/
│   ├── libs/               shared KiCad symbols (TODO: rove.kicad_sym)
│   ├── rove/               ROVE placeholder schematic
│   ├── rove_s/             ROVE-S placeholder schematic
│   ├── rove_v/             ROVE-V full KiCad schematic + routed PCB ← start here
│   ├── rove_sv/            ROVE-SV placeholder schematic
│   └── rove_svx/           ROVE-SVX placeholder schematic
├── firmware/
│   ├── CMakeLists.txt      top-level ESP-IDF project
│   ├── main/               app_main, Kconfig variant selector
│   ├── components/
│   │   ├── motor/          DRV8833 DC motor driver
│   │   ├── servo/          LEDC PWM servo driver
│   │   └── voice/          INMP441 I2S + ESP-SR recognition pipeline
│   └── configs/            per-variant sdkconfig fragments
├── tools/                  Python scripts for KiCad generation
└── docs/
    ├── rove_variants.md    variant comparison + build guide
    └── bom/                per-variant bill of materials
```

## Quick start (ROVE-V)

```bash
# 1. Install ESP-IDF v5.x
# 2. Clone and enter firmware directory
cd firmware

# 3. Apply ROVE-V sdkconfig
cp configs/sdkconfig.rove_v sdkconfig.defaults

# 4. Build and flash
idf.py set-target esp32s3
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

Wake word: **"Hey ESP"** — then say "go forward", "turn left", "stop", etc.

## Hardware (ROVE-V)

- **MCU**: ESP32-S3-WROOM-1 (16 MB flash, 8 MB PSRAM)
- **Motor driver**: DRV8833PW dual H-bridge
- **Charger**: TP4056 via USB-C (580 mA)
- **LDO**: XC6220B331MR (3.3 V)
- **Microphone**: INMP441 I2S MEMS
- **Board**: 60 × 50 mm (smaller than Arduino Uno)
