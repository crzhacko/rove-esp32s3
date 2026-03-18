# ROVE Board Specifications — All Variants

## 개요

ROVE는 ESP32-S3-WROOM-1 기반의 오프라인 음성 제어 RC카 플랫폼입니다.
5종의 variant가 있으며, 모든 variant는 동일한 MCU와 DC 모터 드라이버를 공유합니다.

---

## Variant 비교표

| 항목              | ROVE | ROVE-S | ROVE-V | ROVE-SV | ROVE-SVX |
|-------------------|:----:|:------:|:------:|:-------:|:--------:|
| DC 모터 제어      | ✓    | ✓      | ✓      | ✓       | ✓        |
| 서보 제어         |      | ✓      |        | ✓       | ✓        |
| 음성 인식 (I2S)   |      |        | ✓      | ✓       | ✓        |
| 확장 기능         |      |        |        |         | ✓ (TBD)  |
| 온보드 LiPo 충전  |      |        | ✗      | (계획)  | (계획)   |
| 배터리 보호 회로  |      |        | ✓      | (계획)  | (계획)   |
| 배터리 전압 모니터|      |        | ✓      | (계획)  | (계획)   |
| PCB 상태          | placeholder | placeholder | **완성** | placeholder | placeholder |
| 보드 크기         | TBD  | TBD    | 60×50mm| TBD     | TBD      |
| PSRAM 필수        |      |        | ✓      | ✓       | ✓        |

---

## 공통 하드웨어

모든 variant에 공통으로 적용되는 사양입니다.

### MCU — ESP32-S3-WROOM-1-N16R8

| 항목          | 사양                                |
|---------------|-------------------------------------|
| 칩            | ESP32-S3 (Xtensa LX7 듀얼코어)     |
| 클럭          | 최대 240 MHz                        |
| Flash         | 16 MB (SPI)                         |
| PSRAM         | 8 MB OPI (Octal SPI, 80 MHz)       |
| Wi-Fi         | 802.11 b/g/n 2.4GHz                 |
| Bluetooth     | BLE 5.0                             |
| 패키지        | SMD 모듈 (18 × 25.5 mm)            |

### 모터 드라이버 — DRV8833PW

| 항목            | 사양                          |
|-----------------|-------------------------------|
| 제조사          | Texas Instruments             |
| 패키지          | TSSOP-16                      |
| 채널            | 듀얼 H-브릿지 (2 채널)        |
| 최대 전압 (VM)  | 10.8 V                        |
| 최대 전류       | 1.5 A/채널 (peak 2 A)         |
| 제어 방식       | IN1/IN2 방향 제어 (H-bridge)  |
| 절전 모드       | SLEEP 핀 (active high = 동작) |
| 모터 커넥터     | JST PH 2-pin × 2              |

### 모터 GPIO 핀 (전 variant 공통)

| 신호         | GPIO | 방향 | 기능                  |
|--------------|------|------|-----------------------|
| LEFT_IN1     | 1    | OUT  | DRV8833 AIN1 (좌 모터 방향) |
| LEFT_IN2     | 2    | OUT  | DRV8833 AIN2 (좌 모터 방향) |
| RIGHT_IN1    | 3    | OUT  | DRV8833 BIN1 (우 모터 방향) |
| RIGHT_IN2    | 4    | OUT  | DRV8833 BIN2 (우 모터 방향) |
| DRV_SLEEP    | 5    | OUT  | 드라이버 절전 제어 (HIGH=동작) |

### 모터 제어 진리표

| LEFT_IN1 | LEFT_IN2 | 좌 모터 동작 |
|----------|----------|------------|
| HIGH     | LOW      | 전진        |
| LOW      | HIGH     | 후진        |
| LOW      | LOW      | 정지 (coast)|
| HIGH     | HIGH     | 제동 (brake)|

---

## ROVE — 기본형 (모터 전용)

### 개요
가장 단순한 variant. DC 모터 2개만 제어하는 기본 RC카 보드.
Wi-Fi/BLE 리모트 컨트롤 또는 자율 주행 테스트 베이스로 활용.

### 하드웨어 사양

