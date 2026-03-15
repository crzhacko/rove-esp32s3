#pragma once
#include "driver/gpio.h"

/**
 * ROVE - DC Motor Component (DRV8833)
 *
 * Used by: ROVE, ROVE-S, ROVE-V, ROVE-SV, ROVE-SVX
 */

#define MOTOR_LEFT_IN1   GPIO_NUM_1
#define MOTOR_LEFT_IN2   GPIO_NUM_2
#define MOTOR_RIGHT_IN1  GPIO_NUM_3
#define MOTOR_RIGHT_IN2  GPIO_NUM_4
#define MOTOR_DRV_SLEEP  GPIO_NUM_5

typedef enum {
    MOTOR_STOP    = 0,
    MOTOR_FORWARD = 1,
    MOTOR_BACKWARD = 2,
} motor_dir_t;

void motor_init(void);
void motor_set(motor_dir_t left, motor_dir_t right);
void motor_forward(void);
void motor_backward(void);
void motor_stop(void);
void motor_sleep(bool sleep);
