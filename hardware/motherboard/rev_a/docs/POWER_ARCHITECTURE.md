# Power Architecture — Rev A

## Target source architecture

Rev-A is being frozen around three source classes, with the source front-end still to be implemented on the power sheet:

1. **12V DC barrel — primary.** Normal full-power input and supplied-adapter path. The same input is intended to be made tolerant of a properly fused 12V car/caravan accessory feed after the automotive transient front end is designed.
2. **USB-C PD power input — secondary.** Separate from the frozen DEBUG/UPDATE USB-C. The PD source is qualified before it can feed the system or the recharge branch.
3. **AUX_PWR module — tertiary.** Optional plug-in module. The motherboard does not assume a battery chemistry.

The source-priority mux is now implemented on `08_Source_Priority.kicad_sch` using two cascaded LTC4418 controllers and eight Si7155DP P-channel MOSFETs:

- U4: V1 = BARREL_PROT, V2 = PD_PWR, output = EXT_CHARGE_IN.
- U5: V1 = EXT_CHARGE_IN, V2 = AUX_PWR, output = SYS_IN.
- Each channel uses a back-to-back Si7155DP pair for reverse/cross-conduction isolation.
- This topology structurally prevents AUX_PWR from ever feeding EXT_CHARGE_IN, so an AUX battery module cannot source its own CHARGE_PWR input.
- SYS_IN remains an unregulated selected-source rail. The future high-current buck converts SYS_IN to 5V_MAIN.

Priority is therefore explicit in hardware: **barrel > USB-C PD > AUX**. It does not depend on which source has the numerically highest voltage.

## AUX power / recharge interface

J15 is frozen as a 10-circuit Molex 43045-1000 Micro-Fit 3.0 right-angle header with the following contract:

| Pin | Net | Direction at motherboard | Purpose |
|---|---|---|---|
| 1 | AUX_PWR | in | Module output power, contact A |
| 2 | AUX_PWR | in | Module output power, contact B |
| 3 | GND | common | Power return A |
| 4 | GND | common | Power return B |
| 5 | CHARGE_PWR | out | Protected recharge-module feed A |
| 6 | CHARGE_PWR | out | Protected recharge-module feed B |
| 7 | AUX_ID | in | Module identification / presence |
| 8 | AUX_SDA | bidirectional | Reserved management I2C data |
| 9 | AUX_SCL | out | Reserved management I2C clock |
| 10 | AUX_INT_N | in | Reserved module interrupt/fault |

The recharge path is **not a cell charger**. U3 (TPS259474LRPWR) qualifies and protects external power before presenting it as CHARGE_PWR. The optional module remains responsible for the chemistry-specific charger, BMS/protection, balancing where required, temperature sensing, fuel gauging and any buck/boost conversion its pack needs.

Recharge branch first-pass electrical contract:
- EXT_CHARGE_IN qualified operating window: approximately **8V to 21V**.
- R7/R8/R9 = 464k / 52.3k / 30.1k (1%) gives nominal UVLO ≈7.96V and OVLO ≈21.78V using the TPS25947 1.2V threshold equations. Threshold tolerance must still be checked against the datasheet min/max values before fabrication.
- U3 = **TPS259474L** circuit-breaker / latch-off variant with true reverse-current blocking.
- R10 = 1.33k (1%), setting a nominal overcurrent threshold of about **2.5A**. The module contract is deliberately lower: **≤2.0A continuous CHARGE_PWR draw**.
- C7 = 3.3nF on dVdt, giving a controlled output ramp rather than a hard hot-plug step.
- ITIMER is intentionally left open for the fastest circuit-breaker response.
- C5 = 1uF / 35V local input bypass. C6 = 10uF / 35V local output reservoir.
- R11/R12 = 56.2k / 10k create the CHARGE_PWR power-good threshold; R13 = 100k pulls AUX_CHG_PG to 3V3_AUX.

EXT_CHARGE_IN is now driven by the U4 external-source priority stage (barrel over PD). A weak USB-C source may therefore power the bridge while leaving EXT_CHARGE_IN unavailable; a sufficiently capable source may power the bridge and recharge the optional module simultaneously.

