# Voice Car Controller - Schematic Design Notes

## Overview

The voice-controlled car schematic (`voice_car_controller.kicad_sch`) is derived from the
excavator project (`vehicle_controller_drv8833.kicad_sch`) with the following modifications:
servo-related circuitry removed, TP4056 Li-Po charger added, INMP441 I2S microphone added,
and GPIO assignments updated for voice-control use.

---

## Changes from Excavator Schematic

### Removed Components
| Ref | Value | Reason |
|-----|-------|--------|
| J5 | BoomServo (3-pin 2.54mm) | Not needed for car |
| J6 | BucketServo (3-pin 2.54mm) | Not needed for car |
| J7 | 5V Buck (3-pin 2.54mm) | Replaced by onboard TP4056 charging |

### Removed Net Labels
- `BOOM_SERVO` (both at ESP32-S3 GPIO and at J5)
- `BUCKET_SERVO` (both at ESP32-S3 GPIO and at J6)
- `SERVO_5V` (at J5, J6, J7)
- `VBAT_MOTOR` (at J7)

---

## New Components

### U4 - TP4056 Li-Po Battery Charger (SOP-8)
**Position:** (55, 45) on schematic

The TP4056 provides single-cell Li-Po/Li-Ion charging from USB-C 5V input.

| Pin | Name  | Connection | Notes |
|-----|-------|------------|-------|
| 1   | TEMP  | GND via 10kΩ | Disables temperature protection (NTC absent) |
| 2   | PROG  | GND via 2kΩ  | Sets charge current ≈580 mA (I_CHG = 1200/R_PROG) |
| 3   | GND   | GND power rail | |
| 4   | VCC   | USB_5V net   | Charging input from USB-C |
| 5   | BAT   | VBAT net     | Battery positive; shared with J2 battery connector |
| 6   | CHRG  | 10kΩ pull-up to 3.3V, then to D4 cathode | Open-drain, low = charging |
| 7   | STDBY | 10kΩ pull-up to 3.3V, then to D5 cathode | Open-drain, low = standby/full |
| 8   | CE    | VCC (USB_5V) | Chip Enable tied high = always enabled when USB present |

**Design decision:** CE is tied to VCC so charging begins automatically when USB is connected.
To add a charge-enable switch in a future revision, insert a SPST between CE and VCC.

**Charge current:** R_PROG = 2kΩ → I_CHG = 1200/2000 = 0.6 A (580 mA typical).
Suitable for 500–1000 mAh Li-Po cells commonly used in small RC cars.

### MK1 - INMP441 I2S MEMS Microphone (LGA-6)
**Position:** (155, 175) on schematic

The INMP441 is an omnidirectional, bottom-port MEMS microphone with a built-in 24-bit
sigma-delta ADC and I2S serial output. It requires no external ADC.

| Pin | Name | Connection | Notes |
|-----|------|------------|-------|
| 1   | VDD  | 3.3V rail + 100nF decoupling cap to GND | Supply 1.8–3.3V |
| 2   | GND  | GND power rail | |
| 3   | SD   | I2S_SD net → ESP32-S3 IO17 | Serial data output |
| 4   | WS   | I2S_WS net → ESP32-S3 IO15 | Word Select (LRCLK) input |
| 5   | SCK  | I2S_SCK net → ESP32-S3 IO16 | Bit clock input |
| 6   | L/R  | GND | Selects left channel (0 = left, 1 = right) |

**Design decision:** L/R tied to GND selects the left channel. This is the typical
configuration for a single-microphone design. The ESP32-S3 I2S peripheral is configured
in standard (Philips) mode at 16 kHz / 16-bit for voice recognition.

### Charging Status LEDs

| Ref | Color | Net | Meaning |
|-----|-------|-----|---------|
| D4  | Red   | CHRG active-low | LED on = charging in progress |
| D5  | Green | STDBY active-low | LED on = charge complete / standby |

