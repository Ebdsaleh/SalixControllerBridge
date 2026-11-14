# 5V_MAIN Buck Design — Rev A

Status: **CONTROLLER / TOPOLOGY + POWER-TRAIN + LOOP-COMPENSATION + POWER-STAGE FOOTPRINTS FROZEN; BARREL/RECHARGE LOAD-SHED NATIVE GREEN; KICAD BUCK SHEET NATIVE GREEN / ELECTRICALLY FROZEN**

## Native baseline before buck schematic work

The documentation-only architecture pull was followed by a full native KiCad 10.0.8 rerun on the unchanged schematics. Result: **0 errors / 1036 warnings** (848 endpoint-off-grid + 183 library-symbol-mismatch + 4 intentional isolated AUX labels + 1 intentional pin-to-pin). This confirms the frozen source-priority, barrel and USB-C PD sheets remained unchanged before the buck design moved into calculation.

## Frozen architecture

- Input net: `SYS_IN`
- Steady-state selected-source design envelope: approximately **8.1V to 23V**
- Output net: `5V_MAIN`
- Output target: **5.0V / 12A continuous hardware capability** (60W)
- Controller: **TI LM25149QRGYRQ1**
- Controller footprint: `Package_DFN_QFN:Texas_RGY_R-PVQFN-N24_EP2.05x3.1mm`
- Topology: single-phase synchronous buck
- RT: **49.9k 1%**; TI reference value, approximately 435–440kHz nominal depending equation/rounding
- CNFG: **41.2k 1% to AGND** = primary, single-phase, DRSS enabled
- PFM/SYNC: **GND** = FPWM
- FB: **24.9k to VDDA** = fixed 5V output mode
- VCCX: **5V_MAIN** after output establishes
- CVCC: 2.2uF; CBOOT: 0.1uF; CVDDA: 0.1uF

Important datasheet reconciliation: TI Figure 9-18 labels RCNFG as 24.9k, but the current electrical-characteristics table and Table 8-2 define **41.2k** as the valid primary/single-phase/spread-spectrum configuration. Rev-A follows the current configuration tables, not the inconsistent figure label.

## TI reference basis

TI Design 2 is the starting point: 5.5–36V input, 5V/10A output, 440kHz, 2.2uH, 4mOhm current shunt, external 40V MOSFET half bridge, active EMI filter, 3x10uF local input ceramics, 100uF damping bulk and 4x47uF output ceramics. Rev-A preserves that architecture and scales current margin to 12A.

## Output inductor — FROZEN

Part: **Coilcraft XGL1010-222MED**

- 2.2uH ±20%
- DCR: 2.3mOhm typical / 2.6mOhm maximum at 25C
- Isat: 15A at 10% drop, 26A at 20% drop, 36A at 30% drop
- Irms: 24.6A for 20C rise / 33A for 40C rise
- AEC-Q200

Calculated inductor ripple, using the nominal part and the 49.9k RT operating point, is approximately:

| SYS_IN | nominal ripple p-p |
|---:|---:|
| 8.1V | 2.00A |
| 12V | 3.05A |
| 20V | 3.92A |
| 23V | 4.09A |

For a deliberately conservative ripple corner of **L = 1.76uH (-20%) and fs = 400kHz**, 23V input produces **5.56A p-p** ripple and **14.78A** peak current at a 12A load. That is within TI's preferred 30–50% ripple region at the upper input range and leaves substantial saturation margin in normal operation.

## Current sense — FROZEN

Part: **Susumu KRL2012E-M-R003-F-T5**

- 3mOhm ±1%
- 1W
- wide 0805 / 0508
- ±50ppm/C
- AEC-Q200

LM25149-Q1 current threshold is 49mV min / 60mV typ / 73mV max. With the 5.56A worst-case ripple:

- guaranteed-min equivalent load-current limit, including +1% resistance and a conservative +0.5% TCR allowance: **~13.31A**
- typical equivalent load-current limit: **~17.22A**
- high-threshold equivalent load-current limit, including low resistance corner: **~21.9A**
- shunt dissipation at 12A with worst ripple: **~0.45W**, below the 1W rating

