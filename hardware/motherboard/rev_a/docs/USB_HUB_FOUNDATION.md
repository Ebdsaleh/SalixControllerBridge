# USB Hub Foundation — Rev A

## Frozen hub choice

- Microchip USB2514B/M2-class 4-port USB 2.0 Hi-Speed hub.
- Preferred package family in the current Microchip datasheet: 36-pin SQFN (M2).
- One upstream USB2 pair connects to Pico-A's PIO-USB host root through 22Ω series resistors.
- Pico-A GP16 = hub upstream D+; GP17 = hub upstream D−.

## Downstream deterministic mapping

- Hub DN1 → PRIMARY-1
- Hub DN2 → PRIMARY-2
- Hub DN3 → EXTENDED-3
- Hub DN4 → EXTENDED-4

PRIMARY and EXTENDED each use one dual-bank motherboard interface carrying two USB2 channels. The physical keyed/locking connector is deliberately not frozen yet.

## Hub support values now frozen

- RBIAS: 12.0 kΩ ±1% to ground.
- Reference clock: 24.000 MHz, ±350 ppm or better.
- CRFILT: provision up to 0.1 µF low-ESR to VSS.
- PLLFILT: provision up to 0.1 µF low-ESR to VSS.
- Exposed VSS pad must connect to ground with multiple vias.

## Still TBD

- Exact 24 MHz crystal package and load capacitance, therefore Cload values.
- Exact per-port current-limited high-side VBUS switches and OCS wiring.
- Exact reset/power-good supervisor and VBUS_DET implementation.
- Exact J7/J8 keyed locking connector family.
- USB daughterboard A/C data muxes and Type-C CC/source controllers live on the daughterboards, not in this hub block.

## Important capability boundary

The front USB-A/USB-C receptacles may use mechanically 5Gbps-capable connector parts, but the Rev-A controller-bridge path is USB2 because USB2514B is a USB2 hub. SuperSpeed lanes are not silently claimed as active.
