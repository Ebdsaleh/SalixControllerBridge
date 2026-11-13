# Rev-A Design Notes

## Design objective
Build the stable reusable motherboard first so future console-card development does not force another motherboard spin.

## New frozen GPIO strategy
See GPIO_RESOURCE_MAP.md.

Key change from the current bench firmware: the motherboard uses one Pico-A PIO-USB root on GP16/GP17 after the 4-port hub. GP18/GP19 are reclaimed from the bench prototype's second independent root and assigned to the future console-module SPI bus.

## Cooling
Rev A now provisions two independent cooling channels:

- FAN0: Pico-B GP2 PWM/enable, GP3 tach.
- FAN1: Pico-B GP14 PWM/enable, GP15 tach.

Each fan is powered from 5V_MAIN through its own TPS22919DCK protected load switch. The load-switch ON input is tied to 3V3_AUX, so fan motor power is available whenever the system logic rail is alive. Pico-B never sources motor current.

Each fan PWM input is driven through a 2N7002 open-drain stage. A 1k gate resistor and 100k gate pulldown make reset/boot fail-safe: with the MOSFET off, the fan PWM input is released and a standards-compliant 4-wire fan defaults toward full-speed operation. Firmware must account for the open-drain inversion.

Each TACH line has a 10k pull-up to 3V3_AUX before entering Pico-B. The existing I²C/AUX expansion remains separate.

The final 5V fan MPN must stay within the TPS22919 1.5A continuous-current capability and its startup transient behavior must be validated before fabrication.

## Safety / service rules
- PRIMARY/EXTENDED front USB inputs never route to Pico-B.
- Rear DEBUG/UPDATE USB-C never routes to the controller hub.
- Front USB-C source-to-source misuse must fail safely via hardware isolation/backfeed protection.
- Each physical front port gets a hard-disable service jumper: OPEN=RUN, SHORT=OFF.
- Console cards are power-off insert/remove for Rev A; no hot-swap promise.
- Keep labelled test points for rails, hub root, inter-Pico RPC and both SWD interfaces.

## Manufacturing strategy
Quote the complete architecture first. If optional blocks make PCBA too expensive, DNP them rather than deleting the footprints/nets where possible.


## Pico-A SWD recovery contact

Pico-B can recover Pico-A through GP26=SWDIO, GP27=SWCLK and GP28=RUN.

The motherboard exposes these to a dedicated three-contact target pickup (`J12`) arranged as SWCLK / GND / SWDIO. The target remains powered separately; the SWD contact carries no power.

The schematic is electrically frozen, but the spring-contact footprint is intentionally mechanical-TBD until the final Pico-A module variant and socket height are frozen. The PCB layout must align J12 to the actual Pico-A SWD pads and verify contact compression/clearance.


## Pico-B microSD storage

Pico-B owns a native 3.3V microSD socket on its shared service SPI0 bus.

SPI mapping:
- DAT3 -> CS
- CMD -> MOSI
- CLK -> SCK
- DAT0 -> MISO

DAT1 and DAT2 are not used as host data lines in SPI mode but remain pulled up. The host fits 47k pull-ups on CMD and DAT0-DAT3 and 100nF + 10uF local socket decoupling.

No level shifter is used because Pico-B and the card bus are both 3.3V. No card-detect GPIO is allocated in Rev A; firmware detects media through SPI initialization.

J13 is frozen to Hirose DM3AT-SF-PEJM5, a push-push SMT microSD socket using KiCad footprint `Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5`. The connector card-detect switch contacts are physical pads 9/10 and are explicitly NC in Rev A; repeated shell pad 11 is tied to digital GND.


## Front-panel UI interface

The motherboard no longer assumes a specific undocumented TF034 connector. Instead, J14 is a frozen logical 12-signal service UI interface carrying:
- 3.3V logic power and GND,
- optional 5V auxiliary panel/backlight power,
- a damped branch of the shared service SPI0 bus,
- LCD and touch chip-selects,
- D/C,
- reset,
- touch IRQ,
- logic-only backlight PWM.

33R branch series resistors isolate the front-panel cable from the on-board microSD branch. LCD_CS_N and TOUCH_CS_N are pulled high at boot; backlight PWM is pulled low.

J14 is frozen to JST S12B-PH-SM4-TB, a 12-position 2.0mm side-entry SMT PH header using `Connector_JST:JST_PH_S12B-PH-SM4-TB_1x12-1MP_P2.00mm_Horizontal`. The mating harness uses PHR-12 with SPH-002T-P0.5S contacts (AWG30-24). The PH family is rated 2A with AWG24, giving useful margin for the optional 5V auxiliary panel feed.

The front-panel/TF034 adapter must provide the exact module pin mapping and actual backlight-current driver. The motherboard GP5 signal must never source backlight current directly.


## Front-board motherboard management

A TCA9536DGK at I2C address 0x41 now owns the four motherboard-side front-board management lines:
- P0 -> PRIMARY_ENABLE_N
- P1 -> EXTENDED_ENABLE_N
- P2 <- PRIMARY_INT_N
- P3 <- EXTENDED_INT_N

The TCA9536 power-on default is all ports as inputs. This intentionally preserves the daughterboards' local fail-safe BOARD_ENABLE_N pull-ups: both boards remain data-disconnected until Pico-B explicitly configures P0/P1 as outputs and drives them low.

PRIMARY_INT_N and EXTENDED_INT_N each have a 10k pull-up to 3V3_AUX. P2/P3 are polled by Pico-B over management I2C; P3's optional interrupt-output mode is not used.


## Project-local symbol library

Rev-A carries a project-local `Salix.kicad_sym` and `sym-lib-table`. The library is generated from the exact embedded symbol definitions already used by the schematics. Intentionally different resistor/capacitor drawing variants use distinct names (`R_SERVICE`, `C_SERVICE`, `R_FRONT`, `C_FRONT`) and the daughterboard connector uses `FRONT_USB_BOARD_IF_20_DAUGHTER`, preventing one library name from silently representing different symbol definitions.