Using the 73mV high threshold, minimum shunt resistance and the controller's 65ns typical sense delay gives an approximate short-circuit peak of **~25.4A** at 23V. That can enter the XGL1010's 20%-drop saturation region but remains well below its 36A / 30%-drop rating. The 65ns delay is typical, not a guaranteed maximum, so switch-node ringing and hard-short current still require bench validation.

TI's own design criterion of sizing the current threshold to at least 125% of full-load peak permits a maximum shunt of about **3.25mOhm** at this worst ripple corner, so the selected 3mOhm value has appropriate margin.

## MOSFETs — FROZEN PART, THERMAL/LAYOUT VALIDATION STILL REQUIRED

Parts: **2x Infineon IAUC60N04S6L039**

- 40V AEC-Q101 PG-TDSON-8
- RDS(on) at 4.5V: 4.71mOhm typical / 5.90mOhm maximum
- Qg: 15nC typical / 20nC maximum at the datasheet's 10V test condition
- Qrr: 18nC typical
- RthJC maximum 3.6K/W; datasheet board-level RthJA example 50K/W

This is the exact MOSFET used by TI's 5V/10A/440kHz Design 2. Rev-A's maximum steady `SYS_IN` is only about 23V, giving significantly more drain-voltage headroom than TI's 36V steady-state reference.

A conservative screening calculation using the 4.5V maximum RDS(on), TI's approximate +4500ppm/C temperature coefficient, 7ns switching-edge assumptions and full datasheet reverse-recovery charge puts each MOSFET in roughly the **1.1–1.3W** range at the harsher 12A operating points. At the datasheet example 50K/W board thermal resistance this is roughly a 55–65C junction rise. That is acceptable for selection, but PCB copper, airflow, switching-node overshoot and measured junction/board temperature remain mandatory layout/bench gates.

## Input network — FROZEN FIRST-PASS ELECTRICAL VALUES

### Active EMI input inductor

Part: **Coilcraft XGL6060-102MEC**

- 1.0uH ±20%
- 2.5mOhm typical / 2.9mOhm maximum DCR
- Isat: 11A at 10% drop / 17.2A at 20% / 23A at 30%
- Irms: 20.5A for 20C rise
- AEC-Q200

The 60W buck requires about 7.8–8.2A at the minimum valid source voltage, so this part has useful continuous-current and saturation margin while staying close to TI's Design-2 1uH filter.

### Local switching ceramics

**4x TDK CGA6P3X7S1H106K250AB**, each 10uF / 50V / X7S / 1210 / AEC-Q200.

Calculated input-capacitor AC RMS stress is approximately 5.87A at 8.1V, 5.97A at 12V, 5.25A at 20V and 5.01A at 23V for the full bank. The four ceramics share the high-frequency component; placement directly across the MOSFET power loop is mandatory.

### Damping / bulk reservoir

**Panasonic EEHZC1V101V**, 100uF / 35V hybrid, ±20%, 125C, AEC-Q200, 1.6Arms ripple rating at 100kHz.

Place this **after** the 1uH AEF inductor as TI does with CDAMP1. Do not add a low-ESR bulk capacitor on the VIN-EMI side of LIN without rechecking AEF stability.

### Active EMI compensation network

Freeze the low-frequency AEF values from TI Design 2:

- CSEN = 0.1uF
- CINJ = 0.47uF
- RINC = 0.47ohm
- CINC = 0.1uF
- CDAMP = 0.22uF
- RDAMP = 17.8ohm
- CAEFC = 1nF
- RAEFC = 1k
- RAEFDC = 49.9k
- RAEFVDD = 3ohm
- CAEFVDD = 2.2uF

These are first-pass schematic values. Actual conducted/radiated EMI performance is layout- and enclosure-dependent and must be bench-tested.

## Output capacitors — REVISED AND FROZEN AT 8 PARTS

Part: **8x TDK CGA6P1X7S1A476M250AC**, 47uF / 10V / X7S / 1210 / AEC-Q200.

A current TI design using this exact capacitor reports about **40uF effective per part at 5V**. Eight parts therefore provide roughly **320uF typical effective** at 5V. Applying a deliberately conservative additional ±20% capacitance-tolerance floor and the full X7S -22% temperature coefficient gives about **200uF** effective bank capacitance.