## 5V_MAIN

Rev-A now has a frozen **controller/topology direction** for the selected-source buck, while the exact power-stage values remain intentionally provisional until calculation/simulation/native validation.

### Frozen architecture decision

- Controller: **TI LM25149QRGYRQ1** (`LM25149-Q1`), AEC-Q100, 3.5V to 42V synchronous buck controller.
- Exact KiCad footprint: `Package_DFN_QFN:Texas_RGY_R-PVQFN-N24_EP2.05x3.1mm`.
- Topology: **single-phase synchronous buck** from `SYS_IN` to `5V_MAIN`.
- First-pass switching frequency: **440kHz**, following TI's high-efficiency 5V/10A Design 2 rather than the 2.1MHz density-optimized example.
- Output target: **5.0V, 12A continuous hardware capability** (60W rail).
- Control mode: peak-current-mode; first-pass policy is FPWM for predictable fixed-frequency behavior on the USB/system rail.
- EMI strategy: retain the LM25149-Q1 integrated active EMI filter plus dual-random spread spectrum.
- VCCX should be returned to `5V_MAIN` once the rail is established, as in TI's 5V reference design, to reduce controller bias loss.
- The buck is sized for the **rail capability**, not a promise that every source may deliver 12A simultaneously.

TI's published Design 2 is unusually close to this project: 5.5-36V input, 5V/10A output, 440kHz, 2.2uH, 4mOhm current sensing, external N-FET half bridge and 4x47uF output ceramics. Rev-A uses that as the validated starting architecture and scales only the power-stage current margin to 12A.

### Input envelope

The frozen source selectors present a steady-state `SYS_IN` region of roughly **8V to 23V** across barrel, PD and AUX validity windows. The LM25149-Q1's 42V operating rating leaves useful headroom after the already-frozen source protection/mux stages; it is **not** intended to absorb raw vehicle load-dump energy directly.

At 60W output, a 90-95% efficient stage would draw approximately:
- 7.8-8.2A from an 8.1V source,
- 5.3-5.6A from a 12V source,
- 3.2-3.3A from a 20V source.

These are design-envelope numbers, not final fuse ratings.

### Source-aware output policy

The physical buck may be capable of 12A, but downstream current advertisement must follow the selected source:

- **Barrel:** intended full-power source. Final adapter and fuse rating must cover the 60W system rail **plus** any simultaneously permitted AUX recharge power.
- **USB-C PD:** current standalone straps guarantee only a 15V/3A-class accepted source (45W). Without negotiated-contract telemetry, firmware must **not** expose a 60W downstream budget. At 90-95% conversion efficiency, 45W input corresponds to roughly 8.1-8.55A gross on the 5V rail before reserving Pico/logic/fan power; a conservative downstream-port budget is therefore around 7A until telemetry exists.
- **AUX:** budget remains module-dependent and must be derived from AUX_ID / future management data or a conservative default. The motherboard must not assume every battery module can sustain the full 12A rail.

### Barrel fuse / adapter consequence

The previous 7.5A MINI fuse remains **provisional**. A 12A/5V system load is 60W; the AUX recharge branch can additionally accept up to 2A from `EXT_CHARGE_IN`. Simultaneous full system load and recharge can therefore approach the old fuse budget before conversion losses and transient margin are included. The final barrel adapter rating, fuse value, recharge concurrency policy and wiring gauge must be frozen together.

### Provisional 12A power-stage starting point

The following are **not yet electrically frozen**:
- QHS/QLS: Infineon IAUC60N04S6L039, the 40V/4.7mOhm/7nC AEC-Q101 MOSFET used by TI's 440kHz reference.
- LOUT: Coilcraft XGL1010-222MED, 2.2uH, 2.3mOhm typical DCR, 36A saturation rating and 24.6A RMS rating (20C rise).
- RSENSE: Susumu KRL2012E-M-R003-F-T5, 3mOhm, 1%, 1W, AEC-Q200.
- CIN: 4x 10uF/50V AEC-Q200 1210 ceramics as a first-pass local bank, plus the active-EMI/damping network.
- COUT: 6x 47uF/10V AEC-Q200 1210 ceramics as a first-pass local bank.

