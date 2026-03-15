#pragma once
#include <stdbool.h>
#include "driver/gpio.h"

/**
 * ROVE - Voice Component (INMP441 I2S + ESP-SR)
 *
 * Used by: ROVE-V, ROVE-SV, ROVE-SVX
 * NOT used by: ROVE, ROVE-S
 *
 * I2S pins: I2S_WS=IO15, I2S_SCK=IO16, I2S_SD=IO17 (L/R select = GND → left channel)
 * Recognition: wake word "Hey ESP" + commands: forward, backward, stop, left, right
 */

#define VOICE_I2S_WS    GPIO_NUM_15
#define VOICE_I2S_SCK   GPIO_NUM_16
#define VOICE_I2S_SD    GPIO_NUM_17

typedef enum {
    VOICE_CMD_NONE     = 0,
    VOICE_CMD_FORWARD  = 1,
    VOICE_CMD_BACKWARD = 2,
    VOICE_CMD_LEFT     = 3,
    VOICE_CMD_RIGHT    = 4,
    VOICE_CMD_STOP     = 5,
} voice_cmd_t;

typedef void (*voice_cmd_cb_t)(voice_cmd_t cmd);

/* Initialize I2S and ESP-SR pipeline; cb is called from the recognition task */
void voice_init(voice_cmd_cb_t cb);

/* Start recognition task (call after voice_init) */
void voice_start(void);

/* Stop recognition task */
void voice_stop(void);