| 항목         | 사양                           |
|--------------|--------------------------------|
| MCU          | ESP32-S3-WROOM-1-N16R8         |
| 모터 드라이버 | DRV8833PW (듀얼 H-브릿지)     |
| 배터리       | 단셀 LiPo (JST PH 2-pin)       |
| 전원 입력    | 배터리 직결 (외부 충전기 필요) |
| PCB 상태     | Placeholder (미완성)            |

### 활성 GPIO

| 신호       | GPIO | 용도               |
|------------|------|--------------------|
| LEFT_IN1   | 1    | 좌 모터 방향 A     |
| LEFT_IN2   | 2    | 좌 모터 방향 B     |
| RIGHT_IN1  | 3    | 우 모터 방향 A     |
| RIGHT_IN2  | 4    | 우 모터 방향 B     |
| DRV_SLEEP  | 5    | 모터 드라이버 절전 |
| IO0        | 0    | BOOT 모드 (내부 pull-up) |

### 펌웨어 설정

```
CONFIG_ROVE_VARIANT_ROVE=y
# CONFIG_USE_ESP_SR is not set
```

---

## ROVE-S — 서보 추가형

### 개요
ROVE 기본형에 서보 모터 2채널을 추가한 variant.
굴삭기 버킷/붐 제어, 팬틸트 카메라, 로봇 암 등에 적합.

### 하드웨어 사양

| 항목         | 사양                                  |
|--------------|---------------------------------------|
| MCU          | ESP32-S3-WROOM-1-N16R8                |
| 모터 드라이버 | DRV8833PW (듀얼 H-브릿지)            |
| 서보 채널    | 2채널 (LEDC PWM, 50Hz)               |
| 배터리       | 단셀 LiPo (JST PH 2-pin)             |
| 서보 전원    | 별도 5V 필요 (외부 공급 또는 벅 컨버터) |
| PCB 상태     | Placeholder (미완성)                  |

### 활성 GPIO

| 신호         | GPIO | 방향 | 용도                        |
|--------------|------|------|-----------------------------|
| LEFT_IN1     | 1    | OUT  | 좌 모터 방향 A              |
| LEFT_IN2     | 2    | OUT  | 좌 모터 방향 B              |
| RIGHT_IN1    | 3    | OUT  | 우 모터 방향 A              |
| RIGHT_IN2    | 4    | OUT  | 우 모터 방향 B              |
| DRV_SLEEP    | 5    | OUT  | 모터 드라이버 절전          |
| SERVO_BOOM   | 6    | OUT  | 붐 서보 PWM (LEDC)          |
| SERVO_BUCKET | 7    | OUT  | 버킷 서보 PWM (LEDC)        |

### 서보 제어 사양

| 항목          | 사양                          |
|---------------|-------------------------------|
| PWM 주파수    | 50 Hz (주기 20ms)             |
| 펄스폭 범위   | 500 µs (0°) ~ 2500 µs (180°) |
| 중립 위치     | 1500 µs (90°)                 |
| 제어 드라이버 | ESP-IDF LEDC                  |

### 펌웨어 설정

```
CONFIG_ROVE_VARIANT_ROVE_S=y
# CONFIG_USE_ESP_SR is not set
```

---

## ROVE-V — 음성 제어형 ★ (완성 PCB)

### 개요
음성 인식 기능이 추가된 variant. 현재 유일하게 PCB 설계가 완료된 모델.
INMP441 I2S MEMS 마이크와 ESP-SR을 이용해 기기 내에서 완전히 오프라인으로 음성을 인식.

### 하드웨어 사양

| 항목          | 사양                                         |
|---------------|----------------------------------------------|
| MCU           | ESP32-S3-WROOM-1-N16R8                       |
| 모터 드라이버  | DRV8833PW (TSSOP-16)                        |
| 마이크        | INMP441 I2S MEMS (LGA-6, InvenSense)        |
| 배터리 보호   | DW01A + FS8205A (SOT-23-6 × 2)              |
| LDO           | XC6220B331MR 3.3V (SOT-23-5, Torex)        |
| 배터리        | 단셀 LiPo, JST PH 2-pin                     |
| USB           | 데이터 전용 (충전 기능 없음)                  |
| 보드 크기     | 60 × 50 mm (아두이노 우노보다 작음)          |
| PCB 상태      | **완성 (Gerber 파일 생성 완료)**             |