TI's load-off energy equation for 12A, 2.2uH and 5V requires:

- ~208uF for 150mV overshoot
- ~183uF for 170mV overshoot
- ~155uF for 200mV overshoot

Thus the conservative ~200uF bank predicts roughly **156mV** idealized load-off overshoot, while the typical ~320uF bank predicts about **98mV**. The worst-ripple capacitive component is only about **8.7mV p-p** at the conservative 200uF / 400kHz corner, before ESR/ESL effects.

This is why the earlier six-cap first pass is replaced by **eight** parts: six were comfortable at typical effective capacitance but not robust after stacked derating assumptions.

## UVLO — FROZEN

Use:

- RUV1 = **49.9k 1%** from SYS_IN to EN
- RUV2 = **8.06k 1%** from EN to GND

Using TI's 1.0V typical EN threshold and 10uA hysteresis gives approximately **7.19V turn-on / 6.69V turn-off**. Including 1% resistor tolerance, the guaranteed 0.95–1.05V EN threshold and 8–12uA hysteresis range gives approximately:

- turn-on: **6.72V to 7.68V**
- turn-off: **6.12V to 7.28V**

This stays below the lowest frozen source-valid window (~8.1V), so the buck does not reject a source that the upstream power-path logic has already accepted.

## Loop compensation — ANALYTICALLY FROZEN FOR SCHEMATIC

Freeze the external type-II network as:

- RCOMP = **5.90k 1%**
- CCOMP = **10nF**
- CHF = **DNP by default**, with a **22pF fitted/tuning option**

The values were rechecked directly against the LM25149-Q1 datasheet equations rather than copied from Design 2.

Using TI Equation 46 with VOUT/VREF=6.25, RS=3mOhm, GCS=10, gm=1200uS, conservative effective COUT=200uF and a 30kHz target crossover gives **RCOMP=5.89kOhm**, which maps directly to the selected 5.90kOhm E96 value.

At 12A the 5V load is about 0.417Ohm. With 200uF, the load pole is about **1.91kHz**, while fc/10 is **3.00kHz**; TI therefore places the compensation zero at about 3kHz. Equation 47 gives **CCOMP about 8.98nF**. The selected 10nF standard value places the zero at about **2.70kHz**.

At the more typical **320uF** effective output bank, the same 5.90k network naturally reduces crossover to about **18.78kHz**. The 10nF zero remains about 2.70kHz, roughly fc/7, keeping the loop intentionally conservative.

TI also states CHF may be unpopulated when the calculated high-frequency capacitor is negligible, with **22pF** offered as a small noise-filter option. Rev-A therefore leaves CHF DNP by default and provides 22pF as a tuning value.

TI Design 2 at 440kHz uses 4.22k / 15nF / 150pF with 2.2uH, 4mOhm and 4x47uF. Rev-A does not copy that network because its 3mOhm shunt and substantially larger effective output bank change the required loop gain.

The current TI A4 quickstart calculator is acknowledged as the official spreadsheet tool, but its XLSM could not be directly executed/retrieved in this environment. No claim is made that it was run. These schematic values are frozen from TI's published equations and cross-check against the 440kHz reference architecture; **physical Bode measurement remains a board-level validation gate before production release**.

## PGOOD

Route the open-drain PG/SYNCOUT pin as a normal PGOOD because this is single-phase primary operation. Use a **100k pull-up to 3V3_AUX** and expose the signal to service/realtime supervision. Final receiving GPIO is still to be assigned.

## Source-aware power policy

The 12A converter rating is hardware capability, not a universal source budget.

- Barrel: intended full-power source.
- USB-C PD: present standalone straps guarantee only 45W input; without negotiated-contract telemetry the full 60W rail must not be advertised downstream.
- AUX: module-dependent; full power requires a module capability contract.

## BARREL VS AUX RECHARGE CONCURRENCY — RESOLVED

Rev-A keeps the existing 8A Kycon barrel interface and makes AUX recharge a default-off, firmware-sheddable load. The 60W system rail remains the priority load.

