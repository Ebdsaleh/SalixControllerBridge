# Rev-A Pre-Gerber Audit — 2026-11-13

Status: **NOT FABRICATION READY**

This file is the fabrication gate for the Rev-A motherboard + universal front USB daughterboard design. ERC-clean does not by itself mean PCB-ready.

## Confirmed good / corrected

- Native KiCad ERC rerun from `kicad_fixes(20261113-131905).zip` remained **0 errors** and improved to **667 warnings**: 551 endpoint-off-grid + 116 library-symbol-mismatch. The Noctua/Molex fan-header batch and front-board annotation move introduced no electrical warning/error category.
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
- The USB receptacle / physical Type-C pin-map batch is now native-KiCad validated green. Duplicated physical contacts remain explicit stacked visible pins, while only unused SBU1/SBU2 are hidden NC.
- The motherboard/daughterboard connector family is now frozen to Molex 43045-2000 Micro-Fit 3.0, 20-circuit 2x10 right-angle through-hole, using stock KiCad footprint `Connector_Molex:Molex_Micro-Fit_3.0_43045-2000_2x10_P3.00mm_Horizontal` for J7/J8/J20. Harness mating housing is 43025-2000; 43030-0007 covers 20-24AWG and 43030-0010 covers 26-30AWG loose tin female crimp contacts. Final harness length remains mechanical/enclosure-dependent.
- The Micro-Fit 3.0 J7/J8/J20 assignment is now native-KiCad validated green.
- J13 microSD is now frozen to Hirose DM3AT-SF-PEJM5 with stock KiCad footprint `Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5`; card-detect switch pads 9/10 are explicitly NC in Rev A and shell pad 11 is tied to GND.
- J14 service/TFT interface is now frozen to JST S12B-PH-SM4-TB with stock KiCad footprint `Connector_JST:JST_PH_S12B-PH-SM4-TB_1x12-1MP_P2.00mm_Horizontal`; mating harness is PHR-12 with SPH-002T-P0.5S contacts.
- J13 Hirose microSD and J14 JST PH service/TFT connector assignments are now native-KiCad validated green.
- Cooling is now frozen to two Noctua NF-A4x10 5V PWM fans. Manufacturer maximum current is 0.07A / 0.35W per fan with locked-rotor auto-shutdown/retry, giving very large margin against each TPS22919 1.5A continuous rating.
- J10/J11 are frozen to Molex 47053-1000 standard 4-wire PWM fan headers using project-local `SalixFP:Molex_47053-1000_1x04_P2.54mm_Vertical`, built from Molex drawing SD-47053-001 including its keyed locator hole.
- The Noctua NF-A4x10 5V PWM + Molex 47053-1000 J10/J11 fan/header batch is now native-KiCad validated green.
- Primary/extended front-board TCA9535 address straps are separated by BOARD_ID (primary low / extended high).

## Newly added / awaiting native KiCad validation

- AUX recharge / optional-power interface has been added to 01_Power: U3 TPS259474LRPWR, J15 Molex 43045-1000, CHARGE_PWR protection/qualification, AUX_PWR return path and reserved module-management pins. The first native render exposed one real wiring error: the C5 GND stub overlapped the C6 CHARGE_PWR stub, merging those nets. That overlap has been removed and the AUX block has been respaced onto the 1.27mm grid; native ERC must now be rerun.
- Native KiCad 10.0.8 validation after the AUX net-isolation/layout repair is **0 errors / 682 warnings**. The AUX recharge circuit is electrically green; the remaining count is warning-hygiene work rather than an ERC error.
- U3 now has project-local footprint `SalixFP:TI_RPW0010A_VQFN-HR-10_2x2mm_P0.475mm`, based on TI drawing 4225183/A and cross-checked against the current KiCad upstream package proposal. Native KiCad must be rerun once after this assignment.

## Fabrication blockers

1. **Main external-source front end is not designed/frozen.** The 12V barrel connector/protection, USB-C PD sink, deliberate barrel>PD>AUX priority mux, automotive/caravan transient protection and high-current conversion to 5V_MAIN remain TBD. The new AUX recharge branch only protects CHARGE_PWR and must not be mistaken for the whole-system input stage.
2. **Power budget must be frozen with firmware policy.** Four USB-A paths at ~0.9A plus four Type-C paths at 1.5A can expose 9.6A of demand before Picos, logic and fans. Default Type-C STD advertisement reduces nominal exposed-port demand to 5.6A, still before system loads.
3. **Seven placed physical parts still have no footprint.** They are J12 and SW1/D25/D26/SW2/D27/D28. J10/J11 are now Molex 47053-1000 fan headers; J15 is the Molex 43045-1000 AUX power-module header; J13 microSD and J14 service/TFT are frozen; J7/J8/J20 are Micro-Fit; J21/J23 USB-A and J22/J24 USB-C are frozen; U21/U25 use the exact project-local TI RSE0010A footprint; Y1 and the frozen capacitor networks are footprinted.
4. **Mechanical footprints remain open.** Latching selector switches, SWD spring contacts and front-board LEDs remain TBD.
5. **No fabrication PCB exists yet.** The repository has schematics but no `.kicad_pcb`; board outline, mounting holes, stack-up, placement, controlled USB routing, power planes/high-current paths, fan airflow/mechanical placement, thermal copper, keepouts and DRC remain outstanding.
6. **ERC warning hygiene remains.** Endpoint-off-grid and library-symbol-mismatch warnings should be reduced or explicitly dispositioned before schematic freeze so later regressions stay visible.

## Layout/current constraints

- Each logical bank can power both physical USB-A and USB-C while only one receives data. A bank can therefore require about 2.4A nominal when Type-C advertises 1.5A. The selected Micro-Fit 3.0 connector provides ample connector-contact margin, but the actual 5V/GND harness conductors and crimp contacts must still be selected/derated for wire gauge, ambient temperature and population.
- Four TPS25821 inputs contribute 564uF nominal ceramic bulk across two daughterboards using the TI EVM 47uF/10V/1206 part set. Main-input soft-start/inrush behavior must account for it.
- Four USB-A downstream reservoirs contribute 880uF total switched capacitance across the two daughterboards. They sit after the TPS2553 switches, so place each reservoir at its downstream VBUS/receptacle region and preserve the switch-controlled turn-on path.
- USB D+/D- cross the motherboard/front-board Micro-Fit harness. Bank-A pins 11/12 and Bank-B pins 15/16 are adjacent in the 2x10 header; use dedicated twisted pairs through the harness and preserve 90-ohm differential routing/return paths on both PCBs. Rev-A does not claim the discrete-wire harness as USB Hi-Speed-qualified because the Pico-A PIO root is Full-/Low-Speed.
- TPS25821 OUT is kept below 10uF (currently 4.7uF), consistent with TI's Type-C cold-socket recommendation.
- Per-port current limiting, fault monitoring, ESD arrays and shield RC networks are present conceptually, but their physical placement is a PCB-layout requirement.
- The Salix Module Bus sheet is explicitly future-only in Rev A and contains no fabricated hardware. Do not treat that sheet as a completed backplane/interface during PCB placement.

## Gerber gate

Do not generate manufacturing Gerbers until every blocker above is closed, every physical BOM item has an exact MPN/package/footprint, PCB DRC is clean, USB/high-current layout has been reviewed, and the generated Gerber + drill set has been opened in GerbView for a final visual/mechanical check.