Each LED has an anode-side 330Ω series resistor to 3.3V. The TP4056 open-drain outputs
pull the cathode low to illuminate the respective LED.

---

## Power Architecture

```
USB-C (5V) ──→ TP4056 VCC
               TP4056 BAT ──→ VBAT net ←── J2 Battery JST (when USB absent)
                                  │
                    ┌─────────────┼──────────────┐
                    │             │              │
               DRV8833 VM    LDO (U3) VIN    (reverse protection D2/D3)
               (motor power)      │
                             LDO VOUT = 3.3V
                                  │
                    ┌─────────────┼──────────────┐
                    │             │              │
               ESP32-S3       INMP441 VDD    DRV8833 VCC (logic)
```

**Key points:**
- Battery charges via TP4056 when USB-C is connected.
- Battery (VBAT) directly powers DRV8833 motor supply and LDO input.
- LDO (XC6220B331MR) converts VBAT → 3.3V for ESP32-S3, microphone, and DRV8833 logic.
- Reverse polarity protection diodes D2/D3 protect the VBAT rail.

---

## ESP32-S3 GPIO Assignments

| GPIO | Net | Function |
|------|-----|---------|
| IO1  | LEFT_IN1  | DRV8833 AIN1 - Left motor direction |
| IO2  | LEFT_IN2  | DRV8833 AIN2 - Left motor direction |
| IO3  | RIGHT_IN1 | DRV8833 BIN1 - Right motor direction |
| IO4  | RIGHT_IN2 | DRV8833 BIN2 - Right motor direction |
| IO5  | DRV_SLEEP | DRV8833 sleep control (high = active) |
| IO0  | BOOT      | Boot mode select (pulled up, SW1 to GND) |
| IO15 | I2S_WS    | INMP441 Word Select (LRCLK) |
| IO16 | I2S_SCK   | INMP441 Bit Clock |
| IO17 | I2S_SD    | INMP441 Serial Data |
| IO48 | STATUS_LED | Onboard status LED via current-limit resistor |

---

## Preserved Components (unchanged from excavator schematic)

| Ref | Value | Function |
|-----|-------|---------|
| U1  | ESP32-S3-WROOM-1 | Main MCU |
| U2  | DRV8833PW | Dual H-bridge motor driver |
| U3  | XC6220B331MR | 3.3V LDO regulator |
| J1  | USB-C Receptacle | USB 2.0 / power input |
| J2  | JST PH 2-pin | Li-Po battery connector |
| J3  | JST PH 2-pin | Left motor connector |
| J4  | JST PH 2-pin | Right motor connector |
| SW1 | Tactile switch | Boot mode button |
| R1  | 10kΩ | EN pull-up resistor |
| R2  | 10kΩ | Boot pull-up resistor |
| R4  | 5.1kΩ | USB CC1 pull-down |
| R5  | 5.1kΩ | USB CC2 pull-down |
| D1  | LED  | Status LED |
| D2  | Schottky | Reverse polarity protection |
| D3  | Schottky | Reverse polarity protection |
| C1,C2,C5,C6,C7 | 0.1uF/10uF | Decoupling capacitors |

---

## Schematic Generation

The schematic file is generated by the Python script at:
`tools/generate_schematic.py`

To regenerate:
```bash
cd /Users/crzhacko/projects/maker_lab/voice_car_esp32s3
python3 tools/generate_schematic.py
```

The script:
1. Reads the excavator schematic as a base
2. Uses paren-matching to locate and extend the `lib_symbols` section
3. Removes servo connectors J5, J6, J7 by UUID
4. Removes servo-related net labels by UUID
5. Removes `no_connect` markers at GPIO pins now assigned to I2S
6. Inserts TP4056 and INMP441 symbol instances
7. Inserts I2S net labels at ESP32-S3 IO15/IO16/IO17 and at INMP441
8. Writes valid KiCad S-expression format (parentheses balanced)
