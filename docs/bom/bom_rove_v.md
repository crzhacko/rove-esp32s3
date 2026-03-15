# BOM — ROVE-V

| Ref  | Value / Part          | Package       | Qty | Source / Notes                     |
|------|-----------------------|---------------|-----|------------------------------------|
| U1   | ESP32-S3-WROOM-1-N16R8| Module        | 1   | Espressif — 16MB flash / 8MB PSRAM |
| U2   | DRV8833PW             | TSSOP-16      | 1   | TI                                 |
| U3   | XC6220B331MR          | SOT-23-5      | 1   | Torex — 3.3V LDO                   |
| U4   | TP4056                | SOP-8         | 1   | Li-Po charger (580mA)              |
| MK1  | INMP441               | LGA-6         | 1   | InvenSense I2S MEMS mic            |
| J1   | USB-C receptacle      | SMD           | 1   | USB 2.0 power + data               |
| J2   | JST PH 2-pin          | Through-hole  | 1   | LiPo battery                       |
| J3   | JST PH 2-pin          | Through-hole  | 1   | Left motor                         |
| J4   | JST PH 2-pin          | Through-hole  | 1   | Right motor                        |
| C1   | 100µF / 6.3V          | 0805          | 1   | VBAT bulk cap                      |
| C2   | 10µF / 10V            | 0805          | 1   | 3V3 bulk cap                       |
| C3   | 100nF                 | 0402          | 1   | LDO bypass                         |
| C4   | 100nF                 | 0402          | 1   | TP4056 BAT bypass                  |
| C5   | 100nF                 | 0402          | 1   | INMP441 VDD bypass                 |
| R1   | 2 kΩ                  | 0402          | 1   | TP4056 PROG (580mA charge current) |
| R2   | 10 kΩ                 | 0402          | 1   | ESP32 EN pull-up                   |
| R3   | 10 kΩ                 | 0402          | 1   | ESP32 IO0 pull-up (boot)           |
| R4   | 330 Ω                 | 0402          | 1   | Status LED current-limit           |
| R5   | 330 Ω                 | 0402          | 1   | CHRG LED current-limit             |
| R6   | 330 Ω                 | 0402          | 1   | STDBY LED current-limit            |
| D1   | LED green 0402        | 0402          | 1   | Status / power LED                 |
| D2   | LED red 0402          | 0402          | 1   | Charging indicator                 |
| D3   | LED blue 0402         | 0402          | 1   | Standby / full indicator           |
