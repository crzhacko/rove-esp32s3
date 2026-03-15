# ROVE Variant Comparison

| Variant  | Motors | Servos | Voice (INMP441) | Board status   | sdkconfig fragment      |
|----------|:------:|:------:|:---------------:|----------------|-------------------------|
| ROVE     | ✓      |        |                 | placeholder    | sdkconfig.rove          |
| ROVE-S   | ✓      | ✓      |                 | placeholder    | sdkconfig.rove_s        |
| ROVE-V   | ✓      |        | ✓               | **routed PCB** | sdkconfig.rove_v        |
| ROVE-SV  | ✓      | ✓      | ✓               | placeholder    | sdkconfig.rove_sv       |
| ROVE-SVX | ✓      | ✓      | ✓ + extras      | placeholder    | sdkconfig.rove_svx      |

## Hardware summary (ROVE-V)

| Item       | Part              | Notes                                  |
|------------|-------------------|----------------------------------------|
| MCU        | ESP32-S3-WROOM-1  | 16 MB flash, 8 MB PSRAM (OPI)          |
| Motor drv  | DRV8833PW         | Dual H-bridge, TSSOP-16                |
| Charger    | TP4056 SOP-8      | 580 mA via 2 kΩ PROG, USB-C input      |
| LDO        | XC6220B331MR      | VBAT → 3.3 V, SOT-23-5                 |
| Microphone | INMP441           | I2S MEMS, LGA-6, L channel (GND→L/R)  |
| Battery    | Single-cell LiPo  | JST PH 2-pin                           |
| Motors     | TT gear motors ×2 | JST PH 2-pin each                      |
| Board size | 60 × 50 mm        | Smaller than Arduino Uno (68.6×53.4mm) |

## Pin assignment (ROVE-V)

| Signal       | GPIO | Direction |
|--------------|------|-----------|
| LEFT_IN1     | 1    | OUT       |
| LEFT_IN2     | 2    | OUT       |
| RIGHT_IN1    | 3    | OUT       |
| RIGHT_IN2    | 4    | OUT       |
| DRV_SLEEP    | 5    | OUT       |
| SERVO_BOOM   | 6    | OUT (S only) |
| SERVO_BUCKET | 7    | OUT (S only) |
| I2S_WS       | 15   | OUT       |
| I2S_SCK      | 16   | OUT       |
| I2S_SD       | 17   | IN        |

## Building a variant

```bash
cd firmware

# Copy the desired sdkconfig fragment
cp configs/sdkconfig.rove_v sdkconfig.defaults

# Configure + build (ESP-IDF v5.x)
idf.py set-target esp32s3
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

## Voice commands (ROVE-V / ROVE-SV / ROVE-SVX)

Wake word: **"Hey ESP"**

| Command        | Action        |
|----------------|---------------|
| "go forward"   | Both motors forward  |
| "go backward"  | Both motors backward |
| "turn left"    | Spin left     |
| "turn right"   | Spin right    |
| "stop"         | All motors stop |

Requires [esp-sr](https://github.com/espressif/esp-sr) managed component
(`CONFIG_USE_ESP_SR=y`) and a PSRAM-enabled module (8 MB OPI recommended).