The load-shed implementation uses U3 EN/UVLO rather than adding another series power switch:
- Q11 2N7002BK clamps EN/UVLO low by default.
- A passive 100k/100k EXT_CHARGE_IN divider biases Q11 ON even before 3V3_AUX exists.
- Q12 2N7002BK can pull Q11's gate low when management asserts AUX_CHG_ENABLE.
- U60 is upgraded to TCA9534APWR; P4 is AUX_CHG_ENABLE and P5 reads AUX_CHG_PG.
- TCA9534A power-up input/high-Z behavior plus Q12's 100k pulldown makes the hardware default **recharge disabled**.
- Firmware must write the safe output value 0x03 before changing the direction register to 0xEC. P4 may only be driven high after load/source policy explicitly authorizes charging.

This retains the existing <=2A recharge contract when headroom is available while preventing full system load plus full recharge from being an unconditional barrel requirement.

The 7.5A fuse remains provisional until the actual load-shed thresholds, adapter rating, harness gauge and measured losses are frozen.

## Physical footprint freeze — POWER STAGE COMPLETE

Exact manufacturer land-pattern review produced the following Rev-A assignments:

- XGL1010-222MED -> `SalixFP:Coilcraft_XGL1010_11.3x10.0mm`: two 2.38 x 8.50 mm lands on 6.65 mm centers.
- XGL6060-102MEC -> `SalixFP:Coilcraft_XGL6060_6.71x6.51mm`: two 1.43 x 5.50 mm lands on 4.04 mm centers.
- KRL2012E-M-R003-F-T5 -> `SalixFP:Susumu_KRL2012E_0508_LongSide`: Susumu long-side-terminal >=2mOhm/35um-Cu geometry, a=0.60 mm gap, b=2.00 mm total span, c=2.20 mm height; resulting lands are 0.70 x 2.20 mm at +/-0.65 mm centers.
- EEHZC1V101V -> `SalixFP:Panasonic_EEH_ZC_F_VibrationProof_8x10.5mm`: Panasonic size-F vibration-proof cross land, a=2.7, b=4.0, c=4.7, d=1.3, e=1.0, f=1.7, g=1.1, h=2.5 mm. Pad 1 is positive and pad 2 negative.
- TDK 1210 input/output ceramic banks -> stock `Capacitor_SMD:C_1210_3225Metric`.
- IAUC60N04S6L039 -> `SalixFP:Infineon_PG_TDSON_8_33`: exact Infineon PG-TDSON-8-33 manufacturer copper/stencil geometry, 1.27 mm pitch, numeric datasheet pinout 1-3 Source / 4 Gate / 5-8 Drain. The large central drain copper reuses pad 5 and the source bridge reuses pad 2 because the package has no separate exposed-pad pin number.

The PG-TDSON-8-33 footprint was transcribed from Infineon's current recommended PCB copper/stencil drawing and independently cross-checked against a separately authored KiCad PG-TDSON-8-33 transcription. The asymmetric source/gate region, four drain fingers, central drain copper and segmented stencil apertures agree. This closes the final 5V_MAIN power-stage footprint blocker. Do not substitute PG-TDSON-8-57 or a generic SON-8 footprint.

## KiCad buck-sheet native validation — GREEN / FROZEN

The first native page-12 run exposed eight generated-coordinate endpoint errors around U70 and the two MOSFET gate stubs. Commit `5c50e41` corrected only those wire/label endpoint coordinates; no component values, footprints or frozen topology changed.

The returned KiCad 10.0.8 rerun after `5c50e41` is **0 errors / 1258 warnings** and successfully renders all 12 schematic sheets plus all 12 project-local footprints. Warning breakdown is **1024 endpoint_off_grid + 226 lib_symbol_mismatch + 4 isolated_pin_label + 3 lib_symbol_issues + 1 established USB-C PD pin_to_pin warning**. The page-12 image was visually reviewed after the correction and the U70/Q70/Q71 endpoints are coherent.

Therefore `11_5V_MAIN_Buck.kicad_sch` is **native-green and electrically frozen**. Do not alter the frozen buck topology except for a verified defect.

## Remaining board-level validation gates

1. Physical Bode measurement.
2. PCB-level thermal and switch-node ringing validation.
3. Hard-short/current-limit and load-transient validation.
4. Conducted/radiated EMI validation with the real PCB/enclosure/harness.
