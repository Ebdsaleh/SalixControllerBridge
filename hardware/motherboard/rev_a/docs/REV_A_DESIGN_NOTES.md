# Rev-A Design Notes

## Design objective
Build the stable reusable motherboard first so future console-card development does not force another motherboard spin.

## Safety / service rules
- PRIMARY/EXTENDED front USB inputs never route to Pico-B.
- Rear DEBUG/UPDATE USB-C never routes to the controller hub.
- Front USB-C source-to-source misuse must fail safely via hardware isolation/backfeed protection.
- Each physical front port gets a hard-disable service jumper: OPEN=RUN, SHORT=OFF.
- Console cards are power-off insert/remove for Rev A; no hot-swap promise.
- Keep labelled test points for rails, hub root, inter-Pico RPC and both SWD interfaces.

## Manufacturing strategy
Quote the complete architecture first. If optional blocks make PCBA too expensive, DNP them rather than deleting the footprints/nets where possible.