Before drawing/final-freezing the sheet, calculate worst-case inductor ripple, OCP min/typ/max, MOSFET conduction/switching loss, shunt loss, inductor temperature rise, input-cap RMS ripple, output effective capacitance/transient droop and compensation. The first KiCad buck batch should remain isolated from the frozen source-priority/barrel/PD sheets.

5V_MAIN feeds both Pico VSYS inputs, both USB front-board power feeds, fan power, and the 3V3_AUX regulator.

## 3V3_AUX

Frozen regulator family: TI TLV62569P, 2A synchronous buck.

- VIN: 5V_MAIN
- L1: Coilcraft XAL4020-222ME, 2.2uH
- CIN: 4.7uF X7R
- COUT: 2 x 22uF X7R
- RFB_TOP: 453k 1%
- RFB_BOTTOM: 100k 1%
- CFF: 6.8pF
- PG pull-up: 100k to 3V3_AUX

3V3_AUX powers the USB2514B hub, management logic, future console-card management logic, and other low-voltage motherboard peripherals. It is not intended as a bulk 3.3V motor/peripheral rail.

## USB front boards

The motherboard sends protected bulk 5V and 3V3_AUX to each front board. Per-physical-receptacle current limiting, backfeed protection and charge/data selection live on the front board because each bank has two separately powered A/C receptacles.

## KiCad global nets

The Rev-A power sheet now electrically names 5V_MAIN, 3V3_AUX, 3V3_AUX_PG and GND. Shared rails are exported as KiCad global nets so the regulator, both Pico sockets, USB hub and front-board interfaces are electrically connected across sheets rather than merely sharing text names.


## Pre-Gerber transient constraints

Each TPS25821 currently has 3 x 47uF at IN (141uF nominal), so four Type-C ports contribute 564uF nominal input bulk across the two daughterboards. The exact capacitor MPN/package must be selected by **effective capacitance at 5V**, not nameplate value alone, because TI calls for at least 120uF close to each TPS25821 IN.

The main input connector and protection stage must tolerate/shape charging of that bulk plus the rest of the system. USB-A downstream reservoir capacitors are separately required at each TPS2553 OUT and are charged behind the per-port switches.


## Source-priority validity windows

The LTC4418 uses its internal 3% hysteresis mode (HYS tied to GND) and approximately 1MΩ three-resistor divider strings. Nominal 1V-comparator windows are:

| Channel | Divider top / middle / bottom | Nominal UV | Nominal OV |
|---|---|---:|---:|
| U4 V1 BARREL_PROT | 887k / 61.9k / 56.2k | 8.51V | 17.88V |
| U4 V2 PD_PWR | 931k / 30.1k / 44.2k | 13.53V | 22.74V |
| U5 V1 EXT_CHARGE_IN | 887k / 80.6k / 44.2k | 8.11V | 22.89V |
| U5 V2 AUX_PWR | 887k / 56.2k / 60.4k | 8.61V | 16.62V |

These are source-validation windows, not surge-clamp specifications. The barrel path still requires its own automotive/reverse/load-dump front end, and PD_PWR is still required to come from a compliant PD sink controller.

Both LTC4418s use 1nF TMR capacitors (about 16ms nominal validation time) and 100nF INTVCC bypass capacitors. VALID1/VALID2 and CAS are intentionally not used in this first source-mux pass.

The Si7155DP is a 40V P-channel PowerPAK SO-8 part. Rev-A uses its conservative 4.6mΩ maximum RDS(on) at -4.5V for preliminary conduction-loss budgeting. The selected external source traverses four MOSFETs (two in U4 plus two in U5); AUX traverses only the U5 pair. Final PCB copper and thermal validation remain mandatory.

### Datasheet verification — source-priority stage

