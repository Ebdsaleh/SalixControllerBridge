# Salix Main I/O Firmware

This directory contains the compiled standalone firmware for the **green
Raspberry Pi Pico 2 W**, the SalixControllerBridge real-time Main/Master I/O
Processor.

The existing Python and MicroPython implementations remain in the repository as
known-good behavioral references. They are not removed by the native firmware
work.

## Milestone 0.1 — accepted

GREEN 0.1 proved:

```text
power on
  -> compiled Pico SDK firmware boots from flash
  -> no MicroPython / REPL dependency
  -> native USB exposes CDC/stdout diagnostics
  -> repeating heartbeat proves the firmware stays alive
  -> cold unplug/replug boots autonomously
```

The milestone was physically accepted on the green Pico 2 W.

## Milestone 0.2 — PRIMARY-1 HID host bring-up

GREEN 0.2 adds exactly one standalone controller input path:

```text
PRIMARY-1 USB-A
  -> D+ GP16 / D- GP17
  -> Pico-PIO-USB
  -> TinyUSB host HID
  -> VID / PID / address / interface / protocol
  -> raw HID report bytes
  -> native USB CDC diagnostics
  -> src/pc_host/pico_monitor.py
```

This milestone deliberately does **not** normalize controller state and does
**not** drive the SNES backend yet.

PRIMARY-2 remains reserved on GP18/GP19 but disabled.

## PRIMARY USB electrical rules

Accepted prototype mapping:

```text
PRIMARY-1
  D+ -> GP16
  D- -> GP17

PRIMARY-2
  D+ -> GP18
  D- -> GP19
```

Additional constraints:

- Pico-PIO-USB recommends 22 ohm series resistors on D+ and D- for improved
  signal integrity, but they are not a hard prerequisite for this short-wire
  prototype;
- first bring-up may use direct GP16/GP17 connections;
- if enumeration is unreliable or the data wiring is lengthened, fit 22-27 ohm
  series resistors close to the GREEN GPIO pins before changing firmware;
- keep the D+/D- pair short and close together;
- common USB/Salix ground;
- do not put the XC4486 level shifter in USB D+/D-;
- PRIMARY USB VBUS is supplied through the accepted prototype USB Power
  Distribution Rev A board;
- the Rev A removable jumper isolates source +5 V from the USB +5 V rail;
- Rev A is accepted for bench bring-up, while per-port current limiting/PTC
  protection remains a later hardware-hardening item;
- GP2/GP3/GP4 remain reserved for the proven SNES prototype.

The GREEN 0.2 software-only host initialization has been physically accepted.
The next physical test reconnects Rev A and PRIMARY-1 in a staged power-only,
then data/HID sequence.

## Requirements

Pinned ERIDU environment:

- Raspberry Pi Pico SDK 2.3.1
- ARM GNU Toolchain 14.2.Rel1 / GCC 14.2.1
- CMake 4.3.2
- Ninja 1.12.1
- picotool 2.3.1
- Pico-PIO-USB 0.7.3 at commit `b186e36`

Expected Pico-PIO-USB source path:

```text
C:\Users\Developer.ERIDU\repos\apps_source\Pico-PIO-USB-0.7.3
```

`prepare-pico-sdk.bat` should export:

```text
PICO_SDK_PATH
PICO_ARM_TOOLCHAIN_PATH
PICO_TOOLCHAIN_PATH
PICOTOOL_ROOT
picotool_DIR
PICO_PIO_USB_PATH
CMAKE_GENERATOR
```

## Clock choice

Pico-PIO-USB requires the system clock to be a multiple of 12 MHz. GREEN 0.2
uses **120 MHz** during bring-up, matching the conservative upstream dual-USB
example.

This is intentional; it is not an RP2350 performance target.

## Configure and build

From the repository root:

```bat
prepare-pico-sdk
if exist "%TEMP%\SalixControllerBridge_green_main" rmdir /s /q "%TEMP%\SalixControllerBridge_green_main"
cmake -S src\firmware\green_main -B "%TEMP%\SalixControllerBridge_green_main" -G Ninja -DPICO_BOARD=pico2_w
cmake --build "%TEMP%\SalixControllerBridge_green_main"
```

Expected UF2:

```text
%TEMP%\SalixControllerBridge_green_main\salix_green_main.uf2
```

## Flash

1. Stop `pico_monitor.py` so the native CDC port is released.
2. Put the green Pico 2 W into BOOTSEL.
3. Copy `salix_green_main.uf2` to the RP2350 mass-storage drive.
4. The Pico reboots automatically into the compiled firmware.

The existing MicroPython reference implementation remains in the repository.

## Expected diagnostics

Monitor the native CDC port with:

```bat
py src\pc_host\pico_monitor.py
```

Before any controller is attached, expected GREEN 0.2 output includes:

```text
SalixControllerBridge - Main I/O Processor
Firmware milestone: green-main 0.2
System clock: 120000 kHz
Native USB: CDC/stdout diagnostics
PRIMARY-1 USB host: PIO USB D+=GP16 D-=GP17
PRIMARY-2 USB host: reserved / disabled
SNES backend: not enabled in this milestone

[PRIMARY-1] host ready rhport=1 D+=GP16 D-=GP17
[PRIMARY-1] bus lines D+=0 D-=0 state=SE0/no-device
[green-main] heartbeat=...
```

With Power Distribution Rev A reconnected and a controller attached to
PRIMARY-1, GREEN also reports the raw electrical state of GP16/GP17 whenever
it changes:

```text
D+=0 D-=0 -> SE0/no-device
D+=1 D-=0 -> FS-idle (normal full-speed attachment)
D+=0 D-=1 -> LS-idle (low-speed attachment, or possible D+/D- reversal for a
              controller expected to be full-speed)
D+=1 D-=1 -> SE1/invalid
```

The enumeration target is then:

```text
[PRIMARY-1] USB device mount vid=.... pid=.... addr=...
[PRIMARY-1] HID mount vid=.... pid=.... addr=... instance=... interface=... protocol=...
[PRIMARY-1] HID report ... data=...
```

Gamepads and arcade sticks commonly use HID protocol `None`; GREEN 0.2 requests
reports for every HID protocol rather than only boot keyboards/mice.

## Next milestone

Only after PRIMARY-1 enumeration and raw reports are physically proven:

```text
raw HID
  -> Salix input-device/profile layer
  -> normalized GamepadState / MouseState / KeyboardState
  -> selected console personality
```

The known-good SNES pad/mouse behavior will then be migrated from
`src/pico_client/main.py` without changing its proven external semantics.


## GREEN 0.2 PRIMARY-1 physical HID acceptance

The Mayflash F300 has now been physically captured through PRIMARY-1.

GREEN received continuous 8-byte HID reports on address 1 / interface 0.
Neutral payload:

```text
00 00 0F 80 80 80 80 00
```

Observed movement changed the payload, including axis values reaching
`00` and `FF`.

This physically proves:

- PRIMARY-1 VBUS/GND power path;
- GP16/GP17 PIO USB electrical/data path;
- TinyUSB enumeration/HID receive path;
- native CDC reporting of live controller data.

The current breadboard-kit female Dupont sockets have shown orientation/contact
sensitivity. That is treated as a prototype connector-quality issue; a good
female contact should not depend on rotational orientation around a square
header pin.