### 전원 아키텍처

```
J2 배터리 (LiPo)
    │
    └─→ BATT_RAW ──→ DW01A (U5) + FS8205A (Q1) ──→ VBAT (보호된 출력)
                     배터리 보호 (과방전/과전류)          │
                                                ┌─────────┼──────────────┐
                                                │         │              │
                                           DRV8833      XC6220       R6/R7 분배
                                           VM (모터)    VIN            │
                                                         │         VBAT_MON
                                                    XC6220 VOUT     → GPIO10
                                                    = 3.3V
                                                         │
                                           ┌─────────────┼──────────┐
                                           │             │          │
                                      ESP32-S3      INMP441    DRV8833 VCC
                                                    VDD        (로직)

USB-C (J1) ──→ D+/D- → ESP32-S3 USB (펌웨어 업로드 전용, 배터리 충전 없음)
               CC1/CC2 → R4/R5 (5.1kΩ, 5V 수전 표시용)
```

### 배터리 보호 회로 (DW01A + FS8205A)

| 항목          | 사양                                              |
|---------------|---------------------------------------------------|
| 보호 IC       | DW01A (SOT-23-6)                                  |
| 스위치 소자   | FS8205A 듀얼 N채널 MOSFET (SOT-23-6)             |
| 과방전 보호   | VBAT < ~2.4V 시 차단 (DW01A 내부 기준)           |
| 과전류 보호   | FS8205A 내부 저항 기반 전류 제한                  |
| 입력          | BATT_RAW (배터리 양극 직결)                       |
| 출력          | VBAT (보호된 전원, 나머지 회로로 공급)            |
| 충전 기능     | **없음** — 외부 충전기(USB 충전 어댑터 등) 사용  |

### LDO (XC6220B331MR)

| 항목     | 사양                              |
|----------|-----------------------------------|
| 입력     | VBAT (LiPo 3.0~4.2V)             |
| 출력     | 3.3V 고정                         |
| 최대전류 | 500mA                             |
| 드롭아웃 | 최저 VBAT 3.4V 이상에서 동작 보장 |
| 패키지   | SOT-23-5                          |

### 마이크 (INMP441)

| 항목         | 사양                              |
|--------------|-----------------------------------|
| 타입         | 전방향 MEMS, 바텀 포트            |
| ADC          | 내장 24-bit 시그마-델타           |
| 인터페이스   | I2S (Phillips 모드)               |
| 샘플링 레이트 | 16 kHz (음성 인식 최적화)        |
| 비트 깊이    | 16-bit                            |
| 공급 전압    | 1.8V ~ 3.3V                       |
| 채널 선택    | L/R 핀 → GND (왼쪽 채널)         |
| 패키지       | LGA-6                             |

### 배터리 전압 모니터링 (VBAT_MON)

| 항목          | 사양                                                        |
|---------------|-------------------------------------------------------------|
| 회로          | R6(100kΩ) + R7(47kΩ) 저항 분배기                           |
| 입력          | VBAT (보호된 배터리 전압, 3.0~4.2V)                        |
| 출력          | VBAT_MON = VBAT × 47/(100+47) ≈ VBAT × 0.32               |
| ADC 핀        | GPIO10 (ADC1_CH9)                                           |
| 동작 범위     | VBAT 4.2V → VBAT_MON 1.35V / VBAT 3.0V → VBAT_MON 0.96V  |
| 저전압 임계   | VBAT_MON < 1.06V → VBAT < 3.3V (배터리 교체 필요)          |

### 전체 GPIO 핀 할당

