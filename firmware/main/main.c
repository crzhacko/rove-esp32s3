#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "motor.h"

#if defined(CONFIG_ROVE_VARIANT_ROVE_S)  || \
    defined(CONFIG_ROVE_VARIANT_ROVE_SV) || \
    defined(CONFIG_ROVE_VARIANT_ROVE_SVX)
#  define HAS_SERVO
#  include "servo.h"
#endif

#if defined(CONFIG_ROVE_VARIANT_ROVE_V)  || \
    defined(CONFIG_ROVE_VARIANT_ROVE_SV) || \
    defined(CONFIG_ROVE_VARIANT_ROVE_SVX)
#  define HAS_VOICE
#  include "voice.h"
#endif

#define TAG "rove"

#ifdef HAS_VOICE
static void on_voice_cmd(voice_cmd_t cmd) {
    switch (cmd) {
        case VOICE_CMD_FORWARD:  motor_forward();  break;
        case VOICE_CMD_BACKWARD: motor_backward(); break;
        case VOICE_CMD_LEFT:     motor_set(MOTOR_BACKWARD, MOTOR_FORWARD);  break;
        case VOICE_CMD_RIGHT:    motor_set(MOTOR_FORWARD,  MOTOR_BACKWARD); break;
        case VOICE_CMD_STOP:     /* fall-through */
        default:                 motor_stop(); break;
    }
}
#endif

void app_main(void) {
    ESP_LOGI(TAG, "ROVE firmware starting");

    motor_init();

#ifdef HAS_SERVO
    servo_init();
    /* Default: boom and bucket at neutral (90°) */
    servo_boom(90);
    servo_bucket(90);
#endif

#ifdef HAS_VOICE
    voice_init(on_voice_cmd);
    voice_start();
    ESP_LOGI(TAG, "voice recognition active");
#else
    /* No voice: drive a short demo pattern then stop */
    ESP_LOGI(TAG, "no voice — running demo");
    motor_forward();
    vTaskDelay(pdMS_TO_TICKS(2000));
    motor_backward();
    vTaskDelay(pdMS_TO_TICKS(2000));
    motor_stop();
#endif

    /* main task can exit; voice task keeps running on core 1 */
}