The U4/U5 LTC4418 symbol and Q1-Q8 Si7155DP switching topology were independently rechecked against the manufacturer datasheets on 2026-11-13. LTC4418 pin numbering matches the 20-lead UF QFN definition, including exposed pad 21. Each Si7155DP uses pins 1-4 as source, pin 5 as gate and pins 6-8 as drain. Each source channel uses a common-source back-to-back P-channel pair; VS1/VS2 connect to those common-source nodes, G1/G2 drive the paired gates, and VOUT senses the selected output. HYS is grounded for internal 3% hysteresis, EN and SHDN are tied to INTVCC, TMR uses 1nF to ground and INTVCC uses 100nF to ground. The electrical architecture is therefore datasheet-consistent; only the final page-9 native visual rerender remains before schematic-level freeze.

## Source-priority schematic freeze

Native KiCad 10.0.8 validation after the final pin-coordinate repair is **0 errors / 810 warnings**. The source-priority page now opens and renders directly. The warning count is hygiene-only: 663 endpoint-off-grid, 143 library-symbol-mismatch and 4 intentionally isolated AUX management labels. U4/U5 + Q1-Q8 are therefore frozen at schematic level and should not be functionally changed while the remaining external-source front end is implemented.

## 12V barrel / automotive front end

A dedicated page `09_Barrel_Input.kicad_sch` now implements the primary-source path into the frozen `BARREL_PROT` node. First-pass architecture is J16 Kycon KLDHCX-8-0202-B (2.5mm center-positive, 8A/24V DC), F1 board fuse placeholder, SMBJ36CA bidirectional TVS, U6 LM74800QDRRRQ1, and Q9/Q10 Infineon IAUC100N08S5N034ATMA1 80V N-MOSFETs in TI's common-drain reverse-battery/overvoltage topology. R26/R27 = 93.1k/6.19k gives about 19.75V nominal LM74800 rising overvoltage cutoff. The 99.29k total divider stays below TI's 120k leakage-accuracy guidance. With 1% resistor tolerance and TI OV-threshold limits, first-pass cutoff range is about 18.81–20.71V, still above the frozen LTC4418 U4 barrel-validity range so U4 remains the first source-reject layer.

This is an automotive-capable *architecture*, not a compliance claim. Exact fuse/holder, J16/U6/Q9/Q10 footprints, TVS energy margin, MOSFET SOA/inrush, PCB copper/thermal layout and transient testing remain required before claiming direct raw vehicle-battery compatibility or ISO/LV124 compliance.

### Barrel physical freeze — sub-batch 1

The barrel electrical stage was reconfirmed in native KiCad 10.0.8 at **0 errors / 870 warnings** after the 93.1k/6.19k OVP refinement and is now electrically frozen. U6 uses project-local footprint `SalixFP:TI_DRR0012E_WSON-12_3x3mm_P0.5mm_FloatingEP`, derived from TI DRR0012E land/stencil geometry. Its exposed RTN pad is physically soldered but carries no electrical net and has no thermal vias, preserving LM7480-Q1 reverse-polarity behavior. C13 is frozen to Panasonic EEETQV470XAP (47uF, 35V, ±20%, -40..125C, AEC-Q200) using `Capacitor_SMD:CP_Elec_6.3x7.7`.

The serviceable fuse architecture is now Littelfuse 178.6764.0001 MINI FL1 58V PCB holder with 099707.5WXN 7.5A MINI 58V as the current candidate. The holder MPN is frozen; its exact PCB footprint and the final fuse amp rating remain open. The 7.5A choice must be validated against worst-case 5V output demand, AUX charging and startup/inrush before it is frozen. J16 and Q9/Q10 exact footprints also remain open for the next mechanical sub-batch.

## USB-C PD secondary input

Sheet `10_USB_C_PD_Input.kicad_sch` implements the dedicated secondary POWER receptacle. J17 reuses the frozen GCT USB4085-GF-A (5A/48V/240W) but is power-only; D+/D- and SBU are unused. U8 TVS2200DRVR clamps VBUS, U9 TPD4S201RUKR protects CC1/CC2 from short-to-VBUS and IEC ESD, and U7 TPS25730ADREFR provides a standalone PD3.2 sink with an integrated managed 5A high-voltage path feeding `PD_PWR`.

