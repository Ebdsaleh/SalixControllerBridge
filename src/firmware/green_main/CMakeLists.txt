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

pico_sdk_init()

if(PICO_SDK_VERSION_STRING VERSION_LESS "2.3.0")
    message(FATAL_ERROR
        "Salix green-main firmware requires Raspberry Pi Pico SDK 2.3.0 or newer. "
        "Detected: ${PICO_SDK_VERSION_STRING}"
    )
endif()

add_executable(salix_green_main
    src/main.cpp
)

target_link_libraries(salix_green_main
    PRIVATE
        pico_stdlib
)

target_compile_options(salix_green_main
    PRIVATE
        -Wall
        -Wextra
        -Wpedantic
)

# Development milestone 0.1:
# - native USB = device-side CDC/stdout diagnostics
# - UART stdio disabled so the normal Pico USB connector is the one debug path
pico_enable_stdio_usb(salix_green_main 1)
pico_enable_stdio_uart(salix_green_main 0)

# Generate .uf2 plus the normal ELF/BIN/HEX outputs.
pico_add_extra_outputs(salix_green_main)
