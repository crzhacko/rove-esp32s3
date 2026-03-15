idf_component_register(
    SRCS "voice.c"
    INCLUDE_DIRS "include"
    REQUIRES driver esp_driver_i2s
)
