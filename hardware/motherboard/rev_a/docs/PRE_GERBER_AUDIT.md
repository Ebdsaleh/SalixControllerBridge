# Rev-A Pre-Gerber Audit — 2026-11-13

Status: **NOT FABRICATION READY**

This file is the fabrication gate for the Rev-A motherboard + universal front USB daughterboard design. ERC-clean does not by itself mean PCB-ready.

## Confirmed good / corrected

- Native KiCad ERC rerun from `kicad_fixes(20261113-131905).zip` remained **0 errors** and improved to **667 warnings**: 551 endpoint-off-grid + 116 library-symbol-mismatch. The Noctua/Molex fan-header batch and front-board annotation move introduced no electrical warning/error category.
- USB2514B /M2 pin map has been checked against Microchip. Exposed die paddle is physical pad 37 and is represented that way.
- USB2514B /M2 is frozen to 36-pin 6x6mm, 0.5mm-pitch SQFN with 3.7x3.7mm e-pad; KiCad footprint: `Package_DFN_QFN:QFN-36-1EP_6x6mm_P0.5mm_EP3.7x3.7mm_ThermalVias`.
- TPS25821 DSS exposed thermal pad 13 is explicit and tied to GND.
- TPS25821 IN bulk is now frozen to TI’s own EVM choice: C230/C231/C32 and C34/C35/C36 are Murata GRM31CR61A476KE15L, 47uF, 10V, ±10%, X5R, 1206; footprint `Capacitor_SMD:C_1206_3216Metric`. TI’s EVM uses three of these per controller and recommends 120uF input capacitance with the capacitors kept close to the IC.
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

- **PD physical sub-batch U8/U9/U7/D30 — NATIVE GREEN:** U8/U9 use their exact project-local TI footprints; U7 uses KiCad’s exact official REF0038A footprint; D30 uses project-local `SalixFP:ST_DPAK_STPS5H100Y`. The corrective native KiCad 10.0.8 rerun after `a8f9131` returned **0 errors / 1038 warnings** with the established 848 endpoint-off-grid + 185 library-symbol-mismatch + 4 intentional isolated AUX labels + 1 intentional pin-to-pin breakdown and **0 footprint_link_issues**. D30 is now frozen green.

- Native validation after commit `1949a2a` rendered all 11 sheets successfully and reduced sheet-10 ERC to **1 error / 1038 warnings**. The only remaining error was U9 pin 10 VPWR not being recognized as driven because U7 LDO_3V3 was modeled as a generic output. TI defines LDO_3V3 as the internal 3.3V regulator output used to supply/bypass the support rail, so U7 pin 1 has now been changed to KiCad `power_out`. LDO_1V5 remains a normal output because TI explicitly states it cannot source external circuits. One final native rerun is required before PD electrical freeze.
- Final native KiCad 10.0.8 rerun on commit `44a27dd` is **0 errors / 1038 warnings**. Warning breakdown: **848 endpoint_off_grid + 185 lib_symbol_mismatch + 4 intentional isolated AUX management labels + 1 intentional pin_to_pin warning**. The pin_to_pin warning is U7 I2Ct_SDA (bidirectional) tied to GND, whose global net also contains a PWR_FLAG; TI explicitly permits unused I2C pins to be tied to GND. No PD electrical errors remain.
- Page 11 was visually reviewed after the final rerun: J17 power-only connector, TVS2200, D30 Schottky clamp, TPD4S201 CC protection, TPS25730AD managed path, strap networks and support capacitors all render coherently with the accidental overlap defects removed. The USB-C PD electrical stage is therefore **frozen**; subsequent changes should be footprint/BOM/mechanical only unless a verified electrical defect is found.

- First native KiCad validation of sheet 10 produced **2 ERC errors / 1033 warnings**. One error was expected external-source bookkeeping (J17 VBUS power-input not marked as driven); the other was caused by an accidental PD_LDO3V3-to-GND short from overlapping passive stubs. Visual/static review also found two additional real net-overlap defects that ERC did not elevate to errors: overlapping CC filter stubs and overlapping TPD4S201 VBIAS/GND vertical stubs. All three overlaps have been separated, and #FLG05 now marks external PD_VBUS_RAW as driven.
- Datasheet re-verification confirms the TPS25730AD 38-pin mapping, VBUS-only VIN_3V3-to-GND operation, unused-I2C-to-GND guidance, and the 15V-min / 20V-max / 3A-operating / 5A-max strap policy. TPD4S201 pin mapping and its 1uF VPWR / 0.1uF VBIAS support network also match TI's reference design.
- TI additionally recommends a Schottky clamp from VBUS to GND for cable-disconnect inductive surge current. D30 STPS5H100BY-TR (5A/100V AEC-Q101, 75A surge) is wired A→GND and K→PD_VBUS_RAW. Project-local `SalixFP:ST_DPAK_STPS5H100Y` uses ST’s 2.9x1.5mm lead lands and 6.5x6.3mm tab land; native validation after `a8f9131` is green.