| 신호         | GPIO | 방향 | 기능                        |
|--------------|------|------|-----------------------------|
| LEFT_IN1     | 1    | OUT  | DRV8833 AIN1 (좌 모터)     |
| LEFT_IN2     | 2    | OUT  | DRV8833 AIN2 (좌 모터)     |
| RIGHT_IN1    | 3    | OUT  | DRV8833 BIN1 (우 모터)     |
| RIGHT_IN2    | 4    | OUT  | DRV8833 BIN2 (우 모터)     |
| DRV_SLEEP    | 5    | OUT  | 드라이버 절전 (HIGH=동작)   |
| IO0          | 0    | IN   | BOOT 모드 (10kΩ pull-up, SW1→GND) |
| I2S_WS       | 15   | OUT  | INMP441 Word Select (LRCLK) |
| I2S_SCK      | 16   | OUT  | INMP441 Bit Clock           |
| I2S_SD       | 17   | IN   | INMP441 Serial Data         |
| STATUS_LED   | 48   | OUT  | 상태 LED (330Ω 직렬)        |
| VBAT_MON     | 10   | IN   | 배터리 전압 모니터 (ADC1_CH9, R6/R7 분배) |

### BOM (Bill of Materials) — 30부품

#### IC / 모듈

| Ref  | 부품명                  | 패키지   | 수량 | 비고                              |
|------|-------------------------|----------|------|-----------------------------------|
| U1   | ESP32-S3-WROOM-1-N16R8  | Module   | 1    | Espressif, 16MB flash/8MB PSRAM  |
| U2   | XC6220B331MR            | SOT-23-5 | 1    | Torex, 3.3V LDO 500mA            |
| U3   | DRV8833PW               | TSSOP-16 | 1    | TI, 듀얼 H-브릿지 모터 드라이버  |
| U5   | DW01A                   | SOT-23-6 | 1    | 배터리 보호 IC (과방전/과전류)    |
| Q1   | FS8205A                 | SOT-23-6 | 1    | 듀얼 N채널 MOSFET (보호 스위치)  |
| MK1  | INMP441                 | LGA-6    | 1    | InvenSense, I2S MEMS 마이크       |

#### 커넥터

| Ref  | 부품명                       | 타입         | 수량 | 용도                      |
|------|------------------------------|--------------|------|---------------------------|
| J1   | HRO TYPE-C-31-M-12 USB-C     | SMD          | 1    | 데이터 전용 (충전 없음)    |
| J2   | JST PH B2B-PH-K 2-pin       | Through-hole | 1    | LiPo 배터리               |
| J3   | JST PH B2B-PH-K 2-pin       | Through-hole | 1    | 좌 모터                   |
| J4   | JST PH B2B-PH-K 2-pin       | Through-hole | 1    | 우 모터                   |

#### 커패시터

| Ref  | 값     | 패키지           | 수량 | 용도                     |
|------|--------|------------------|------|--------------------------|
| C1   | 10µF   | CP_Elec_6.3x5.8  | 1    | VBAT 벌크 캡 (전해)     |
| C2   | 100nF  | C_0805           | 1    | 바이패스                 |
| C3   | 10µF   | CP_Elec_6.3x5.8  | 1    | 3.3V 벌크 캡 (전해)     |
| C4   | 100nF  | C_0805           | 1    | 바이패스                 |
| C5   | 100µF  | CP_Elec_6.3x5.8  | 1    | VBAT 대용량 벌크 캡     |
| C6   | 10nF   | CP_Elec_6.3x5.8  | 1    | 고주파 바이패스          |
| C7   | 100nF  | C_0805           | 1    | 바이패스                 |
| C8   | 100nF  | C_0805           | 1    | 바이패스                 |

#### 저항

| Ref  | 값     | 패키지 | 수량 | 용도                              |
|------|--------|--------|------|-----------------------------------|
| R1   | 10 kΩ  | 0805   | 1    | ESP32 EN pull-up                  |
| R2   | 10 kΩ  | 0805   | 1    | ESP32 IO0 pull-up (BOOT)          |
| R3   | 330 Ω  | 0805   | 1    | 상태 LED 전류 제한                |
| R4   | 5.1 kΩ | 0805   | 1    | USB CC1 pull-down (5V 수전)       |
| R5   | 5.1 kΩ | 0805   | 1    | USB CC2 pull-down (5V 수전)       |
| R6   | 100 kΩ | 0402   | 1    | VBAT_MON 분배기 상단 (VBAT→ADC)  |
| R7   | 47 kΩ  | 0402   | 1    | VBAT_MON 분배기 하단 (ADC→GND)   |

#### LED

