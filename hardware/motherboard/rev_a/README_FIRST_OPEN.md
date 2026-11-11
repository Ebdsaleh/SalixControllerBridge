# SalixControllerBridge Rev-A — KiCad Starter

This is the first **KiCad architecture skeleton** for the new SalixControllerBridge motherboard.

## Open this first
`SalixControllerBridge_RevA.kicad_pro`

Then open:
`SalixControllerBridge_RevA.kicad_sch`

## Hierarchical sheets
1. Power / Protection
2. Pico-A Realtime / Bridge
3. USB Hub / Input Interface
4. Pico-B Service / Storage / UI
5. Salix Module Bus / Future Backplane
6. Service / Debug / Supervision

This is intentionally an **architecture skeleton**, not a fabrication-ready schematic.

## Frozen architecture
- Two socketed Pico-family modules.
- Pico-A = realtime USB/Bluetooth/controller/console bridge.
- Pico-B = storage/UI/service/update/recovery.
- Front PRIMARY/EXTENDED USB banks route only to Pico-A through a 4-port hub.
- Rear DEBUG/UPDATE USB-C belongs only to Pico-B.
- Pico-B recovers Pico-A over SWD.
- Full Pico-A raw 40-pin breakout remains available.
- Console RJ50s belong on future console personality cards, not the motherboard.
- Mainboard exposes a future Salix Module Bus/backplane interface.
- TF034 TFT belongs to Pico-B.

## Still to freeze
- exact hub IC
- USB A/C mux
- USB power-switch/eFuse parts
- 3V3_AUX regulator
- module-bus connector/lane count
- exact Pico-A/Pico-B GPIO allocations
- exact TF034 pinout/driver
- board outline/enclosure dimensions
- SuperSpeed pass-through implementation

## Next pass
Place real symbols for both Pico sockets, hub, power/protection, USB0/USB1, inter-Pico SPI/SWD, microSD, TFT header, test points/service LEDs, and Salix Module Bus connector placeholder.