- New sheet 10 adds J17 GCT USB4085-GF-A dedicated power-only receptacle, U8 TVS2200 VBUS clamp, U9 TPD4S201 CC OVP/ESD protector and U7 TPS25730AD integrated 5A PD sink path feeding `PD_PWR`.
- Pin straps target 15–20V, 3A operating / 5A maximum, auto-disable on capability mismatch. I2C is intentionally grounded for this first standalone pass; negotiated-contract telemetry is deferred to a power-safe buffered interface.
- J17/U8/U9/U7/D30 and the C17-C31 support-capacitor set are now frozen and native-validated. Native KiCad 10.0.8 after `c852b84` is **0 errors / 1036 warnings** (848 endpoint-off-grid + 183 library-symbol-mismatch + 4 intentional isolated AUX labels + 1 intentional pin-to-pin), with no new warning category. C22/C23 polarity is visually correct. The complete USB-C PD electrical + physical stage is now frozen green.
- USB-C PD electrical and physical freeze is complete and native-green; do not alter the frozen barrel, source-priority or PD sheets unless a verified defect is found.

- **PD exact-capacitor batch — NATIVE GREEN:** C17 Murata GRM188R6YA475KE15D; C18-C21 Murata GRM188R71H103JA01; C22/C23 Panasonic EEHZC1H330XP polarized hybrids; C24 Murata GRM32ER71H106KA12; C25/C26 TDK C2012X7R1A106K125AE; C27/C28 TDK CGA3E2C0G1H331J080AE; C29 Murata GRM188R6YA105KA12; C30/C31 TDK C2012X7R2A104K125AE. PPHV nominal is 76uF and tolerance-only 61.8-90.2uF. The two hybrid bulk parts alone have a 52.8uF tolerance floor, so the design does not rely on a highly DC-biased large MLCC to meet TI's 47uF minimum.

## 5V_MAIN calculated power-train checkpoint — 2026-11-14

- Documentation-only pull `3224768` was followed by a native KiCad 10.0.8 rerun: **0 errors / 1036 warnings**, unchanged categories.
- Worst 12A ripple corner used for screening: 23V input, 1.76uH, 400kHz -> **5.56A p-p**, **14.78A peak**.
- 3mOhm shunt guarantees approximately **13.31A** equivalent load current at the 49mV low threshold with worst ripple/tolerance allowance; dissipation about **0.45W**.
- XGL1010-222MED and IAUC60N04S6L039 are therefore frozen as power-train MPNs pending PCB thermal/ringing validation.
- COUT is increased from six to **eight** CGA6P1X7S1A476M250AC parts. Using ~40uF effective/part at 5V gives ~320uF typical; conservative stacked tolerance/temperature estimate is ~200uF, enough for about 156mV idealized 12A load-off overshoot.
- AEF first-pass is frozen around XGL6060-102MEC + EEHZC1V101V and TI Design-2 low-frequency compensation values.
- AUX recharge load shedding is native-green/frozen. The 5V_MAIN loop-compensation values are analytically frozen; remaining pre-buck-sheet work is physical footprint assignment.

## AUX recharge load-shed first native render — ERC GREEN / VISUAL RED

The first native KiCad 10.0.8 run after `d509061`/`dd42ce6` returned **0 errors / 1062 warnings** with no new warning class:
- 870 endpoint_off_grid
- 187 lib_symbol_mismatch
- 4 isolated_pin_label
- 1 pin_to_pin
- 0 footprint_link_issues

Electrical ERC therefore passed, but visual freeze was correctly withheld. Page 03 showed U60's old bypass/pull-up layout colliding with the expanded TCA9534A presentation, and page 01 showed cramped Q11/Q12/load-shed labels plus a pre-existing CHARGE_PWR/AUX_CHG_PG label collision beside U3. The follow-up schematic batch respaces U60/C64/R58/R59, separates R13 from the U3 OUT label corridor, and rewrites the load-shed control presentation without changing the fail-safe topology.
## AUX recharge second native render — 15 ERC errors / corrective rollback to known-good connectivity

The native run at `e2a36e5` exposed **15 ERC errors** even though the visual spacing improved. All 15 errors are confined to the redrawn load-shed block:
- 13 `pin_not_connected` errors across R200/R201/Q11/R203/Q12/R202;
- 2 `pin_not_driven` errors on the Q11/Q12 gates.

Root cause: the spacing rewrite recreated the load-shed wires by hand; several visually adjacent endpoints were not electrically snapped to their symbol pins in KiCad. This also made the cross-sheet `AUX_CHG_ENABLE` appear as a one-pin isolated label.

Corrective action: restore the exact electrically-known-good load-shed geometry from `d509061` (the version that previously produced 0 ERC errors), while retaining only non-electrical readability changes to reference/value positions and text sizes. The separate U60 management-region spacing fix and the R13 `AUX_CHG_PG` separation remain because neither introduced ERC errors.
## AUX recharge load-shed final native render — GREEN / FROZEN

The corrective run at `1145008` passed native KiCad 10.0.8 validation:

- **0 errors / 1065 warnings**
- 873 endpoint_off_grid
- 187 lib_symbol_mismatch
- 4 isolated_pin_label
- 1 pin_to_pin
- **0 footprint_link_issues**
- `pin_not_connected = 0`
- `pin_not_driven = 0`

Visual review of `01_Power.png` confirms the restored Q11/Q12/R200-R203 block is electrically coherent, while `03_USB_Hub_and_Input.png` confirms the respaced TCA9534A/C64/R58/R59 management block is intact. `AUX_CHG_ENABLE` is no longer isolated.

The AUX recharge load-shed architecture is therefore **schematic-level frozen green**. Do not alter its topology unless a verified defect is found.

## 5V_MAIN loop-compensation analytical freeze

Freeze **RCOMP=5.90k 1%, CCOMP=10nF, CHF=DNP with 22pF tuning option**. TI Equation 46 gives 5.89k at a 30kHz target using the conservative 200uF effective bank; Equation 47 gives about 8.98nF. With the typical ~320uF bank, crossover naturally falls to ~18.8kHz. Physical Bode measurement remains a board-level production gate.

