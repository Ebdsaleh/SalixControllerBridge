# Rev-A GPIO / Resource Map

## Pico-A — Realtime / Bridge (Pico 2 W preferred)

| GPIO | Rev-A role | Notes |
|---|---|---|
| GP0–GP7 | MODULE_PIO[0..7] | Direct low-latency console-module lane pool. GP3/4/5 deliberately preserve the proven SNES prototype grouping. |
| GP8 | Developer UART TX / spare | Not required for shipping firmware. |
| GP9 | Developer UART RX / spare | Not required for shipping firmware. |
| GP10 | Inter-Pico SPI1 SCK | Pico-A intended SPI master. |
| GP11 | Inter-Pico SPI1 MOSI | A TX → B GP12 (SPI1 RX). |
| GP12 | Inter-Pico SPI1 MISO | A RX ← B GP11 (SPI1 TX). |
| GP13 | Inter-Pico SPI1 CS | Selects Pico-B service RPC endpoint. |
| GP14 | A→B IRQ | Runtime notification / heartbeat assistance. |
| GP15 | B→A IRQ | Service/update/profile notification. |
| GP16 | USB hub root D+ | One PIO-USB root only. 22Ω series resistor near Pico. |
| GP17 | USB hub root D− | One PIO-USB root only. 22Ω series resistor near Pico. |
| GP18 | Console-module SPI0 SCK | Shared active-card high-speed link. |
| GP19 | Console-module SPI0 MOSI | Shared active-card high-speed link. |
| GP20 | Console-module SPI0 MISO | Shared active-card high-speed link. |
| GP21 | Console-module SPI0 CS | Active-card selection/data path. |
| GP22 | Console-module IRQ | Active module event line. |
| GP26–GP28 | FREE / RAW | Intentionally left free in Rev A. |
| RUN | Pico-A reset | Also controllable by Pico-B recovery path. |

Retired bench mapping: GP18/GP19 are no longer a second PIO-USB root. The 4-port hub collapses all four logical USB input banks to one GP16/GP17 root.

## Pico-B — Service / Storage / UI (red USB-C Pico 2 preferred)

| GPIO | Rev-A role | Notes |
|---|---|---|
| GP0 | Management I²C SDA | Motherboard / future module-management devices. |
| GP1 | Management I²C SCL | Motherboard / future module-management devices. |
| GP2 | FAN0 PWM / ENABLE | 2N7002 open-drain PWM command; FAN0 5V is switched by TPS22919DCK. |
| GP3 | FAN0 TACH | Tach input with 10k pull-up to 3V3_AUX. |
| GP4 | TFT touch IRQ | TF034 touch interrupt. |
| GP5 | TFT backlight PWM | Drives backlight driver/enable, not backlight current directly. |
| GP6 | TFT RESET | Front TF034 display. |
| GP7 | TFT D/C | Front TF034 display. |
| GP8 | TFT TOUCH_CS | Shared service SPI bus. |
| GP9 | TFT LCD_CS | Shared service SPI bus. |
| GP10 | Inter-Pico SPI1 SCK | Clock from Pico-A master. |
| GP11 | Inter-Pico SPI1 MISO | B TX → A GP12. |
| GP12 | Inter-Pico SPI1 MOSI | B RX ← A GP11. |
| GP13 | Inter-Pico SPI1 CS | Chip-select from Pico-A. |
| GP14 | FAN1 PWM / ENABLE | 2N7002 open-drain PWM command; FAN1 5V is switched by TPS22919DCK. |
| GP15 | FAN1 TACH | Second fan tach input with 10k pull-up to 3V3_AUX. |
| GP16 | B→A IRQ | Connects to Pico-A GP15. |
| GP17 | A→B IRQ | Connects from Pico-A GP14. |
| GP18 | TFT+SD SPI0 SCK | Shared non-realtime service bus. |
| GP19 | TFT+SD SPI0 MOSI | Shared bus. |
| GP20 | TFT+SD SPI0 MISO | Shared bus. |
| GP21 | SD_CS | microSD exclusively owned by Pico-B. |
| GP22 | USB2514B RESET_N | Hard hub reset / recovery; Pico-B may assert low during service/update or fault recovery. |
| GP26 | Pico-A SWDIO | In-system programming/recovery. |
| GP27 | Pico-A SWCLK | In-system programming/recovery. |
| GP28 | Pico-A RUN | Hard reset/recovery control. |

## Rev-A cross-sheet net names

The frozen inter-Pico physical nets are:
- `RPC_SCK`: Pico-A GP10 ↔ Pico-B GP10.
- `RPC_MOSI`: Pico-A GP11 → Pico-B GP12.
- `RPC_MISO`: Pico-B GP11 → Pico-A GP12.
- `RPC_CS_N`: Pico-A GP13 → Pico-B GP13.
- `IRQ_A2B`: Pico-A GP14 → Pico-B GP17.
- `IRQ_B2A`: Pico-B GP16 → Pico-A GP15.
- `FAN0_PWM_EN` / `FAN0_TACH`: Pico-B GP2 / GP3.
- `FAN1_PWM_EN` / `FAN1_TACH`: Pico-B GP14 / GP15.

