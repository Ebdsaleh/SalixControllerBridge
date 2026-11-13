# Rev-A Pre-Gerber Audit — 2026-11-13

Status: **NOT FABRICATION READY**

This file is the fabrication gate for the Rev-A motherboard + universal front USB daughterboard design. ERC-clean does not by itself mean PCB-ready.

## Confirmed good / corrected

- Native KiCad ERC rerun from `kicad_fixes(20261113-093843).zip` remained at **0 errors** and **677 warnings**: 550 endpoint-off-grid and 127 library-symbol-mismatch. The new project-local `SalixFP` library and U21/U25 TS3USB221A RSE0010A footprint assignments caused no ERC-count or category regression.
- USB2514B /M2 pin map has been checked against Microchip. Exposed die paddle is physical pad 37 and is represented that way.
- USB2514B /M2 is frozen to 36-pin 6x6mm, 0.5mm-pitch SQFN with 3.7x3.7mm e-pad; KiCad footprint: `Package_DFN_QFN:QFN-36-1EP_6x6mm_P0.5mm_EP3.7x3.7mm_ThermalVias`.
- TPS25821 DSS exposed thermal pad 13 is explicit and tied to GND.
- TPS25821 IN bulk is now frozen to TI’s own EVM choice: C30/C31/C32 and C34/C35/C36 are Murata GRM31CR61A476KE15L, 47uF, 10V, ±10%, X5R, 1206; footprint `Capacitor_SMD:C_1206_3216Metric`. TI’s EVM uses three of these per controller and recommends 120uF input capacitance with the capacitors kept close to the IC.
- USB-A TPS2553 downstream reservoirs are now explicit: C42/C43 on each daughterboard are Panasonic EEHZL1E221XP, 220uF, 25V, ±20% hybrid aluminum electrolytics. Their -20% tolerance floor is 176uF, above the 120uF downstream-port requirement; footprint is `Capacitor_SMD:CP_Elec_6.3x7.7`.
- TPS2553 local input bypass is now explicit: C44/C45 are 100nF 25V X7R 0603 from `5V_BOARD` to GND and must be placed adjacent to each switch IN/GND pair.
- SN74LVC2G157/SN74LVC2G08 DCU devices use the correct 0.5mm-pitch DCU land pattern: `Package_SO:VSSOP-8_2.3x2mm_P0.5mm`.
- USB2514B SMBus straps are CFG_SEL1=0 / CFG_SEL0=1; CFG_SEL1 low strap is normalized to 100k.
- USB2514B pin 28 (`SUSP_IND/LOCAL_PWR/NON_REM0`) is intentionally NC in Rev A: SMBus configuration disables strap options; fixed self-powered operation uses `SELF_BUS_PWR=1` and `DYNAMIC=0`; front ports remain removable with `NR_DEVICE=0x00`; no suspend-status LED is fitted. Pins 25 and 28 are modeled as bidirectional to reflect their multifunction I/O behavior.
- USB2514B clock is now frozen: Y1 is CTS 445I25A24M00000, 24.000MHz, 10pF CL, ±20ppm tolerance, ±50ppm stability, 40ohm ESR, -40C to +85C, with `Crystal:Crystal_SMD_5032-2Pin_5.0x3.2mm`.
- C62/C63 are frozen as Yageo CC0603JRNPO9BN180, 18pF ±5%, 50V, C0G/NP0, 0603. For equal 18pF caps with roughly 1-2pF stray per side, the effective load is about 9.5-10pF, matching Y1 CL=10pF; final frequency/stability still requires board-level measurement as Microchip recommends.
- TLV62569P 2.2uH reference inductor is frozen as Coilcraft XAL4020-222ME with `Inductor_SMD:L_Coilcraft_XxL4020`.
- SN74LVC2G157 fail-safe logic is intentional: strobe HIGH forces Y=0 and complementary Y_N=1; TS3USB221A OE HIGH disconnects the data mux.
- TS3USB221A U21/U25 now use the project-local `SalixFP:TI_RSE0010A_UQFN-10_1.5x2.0mm_P0.5mm` footprint. Copper lands follow TI RSE0010A drawing 4220307/A: 1.35mm left/right pad-column center spacing, 1.8mm top/bottom end-pad center spacing, 0.5mm side-row pitch, 0.55mm side-land length, 0.25mm corner-land height, 0.20mm inner-land height, and 0.6x0.3mm end lands. Footprint uses 0.05mm mask expansion for the TI-preferred NSMD treatment.
- Native KiCad 10.0.8 has now validated the `SalixFP` footprint library resolution and both U21/U25 assignments with no new ERC warning or error.
- Front receptacles are now frozen: J21/J23 use Molex 67643-2910 with `Connector_USB:USB_A_Molex_67643_Horizontal`; J22/J24 use GCT USB4085-GF-A with `Connector_USB:USB_C_Receptacle_GCT_USB4085`. The USB-C symbol has been converted from logical pin numbers to the connector’s physical A/B contact IDs, with SBU1/SBU2 explicitly NC.
- The 677-warning / 0-error native ERC baseline predates the USB-A/USB-C receptacle and USB-C physical-pin freeze; rerun native KiCad after this commit.
- Primary/extended front-board TCA9535 address straps are separated by BOARD_ID (primary low / extended high).