## AUX recharge load-shed checkpoint — FROZEN GREEN

- Decision: retain the existing 8A barrel connector; AUX charging is the deferrable load.
- U60 changes from TCA9536DGK (4-bit, 0x41) to TCA9534APWR (8-bit, A2/A1/A0=000 -> 0x38).
- U60 P4 = AUX_CHG_ENABLE; P5 = AUX_CHG_PG; P6/P7 reserved.
- Q11/Q12 = Nexperia 2N7002BK,215. Q11 clamps U3 EN/UVLO low by default; Q12 only releases Q11 when management explicitly asserts AUX_CHG_ENABLE.
- R200/R201 = 100k/100k default-off bias from EXT_CHARGE_IN; R202 = 100k Q12 gate pulldown; R203 = 10k control series.
- Safe firmware init: Output Port 0x01 <- 0x03, then Configuration 0x03 <- 0xEC. Do not configure P4 as output before loading the safe output register.
- Native KiCad 10.0.8 render/ERC and visual review are required before this architecture is frozen green.

## 5V_MAIN power-stage footprint audit

Project-local manufacturer-derived footprints added:

- `SalixFP:Coilcraft_XGL1010_11.3x10.0mm`
- `SalixFP:Coilcraft_XGL6060_6.71x6.51mm`
- `SalixFP:Susumu_KRL2012E_0508_LongSide`
- `SalixFP:Panasonic_EEH_ZC_F_VibrationProof_8x10.5mm`
- `SalixFP:Infineon_PG_TDSON_8_33` for IAUC60N04S6L039, using the exact PG-TDSON-8-33 manufacturer copper/stencil geometry and datasheet numeric pinout 1-3 Source / 4 Gate / 5-8 Drain.

The two TDK ceramic banks remain on stock `Capacitor_SMD:C_1210_3225Metric`.

The Infineon footprint's four drain fingers, central drain region, three source fingers/source bridge and separate gate were independently cross-checked against a second PG-TDSON-8-33 KiCad transcription. The 5V_MAIN power-stage footprint set is now complete; the next gate is schematic placement and native validation.

## 5V_MAIN KiCad sheet — NATIVE GREEN / ELECTRICALLY FROZEN

- Page 12 is `11_5V_MAIN_Buck.kicad_sch`, implementing the frozen LM25149QRGYRQ1 FPWM/DRSS architecture from `SYS_IN` to `5V_MAIN`.
- The first native run exposed eight generated-coordinate endpoint errors only. Commit `5c50e41` corrected those U70/Q70/Q71 wire/label endpoints without changing values or topology.
- Final returned KiCad 10.0.8 rerun is **0 errors / 1258 warnings**: 1024 endpoint-off-grid + 226 library-symbol-mismatch + 4 intentional isolated AUX labels + 3 lib-symbol issues + the established USB-C PD pin-to-pin warning.
- All 12 schematic sheets render, all 12 project-local footprints export, and page 12 was visually reviewed. The buck schematic is now **native-green and electrically frozen**.

## Barrel Q9/Q10 exact physical footprint freeze

- Q9/Q10 remain Infineon **IAUC100N08S5N034ATMA1**, 80V AEC-Q101, package **PG-TDSON-8-34**.
- New project footprint: `SalixFP:Infineon_PG_TDSON_8_34`.
- Infineon's SSO8 package application note explicitly specifies one recommended PCB copper/stencil footprint for **PG-TDSON-8-33/34/43/53**. The new -34 library entry therefore intentionally reuses the already-native-green -33 manufacturer geometry while preserving the correct package-variant name and IAUC100N08S5N034 datasheet traceability.
- Returned KiCad 10.0.8 validation on commit `42444a0` is **0 errors / 1260 warnings** and exports all **13/13** project-local footprints, including `Infineon_PG_TDSON_8_34.kicad_mod`. Warning classes are unchanged: 1024 endpoint_off_grid + 228 lib_symbol_mismatch + 4 isolated_pin_label + 3 lib_symbol_issues + 1 established USB-C PD pin_to_pin warning.
- Q9/Q10 are therefore **native-green / physical-footprint frozen**.
- J16 and F1 remained open at that checkpoint; the next sub-batch addresses J16 from the manufacturer engineering drawing.

## Barrel J16 exact physical footprint — NATIVE GREEN / FROZEN

- J16 remains Kycon **KLDHCX-8-0202-B**, 2.5mm center pin, 8A / 24V DC.
- Project footprint: `SalixFP:Kycon_KLDHCX-8-0202-B`.
- Returned KiCad 10.0.8 validation on commit `9930159` is **0 errors / 1261 warnings** and exports all **14/14** project-local footprints, including `Kycon_KLDHCX-8-0202-B.kicad_mod`.
- Warning classes are unchanged: 1024 endpoint_off_grid + 229 lib_symbol_mismatch + 4 isolated_pin_label + 3 lib_symbol_issues + 1 established USB-C PD pin_to_pin warning.
- The native J16 SVG was visually checked: two plated electrical slots, one locator hole and two NPTH retention slots render as intended.
- J16 is therefore **native-green / physical-footprint frozen**.

## Barrel F1 exact physical footprint — NATIVE GREEN / FROZEN

