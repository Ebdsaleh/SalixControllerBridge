# Rev-A Pre-Gerber Audit — 2026-11-12

Status: **NOT FABRICATION READY**

This file is the fabrication gate for the Rev-A motherboard + universal front USB daughterboard design. ERC-clean does not by itself mean PCB-ready.

## Confirmed good / corrected

- Native KiCad ERC supplied on 2026-11-12 reached **0 errors**. Remaining warnings were 548 endpoint-off-grid and 125 library-symbol-mismatch warnings.
- USB2514B /M2 pin map has been checked against Microchip. Exposed die paddle is physical pad 37 and is represented that way.
- USB2514B /M2 is frozen to 36-pin 6x6mm, 0.5mm-pitch SQFN with 3.7x3.7mm e-pad; KiCad footprint: `Package_DFN_QFN:QFN-36-1EP_6x6mm_P0.5mm_EP3.7x3.7mm_ThermalVias`.
- TPS25821 DSS exposed thermal pad 13 is explicit and tied to GND.
- SN74LVC2G157/SN74LVC2G08 DCU devices use the correct 0.5mm-pitch DCU land pattern: `Package_SO:VSSOP-8_2.3x2mm_P0.5mm`.
- USB2514B SMBus straps are CFG_SEL1=0 / CFG_SEL0=1; CFG_SEL1 low strap is normalized to 100k.
- TLV62569P 2.2uH reference inductor is frozen as Coilcraft XAL4020-222ME with `Inductor_SMD:L_Coilcraft_XxL4020`.

## Fabrication blockers

1. **Main 5V input/protection is not designed/frozen.** Exact connector, TVS, fuse/eFuse, reverse-current/backfeed behavior, inrush strategy and high-current copper are TBD.
2. **Power budget must be frozen with firmware policy.** Four USB-A paths at ~0.9A plus four Type-C paths at 1.5A can expose 9.6A of port demand before Picos, logic and fans. Default Type-C STD advertisement reduces nominal exposed-port demand to 5.6A, still before system loads.
3. **USB-A VBUS reservoir capacitors are missing from the schematic.** Add >=120uF at each TPS2553 OUT/downstream USB-A receptacle before layout and select an exact voltage/ESR/package/MPN.
4. **TPS25821 input bulk is only nominally qualified.** 3 x 47uF = 141uF nominal per Type-C port, but TI calls for at least 120uF close to IN. Freeze exact capacitors and verify effective capacitance at 5V after DC bias, tolerance and temperature.
5. **USB2514B clock is not frozen.** Select exact 24.000MHz crystal package/MPN and compute C62/C63 from its CL plus PCB parasitics.
6. **Mechanical footprints remain open.** USB-A/USB-C receptacles, 20-pin front-board connectors, latching selector switches, fan headers, microSD socket, SWD spring contacts, TFT/service connector, LEDs and TS3USB221A RSE land pattern remain TBD.
7. **No fabrication PCB exists yet.** The repository has schematics but no `.kicad_pcb`; board outline, mounting holes, stack-up, placement, controlled USB routing, power planes/high-current paths, thermal copper, keepouts and DRC remain outstanding.
8. **ERC warning hygiene remains.** Endpoint-off-grid and library-symbol-mismatch warnings should be reduced or explicitly dispositioned before schematic freeze so later regressions stay visible.

## Layout/current constraints

- Each logical bank can power both physical USB-A and USB-C while only one receives data. A bank can therefore require about 2.4A nominal when Type-C advertises 1.5A. Select/derate front-board connector contacts for this current; do not use an unrated signal-only connector.
- Four TPS25821 inputs contribute 564uF nominal bulk across two daughterboards before DC-bias derating. Main-input soft-start/inrush behavior must account for it.
- USB D+/D- cross the motherboard/front-board interconnect. Preserve pair adjacency and return paths through the selected connector/harness and route controlled differential pairs during PCB layout.
- TPS25821 OUT is kept below 10uF (currently 4.7uF), consistent with TI's Type-C cold-socket recommendation.
- Per-port current limiting, fault monitoring, ESD arrays and shield RC networks are present conceptually, but their physical placement is a PCB-layout requirement.

## Gerber gate

Do not generate manufacturing Gerbers until every blocker above is closed, every physical BOM item has an exact MPN/package/footprint, PCB DRC is clean, USB/high-current layout has been reviewed, and the generated Gerber + drill set has been opened in GerbView for a final visual/mechanical check.
