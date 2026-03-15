#pragma once
#include "driver/gpio.h"

/**
 * ROVE - Servo Component
 *
 * Used by: ROVE-S, ROVE-SV, ROVE-SVX
 * NOT used by: ROVE, ROVE-V
 */

#define SERVO_BOOM_PIN    GPIO_NUM_6
#define SERVO_BUCKET_PIN  GPIO_NUM_7

/* Pulse width: 500us (0°) ~ 2500us (180°), period 20ms (50Hz) */
void servo_init(void);
void servo_set_angle(gpio_num_t pin, uint8_t angle_deg); /* 0–180 */
void servo_boom(uint8_t angle_deg);
void servo_bucket(uint8_t angle_deg);