| Ref  | 색상 | 패키지    | 수량 | 의미                              |
|------|------|-----------|------|-----------------------------------|
| D1   | 청색 | LED_0805  | 1    | 상태 LED (GPIO48, active-high)    |

#### 보호 소자 / 스위치

| Ref  | 부품명           | 수량 | 용도                                      |
|------|------------------|------|-------------------------------------------|
| D2   | SS14 (Schottky)  | 1    | 배터리 보호 회로 역류 방지               |
| D3   | SS14 (Schottky)  | 1    | 배터리 보호 회로 역류 방지               |
| SW1  | Tactile (SKQG)   | 1    | BOOT 버튼 (IO0→GND, 펌웨어 업로드 모드) |
| SW2  | Tactile (SKQG)   | 1    | RST 버튼 (EN→GND, 리셋)                 |

### 음성 인식 사양 (ESP-SR)

| 항목          | 사양                                     |
|---------------|------------------------------------------|
| 라이브러리    | ESP-SR (Espressif managed component)     |
| 웨이크워드    | "Hey ESP"                                |
| 인식 명령어   | forward / backward / left / right / stop |
| 동작 조건     | 8MB OPI PSRAM 필수                       |
| I2S 설정      | 16 kHz, 16-bit, Philips 모드             |
| 처리 방식     | 완전 온디바이스 (인터넷 불필요)          |

### 음성 명령어 목록

| 명령어         | 동작              |
|----------------|-------------------|
| "go forward"   | 양쪽 모터 전진    |
| "go backward"  | 양쪽 모터 후진    |
| "turn left"    | 좌회전 (스핀)     |
| "turn right"   | 우회전 (스핀)     |
| "stop"         | 모든 모터 정지    |

### 펌웨어 설정

```
CONFIG_ROVE_VARIANT_ROVE_V=y
CONFIG_USE_ESP_SR=y
CONFIG_ESP32S3_SPIRAM_SUPPORT=y
CONFIG_SPIRAM_MODE_OCT=y
CONFIG_SPIRAM_SPEED_80M=y
```

---

## ROVE-SV — 서보 + 음성 복합형

### 개요
ROVE-S (서보)와 ROVE-V (음성)의 기능을 통합한 variant.
음성 명령으로 주행과 굴삭기 팔(붐/버킷)을 동시에 제어.

### 하드웨어 사양

| 항목          | 사양                                  |
|---------------|---------------------------------------|
| MCU           | ESP32-S3-WROOM-1-N16R8                |
| 모터 드라이버  | DRV8833PW                            |
| 마이크        | INMP441 I2S MEMS                     |
| 서보 채널     | 2채널 (GPIO 6, 7 LEDC PWM)           |
| 배터리 충전기  | TP4056 (ROVE-V 기준, 계획 중)        |
| PCB 상태      | Placeholder (미완성)                  |
| PSRAM 필수    | 8MB OPI (ESP-SR 사용)                |

### 전체 GPIO 핀 할당

| 신호         | GPIO | 방향 | 기능                        |
|--------------|------|------|-----------------------------|
| LEFT_IN1     | 1    | OUT  | 좌 모터 방향 A              |
| LEFT_IN2     | 2    | OUT  | 좌 모터 방향 B              |
| RIGHT_IN1    | 3    | OUT  | 우 모터 방향 A              |
| RIGHT_IN2    | 4    | OUT  | 우 모터 방향 B              |
| DRV_SLEEP    | 5    | OUT  | 드라이버 절전               |
| SERVO_BOOM   | 6    | OUT  | 붐 서보 PWM                 |
| SERVO_BUCKET | 7    | OUT  | 버킷 서보 PWM               |
| I2S_WS       | 15   | OUT  | INMP441 Word Select         |
| I2S_SCK      | 16   | OUT  | INMP441 Bit Clock           |
| I2S_SD       | 17   | IN   | INMP441 Serial Data         |

### 펌웨어 설정

```
CONFIG_ROVE_VARIANT_ROVE_SV=y
CONFIG_USE_ESP_SR=y
CONFIG_ESP32S3_SPIRAM_SUPPORT=y
CONFIG_SPIRAM_MODE_OCT=y
CONFIG_SPIRAM_SPEED_80M=y
```