- F1 holder remains Littelfuse **178.6764.0001 MINI FL1**, current official rating **22A continuous / 30A maximum**, PCB mount.
- Project footprint: `SalixFP:Littelfuse_178.6764.0001_MINI_FL1`.
- Returned KiCad 10.0.8 validation on commit `e0ea0aa` rendered all **12/12** sheets and exported all **15/15** project-local footprints, including `Littelfuse_178.6764.0001_MINI_FL1.kicad_mod`.
- ERC remains **0 errors / 1261 warnings**, unchanged from the J16 validation; no new electrical warning class appeared.
- Native F1 render was visually checked and shows exactly two plated electrical holes plus the central NPTH lock hole.
- Single-holder manufacturer geometry remains:
  - electrical terminal 1: **(-4.00, -0.80)mm**;
  - electrical terminal 2: **(+4.00, -0.80)mm**;
  - central lock: **(0, 0)mm**;
  - terminal holes: **Ø1.50 ±0.10mm**; project plated drills use the manufacturer maximum **Ø1.60mm**;
  - lock hole: **Ø2.70 ±0.10mm**; project NPTH uses the manufacturer maximum **Ø2.80mm**.
- F1 holder is therefore **native-green / physical-footprint frozen**.
- The fuse candidate remains Littelfuse **099707.5WXN 7.5A / 58V**, but the **7.5A current rating remains provisional** pending the final source/load-shed/harness/inrush budget.

## Rev-A design-first / quote-second / cost-down-third strategy

The user has an eventual **AUD$150 target**, but Rev-A will **not** be prematurely stripped to hit that number before the real fabrication/BOM cost is known.

The frozen workflow is:

1. Finish the electrically and mechanically complete design the project actually wants.
2. Preserve useful features that materially improve the product, including port-presence telemetry, unless they create a verified technical problem.
3. Complete PCB placement/routing and generate the first realistic BOM/fabrication/assembly package.
4. Obtain an actual quote using Australian landed-cost assumptions.
5. Only then perform a deliberate cost-down pass, ranking changes by real dollar impact rather than schematic intuition.

This avoids optimizing against imaginary costs and accidentally deleting features that may cost only cents while overlooking the parts, PCB area, assembly operations or connectors that actually dominate the quote.

Current schematic source contains **264 unique reference designators** across the 13 logical child sheets. This is not 264 unique expensive MPNs: 219 are resistors/capacitors, and many other references are repeated interface/support parts. Physical placement count can still be higher when a daughterboard design is fabricated more than once, so the costed BOM—not raw reference count—will be the governing metric.

### USB port-presence telemetry — proceed in Rev A

Desired behaviour: management firmware can distinguish **EMPTY**, **PRESENT + INACTIVE**, and **PRESENT + SELECTED** for each physical USB receptacle.

Planned implementation:
- USB-C: use existing TPS25821 `SINK_N` attach/detach indication from CC detection.
- USB-A: Rev-A now uses high-impedance filtered D+/D- sensing with TLV3704 comparators. Each line is isolated by 100k, pulled down by 1M and filtered by 100nF; firmware ORs the two line-state bits per USB-A receptacle.
- The existing TCA9535 is fully allocated, so USB-A presence uses a second TCA9534A on the same management bus. Address straps are A2=1, A1=0, A0=BOARD_ID -> Primary 0x3C / Extended 0x3D. Its open-drain INT_N shares `FRONT_INT_N`.
- Firmware combines `PRESENT` with the existing bank selection state to derive:
  - empty/inactive;
  - selected but empty;
  - present/inactive (waiting);
  - present/selected (active).
- Keep the sensing circuits electrically separable so the later cost-down pass can remove or simplify them cleanly if the real quote shows they materially affect cost.

## Front USB per-port presence implementation — NATIVE GREEN / FROZEN

- USB-C presence was already present through TPS25821 `SINK_A_C_N` / `SINK_B_C_N`, both monitored by the existing TCA9535.
- U20 TCA9535 is fully allocated; no existing selector/fault/LED/charge signal was repurposed.
- Added U80 **TLV3704IPWR** (TSSOP-14) and U81 **TCA9534APWR** (TSSOP-16) to the universal front daughterboard.
- USB-A line sensing is deliberately high impedance and slow:
  - D+ or D- -> **100k** series -> sense node;
  - sense node -> **1M** pulldown + **100nF** to GND;
  - DC load seen from each USB line is about **1.1M**;
  - first-order filter time constant is approximately **9.1ms**;
  - comparator reference is **180k / 100k** from 3V3_AUX, about **1.18V**;
  - a conservative **2.7V** attached-line level produces about **2.45V** at the sense node.
- TLV3704 input bias is in the pA/nA range and its input common-mode range includes the rails, so the sense-divider error is negligible relative to the attach margin.
- U81 mapping:
  - P0 = A D+ presence;
  - P1 = A D- presence;
  - P2 = B D+ presence;
  - P3 = B D- presence;
  - P4-P7 reserved.
