# SalixControllerBridge

SalixControllerBridge translates modern USB fight-stick/controller input into the native electrical and serial protocol expected by retro console controller ports.

The first hardware target is a **PAL Super Nintendo / Super Famicom-compatible controller port** using a **Raspberry Pi Pico 2 W** as the protocol bridge. The current PC-side controller target is a **Mayflash F300 in PS3/DINPUT mode** on Windows Server 2022 x64.

## Current status

- PC -> Pico serial framing: `AA 55 <mask-low> <mask-high>`.
- SNES 12-button active-low bit order implemented: `B Y Select Start Up Down Left Right A X L R`.
- Standard-controller signature implemented as `0000` in serial bits 12-15.
- Pico PIO shifts bit 0 first and changes to the next bit on the clock rising edge, matching the SNES controller behaviour.
- Uploaded Mayflash F300 and clone-cable captures are preserved under `docs/`.
- Physical PAL SNES validation of the corrected PIO firmware is the next checkpoint.

## SNES connector wiring

Your measured clone-cable pin numbers are the authority; do not rely on clone wire colours alone.

| SNES pin | Measured wire | Signal | Bridge connection |
| --- | --- | --- | --- |
| 1 | White | +5 V | Level shifter **HV reference/supply only** |
| 2 | Blue | Clock, SNES -> controller | Level shift 5 V -> 3.3 V -> Pico GP2 |
| 3 | Yellow | Latch, SNES -> controller | Level shift 5 V -> 3.3 V -> Pico GP3 |
| 4 | Red | Serial data, controller -> SNES | Pico GP4 -> level shift 3.3 V -> 5 V |
| 5 | N/A | Secondary data | Not used for standard pad |
| 6 | N/A | Peripheral I/O | Not used for standard pad |
| 7 | Brown | Ground | Common ground with Pico and level shifter |

**Do not connect the SNES 5 V clock/latch signals directly to Pico GPIO.** Pico 2 W GPIO is 3.3 V logic. Power the Pico from USB during development; use SNES pin 1 as the high-side reference/supply for the level shifter, not as a Pico GPIO supply.

If the level shifter has `HV`, `LV`, and `GND` rails, use SNES +5 V on `HV`, Pico `3V3` on `LV`, and a common ground.

## PC setup

```bat
py -m pip install -r requirements.txt
```

Serial-based host tools now auto-detect the Pico when exactly one likely Pico serial device is present. You can always force a specific port with a positional argument such as `COM4`, or with the compatible `--port COM4` form.

Examples:

```bat
py src\pc_host\bridge.py COM4
py src\pc_host\bridge.py --port COM4
```

If multiple Pico serial devices are connected at once, automatic selection deliberately stops and asks you to specify the desired COM port rather than guessing.

### Windows controller detection / XInput driver

If a controller is not detected or does not enumerate correctly in Windows, try installing the Microsoft XUSB/Xbox 360 controller driver from the Microsoft Update Catalog before assuming the controller is unsupported:

