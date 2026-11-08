# Salix Main I/O Firmware

This directory is the beginning of the compiled standalone firmware for the
**green Raspberry Pi Pico 2 W**, the SalixControllerBridge real-time
Main/Master I/O Processor.

The existing Python and MicroPython implementations remain in the repository as
known-good behavioral references. This firmware does **not** replace or modify
them yet.

## Milestone 0.1

The first milestone is intentionally small:

```text
power on
  -> compiled Pico SDK firmware boots from flash
  -> no MicroPython / REPL dependency
  -> native USB exposes CDC/stdout diagnostics
  -> repeating heartbeat proves the firmware stays alive
```

PRIMARY USB host support and the proven SNES backend are deliberately deferred
until this foundation builds and boots on the real green Pico 2 W.

## Requirements

- Raspberry Pi Pico SDK 2.3.0 or newer
- ARM GNU embedded toolchain
- CMake 3.13 or newer
- Ninja recommended
- Pico SDK submodules initialized so TinyUSB device support is available

Set `PICO_SDK_PATH` to the local Pico SDK checkout.

Example Windows Command Prompt setup:

```bat
set "PICO_SDK_PATH=C:\path\to\pico-sdk"
```

## Configure and build

From the repository root:

```bat
cmake -S src\firmware\green_main ^
      -B "%TEMP%\SalixControllerBridge_green_main" ^
      -G Ninja ^
      -DPICO_BOARD=pico2_w

cmake --build "%TEMP%\SalixControllerBridge_green_main"
```

Expected UF2:

```text
%TEMP%\SalixControllerBridge_green_main\salix_green_main.uf2
```

## Flash

1. Hold BOOTSEL on the green Pico 2 W while connecting USB.
2. Copy `salix_green_main.uf2` to the `RPI-RP2` drive.
3. The Pico reboots automatically into the compiled firmware.

This is destructive only to the Pico firmware image. The existing repository
files are unaffected. The current MicroPython firmware can be restored later if
needed.

## Expected diagnostic output

After the native USB CDC port appears, use the Salix Pico monitor:

```bat
py src\\pc_host\\pico_monitor.py
```

An explicit port is also accepted:

```bat
py src\\pc_host\\pico_monitor.py COM6
```

The monitor uses Ctrl+C as the exit path and closes the serial port before
returning to the command prompt.

The firmware repeatedly prints a heartbeat similar to:

```text
SalixControllerBridge - Main I/O Processor
Firmware milestone: green-main 0.1
Board role: GREEN Pico 2 W / real-time master
Runtime: Pico SDK C++ (MicroPython-free)
Native USB: CDC/stdout diagnostics
PRIMARY USB host: not enabled in this milestone
SNES backend: not enabled in this milestone

[green-main] heartbeat=0 uptime_ms=...
[green-main] heartbeat=1 uptime_ms=...
```

The firmware does not wait for a PC connection. It continues running even if
the native USB diagnostic cable is unplugged.

## Next milestone

After 0.1 is physically proven:

```text
PRIMARY-1 USB-A
    -> PIO USB host
    -> enumerate one HID controller
    -> report VID/PID/interface/raw HID reports
    -> native USB CDC diagnostics
```

Only after that path is green will the known-good SNES pad behavior be migrated
from `src/pico_client/main.py` into the compiled C++ firmware.