- Firmware derives USB-A port presence as `DP_PRESENT || DM_PRESENT` and should debounce attach/detach for roughly **50ms**, which also masks USB reset/SE0 transients.
- U81 addressing: A2=1, A1=0, A0=BOARD_ID -> **0x3C Primary / 0x3D Extended**.
- U81 INT_N is open-drain and shares the existing `FRONT_INT_N` path.
- This block changes telemetry only. Existing TS3USB221A data selection, TPS2553/TPS25821 power control, fail-safe BOARD_ENABLE_N and service jumpers are unchanged.
- First native run at `571649c` was electrically GREEN (**0 errors / 1359 warnings**) but visual review rejected the crowded page. A subsequent screenshot confirmed page 07 had reached its useful A3 density limit, so the fix is architectural documentation cleanup rather than further squeezing.
- Presence circuitry is now moved intact to new page 13, `07a_Front_USB_Presence.kicad_sch`, representing the **same physical universal front daughterboard**. Page 07 retains USB power/mux/selector circuitry. No presence values or control topology changed.
- Cross-page connectivity uses global anchors only for `USB_A_A_DP`, `USB_A_A_DM`, `USB_B_A_DP`, `USB_B_A_DM`, `BOARD_ID`, and `FRONT_INT_N`; I2C, 3V3_AUX and GND were already global.
- The root architecture overview is enlarged from A4 to A3 to accommodate the thirteenth logical schematic page cleanly. A fresh native render/ERC/visual pass is required before presence freeze.
- First native validation of the 13-page split at `17eaeac` rendered all **13/13** sheets and **15/15** local footprints, but ERC correctly reported **4 errors**: U81 reserved pins P4-P7 were missing their no-connect flags because those four flags retained their pre-split coordinates. The same run also added six `same_local_global_label` warnings from mixing the new global cross-page anchors with old local aliases.
- Corrective batch moves the four NC flags onto U81 P4-P7 and converts every page-07 occurrence of the six cross-page nets to consistent global labels. **No electrical net identity, presence value, threshold, address, mux/power behavior or component footprint changes.**
- Returned KiCad 10.0.8 validation on commit `2806c87` rendered **13/13** sheets, exported **15/15** project-local footprints, and finished at **0 ERC errors / 1359 warnings**.
- Final warning classes are: 1103 endpoint_off_grid + 247 lib_symbol_mismatch + 4 isolated_pin_label + 4 lib_symbol_issues + 1 established USB-C PD pin_to_pin warning.
- The temporary split-specific `pin_not_connected`, `no_connect_dangling`, and `same_local_global_label` classes are gone.
- Visual review of page 07, page 13 and the A3 root hierarchy is clean. USB-A + USB-C per-port presence telemetry is therefore **native-green / frozen**.
- **Reference-designator correction before native validation:** the first source commit used R41-R50/C46-C52/U32-U33, which overlapped existing project references. The post-commit audit caught this before user validation. The presence block was renumbered only—no values/topology changed—to **U80/U81, R100-R109 and C100-C106**.

## Front selector switches and status LEDs — NATIVE GREEN / FROZEN

- SW1/SW2 exact selection: **E-Switch LC1258EENP1RBLK**, SPDT latching ON-ON, non-shorting, right-angle through-hole, black 1RBLK cap.
- Project footprint: `SalixFP:E_Switch_LC1258EENP1RBLK`.
- E-Switch drawing XP0274P Rev A transcribed as:
  - terminal 3: (-2.50, 0), Ø0.90 plated drill;
  - terminal 2 common: (0, 0), Ø0.90 plated drill;
  - terminal 1: (+2.50, 0), Ø0.90 plated drill;
  - unnumbered mechanical locator: (-5.70, +1.20), Ø1.20 NPTH;
  - unnumbered mechanical locator: (+5.60, -2.20), Ø1.20 NPTH.
- Footprint F.Fab also records the 12.0mm body and actuator/cap direction so enclosure/front-panel placement cannot silently reverse the switch.
- D25-D28 use Kingbright **APDA3020L** 3.0x2.0mm low-current right-angle LEDs. Manufacturer land pattern is two 2.0x1.0mm pads with 1.0mm gap, centers ±1.5mm.
- Kingbright's APDA3020L polarity orientation differs by material while the right-angle optical direction must remain the same:
  - InGaN blue/green: manufacturer terminal 1 is cathode-side and terminal 2 anode-side;
  - AlGaInP red/yellow: manufacturer terminal 1 is anode-side and terminal 2 cathode-side.
- Rev-A therefore uses two geometry-identical project footprints whose **project pad numbers follow the existing Salix semantic pinout 1=A / 2=K**:
  - `SalixFP:Kingbright_APDA3020L_InGaN_RightAngle_AK` for D25/D26;
  - `SalixFP:Kingbright_APDA3020L_AlGaInP_RightAngle_AK` for D27/D28.
- Population:
  - D25 A-A: Primary blue APDA3020LVBC/D; Extended green APDA3020LZGCK;
  - D26 A-C: blue APDA3020LVBC/D on both;
  - D27 B-A: Primary yellow APDA3020LSYCK/J3-PF; Extended red APDA3020LSECK/J3-PF;
  - D28 B-C: yellow APDA3020LSYCK/J3-PF on both.
- **Electrical defect fixed:** BOM always intended a series resistor per LED, but page 07 had D25-D28 wired directly from U20 TCA9535 outputs to GND. Added R110-R113 = **1k 1% 0603** in series with the four LED anodes.
- 1k is retained as the first-pass brightness value. Typical ideal current is roughly 0.6mA for blue/green and 1.4mA for red/yellow; first-article brightness may be tuned without changing the LED mechanical footprint.
- Returned KiCad 10.0.8 validation on commit `0cc0ba3` rendered all **13/13** schematic sheets and exported all **18/18** project-local footprints, including the E-Switch and both Kingbright APDA3020L variants.
- ERC finished at **0 errors / 1371 warnings**: 1111 endpoint_off_grid + 251 lib_symbol_mismatch + 4 isolated_pin_label + 4 lib_symbol_issues + 1 established USB-C PD pin_to_pin warning. No new warning class appeared.
- Page-07 visual review confirms R110-R113 are in series with D25-D28 and the LED control nets enter on the resistor-input side; the restored current-limit resistors are not bypassed.
- Native footprint review confirms the E-Switch footprint has three electrical terminals plus two mechanical NPTH locators, and both Kingbright variants preserve the same optical direction while mapping project pads to the correct A/K polarity.
- SW1/SW2, D25-D28 and R110-R113 are therefore **native-green / physical-footprint frozen**.
- **Embedded-symbol metadata correction before native validation:** post-commit audit caught that the first metadata edit accidentally placed the E-Switch default footprint on the embedded `SN74LVC2G157` symbol. No mux instance footprint/net was changed. Corrective commit restores the mux symbol default to blank (its instances retain their stock VSSOP footprints) and assigns the E-Switch footprint to the embedded `PUSH_PUSH_SPDT` symbol where intended.