---

## ROVE-SVX — 확장형 (최고 사양)

### 개요
ROVE-SV에 추가 기능(TBD)을 더한 최고 사양 variant.
확장 센서, 디스플레이, UART 외부 장치 등 추가 예정.

### 하드웨어 사양

| 항목          | 사양                                   |
|---------------|----------------------------------------|
| MCU           | ESP32-S3-WROOM-1-N16R8                 |
| 모터 드라이버  | DRV8833PW                             |
| 마이크        | INMP441 I2S MEMS                      |
| 서보 채널     | 2채널 (GPIO 6, 7)                     |
| 확장 기능     | TBD (추가 센서/디스플레이/통신 예정)   |
| PCB 상태      | Placeholder (미완성)                   |
| PSRAM 필수    | 8MB OPI (80MHz, OCT 모드)             |

### 활성 GPIO (기본)

ROVE-SV와 동일한 핀 배치 + 확장 GPIO (TBD):

| 신호         | GPIO | 방향 | 기능                        |
|--------------|------|------|-----------------------------|
| LEFT_IN1     | 1    | OUT  | 좌 모터 방향 A              |
| LEFT_IN2     | 2    | OUT  | 좌 모터 방향 B              |
| RIGHT_IN1    | 3    | OUT  | 우 모터 방향 A              |
| RIGHT_IN2    | 4    | OUT  | 우 모터 방향 B              |
| DRV_SLEEP    | 5    | OUT  | 드라이버 절전               |
| SERVO_BOOM   | 6    | OUT  | 붐 서보 PWM                 |
| SERVO_BUCKET | 7    | OUT  | 버킷 서보 PWM               |
| I2S_WS       | 15   | OUT  | INMP441 Word Select         |
| I2S_SCK      | 16   | OUT  | INMP441 Bit Clock           |
| I2S_SD       | 17   | IN   | INMP441 Serial Data         |
| (TBD)        | 8~14 | -    | 확장 기능 예약              |

### 펌웨어 설정

```
CONFIG_ROVE_VARIANT_ROVE_SVX=y
CONFIG_USE_ESP_SR=y
CONFIG_ESP32S3_SPIRAM_SUPPORT=y
CONFIG_SPIRAM_MODE_OCT=y
CONFIG_SPIRAM_SPEED_80M=y
```

---

## 빌드 가이드

### 요구 환경

- ESP-IDF v5.x
- Python 3.8+
- esp-sr managed component (음성 variant)

### 빌드 명령

```bash
cd firmware

# variant 선택 (예: ROVE-V)
cp configs/sdkconfig.rove_v sdkconfig.defaults

# 타겟 설정 및 빌드
idf.py set-target esp32s3
idf.py build

# 플래시 및 모니터
idf.py -p /dev/ttyUSB0 flash monitor
```

### sdkconfig 파일 목록

| 파일                       | 적용 Variant |
|----------------------------|-------------|
| `configs/sdkconfig.rove`   | ROVE        |
| `configs/sdkconfig.rove_s` | ROVE-S      |
| `configs/sdkconfig.rove_v` | ROVE-V      |
| `configs/sdkconfig.rove_sv`| ROVE-SV     |
| `configs/sdkconfig.rove_svx`| ROVE-SVX  |

---

## 관련 파일

| 파일                                       | 내용                         |
|--------------------------------------------|------------------------------|
| `docs/rove_variants.md`                    | Variant 비교 및 빌드 가이드  |
| `docs/bom/bom_rove_v.md`                  | ROVE-V 전체 BOM              |
| `docs/rove_v_schematic_notes.md`          | ROVE-V 회로 설계 노트        |
| `electronics/rove_v/rove_v.kicad_sch`    | ROVE-V KiCad 회로도          |
| `electronics/rove_v/rove_v.kicad_pcb`    | ROVE-V KiCad PCB (완성)      |
| `electronics/rove_v/gerber/`             | 제조용 Gerber 파일           |
| `firmware/components/motor/include/motor.h` | 모터 드라이버 API          |
| `firmware/components/servo/include/servo.h` | 서보 드라이버 API          |
| `firmware/components/voice/include/voice.h` | 음성 인식 API              |
