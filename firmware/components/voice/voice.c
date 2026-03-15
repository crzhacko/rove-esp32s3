#include "voice.h"
#include "driver/i2s_std.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

/* ---- optional ESP-SR integration ----------------------------------------
 * ESP-SR (esp-sr component) provides wake-word detection (WakeNet) and
 * command recognition (MultiNet). It is available in ESP-IDF v5.x via the
 * managed components registry:
 *
 *   idf_component.yml:
 *     dependencies:
 *       espressif/esp-sr: ">=1.0.0"
 *
 * When CONFIG_USE_ESP_SR is enabled (set in sdkconfig / Kconfig), the full
 * pipeline runs.  Without it, raw I2S audio is captured but recognition is
 * a no-op — useful for prototyping on boards without sufficient PSRAM.
 * -------------------------------------------------------------------------*/

#ifdef CONFIG_USE_ESP_SR
#include "esp_wn_iface.h"
#include "esp_wn_models.h"
#include "esp_mn_iface.h"
#include "esp_mn_models.h"
#include "model_path.h"
#endif

#define TAG             "voice"
#define SAMPLE_RATE     16000
#define DMA_BUF_COUNT   3
#define DMA_BUF_FRAMES  1024  /* frames per DMA buffer */

static i2s_chan_handle_t  _rx_chan = NULL;
static voice_cmd_cb_t     _cmd_cb  = NULL;
static TaskHandle_t       _task    = NULL;

/* ---------- I2S initialisation ------------------------------------------ */

static void _i2s_init(void) {
    i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(
        I2S_NUM_0, I2S_ROLE_MASTER);
    chan_cfg.dma_desc_num  = DMA_BUF_COUNT;
    chan_cfg.dma_frame_num = DMA_BUF_FRAMES;
    ESP_ERROR_CHECK(i2s_new_channel(&chan_cfg, NULL, &_rx_chan));

    i2s_std_config_t std_cfg = {
        .clk_cfg  = I2S_STD_CLK_DEFAULT_CONFIG(SAMPLE_RATE),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(
            I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_MONO),
        .gpio_cfg = {
            .mclk = I2S_GPIO_UNUSED,
            .bclk = VOICE_I2S_SCK,
            .ws   = VOICE_I2S_WS,
            .dout = I2S_GPIO_UNUSED,
            .din  = VOICE_I2S_SD,
            .invert_flags = {
                .mclk_inv = false,
                .bclk_inv = false,
                .ws_inv   = false,
            },
        },
    };
    ESP_ERROR_CHECK(i2s_channel_init_std_mode(_rx_chan, &std_cfg));
    ESP_ERROR_CHECK(i2s_channel_enable(_rx_chan));
}

/* ---------- Recognition task -------------------------------------------- */

static void _voice_task(void *arg) {
#ifdef CONFIG_USE_ESP_SR
    /* Allocate scratch buffer: 32-bit I2S samples → 16-bit PCM for ESP-SR */
    const int frames = DMA_BUF_FRAMES;
    int32_t  *raw   = malloc(frames * sizeof(int32_t));
    int16_t  *pcm   = malloc(frames * sizeof(int16_t));

    srmodel_list_t *models = esp_srmodel_init("model");
    char *wn_name = esp_srmodel_filter(models, ESP_WN_PREFIX, NULL);
    char *mn_name = esp_srmodel_filter(models, ESP_MN_PREFIX, "en");

    const esp_wn_iface_t *wakenet = &WAKENET_MODEL;
    model_iface_data_t   *wn_model = wakenet->create(wn_name, DET_MODE_90);
    int wn_chunk = wakenet->get_samp_chunksize(wn_model);

    const esp_mn_iface_t *multinet = &MULTINET_MODEL;
    model_iface_data_t   *mn_model = multinet->create(mn_name, 6000);

    /* Add movement commands (IDs must match voice_cmd_t values) */
    esp_mn_commands_clear(mn_model);
    esp_mn_commands_add(mn_model, VOICE_CMD_FORWARD,  "go forward");
    esp_mn_commands_add(mn_model, VOICE_CMD_BACKWARD, "go backward");
    esp_mn_commands_add(mn_model, VOICE_CMD_LEFT,     "turn left");
    esp_mn_commands_add(mn_model, VOICE_CMD_RIGHT,    "turn right");
    esp_mn_commands_add(mn_model, VOICE_CMD_STOP,     "stop");
    esp_mn_commands_update(mn_model);

    bool awake = false;
    size_t bytes_read;

    while (true) {
        i2s_channel_read(_rx_chan, raw, frames * sizeof(int32_t), &bytes_read, portMAX_DELAY);
        int actual = bytes_read / sizeof(int32_t);
        /* Shift 32-bit I2S data to 16-bit (INMP441 data is left-justified) */
        for (int i = 0; i < actual; i++) {
            pcm[i] = (int16_t)(raw[i] >> 14);
        }

        if (!awake) {
            wn_state_t state = wakenet->detect(wn_model, pcm);
            if (state == WAKENET_DETECTED) {
                ESP_LOGI(TAG, "wake word detected");
                awake = true;
                multinet->clean(mn_model);
            }
        } else {
            esp_mn_state_t mn_state = multinet->detect(mn_model, pcm);
            if (mn_state == ESP_MN_STATE_DETECTED) {
                esp_mn_results_t *res = multinet->get_results(mn_model);
                voice_cmd_t cmd = (voice_cmd_t)res->command_id[0];
                ESP_LOGI(TAG, "command: %d", cmd);
                if (_cmd_cb) _cmd_cb(cmd);
                awake = false;
            } else if (mn_state == ESP_MN_STATE_TIMEOUT) {
                ESP_LOGD(TAG, "command timeout, sleeping");
                awake = false;
            }
        }
    }
    /* unreachable */
    free(raw);
    free(pcm);
#else
    /* Without ESP-SR: just drain the I2S FIFO so DMA doesn't stall */
    const int frames = DMA_BUF_FRAMES;
    int32_t *buf = malloc(frames * sizeof(int32_t));
    size_t bytes_read;
    while (true) {
        i2s_channel_read(_rx_chan, buf, frames * sizeof(int32_t), &bytes_read, portMAX_DELAY);
    }
    free(buf);
#endif
    vTaskDelete(NULL);
}

/* ---------- Public API --------------------------------------------------- */

void voice_init(voice_cmd_cb_t cb) {
    _cmd_cb = cb;
    _i2s_init();
}

void voice_start(void) {
    if (_task) return;
    xTaskCreatePinnedToCore(_voice_task, "voice", 8192, NULL, 5, &_task, 1);
}

void voice_stop(void) {
    if (!_task) return;
    vTaskDelete(_task);
    _task = NULL;
}