[Microsoft Update Catalog — XUSB/Xbox 360 Controller driver](https://www.catalog.update.microsoft.com/Search.aspx?q=4015a39c-7c66-46bb-a5bc-db6c33ca5114)

This is a troubleshooting prerequisite for devices that depend on the Windows XInput/XUSB stack; it is not required for controllers that already enumerate and work correctly.

## Pico setup

Copy:

```text
src/pico_client/main.py
```

to the Pico as:

```text
main.py
```

Then reset the Pico.

## Unified bridge launcher

`bridge.py` is now the primary user-facing launcher for both normal controller
translation and mouse emulation.

Normal controller mode is unchanged:

```bat
py src\pc_host\bridge.py COM3
```

Launch mouse emulation with either spelling:

```bat
py src\pc_host\bridge.py COM3 mouse_emu
py src\pc_host\bridge.py COM3 mouse-emu
```

Translate the PC's physical mouse into the current console mouse personality:

```bat
py src\pc_host\bridge.py COM3 mouse
```

In `mouse` mode the capture window grabs relative mouse motion; press **ESC**
in that window to release capture and exit. Physical left/right mouse buttons
map directly to MouseLeft/MouseRight. The first host proof uses the operating
system's active mouse stream; individual USB-HID device selection belongs to
the later standalone hardware-host layer.

High-DPI desktop mice use a 0.50x software gain by default, followed by a
direction-preserving per-report throw limit. This keeps Windows hardware DPI
independent from console sensitivity. Override the source gain when needed:

```bat
py src\pc_host\bridge.py COM3 mouse --mouse-gain 0.35
```

When only one likely Pico serial device is connected, the COM port can still be
auto-detected:

```bat
py src\pc_host\bridge.py mouse_emu
```

The launcher routes mouse emulation through `mouse_bridge.py`. That module owns
the console-independent relative `MouseState` and input/sensitivity behavior.
The current SNES 32-bit mouse encoder is an output personality behind that
generic layer.

The previous direct command remains valid for compatibility:

```bat
py src\pc_host\snes_mouse_bridge.py COM3
```

It is now only a thin wrapper around the generic mouse bridge.

## SNES Mouse emulation

The current Pico firmware can switch between the existing 16-bit standard-pad
personality and a 32-bit SNES Mouse personality without changing the proven SNES
wiring.

The first mouse-emulation proof deliberately uses an already-supported gamepad
as the input source before USB-mouse hosting is introduced. With the Nintendo
Switch Pro Controller:

- left analog stick -> relative mouse X/Y motion;
- D-pad -> relative mouse motion;
- canonical SNES B face position -> mouse left click;
- canonical SNES A face position -> mouse right click;
- canonical SNES L or Y position -> decrease mouse sensitivity;
- canonical SNES R or X position -> increase mouse sensitivity.

Bridge cursor sensitivity has five edge-triggered steps: VERY LOW, LOW,
MEDIUM, HIGH, and VERY HIGH. The bridge starts at MEDIUM and preserves the
physically validated MEDIUM movement rate exactly. Analog movement scales to
0.25x / 0.5x / 1.0x / 1.5x / 2.0x, while D-pad movement uses a stronger upper
curve of 0.25x / 0.5x / 1.0x / 2.0x / 3.0x. This is deliberately independent
from the SNES Mouse's hardware speed/sensitivity command protocol so the proven
MouseLeft and MouseRight report remains unchanged.

For Mario Paint, connect the proven Salix SNES adapter to controller port 1 and
run:

```bat
py src\pc_host\snes_mouse_bridge.py COM3
```

Replace `COM3` with the Pico connected to SNES controller port 1. If only one
likely Pico serial device is attached, the port argument can be omitted.

Optional motion tuning:

```bat
py src\pc_host\snes_mouse_bridge.py COM3 --max-speed 6 --dpad-speed 3
```

The first physical-validation batch reports SNES Mouse sensitivity level 0.
Console-driven sensitivity cycling is intentionally deferred until the basic
Mario Paint identification, motion, and button mapping are proven.

See `docs/validation/SNES_MOUSE_EMULATION_2026-11-02.md` for the complete
hardware acceptance checklist.

## First physical test: isolate the SNES protocol

Before involving the Mayflash mapping, test one known SNES state directly:

```bat
py src\pc_host\snes_test_pattern.py COM4 --button up
```

The script continuously presents SNES `UP` until Ctrl+C, then releases the controller state. Other useful tests:

```bat
py src\pc_host\snes_test_pattern.py COM4 --button b
py src\pc_host\snes_test_pattern.py COM4 --button start
py src\pc_host\snes_test_pattern.py COM4 --button neutral
```

If these work on the console, the SNES wiring, level conversion, serial framing, Pico parser, PIO bit order, timing, and controller signature are all proven independently of the USB fight-stick profile.

## Mayflash F300 calibration

The supplied capture proves the D-pad states are stable in PS3/DINPUT mode, but the previous source contains conflicting generations of button mapping. To identify exactly what Pygame reports on this Windows Server 2022 machine, run:

```bat
py src\pc_host\calibrate_pygame.py
```

Press one control at a time and record the printed button index for:

```text
A/Cross
B/Circle
X/Square
Y/Triangle
LB/L1
RB/R1
LT/L2
RT/R2
Select
Start
Home/PS
```

Once that table is confirmed, `bridge.py` can use a named Mayflash F300 profile rather than guessing SDL/Pygame button order.

## Existing source roles

- `src/pc_host/bridge.py` - latest Pygame -> framed serial prototype; auto-detects the Pico or accepts a positional/--port COM override.
- `src/pc_host/serial_ports.py` - shared safe Pico serial-port discovery/selection helper.
- `src/pc_host/calibrate_pygame.py` - raw Pygame index calibration tool.
- `src/pc_host/snes_test_pattern.py` - known-state SNES hardware test sender.
- `src/pc_host/probe_hid.py` - HID enumeration helper.
- `src/pc_host/inspect_packet.py` - raw HID packet inspection helper for the older direct-HID path.
- `src/pc_host/read_stick.py` - older direct-HID experiment for VID:PID `20bc:5501`; retained for reference, but its old two-byte transport does not match the current framed Pico protocol.
- `src/pico_client/main.py` - Pico 2 W SNES serial-controller emulator.

## Protocol notes

A standard SNES controller returns 16 serial bits. The first 12 are buttons and are active-low. The final four bits are the standard-controller device signature `0000`. The console controls latch and clock; the controller presents `B` first, then advances through the remaining bits as the clock cycles.


## Hardware profiler and calibration utility

SalixControllerBridge now includes a DearPyGui hardware-profiler utility. Its
desktop shell follows the same Salix application style used by SalixTorrent,
while the profile/calibration backend remains independent from DearPyGui.

Install/update dependencies:

```bat
py -m pip install -r requirements.txt
```

Launch the utility:

```bat
py src\pc_host\calibration_app.py
```

The utility creates one versioned profile per physical device and keeps every
compatible console module under that same profile.

Mouse example:

```text
Razer Naga Pro
  identity / raw baseline
  SNES.mouse
  Saturn.mouse
  Dreamcast.mouse
```

Controller example:

```text
Switch Pro
  identity / axis baseline
  SNES.pad
  SNES.mouse_emu
  Saturn.pad
  Saturn.mouse_emu
  Dreamcast.controller
  Dreamcast.mouse_emu
```

The current SNES mouse calibration launches a separate 256x224 SDL/Pygame
surface, captures unaccelerated Win32 Raw Input counts, measures four natural
full throws, derives a scalar mouse gain, and then lets the user test/adjust
that gain in the same logical console environment before saving it.

Windows pointer acceleration can be temporarily disabled during that test and
is restored automatically afterward. Raw Input remains the authoritative
measurement.

Generated profiles are stored outside the repository under the user's
application-state directory. On Windows the default location is:

```text
%LOCALAPPDATA%\SalixControllerBridge\profiles\hardware\
```

Use a calibrated physical-mouse profile:

```bat
py src\pc_host\bridge.py COM3 mouse --hardware-profile "Razer Naga Pro"
```

Use a calibrated controller mouse-emulation profile:

```bat
py src\pc_host\bridge.py COM3 mouse_emu --hardware-profile "Switch Pro"
```

A JSON profile path can be supplied instead of the profile name.

See `docs/architecture/HARDWARE_PROFILE_CALIBRATION.md` for the schema,
calibration model, Windows Raw Input behavior, and the PC-host versus final
standalone-box boundary.


### Default hardware profiles

The Hardware Profiler can mark one saved mouse profile and one saved controller
profile as the defaults for their source type.

After setting `Razer Naga Pro` as the default mouse profile:

```bat
py src\pc_host\bridge.py COM3 mouse
```

automatically loads it.

An explicit `--hardware-profile` always overrides the saved default. Use
`--no-default-profile` when you intentionally want the bridge's built-in
fallback behavior.