First-pass strap policy is 15V minimum / 20V maximum, 3A operating / 5A maximum, with automatic sink disable on capability mismatch. This means an accepted source must provide at least a 45W-class contract while allowing up to 100W. Until negotiated-contract telemetry is added through a power-safe I2C buffer, Rev-A firmware/power policy must treat PD as a conservative 45W-guaranteed source rather than assuming 100W. The frozen LTC4418 U4 PD-valid window (~13.53–22.74V) accepts both negotiated 15V and 20V rails.

The PD page also includes a dedicated cable-disconnect Schottky clamp in addition to TVS2200. TI recommends a Schottky from VBUS to GND on TPS25730AD to absorb inductive disconnect current; Rev-A selects STPS5H100BY-TR (5A, 100V, AEC-Q101, 75A non-repetitive surge) with anode at GND and cathode at PD_VBUS_RAW. ST specifies DPAK with the tab/cathode, one anode lead and one NC lead. The first native run after `23c0233` exposed one new ERC warning because KiCad 10.0.8 does not contain the old `TO-252-2_Rectifier` library entry. D30 is therefore moved to project-local `SalixFP:ST_DPAK_STPS5H100Y`, transcribed from ST DS6906 Rev 3 Figure 10: 2.9x1.5mm lead lands at 4.75mm pitch, 6.5x6.3mm tab/cathode land and 1.8mm minimum lead-to-tab gap. Pin 3 is modeled as a hidden NC pin so the physical NC lead remains represented without joining an electrical net.

### USB-C PD electrical freeze

Native KiCad 10.0.8 validation on commit `44a27dd` is **0 errors / 1038 warnings**. The warning count is hygiene-only: 848 endpoint-off-grid, 185 library-symbol-mismatch, 4 intentional isolated AUX management labels, and one intentional pin-to-pin warning from unused TPS25730AD I2C tied to the globally power-flagged GND net. Sheet 10 has been visually reviewed after the final net-overlap repairs and is now electrically frozen. Native validation after commit `302180d` remained **0 errors / 1038 warnings**, so U8/U9 footprint assignments are frozen green. Native validation after commit `644dca0` again remained **0 errors / 1038 warnings** with the same warning categories, so U7 REF0038A is also frozen green. The first D30 native validation produced **0 errors / 1039 warnings** because `Package_TO_SOT_SMD:TO-252-2_Rectifier` is absent in KiCad 10.0.8. Corrective commit `a8f9131` moved D30 to project-local ST geometry; the native rerun returned to the established **0 errors / 1038 warnings** baseline with **0 footprint-link warnings**, so D30 is now physically frozen green. Exact PD capacitor MPNs are assigned in the next physical sub-batch and await native validation. The remaining major electrical design block is `SYS_IN -> 5V_MAIN`.

### PD physical freeze — U8/U9/U7 native green; D30 assigned

U8 TVS2200DRVR is assigned to project-local `SalixFP:TI_DRV0006A_WSON-6_2x2mm_P0.65mm_EP1x1.6mm`, transcribed from TI DRV0006A: six 0.45x0.30mm perimeter lands on 0.65mm pitch with a 1.0x1.6mm exposed pad. The exposed-pad paste is split into two 1.0x0.70mm apertures for approximately 88% paste coverage, following TI's example stencil.

U9 TPD4S201RUKR is assigned to project-local `SalixFP:TI_RUK0020B_WQFN-20_3x3mm_P0.4mm_EP1.7x1.7mm`, transcribed from TI RUK0020B: twenty 0.60x0.20mm perimeter lands on 0.4mm pitch around a 1.7x1.7mm exposed pad. The exposed-pad paste uses four 0.75x0.75mm apertures centered at ±0.47mm, matching TI's approximately 78% stencil coverage example. Thermal vias are intentionally not embedded in the footprint; board-level via strategy remains a layout decision.

Native KiCad 10.0.8 validation on commit `302180d` remained **0 errors / 1038 warnings**, with the exact same 848 endpoint-off-grid + 185 library-symbol-mismatch + 4 intentional isolated AUX labels + 1 intentional pin-to-pin warning breakdown. U8/U9 are therefore physically assigned and native-validated green.

