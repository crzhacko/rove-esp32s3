#pragma once
#include "driver/gpio.h"

/**
 * ROVE - Servo Component
 *
 * Used by: ROVE-S, ROVE-SV, ROVE-SVX
 * NOT used by: ROVE, ROVE-V
 *
 * GPIO pin assignment differs by PCB variant:
 *
 *   ROVE-S / ROVE-SVX  : BOOM=GPIO6,  BUCKET=GPIO7   (placeholder PCB)
 *   ROVE-SV R1         : BOOM=GPIO12, BUCKET=GPIO11
 *     → ESP32-S3-WROOM-1 module pad 12 (J5 connector) and pad 11 (J6 connector)
 *     → I2S mic uses GPIO15/16/17, so GPIO11/12 are the first free adjacent pins
 */
#if defined(CONFIG_ROVE_VARIANT_ROVE_SV)
#  define SERVO_BOOM_PIN    GPIO_NUM_12
#  define SERVO_BUCKET_PIN  GPIO_NUM_11
#else  /* ROVE-S, ROVE-SVX (placeholder PCB, GPIOs TBD on final board) */
#  define SERVO_BOOM_PIN    GPIO_NUM_6
#  define SERVO_BUCKET_PIN  GPIO_NUM_7
#endif

/* Pulse width: 500us (0°) ~ 2500us (180°), period 20ms (50Hz) */
void servo_init(void);
void servo_set_angle(gpio_num_t pin, uint8_t angle_deg); /* 0–180 */
void servo_boom(uint8_t angle_deg);
void servo_bucket(uint8_t angle_deg);
