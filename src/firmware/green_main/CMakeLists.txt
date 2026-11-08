cmake_minimum_required(VERSION 3.13)

# Salix Main I/O Processor currently targets the green Raspberry Pi Pico 2 W.
# Keep this before importing the SDK so board-specific configuration is active
# during SDK initialization.
set(PICO_BOARD pico2_w CACHE STRING "Raspberry Pi Pico board target")

include(pico_sdk_import.cmake)

project(salix_green_main C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# GREEN 0.2 uses TinyUSB host over the external Pico-PIO-USB dependency.
# Keep the dependency outside this repository and make its location explicit.
if(DEFINED ENV{PICO_PIO_USB_PATH} AND NOT PICO_PIO_USB_PATH)
    set(PICO_PIO_USB_PATH "$ENV{PICO_PIO_USB_PATH}" CACHE PATH
        "Path to the pinned Pico-PIO-USB checkout"
    )
    message("Using PICO_PIO_USB_PATH from environment ('${PICO_PIO_USB_PATH}')")
endif()

if(NOT PICO_PIO_USB_PATH)
    message(FATAL_ERROR
        "GREEN 0.2 requires PICO_PIO_USB_PATH. "
        "Point it at the pinned Pico-PIO-USB 0.7.3 checkout."
    )
endif()

if(NOT EXISTS "${PICO_PIO_USB_PATH}/src/pio_usb.c")
    message(FATAL_ERROR
        "PICO_PIO_USB_PATH does not contain src/pio_usb.c: "
        "${PICO_PIO_USB_PATH}"
    )
endif()

pico_sdk_init()

if(PICO_SDK_VERSION_STRING VERSION_LESS "2.3.0")
    message(FATAL_ERROR
        "Salix green-main firmware requires Raspberry Pi Pico SDK 2.3.0 or newer. "
        "Detected: ${PICO_SDK_VERSION_STRING}"
    )
endif()

if(NOT TARGET tinyusb_pico_pio_usb)
    message(FATAL_ERROR
        "TinyUSB did not expose tinyusb_pico_pio_usb. "
        "Check PICO_PIO_USB_PATH and the Pico SDK/TinyUSB checkout."
    )
endif()

add_executable(salix_green_main
    src/main.cpp
)

# Our dual-role TinyUSB configuration must win over the device-only stdio
# default configuration supplied by the Pico SDK.
target_include_directories(salix_green_main
    BEFORE
    PRIVATE
        ${CMAKE_CURRENT_LIST_DIR}/src
)

target_link_libraries(salix_green_main
    PRIVATE
        pico_stdlib
        pico_multicore
        pico_util
        tinyusb_host
        tinyusb_pico_pio_usb
)

target_compile_definitions(salix_green_main
    PRIVATE
        # TinyUSB host uses Pico-PIO-USB on roothub port 1.
        CFG_TUH_RPI_PIO_USB=1

        # main.cpp initializes native USB device mode explicitly before
        # stdio_init_all(), then initializes the PIO host stack on core 1.
        PICO_STDIO_USB_ENABLE_TINYUSB_INIT=0
)

target_compile_options(salix_green_main
    PRIVATE
        -Wall
        -Wextra
        -Wpedantic
)

if(COMMAND suppress_tinyusb_warnings)
    suppress_tinyusb_warnings()
endif()

# Native USB remains device-side CDC/stdout diagnostics to ERIDU.
# The separate PRIMARY-1 USB host runs over GP16/GP17 through Pico-PIO-USB.
pico_enable_stdio_usb(salix_green_main 1)
pico_enable_stdio_uart(salix_green_main 0)

# Generate .uf2 plus the normal ELF/BIN/HEX outputs.
pico_add_extra_outputs(salix_green_main)