## Rev-A scope boundary

- Rev A is the **SalixControllerBridge box motherboard/front-USB platform**, not the future console-personality-card/backplane fabrication job.
- Front I/O presents **8 physical USB receptacles** as **4 logical/concurrent controller inputs** across the Primary + Extended front boards.
- The two Pico-class MCUs remain **soft-linked with isolated roles**: Pico-A handles realtime USB-host/controller-bridge work; Pico-B handles service/storage/update/diagnostics.
- Console personality cards and their RJ50 rear-I/O hardware remain future separate PCBs; sheet 05 is intentionally a future module-bus/backplane interface only and must not block the Rev-A PCBWay fabrication path.
- Rev A remains frozen at **two independently controlled 5V 4-wire PWM chassis-fan channels**. A possible third chassis fan is deferred and does not block Rev A.

## Pico-A socket and SWD closure — NATIVE GREEN / FROZEN

- Rev-A Pico-A baseline is now the official **Raspberry Pi Pico 2 W with headers**, socketed and user-replaceable.
- Motherboard Pico sockets are frozen to **Samtec SSW-120-01-F-S**, 1x20, 2.54mm vertical socket strips; the existing stock KiCad 1x20 vertical socket footprint remains appropriate.
- The previous spring/pogo J12 concept is removed. J12 is now **JST SM03B-SRSS-TB**, 3-pin 1.0mm side-entry SH, using stock KiCad footprint `Connector_JST:JST_SH_SM03B-SRSS-TB_1x03-1MP_P1.00mm_Horizontal`.
- J12 pinout remains unchanged and now directly follows Raspberry Pi's standardized debug connector: **1=SWCLK, 2=GND, 3=SWDIO**.
- The Pico 2 W with headers provides the matching factory keyed JST-SH debug connector, so J12 uses a short **straight-through pin-1-to-pin-1** SH cable instead of height-sensitive pogo contacts.
- **R114/R115 = 100R 1% 0603** are added at the Pico-B debug-host pins for SWDIO/SWCLK source termination, following Raspberry Pi's 3-pin debug connector specification.
- This batch changes the SWD physical interconnect and adds the two specified host-termination resistors only. The dual-Pico role split, RUN recovery path and other Pico-B assignments are unchanged.
- Returned KiCad 10.0.8 validation on `82ce636` completed at **0 ERC errors / 1373 warnings**. J6 GP26/GP27 are visibly connected through R114/R115 to the SWD nets, J12 is readable, and no new warning class is present.
- This closure is therefore **native-green / frozen**.

## Full schematic visual-hygiene gate — PASSED / SCHEMATIC FROZEN

Before any `.kicad_pcb` work begins, the complete 13-page schematic set must pass a dedicated readability review in addition to ERC.

Cleanup batch committed after the returned `a57d3df` native render:
- page 01: separated crowded 3V3_AUX/GND and AUX-control annotations;
- page 04: removed R114/R115 text congestion at the Pico-B pins while retaining the same 100R series termination and added one clear SWD termination note;
- page 07: shortened repeated visible TPS25821 bulk-capacitor values; exact Murata MPN remains in hidden part metadata/BOM documentation;
- page 07A: removed the stale spring-contact/TBD wording now that Pico-A SWD is JST-SH;
- page 08: moved the lower validity-window engineering note completely clear of the title block;
- page 10: shortened C27/C28 visible CC-filter values while retaining full device detail in hidden metadata;
- page 11: shortened repeated capacitor/shunt display strings and moved the bottom-right controller-bypass/PGOOD row above the title block.

No circuit topology, net identity, footprint, fitted value, or frozen electrical decision is intentionally changed by this batch.

**Gate result:** returned native run at `82ce636` rendered all **13/13** pages and **18/18** project-local footprints, finished at **0 ERC errors / 1373 warnings**, and passed a second visual inspection of the complete set. No visible label/object overlap or title-block bleed remains. The schematic phase is now **frozen for PCB layout**.

## Fabrication blockers

