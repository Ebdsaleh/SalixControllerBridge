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

The default Pico serial port in the current tools is `COM3`. Override it where a tool offers `--port` if Windows assigns another port.

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

## First physical test: isolate the SNES protocol

Before involving the Mayflash mapping, test one known SNES state directly:

```bat
py src\pc_host\snes_test_pattern.py --port COM3 --button up
```

The script continuously presents SNES `UP` until Ctrl+C, then releases the controller state. Other useful tests:

```bat
py src\pc_host\snes_test_pattern.py --port COM3 --button b
py src\pc_host\snes_test_pattern.py --port COM3 --button start
py src\pc_host\snes_test_pattern.py --port COM3 --button neutral
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

- `src/pc_host/bridge.py` - latest Pygame -> framed serial prototype.
- `src/pc_host/calibrate_pygame.py` - raw Pygame index calibration tool.
- `src/pc_host/snes_test_pattern.py` - known-state SNES hardware test sender.
- `src/pc_host/probe_hid.py` - HID enumeration helper.
- `src/pc_host/inspect_packet.py` - raw HID packet inspection helper for the older direct-HID path.
- `src/pc_host/read_stick.py` - older direct-HID experiment for VID:PID `20bc:5501`; retained for reference, but its old two-byte transport does not match the current framed Pico protocol.
- `src/pico_client/main.py` - Pico 2 W SNES serial-controller emulator.

## Protocol notes

A standard SNES controller returns 16 serial bits. The first 12 are buttons and are active-low. The final four bits are the standard-controller device signature `0000`. The console controls latch and clock; the controller presents `B` first, then advances through the remaining bits as the clock cycles.
