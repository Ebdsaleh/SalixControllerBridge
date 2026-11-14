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

## Source-priority mux batch — FROZEN GREEN

- Once the page-9 syntax defect was corrected, KiCad could finally instantiate the sheet fully and exposed **40 real ERC errors** caused by generated wiring coordinates using the wrong local-Y orientation. The LTC4418 symbol/pin numbering itself remained correct, but the instance fanout was mirrored vertically and all eight MOSFET gate stubs were attached on the wrong side of the rotated symbols. Those coordinates were corrected and the sheet rerendered.

- KiCad GUI subsequently exposed the actual page-9 load failure at line 187: the generated Si7155DP duplicate source/drain pins used invalid pin text-effects syntax `(effects (...)) hide`. KiCad requires `hide` inside the `effects` block. The embedded page-9 symbol and project `Salix.kicad_sym` copy have both been corrected. This was a file-format defect only; it did not change the verified Si7155DP pin numbers or source-priority electrical topology.

- New sheet 08 implements the two-stage source-priority mux: BARREL_PROT > PD_PWR → EXT_CHARGE_IN, then EXT_CHARGE_IN > AUX_PWR → SYS_IN.
- U4/U5 are LTC4418IUF#PBF; Q1-Q8 are Si7155DP-T1-GE3 back-to-back P-channel MOSFETs.
- Native KiCad 10.0.8 ERC on the first page-9 batch is **0 errors / 721 warnings**. The increase from 682 is entirely 39 additional `lib_symbol_issues`; `endpoint_off_grid` remains 551 and the four intentionally isolated AUX management labels remain unchanged.
- ERC already sees `/MAIN SOURCE PRIORITY / POWERPATH/`. The helper renderer sheet-discovery bug was fixed and page 9 is now enumerated, but KiCad 10.0.8 exported the page as title-block-only when selected through the root hierarchy. The helper now renders child schematics directly to work around that KiCad CLI export behavior; a final visual rerender is still required.
- LTC4418 U4/U5 pin numbering has been rechecked against the Analog Devices Rev-A datasheet: TMR=1, UV1=2, OV1=3, UV2=4, OV2=5, VALID1=6, VALID2=7, GND=8, CAS=9, INTVCC=10, G2=11, VS2=12, G1=13, VS1=14, VOUT=15, V2=16, V1=17, EN=18, SHDN=19, HYS=20, exposed pad=21.
- The control connections also match the datasheet intent: HYS→GND (internal 3% hysteresis), EN/SHDN→INTVCC when unused, TMR uses 1nF to GND (~16ms nominal), INTVCC uses 100nF to GND, CAS/VALID outputs are unused, and VS1/VS2 sense the common-source nodes.
- Q1-Q8 Si7155DP pinout is confirmed from Vishay: pins 1-4 source, 5 gate, 6-8 drain. Each channel's two P-FETs are arranged common-source back-to-back, with VSx at the common-source node and both gates driven together, matching the LTC4418 application topology.
- Native KiCad 10.0.8 rerun after the coordinate repair is now **0 errors / 810 warnings**. Warning breakdown: **663 endpoint_off_grid + 143 lib_symbol_mismatch + 4 isolated_pin_label**. The four isolated labels remain the intentional J15 AUX_ID/AUX_SDA/AUX_SCL/AUX_INT_N management pins. No source-priority electrical errors remain.
- Page 9 now loads directly in KiCad and renders normally without the hierarchy fallback. Visual review confirms both LTC4418 stages, all four back-to-back P-FET channel pairs, gate-control nets, source-sense nodes, divider networks, TMR capacitors and INTVCC bypass capacitors are present and connected as intended.
- The U4/U5 source-priority stage is therefore **schematic-level frozen**. Remaining page-9 issues are cosmetic/warning-hygiene only; do not alter the verified source-priority topology while proceeding to the barrel, PD and SYS_IN→5V_MAIN front-end batches.

## Newly added / awaiting native KiCad validation