1. **Selected-source front end, barrel front end and complete `SYS_IN -> 5V_MAIN` buck are native-green/electrically frozen, and the complete barrel physical footprint set is closed.** J16, F1, U6, Q9/Q10 and C13 all have native-green/frozen footprints. Only the final F1 fuse amperage remains provisional; the current candidate is 7.5A.
2. **Barrel/recharge concurrency and AUX load-shed implementation are native-green/frozen.** Rev-A retains the 8A Kycon barrel interface; U3 recharge is hardware-default OFF through Q11/Q12 and is only released by U60 P4 after safe firmware initialization. The 7.5A fuse remains provisional until firmware load-shed thresholds, adapter rating, harness gauge and measured losses are frozen.
3. **J12 is native-green/frozen.** It is JST SM03B-SRSS-TB with stock exact KiCad footprint; R114/R115 provide the specified 100R host termination. SW1/SW2, D25-D28 and R110-R113 are also native-green.
4. **The Pico-A/J12 height dependency is removed.** Rev-A uses the headered Pico 2 W factory JST-SH debug connector and a short cable to motherboard J12, while the Pico itself remains socketed. Remaining mechanical work is PCB/enclosure placement: front-panel selector/LED alignment, board outline/mounting, connector locations and airflow.
5. **The first motherboard `.kicad_pcb` foundation now exists.** It uses a provisional 160x100mm working envelope, four 3.2mm M3 NPTH mounting holes at 5mm corner insets, and a 1.6mm four-layer working stack (F.Cu / GND intent / PWR intent / B.Cu). These dimensions are layout scaffolding, not enclosure-frozen mechanics. Native PCB DRC/render validation, schematic forward-annotation, placement, controlled USB routing, power planes/high-current paths, thermal copper, keepouts and final DRC remain outstanding.
6. **Buck control-loop schematic values are analytically frozen.** RCOMP=5.90k, CCOMP=10nF, CHF=DNP with a 22pF tuning option follow TI Equations 46-48 for the Rev-A shunt/output-bank values. Physical Bode measurement remains required before production release.
7. **Schematic warning baseline is frozen at 1373 warnings / 0 errors:** 1111 endpoint_off_grid + 253 lib_symbol_mismatch + 4 isolated_pin_label + 4 lib_symbol_issues + 1 established USB-C PD pin_to_pin. Further warning cleanup is optional housekeeping unless it reveals a real regression; new warning classes or ERC errors remain blockers.

## Motherboard PCB foundation — NATIVE GREEN / FROZEN AS WORKING SCAFFOLD

- New file: `SalixControllerBridge_RevA.kicad_pcb`.
- Working envelope: **160.0 x 100.0mm**. This is adopted from the old concept only as a practical first placement/quote envelope; it is **not** an enclosure-frozen dimension.
- Working board thickness: **1.6mm**.
- Working layer count: **4 layers**:
  - F.Cu = components / critical signals / local power copper;
  - In1.Cu = intended continuous GND reference plane;
  - In2.Cu = intended power-distribution plane/pours;
  - B.Cu = secondary routing / low-speed / escape routing.
- Working mounting pattern: **4 x M3**, 3.2mm NPTH, hole centres 5mm in from each board corner.
- Board comments mark rear/power-service side versus front/front-USB-harness side.
- No schematic footprints are placed yet. The board must pass a native file-format/outline DRC + render gate first; then KiCad forward annotation will populate the schematic footprints for real placement.
- Added `tools/render_kicad_pcb.py` to produce native top/bottom renders and `PCB_DRC.rpt` in `Downloads\\kicad_pcb_validation.zip`.
- Final copper weight, exact fab stack-up, enclosure connector coordinates and mounting geometry remain open until placement and chassis integration prove the working envelope.

## Global reference-annotation closure — NATIVE GREEN / FROZEN

KiCad F8 requires every non-power symbol in the complete hierarchy to have a globally unique reference, including sheets marked Exclude from board. A pre-F8 audit found **36 duplicate designators** created historically as sheets were developed independently.

This was corrected by reference-only renumbering; no value, footprint, net, symbol, or topology changed:

- page 01 Power: R70-R73 -> **R200-R203**;
- page 04 Pico-B Service: R80-R83 -> **R210-R213**; C81/C90/C91 -> **C210-C212**;
- page 06 Service/Debug: R70-R75 -> **R220-R225**; C70-C73 -> **C220-C223**; Q70/Q71 -> **Q220/Q221**;
- page 07 Front USB: R30-R44 -> **R230-R244**; C30/C31 -> **C230/C231**.

Repository preflight now sees **310 unique non-power designators / 0 duplicate designators**. `render_kicad_schematics.py` now performs this annotation preflight automatically and fails before rendering if a `?` reference or cross-sheet duplicate is present.

Returned KiCad 10.0.8 validation after the reference-only cleanup rendered all **13/13** sheets and **19/19** project-local footprints at **0 ERC errors / 1373 warnings**, unchanged in warning classes. Visual review of pages 01, 04, 06 and 07 confirms the new 200-series references are readable and introduce no new overlap/title-block bleed. The global annotation gate is therefore **native-green/frozen**, and KiCad F8 may be retried.

## Root hierarchy instance closure — SOURCE FIXED / NATIVE RETEST REQUIRED

A second KiCad F8 attempt still opened the annotation dialog even after all 310 non-power references were globally unique. Source audit found the remaining structural defect: page 13 (`07a_Front_USB_Presence.kicad_sch`, sheet UUID `...0062`) existed as a child sheet and its symbols carried valid instance paths, but the root `sheet_instances` table stopped at page 12 and omitted the page-13 path.

This can make KiCad treat the hierarchy as not fully instantiated even though direct child rendering and ERC continue to succeed.

Corrective action:
- restored the page-13 root sheet-instance path;
- added `validate_root_sheet_instances()` to `render_kicad_schematics.py`;
- the renderer now fails early if any direct child sheet is missing from the root `sheet_instances` table.

A fresh native schematic validation is required before retrying F8.

## Hidden power-flag annotation closure — SOURCE FIXED / NATIVE RETEST REQUIRED

KiCad's annotation dialog identified the remaining duplicate explicitly as `#FLG04`. The earlier global-reference preflight intentionally ignored hidden `#...` references, so it missed that page 01 Power and page 07 Front USB both used `#FLG04`.