The fan power paths are implemented: 5V_MAIN -> TPS22919DCK load switch -> FANx_5V, with local input/output capacitance, open-drain 2N7002 PWM sinks, and 10k tach pull-ups to 3V3_AUX.

## Power / physical constraints

- Both Pico modules remain socketed.
- Pico-A exposes a complete second pair of 1×20 raw breakout rails mirroring physical pins 1–40.
- Pico-B owns the rear DEBUG/UPDATE USB-C service path.
- PRIMARY and EXTENDED USB input boards route only through the 4-port hub to Pico-A.
- Two fan headers are provisioned; cooling is a Pico-B/system-management responsibility.
- Console personality cards are not hot-swappable in Rev A.

Pico-B motherboard-intentional NC pins:
- pin 30 RUN: left open; Pico 2 has an internal RUN pull-up.
- pin 35 ADC_VREF: no motherboard ADC reference load is used.
- pin 36 3V3_OUT: motherboard logic uses independent 3V3_AUX instead.
- pin 37 3V3_EN: left open so the Pico 2 on-board 100k pull-up keeps its SMPS enabled.
- pin 40 VBUS: not connected to motherboard power; Pico-B is powered through VSYS and its own USB connector may still see VBUS locally.

Pico-B GP28 is now hard-wired to Pico-A RUN as `PICO_A_RUN` for recovery/reset control.


### Pico-A SWD physical pickup

Pico-B recovery nets are now electrically terminated at motherboard contact interface `J12`:

- J12 pin 1 = `PICO_A_SWCLK`
- J12 pin 2 = `GND`
- J12 pin 3 = `PICO_A_SWDIO`

Pico-B GP27 drives SWCLK and GP26 carries SWDIO. Pico-B GP28 already controls Pico-A RUN.

J12 represents spring/pogo contacts that physically touch the Pico-A SWD pads; it is not a normal 40-pin Pico header connection. Raspberry Pi's SWD interface is three wires only and does not carry target power.

The exact J12 footprint is deliberately left mechanical-TBD until the Pico-A variant is frozen. Pico 2 W places its SWD pads centrally below the MCU, while non-wireless Pico 2 uses a different physical location. Rev-A software therefore requires a custom Pico-B SWD/recovery implementation on GP26/GP27 rather than assuming the stock Raspberry Pi debugprobe GPIO map.


### Rev-A microSD SPI wiring

The Pico-B service SPI0 bus is now electrically terminated at microSD socket `J13`:

- GP18 = `SERVICE_SPI_SCK` -> microSD CLK (pin 5).
- GP19 = `SERVICE_SPI_MOSI` -> microSD CMD/DI (pin 3).
- GP20 = `SERVICE_SPI_MISO` <- microSD DAT0/DO (pin 7).
- GP21 = `SD_CS_N` -> microSD DAT3/CS (pin 2).

microSD VDD is powered directly from `3V3_AUX`; VSS is GND.

Host-side 47k pull-ups are fitted on CMD and DAT0-DAT3, including the SPI-reserved DAT1/DAT2 contacts. Local 100nF + 10uF bypass capacitance is fitted at the socket supply.

Rev A does not allocate a separate card-detect GPIO. Presence is detected in firmware by card initialization/response.

The exact push-push/push-pull microSD socket footprint remains mechanical-TBD.


### Front-panel UI logical interface

Rev-A terminates the six TFT-specific Pico-B GPIOs at logical 12-position service connector `J14` rather than hard-coding an undocumented TF034 module pinout.

J14 logical pinout:
1. GND
2. 3V3_AUX logic supply
3. 5V_MAIN auxiliary panel/backlight supply
4. TFT_SPI_SCK
5. TFT_SPI_MOSI
6. TFT_SPI_MISO
7. TFT_LCD_CS_N
8. TFT_TOUCH_CS_N
9. TFT_DC
10. TFT_RESET
11. TFT_TOUCH_IRQ
12. TFT_BL_PWM (logic only)

Pico-B mappings:
- GP4 = TFT_TOUCH_IRQ
- GP5 = TFT_BL_PWM
- GP6 = TFT_RESET
- GP7 = TFT_DC
- GP8 = TFT_TOUCH_CS_N
- GP9 = TFT_LCD_CS_N

The TFT branch shares Pico-B SPI0 with microSD through separate 33R series resistors on SCK/MOSI/MISO. LCD_CS_N and TOUCH_CS_N each default high through 47k pull-ups; TFT_BL_PWM defaults low through 100k so the backlight command is off during reset/boot.

The actual TF034 panel pinout, backlight current driver and cable/harness belong on the front-panel adapter and remain module-specific. J14's exact keyed connector footprint is mechanical-TBD.