U7 TPS25730AD REF0038A is deliberately **not** approximated from a generic QFN. KiCad already ships the exact manufacturer-specific `Package_DFN_QFN:Texas_REF0038A_WQFN-38-2EP_6x4mm_P0.4` footprint, including separate exposed pads 39/40 and the package-specific mask treatment. Native KiCad 10.0.8 validation after `644dca0` remained **0 errors / 1038 warnings** with the unchanged 848 + 185 + 4 + 1 warning breakdown, so U7 is now physically assigned and frozen green.

D30 STPS5H100BY-TR is an ST automotive DPAK Schottky. The manufacturer package drawing identifies the tab as cathode, one lead as anode and the other as NC. Rev-A uses project-local `SalixFP:ST_DPAK_STPS5H100Y` derived directly from ST Figure 10. Symbol pin 1 maps to the anode, symbol pin 2 maps to the cathode/tab and hidden symbol pin 3 maps to the package NC lead. The corrective native KiCad 10.0.8 rerun after `a8f9131` returned **0 errors / 1038 warnings** with no footprint-link warning, so D30 is frozen green.
### PD physical freeze — exact capacitor batch assigned

TI specifies TPS25730A capacitor minima after tolerance and voltage/DC-bias derating, so the final Rev-A choices are based on real part technology rather than nominal capacitance alone. This batch intentionally changes only component selections/footprints on the already-frozen PD topology:

| Ref(s) | Exact part | Electrical role / reason |
|---|---|---|
| C17 | Murata GRM188R6YA475KE15D, 4.7uF 35V X5R 0603 | VBUS local bypass; matches the TPS25730A EVM-class choice. |
| C18-C21 | Murata GRM188R71H103JA01, 10nF 50V X7R 0603 | High-voltage filtering/snubbing support. |
| C22/C23 | Panasonic EEHZC1H330XP, 33uF 50V hybrid, 6.3x7.7mm | Polarized PPHV bulk. Hybrid technology avoids Class-II MLCC DC-bias collapse; AEC-Q200 and 125C rated. |
| C24 | Murata GRM32ER71H106KA12, 10uF 50V X7R 1210 | PPHV high-frequency ceramic bypass. |
| C25 | TDK C2012X7R1A106K125AE, 10uF 10V X7R 0805 | LDO_3V3 bypass. |
| C26 | TDK C2012X7R1A106K125AE, 10uF 10V X7R 0805 | LDO_1V5 bypass; increased from 4.7uF because TI requires at least 4.5uF after tolerance/derating and permits up to 12uF. |
| C27/C28 | TDK CGA3E2C0G1H331J080AE, 330pF 50V C0G 0603 | CC filtering within TI's 200-480pF requirement; AEC-Q200. |
| C29 | Murata GRM188R6YA105KA12, 1uF 35V X5R 0603 | TPD4S201 VPWR bypass; comfortably above the 0.3uF effective minimum. |
| C30 | TDK C2012X7R2A104K125AE, 100nF 100V X7R 0805 | TPD4S201 VBIAS bypass; upgraded from 50V because the current TPD4S201 requirement is >=63V and recommends 100V. |
| C31 | TDK C2012X7R2A104K125AE, 100nF 100V X7R 0805 | Shield high-frequency coupling; same robust 100V part consolidates the BOM. |

For the TPS25730AD PPHV bank, C22 + C23 + C24 provide **76uF nominal**. The two hybrid parts alone have a tolerance-only minimum of 52.8uF; including C24's tolerance gives a nominal-tolerance range of **61.8uF to 90.2uF**, inside TI's 47-100uF D-variant window before relying on the ceramic for the minimum. C22/C23 are now represented as polarized capacitors with `PD_PWR` on `+` and GND on `-`.

Native KiCad 10.0.8 validation after commit `c852b84` completed with **0 errors / 1036 warnings**: 848 endpoint-off-grid + 183 library-symbol-mismatch + 4 intentional isolated AUX labels + 1 intentional pin-to-pin warning. No new warning category appeared; the two-warning reduction is from C22/C23 moving to the dedicated `CP_PD` library symbol. Page 11 was visually checked with C22/C23 polarity correct (`PD_PWR` to `+`, GND to `-`). The USB-C PD electrical and physical stage is therefore **fully frozen green**.