Corrective action:
- page 07 Front USB power flag `#FLG04` -> **`#FLG06`**;
- `#FLG05` remains reserved by the USB-C PD sheet;
- annotation preflight now validates hidden `#FLG/#PWR` instance references globally instead of skipping them.

No electrical topology, visible reference, value, footprint, or net changed.

## First F8 population pin-map closure — NATIVE GREEN

The first successful motherboard F8 population imported the real circuit group, but KiCad reported **92 errors / 72 warnings**. The user captured the complete F8 report before closing the dialog. All 92 errors reduce to five deterministic pin-map classes:

- **J2/J4/J6 = 60 errors:** schematic right rails use physical Pico pin IDs 21-40, while ordinary 1x20 footprints expose pads 1-20. Added project-local 21-40 pin socket/header footprints and assigned them to the right rails.
- **Q1-Q8 = 24 errors:** the Si7155DP symbol incorrectly described pins 1-4 as source and pin 5 as gate. Vishay's actual device is pins 1-3 source, pin 4 gate, pins 5-8 drain. The symbol is corrected and the project-local PowerPAK footprint uses KiCad's grouped drain land pad 5.
- **U7 = 6 errors:** TI REF0038A physically groups PPHV 20-22, VBUS_IN 23-25, VBUS 32-33 and GND 34-35 into package lands represented by KiCad as pads 20/23/32/34. The TPS25730AD symbol now maps those grouped package terminals to the grouped land numbers and uses a frozen project-local REF0038A footprint.
- **J13 = 1 error:** installed stock microSD footprint did not expose shell pad 11 to F8. The project now carries a known-good exact Hirose footprint including pads 1-11.
- **J17 = 1 error:** installed stock GCT USB4085 footprint did not expose shell pad S1 to F8. The project now carries a known-good exact GCT footprint including S1.

**92 = 60 + 24 + 6 + 1 + 1**, so every F8 error is accounted for.

The project-local symbol/footprint source check now reports no missing pads for the affected symbol families. `render_kicad_schematics.py` now performs this project-local pin-map preflight automatically.

The piled/overlapping first-import PCB is not a placement baseline and its DRC noise is intentionally ignored until the corrected F8 update succeeds with **0 update errors**.

Corrected F8 native result: **0 errors / 4 warnings**. The four warnings are exactly the two mechanical `MP` pads on J12 and the two mechanical `MP` pads on J14, which intentionally have no schematic pins/nets. All 92 hard pad-map errors and the other 68 warnings are gone. The F8 population/pin-map correction gate is therefore **native-green**.

## Motherboard / front-board schematic boundary

The system schematic intentionally includes both physical PCBs, but KiCad supports one board per project. For the Rev-A motherboard project:

- sheet 07 `FRONT USB DUAL-BANK DAUGHTERBOARD` is marked **Exclude from board** (`on_board no`);
- sheet 07A `FRONT USB PRESENCE / MANAGEMENT` is marked **Exclude from board** (`on_board no`);
- this preserves the complete system schematic and cross-board signal documentation while preventing those daughterboard components from being forward-annotated onto the motherboard PCB;
- the future universal front-USB PCB will use its own KiCad project/root that instantiates those same physical-board source sheets with board inclusion enabled;
- do not manually delete daughterboard footprints after motherboard forward annotation as a substitute for this boundary.

## Corrected populated-board native baseline — CAPTURED

After the corrected F8 update completed at **0 errors / 4 expected J12/J14 MP warnings**, the saved populated motherboard was validated natively with `render_kicad_pcb.py --expect-populated`.

Population guard:
- **224 total footprints**;
- **220 non-scaffold motherboard footprints**;
- **0 page-07/page-07A front-board references**.

Native DRC baseline before placement/routing:
- **265 DRC violations**;
- **499 unconnected items**;
- **0 footprint errors**.

The 265 DRC violations are classified as:
- 66 clearance;
- 17 drill-out-of-range;
- 28 copper-edge clearance;
- 79 silkscreen-over-copper;
- 46 silkscreen overlap;
- 20 silkscreen-edge clearance;
- 2 hole clearance;
- 2 courtyard overlap;
- 2 NPTH-inside-courtyard;
- 2 text-height;
- 1 solder-mask bridge.

This is intentionally **not** a failure baseline: the first-import group is still piled/partly outside the 160x100mm working envelope and has not been functionally placed or routed.

However, not every violation is caused by the pile. Source review of the DRC report found:
- **56 same-footprint clearance findings on J17** (GCT USB4085);
- **6 same-footprint clearance findings on U3** (TPS2121/related fine-pitch package);
- **4 same-footprint clearance findings on U7** (TPS25730A REF0038A);
- **9 x 0.20mm drill findings on U1 thermal-via pads**;
- **8 x 0.20mm drill findings on U7 thermal-via pads**.

These are board-rule/fabrication-constraint alignment items and must be closed deliberately rather than by moving components. PCBWay's published standard capabilities list 0.10mm minimum spacing and 0.20mm CNC drills for a 1.6mm board, so the physical geometries are within published manufacturing capability; KiCad's current generic 0.20mm clearance / 0.30mm minimum-hole defaults are more conservative than these exact footprints.

Next physical-layout gate:
1. capture the corrected populated `.kicad_pcb` in Git;
2. establish functional placement zones;
3. update board constraints/custom rules for exact fine-pitch and thermal-via features;
4. rerun DRC after placement before routing.

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
