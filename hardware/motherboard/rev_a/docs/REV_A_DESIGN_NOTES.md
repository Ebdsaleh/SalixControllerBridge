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

Fan motor current comes from 5V_MAIN via a proper driver/load switch. GPIO controls only logic. The existing I²C/AUX expansion remains separate.

## Safety / service rules
- PRIMARY/EXTENDED front USB inputs never route to Pico-B.
- Rear DEBUG/UPDATE USB-C never routes to the controller hub.
- Front USB-C source-to-source misuse must fail safely via hardware isolation/backfeed protection.
- Each physical front port gets a hard-disable service jumper: OPEN=RUN, SHORT=OFF.
- Console cards are power-off insert/remove for Rev A; no hot-swap promise.
- Keep labelled test points for rails, hub root, inter-Pico RPC and both SWD interfaces.

## Manufacturing strategy
Quote the complete architecture first. If optional blocks make PCBA too expensive, DNP them rather than deleting the footprints/nets where possible.
