# PAL SNES Physical Validation — 2026-10-25

## Hardware

- PAL Super Nintendo Entertainment System
- Raspberry Pi Pico 2 W
- Duinotech XC4486 two-channel logic-level converter
- Clone SNES/SFC controller cable

## Confirmed SNES cable mapping

| SNES pin | Conductor | Function |
| ---: | --- | --- |
| 1 | White | +5 V |
| 2 | Blue | Clock |
| 3 | Yellow | Latch |
| 4 | Red | Serial Data |
| 5 | — | Unused for standard pad |
| 6 | — | Unused for standard pad |
| 7 | Brown | Ground |

## Bridge signal mapping

- Clock: SNES pin 2 -> XC4486 5 V-to-3.3 V receive path -> Pico GP2
- Latch: SNES pin 3 -> XC4486 5 V-to-3.3 V receive path -> Pico GP3
- Data: Pico GP4 -> XC4486 3.3 V-to-5 V transmit path -> SNES pin 4
- XC4486 HV: SNES +5 V
- XC4486 LV: Pico 3V3
- Common ground: SNES pin 7 / XC4486 GND / Pico GND

## Physical validation result

The corrected Pico firmware and deterministic host test sender were validated on the physical PAL SNES.

Observed successful test states:

| Test | Host logical mask |
| --- | ---: |
| UP | 0xFFEF |
| B | 0xFFFE |
| START | 0xFFF7 |
| DOWN | 0xFFDF |
| R | 0xF7FF |

The console responded correctly to the commanded states and remained stable during testing.

## Significance

This validates the SNES-facing path independently of the USB fight stick:

PC serial test sender -> Pico 2 W -> PIO SNES controller emulation -> XC4486 level conversion -> physical PAL SNES.

The next validation stage is the live Mayflash F300 PS3/DINPUT input path through `src/pc_host/bridge.py`.
