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
| GP2 | FAN0 PWM / ENABLE | Fan power driven from 5V_MAIN via driver/load switch. |
| GP3 | FAN0 TACH | Tach input; pull-up topology TBD with fan choice. |
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
| GP14 | FAN1 PWM / ENABLE | Second independent cooling channel. |
| GP15 | FAN1 TACH | Second fan tach input. |
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

The fan `+5V_FAN` pins remain intentionally unconnected until the Rev-A load-switch/driver is selected. This is a deliberate ERC-visible fabrication blocker, not a no-connect.

## Power / physical constraints

- Both Pico modules remain socketed.
- Pico-A exposes a complete second pair of 1×20 raw breakout rails mirroring physical pins 1–40.
- Pico-B owns the rear DEBUG/UPDATE USB-C service path.
- PRIMARY and EXTENDED USB input boards route only through the 4-port hub to Pico-A.
- Two fan headers are provisioned; cooling is a Pico-B/system-management responsibility.
- Console personality cards are not hot-swappable in Rev A.
