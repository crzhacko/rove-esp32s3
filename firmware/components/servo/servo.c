#include "servo.h"
#include "driver/ledc.h"
#include "esp_log.h"

#define LEDC_TIMER      LEDC_TIMER_0
#define LEDC_MODE       LEDC_LOW_SPEED_MODE
#define LEDC_FREQ_HZ    50
#define LEDC_RESOLUTION LEDC_TIMER_14_BIT  /* 16384 ticks */
#define PERIOD_US       20000              /* 20ms */

static uint32_t _us_to_duty(uint32_t us) {
    return (us * (1 << LEDC_RESOLUTION)) / PERIOD_US;
}

static void _init_channel(ledc_channel_t ch, gpio_num_t pin) {
    ledc_channel_config_t cfg = {
        .gpio_num   = pin,
        .speed_mode = LEDC_MODE,
        .channel    = ch,
        .timer_sel  = LEDC_TIMER,
        .duty       = _us_to_duty(1500),
        .hpoint     = 0,
    };
    ledc_channel_config(&cfg);
}

void servo_init(void) {
    ledc_timer_config_t timer = {
        .speed_mode      = LEDC_MODE,
        .duty_resolution = LEDC_RESOLUTION,
        .timer_num       = LEDC_TIMER,
        .freq_hz         = LEDC_FREQ_HZ,
        .clk_cfg         = LEDC_AUTO_CLK,
    };
    ledc_timer_config(&timer);
    _init_channel(LEDC_CHANNEL_0, SERVO_BOOM_PIN);
    _init_channel(LEDC_CHANNEL_1, SERVO_BUCKET_PIN);
}

void servo_set_angle(gpio_num_t pin, uint8_t deg) {
    uint32_t us   = 500 + (deg * 2000) / 180;  /* 500~2500us */
    uint32_t duty = _us_to_duty(us);
    ledc_channel_t ch = (pin == SERVO_BOOM_PIN) ? LEDC_CHANNEL_0 : LEDC_CHANNEL_1;
    ledc_set_duty(LEDC_MODE, ch, duty);
    ledc_update_duty(LEDC_MODE, ch);
}

void servo_boom(uint8_t deg)   { servo_set_angle(SERVO_BOOM_PIN,   deg); }
void servo_bucket(uint8_t deg) { servo_set_angle(SERVO_BUCKET_PIN, deg); }