## Fabrication blockers

1. **Main 5V input/protection is not designed/frozen.** Exact connector, TVS, fuse/eFuse, reverse-current/backfeed behavior, inrush strategy and high-current copper are TBD.
2. **Power budget must be frozen with firmware policy.** Four USB-A paths at ~0.9A plus four Type-C paths at 1.5A can expose 9.6A of port demand before Picos, logic and fans. Default Type-C STD advertisement reduces nominal exposed-port demand to 5.6A, still before system loads.
3. **Fourteen placed physical parts still have no footprint.** They are J7/J8; J12/J13/J14; J10/J11; and J20/SW1/D25/D26/SW2/D27/D28. J21/J23 USB-A and J22/J24 USB-C are now frozen to exact receptacle MPNs/footprints; U21/U25 use the project-local TI RSE0010A footprint; Y1 and the frozen capacitor networks are footprinted.
4. **Fan selection remains a current/thermal check.** TPS22919 is rated for 1.5A maximum continuous current; the exact 5V PWM fan MPN must have normal and startup/stall demand compatible with that switch and the connector/traces.
5. **Mechanical footprints remain open.** The 20-pin front-board connector, latching selector switches, fan headers, microSD socket, SWD spring contacts, TFT/service connector and LEDs remain TBD.
6. **No fabrication PCB exists yet.** The repository has schematics but no `.kicad_pcb`; board outline, mounting holes, stack-up, placement, controlled USB routing, power planes/high-current paths, thermal copper, keepouts and DRC remain outstanding.
7. **ERC warning hygiene remains.** Endpoint-off-grid and library-symbol-mismatch warnings should be reduced or explicitly dispositioned before schematic freeze so later regressions stay visible.

## Layout/current constraints

- Each logical bank can power both physical USB-A and USB-C while only one receives data. A bank can therefore require about 2.4A nominal when Type-C advertises 1.5A. Select/derate front-board connector contacts for this current; do not use an unrated signal-only connector.
- Four TPS25821 inputs contribute 564uF nominal ceramic bulk across two daughterboards using the TI EVM 47uF/10V/1206 part set. Main-input soft-start/inrush behavior must account for it.
- Four USB-A downstream reservoirs contribute 880uF total switched capacitance across the two daughterboards. They sit after the TPS2553 switches, so place each reservoir at its downstream VBUS/receptacle region and preserve the switch-controlled turn-on path.
- USB D+/D- cross the motherboard/front-board interconnect. Preserve pair adjacency and return paths through the selected connector/harness and route controlled differential pairs during PCB layout.
- TPS25821 OUT is kept below 10uF (currently 4.7uF), consistent with TI's Type-C cold-socket recommendation.
- Per-port current limiting, fault monitoring, ESD arrays and shield RC networks are present conceptually, but their physical placement is a PCB-layout requirement.
- The Salix Module Bus sheet is explicitly future-only in Rev A and contains no fabricated hardware. Do not treat that sheet as a completed backplane/interface during PCB placement.

## Gerber gate

Do not generate manufacturing Gerbers until every blocker above is closed, every physical BOM item has an exact MPN/package/footprint, PCB DRC is clean, USB/high-current layout has been reviewed, and the generated Gerber + drill set has been opened in GerbView for a final visual/mechanical check.
