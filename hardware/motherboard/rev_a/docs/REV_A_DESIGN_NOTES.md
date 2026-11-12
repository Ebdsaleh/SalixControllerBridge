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
