#include "motor.h"
#include "driver/gpio.h"

static void _set_pin(gpio_num_t pin, int level) {
    gpio_set_level(pin, level);
}

void motor_init(void) {
    gpio_config_t cfg = {
        .pin_bit_mask = (1ULL << MOTOR_LEFT_IN1)  | (1ULL << MOTOR_LEFT_IN2)  |
                        (1ULL << MOTOR_RIGHT_IN1) | (1ULL << MOTOR_RIGHT_IN2) |
                        (1ULL << MOTOR_DRV_SLEEP),
        .mode         = GPIO_MODE_OUTPUT,
        .pull_up_en   = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    gpio_config(&cfg);
    motor_stop();
    motor_sleep(false);
}

void motor_set(motor_dir_t left, motor_dir_t right) {
    // Left motor
    _set_pin(MOTOR_LEFT_IN1,  left  == MOTOR_FORWARD  ? 1 : 0);
    _set_pin(MOTOR_LEFT_IN2,  left  == MOTOR_BACKWARD ? 1 : 0);
    // Right motor
    _set_pin(MOTOR_RIGHT_IN1, right == MOTOR_FORWARD  ? 1 : 0);
    _set_pin(MOTOR_RIGHT_IN2, right == MOTOR_BACKWARD ? 1 : 0);
}

void motor_forward(void)  { motor_set(MOTOR_FORWARD,  MOTOR_FORWARD);  }
void motor_backward(void) { motor_set(MOTOR_BACKWARD, MOTOR_BACKWARD); }
void motor_stop(void)     { motor_set(MOTOR_STOP,     MOTOR_STOP);     }
void motor_sleep(bool s)  { _set_pin(MOTOR_DRV_SLEEP, s ? 0 : 1);     }
