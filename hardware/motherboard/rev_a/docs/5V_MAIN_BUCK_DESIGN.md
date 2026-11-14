# 5V_MAIN Buck Design — Rev A

Status: **CONTROLLER / TOPOLOGY FROZEN; POWER STAGE PROVISIONAL**

## Design target

- Input net: `SYS_IN`
- Steady-state selected-source envelope: approximately **8V to 23V**
- Output net: `5V_MAIN`
- Output target: **5.0V / 12A continuous** (60W)
- Topology: single-phase synchronous buck
- First-pass switching frequency: **440kHz**
- Controller: **TI LM25149QRGYRQ1**
- Controller footprint: `Package_DFN_QFN:Texas_RGY_R-PVQFN-N24_EP2.05x3.1mm`
- First-pass operating mode: FPWM, active EMI filter enabled, dual-random spread spectrum enabled
- VCCX: return to the established 5V output as recommended by TI for the 5V design

## Why LM25149-Q1

The LM25149-Q1 is a current-production AEC-Q100 42V synchronous buck controller with peak-current-mode control, external MOSFETs, integrated active EMI filtering and dual-random spread spectrum. Its 3.5-42V operating range comfortably spans the already-protected selected-source rail.

TI Design 2 in the LM25149-Q1 datasheet is a particularly close reference:
- 5.5-36V input
- 5V / 10A output
- 440kHz
- 2.2uH output inductor
- 4mOhm shunt
- two external 40V N-channel MOSFETs
- 4x47uF output capacitors
- approximately 95% full-load target efficiency

Rev-A scales the current capability from 10A to 12A while preserving the proven control/EMI architecture.

## Power envelope

The buck is a **12A-capable rail**, not a guarantee that every source can supply 12A.

Approximate input current for 60W output:
- 8.1V source: ~7.8A at 95% efficiency, ~8.2A at 90%
- 12V source: ~5.3A at 95%, ~5.6A at 90%
- 20V source: ~3.2A at 95%, ~3.3A at 90%

### Barrel

Barrel is the intended full-power source. Final adapter and fuse ratings must include 5V_MAIN system power, conversion loss, any concurrently enabled AUX recharge power, and startup/inrush/transient margin. The existing 7.5A MINI fuse remains provisional.

### USB-C PD

The current standalone PD straps accept a 15V/3A-class source, so firmware must treat PD as **45W-guaranteed** until negotiated-contract telemetry exists. At 90-95% conversion efficiency, 45W input yields about 8.1-8.55A gross at 5V. After reserving about 1A for motherboard/Pico/fan load, a conservative downstream-port budget is around 7A. This is a policy starting point, not yet a frozen per-bank allocation.

### AUX

AUX source capability is module-dependent. Full 12A output must not be assumed without a module contract.

## Provisional power-stage candidates

### MOSFETs

**Infineon IAUC60N04S6L039** x2 — 40V, 4.7mOhm class, ~7nC gate charge, AEC-Q101, and TI's Design-2 reference MOSFET. Final checks: conduction loss, switching loss, dead-time/body-diode loss, switch-node overshoot, and copper/thermal spreading.

### Output inductor

**Coilcraft XGL1010-222MED** — 2.2uH ±20%, 2.3mOhm typical DCR, 36A Isat (30% inductance drop), 24.6A Irms for 20C rise, AEC-Q200.

### Current shunt

**Susumu KRL2012E-M-R003-F-T5** — 3mOhm, ±1%, 1W, 0508/wide-0805, AEC-Q200. LM25149-Q1 current-limit threshold is 49mV min / 60mV typ / 73mV max. The 3mOhm candidate is intentionally lower than TI's 4mOhm 10A design so minimum-threshold current limit remains above the 12A continuous target after inductor ripple. Exact OCP min/typ/max remains to be calculated.

### Input capacitors

First pass: 4x TDK CGA6P3X7S1H106K250AB, 10uF / 50V / X7S / 1210 / AEC-Q200. The active EMI filter also requires its input inductor, damping reservoir and compensation network.

### Output capacitors

First pass: 6x TDK CGA6P1X7S1A476M250AC, 47uF / 10V / X7S / 1210 / AEC-Q200. Final count depends on effective capacitance at 5V, load-step droop, ESR/ESL and loop compensation.

## Next calculations before schematic freeze

1. Inductor ripple at min/max SYS_IN and ±20% L.
2. RSENSE current-limit min/typ/max including ripple.
3. MOSFET conduction + switching + gate-drive loss at 8V, 12V and 20V.
4. Inductor copper/core loss and temperature rise.
5. Input-cap RMS ripple and source-mux stress.
6. Output effective capacitance and 0→12A / 6→12A load-step droop.
7. Compensation values for the final L/C/ESR network.
8. EN/UVLO divider so the buck does not start on an invalid/decaying SYS_IN rail.
9. Active-EMI-filter component values.
10. PGOOD routing into the service/realtime management logic.
11. Startup/inrush against the downstream 5V capacitance already present on the motherboard/front boards.
12. Barrel adapter/fuse policy with simultaneous AUX recharge.

Only after those checks should the new KiCad buck sheet be called electrically frozen.