- AUX recharge / optional-power interface has been added to 01_Power: U3 TPS259474LRPWR, J15 Molex 43045-1000, CHARGE_PWR protection/qualification, AUX_PWR return path and reserved module-management pins. The first native render exposed one real wiring error: the C5 GND stub overlapped the C6 CHARGE_PWR stub, merging those nets. That overlap has been removed and the AUX block has been respaced onto the 1.27mm grid; native ERC must now be rerun.
- Native KiCad 10.0.8 validation after the AUX net-isolation/layout repair is **0 errors / 682 warnings**. The AUX recharge circuit is electrically green; the remaining count is warning-hygiene work rather than an ERC error.
- U3 now has project-local footprint `SalixFP:TI_RPW0010A_VQFN-HR-10_2x2mm_P0.475mm`, based on TI drawing 4225183/A and cross-checked against the current KiCad upstream package proposal. Native KiCad 10.0.8 was rerun after assignment and remained **0 errors / 682 warnings**, so the AUX recharge branch and U3 footprint are schematic-level frozen.

## 12V barrel / automotive front-end — ELECTRICAL FROZEN GREEN

- First native page-10 validation produced **6 ERC errors / 875 warnings**. All six errors were confined to the new barrel sheet: Q9/Q10 gate stubs and the U6 LM74800 pin fanout were vertically mirrored by generated-coordinate orientation, and the RTN thermal-pad no-connect flag was placed on the wrong side. These have been remapped to the actual KiCad coordinates. TI Rev-C also confirms the 12V example TVS is **SMBJ36CA** and that the exposed RTN thermal pad must be left floating; both are now reflected in the schematic.

- New page 09 adds the primary-source path J16 → F1 → SMBJ36CA → U6 LM74800-Q1 + Q9/Q10 IAUC100N08S5N034 common-drain pair → BARREL_PROT.
- J16, U6 and Q9/Q10 MPNs are selected; their exact PCB footprints remain deliberately pending this first schematic validation. F1 holder/MPN and C13 exact MPN also remain open.
- Native KiCad rerun after the wiring correction is **0 errors / 870 warnings**. Warning breakdown is 713 endpoint_off_grid + 153 lib_symbol_mismatch + 4 intentional isolated AUX management labels. Visual review shows the corrected U6/Q9/Q10 topology is coherent.
- Manufacturer review found the original 137k + 10k OVP divider exceeded TI's recommended <120k total resistance for leakage-error control. It was changed to **93.1k + 6.19k (99.29k total)** for ~19.75V nominal cutoff and ~18.81–20.71V first-pass worst-case range, keeping U6 as a backup protection layer above the frozen LTC4418 barrel-validity ceiling.
- Final native KiCad 10.0.8 rerun on commit `1f3dea9` remained **0 errors / 870 warnings** with the same 713 endpoint-off-grid + 153 library-symbol-mismatch + 4 intentional isolated AUX-label warning buckets. Page 10 was visually reviewed again and remained coherent. The barrel/automotive front end is therefore **electrically frozen**; subsequent work must be footprint/BOM/mechanical only unless a verified electrical defect is found.
- Physical sub-batch 1 assigns U6 to project-local `SalixFP:TI_DRR0012E_WSON-12_3x3mm_P0.5mm_FloatingEP`, following TI DRR0012E land geometry (0.62x0.25mm perimeter lands, 0.5mm pitch, 1.3x2.5mm exposed pad with 82% split paste). RTN/EP remains soldered to an isolated pad but electrically floating, as the LM7480-Q1 requires. C13 is frozen to Panasonic EEETQV470XAP, 47uF/35V TQ, AEC-Q200, 125C, using `Capacitor_SMD:CP_Elec_6.3x7.7`.
- F1 holder MPN is selected as Littelfuse 178.6764.0001 MINI FL1 58V PCB holder. Fuse candidate is Littelfuse 099707.5WXN (7.5A, 58V, 1kA interrupt), but **7.5A remains provisional** until the full 5V load + AUX-recharge + inrush policy is frozen. Holder footprint remains pending exact manufacturer-hole transcription.
- Automotive capability remains conditional on final TVS energy margin, MOSFET SOA/inrush, fuse/harness selection, PCB layout and physical transient testing; no compliance claim is made at schematic stage.

## USB-C PD secondary-input — ELECTRICAL FROZEN GREEN

- **PD physical sub-batch U8/U9 — NATIVE GREEN:** U8 TVS2200DRVR uses project-local `SalixFP:TI_DRV0006A_WSON-6_2x2mm_P0.65mm_EP1x1.6mm`; U9 TPD4S201RUKR uses `SalixFP:TI_RUK0020B_WQFN-20_3x3mm_P0.4mm_EP1.7x1.7mm`. Native KiCad 10.0.8 validation on commit `302180d` remained **0 errors / 1038 warnings** with no warning-category change, so both assignments are frozen green. **U7 REF0038A:** rather than duplicate the difficult dual-exposed-pad/mixed-mask package locally, Rev-A now assigns KiCad’s exact official `Package_DFN_QFN:Texas_REF0038A_WQFN-38-2EP_6x4mm_P0.4`; this U7 assignment awaits native validation.

