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

Rev-A fan choice is now frozen to Noctua NF-A4x10 5V PWM. Noctua rates the fan at 5V, 0.07A maximum / 0.35W maximum, 5000rpm maximum, with locked-rotor auto power-off after about 1 second and automatic restart attempts every 2-6 seconds. This is more than 20x below the TPS22919 1.5A continuous-current capability, leaving large electrical margin. The fan uses the standard 4-wire pinout: pin 1 GND, 2 Vcc, 3 RPM/tach, 4 PWM.

J10/J11 are frozen to Molex 47053-1000 standard 4-wire fan headers. The project-local `SalixFP:Molex_47053-1000_1x04_P2.54mm_Vertical` footprint follows Molex drawing SD-47053-001 including the four 1.02mm nominal plated pin holes and the 1.25mm nominal PCB locating hole. The fan itself remains enclosure-mounted, not PCB-mounted; final airflow direction and grille geometry are mechanical-layout tasks. Firmware should use the standard 4-wire PWM target near 25kHz and preserve the existing fail-safe release-to-full-speed behavior.

## Safety / service rules
- PRIMARY/EXTENDED front USB inputs never route to Pico-B.
- Rear DEBUG/UPDATE USB-C never routes to the controller hub.
- Front USB-C source-to-source misuse must fail safely via hardware isolation/backfeed protection.
- Each physical front port gets a hard-disable service jumper: OPEN=RUN, SHORT=OFF.
- Console cards are power-off insert/remove for Rev A; no hot-swap promise.
- Keep labelled test points for rails, hub root, inter-Pico RPC and both SWD interfaces.


## AUX power module / recharge contract

Rev-A now reserves a dedicated optional-power interface rather than choosing a battery chemistry on the motherboard.

J15 is a Molex 43045-1000 10-circuit Micro-Fit 3.0 right-angle header. Pins 1/2 duplicate AUX_PWR from the module into the motherboard; pins 3/4 duplicate GND; pins 5/6 duplicate CHARGE_PWR from the motherboard to the module. Pins 7-10 reserve AUX_ID, AUX_SDA, AUX_SCL and AUX_INT_N for module identification, telemetry and fault reporting.

The two power directions are intentionally separate:
- **AUX_PWR** is produced by the optional module and will later enter the motherboard source-priority mux as the tertiary source.
- **CHARGE_PWR** is produced by the motherboard recharge-protection branch from qualified external power and is consumed by the optional module.
- The motherboard must never connect a cell stack directly to CHARGE_PWR and must never assume Li-ion, LiFePO4, NiMH or any other chemistry.

U3 is frozen to TPS259474LRPWR for the recharge branch because this variant combines adjustable UVLO/OVLO, circuit-breaker overcurrent response, latch-off after fault and true reverse-current blocking. The first-pass divider values target an approximately 8V-to-21V accepted external-charge window. R10 = 1.33k sets about a 2.5A nominal breaker threshold; the interface contract limits a module to 2.0A continuous draw so normal charging is not designed to ride the protection threshold.

The module must contain the chemistry-specific charger/BMS/protection, any required cell balancing, temperature supervision and whatever DC/DC conversion is required. This deliberately allows a future NiMH, Li-ion, LiFePO4 or other protected rechargeable module to use the same motherboard.

U3's land pattern is now frozen to project-local footprint `SalixFP:TI_RPW0010A_VQFN-HR-10_2x2mm_P0.475mm`. The copper geometry follows TI RPW0010A drawing 4225183/A and was cross-checked against the current KiCad upstream footprint proposal for the same package. The project footprint uses 0.05mm NSMD mask expansion and split paste apertures on the long IN/OUT lands.

The J15 management pins are reserved electrically in this pass; firmware ownership and AUX_ID encoding are not frozen yet. They must not be repurposed casually because the whole point of J15 is to keep the Rev-A motherboard compatible with future smart power modules.

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