- Native validation after commit `1949a2a` rendered all 11 sheets successfully and reduced sheet-10 ERC to **1 error / 1038 warnings**. The only remaining error was U9 pin 10 VPWR not being recognized as driven because U7 LDO_3V3 was modeled as a generic output. TI defines LDO_3V3 as the internal 3.3V regulator output used to supply/bypass the support rail, so U7 pin 1 has now been changed to KiCad `power_out`. LDO_1V5 remains a normal output because TI explicitly states it cannot source external circuits. One final native rerun is required before PD electrical freeze.
- Final native KiCad 10.0.8 rerun on commit `44a27dd` is **0 errors / 1038 warnings**. Warning breakdown: **848 endpoint_off_grid + 185 lib_symbol_mismatch + 4 intentional isolated AUX management labels + 1 intentional pin_to_pin warning**. The pin_to_pin warning is U7 I2Ct_SDA (bidirectional) tied to GND, whose global net also contains a PWR_FLAG; TI explicitly permits unused I2C pins to be tied to GND. No PD electrical errors remain.
- Page 11 was visually reviewed after the final rerun: J17 power-only connector, TVS2200, D30 Schottky clamp, TPD4S201 CC protection, TPS25730AD managed path, strap networks and support capacitors all render coherently with the accidental overlap defects removed. The USB-C PD electrical stage is therefore **frozen**; subsequent changes should be footprint/BOM/mechanical only unless a verified electrical defect is found.

- First native KiCad validation of sheet 10 produced **2 ERC errors / 1033 warnings**. One error was expected external-source bookkeeping (J17 VBUS power-input not marked as driven); the other was caused by an accidental PD_LDO3V3-to-GND short from overlapping passive stubs. Visual/static review also found two additional real net-overlap defects that ERC did not elevate to errors: overlapping CC filter stubs and overlapping TPD4S201 VBIAS/GND vertical stubs. All three overlaps have been separated, and #FLG05 now marks external PD_VBUS_RAW as driven.
- Datasheet re-verification confirms the TPS25730AD 38-pin mapping, VBUS-only VIN_3V3-to-GND operation, unused-I2C-to-GND guidance, and the 15V-min / 20V-max / 3A-operating / 5A-max strap policy. TPD4S201 pin mapping and its 1uF VPWR / 0.1uF VBIAS support network also match TI's reference design.
- TI additionally recommends a Schottky clamp from VBUS to GND for cable-disconnect inductive surge current. D30 STPS5H100BY-TR (5A/100V AEC-Q101, 75A surge) has been added with A→GND and K→PD_VBUS_RAW; footprint remains pending. A fresh native KiCad render/ERC is required before the PD electrical batch can be called green.

- New sheet 10 adds J17 GCT USB4085-GF-A dedicated power-only receptacle, U8 TVS2200 VBUS clamp, U9 TPD4S201 CC OVP/ESD protector and U7 TPS25730AD integrated 5A PD sink path feeding `PD_PWR`.
- Pin straps target 15–20V, 3A operating / 5A maximum, auto-disable on capability mismatch. I2C is intentionally grounded for this first standalone pass; negotiated-contract telemetry is deferred to a power-safe buffered interface.
- J17/U8/U9 footprints are frozen and native-validated. U7 now has the exact official KiCad REF0038A footprint assigned and awaits native render/ERC validation. D30 and exact PD capacitor MPNs remain open physical-freeze items.
- Native KiCad render/ERC is required before this PD electrical batch can be considered green; do not alter the frozen barrel or LTC4418 source-priority sheets while validating it.

## Fabrication blockers

1. **Main external-source front end is partially frozen.** Source priority (sheet 08) and the 12V barrel/reverse/load-dump electrical front end (sheet 09) are frozen. USB-C PD secondary-source circuitry is now on sheet 10 awaiting native validation. J16/F1/Q9/Q10 physical footprints remain open. The PD electrical stage is now frozen. The major remaining electrical blocker is SYS_IN→5V_MAIN high-current buck.
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
