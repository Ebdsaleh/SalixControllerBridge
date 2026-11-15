# SalixControllerBridge Rev-A — Current Hardware Handoff

Date: 2026-11-15

## Current phase

**Schematic phase: GREEN / FROZEN.**

**Motherboard PCB phase: POPULATED / READY FOR FUNCTIONAL PLACEMENT.**

The corrected populated motherboard baseline is committed as:

```text
c12a1be  Capture corrected Rev-A motherboard population baseline
```

Do not restore the motherboard `.kicad_pcb` to an earlier scaffold-only revision.

## Native validation state

### Schematic

- KiCad 10.0.8.
- 13/13 sheets render.
- 25/25 project-local footprints validate.
- ERC: **0 errors / 1375 warnings**.
- Global annotation cleanup complete:
  - 310 unique non-power references;
  - hidden `#FLG/#PWR` references are also preflighted;
  - duplicate `#FLG04` was resolved by moving the front-USB flag to `#FLG06`.
- Root hierarchy page-13 `sheet_instances` defect repaired.
- Renderer now preflights:
  - root sheet-instance completeness;
  - annotation uniqueness including hidden references;
  - project-local symbol-to-footprint pad mapping.

### PCB / F8 population

The first real F8 population exposed **92 hard pad-map errors / 72 warnings**. These were source defects, not user placement errors.

All 92 were closed:

- J2/J4/J6 right-hand Pico rails: 60 errors; fixed with project-local 21-40 socket/header footprints.
- Q1-Q8 Si7155DP: 24 errors; symbol corrected to real package numbering: pins 1-3 source, 4 gate, 5-8 drain; PowerPAK grouped drain land maps to pad 5.
- U7 TPS25730A REF0038A: 6 errors; grouped TI package terminals mapped to grouped lands.
- J13 microSD shell: 1 error; frozen project-local exact Hirose footprint.
- J17 USB-C shell: 1 error; frozen project-local exact GCT USB4085 footprint.

Corrected F8 result:

```text
0 errors / 4 warnings
```

The four warnings are expected unnetted `MP` mechanical mounting pads on J12/J14.

### Populated-board guard

Latest native PCB validation:

- 224 total footprints;
- 220 non-scaffold motherboard footprints;
- **no page-07/page-07A front-board leakage**;
- 0 footprint errors;
- 265 DRC violations;
- 499 unconnected items.

The DRC totals are expected for the temporary first-import pile and unrouted board. Do not treat them as a routed-layout failure.

Known non-placement DRC items already separated from pile noise:

- fine-pitch internal clearance on J17/U3/U7 versus generic 0.20mm board clearance;
- 0.20mm thermal vias in U1/U7 versus current generic 0.30mm minimum-hole rule.

These should be resolved by deliberate board-rule/fabrication-rule alignment, not by moving parts.

## Working motherboard mechanics

These remain a **working layout envelope**, not enclosure-frozen geometry:

- board: 160 x 100mm;
- thickness: 1.6mm;
- four layers:
  - F.Cu;
  - In1.Cu intended GND reference;
  - In2.Cu intended power distribution;
  - B.Cu;
- 4 x M3 mounting holes;
- 3.2mm NPTH;
- hole centres 5mm in from corners;
- rear = power/service side;
- front = front-USB harness side.

The enclosure concept remains GameCube-scale with a layered/stacked internal arrangement. The motherboard sits low in the chassis; the future rechargeable-battery PCB is a separate module below/adjacent through the existing AUX interface. Console personality cards/backplane remain future separate PCBs and do not block Rev-A.

Rev-A cooling remains **two independently controlled 5V 4-wire PWM fans**. A third/top fan may be considered later, not for Rev-A.

## Rev-A scope — do not drift

Rev-A is the SalixControllerBridge box:

- 8 physical USB receptacles;
- 4 concurrent/logical controller inputs;
- two universal front USB daughterboards;
- Pico-A = realtime USB-host/controller bridge;
- Pico-B = service/storage/update/diagnostics;
- dual-Pico soft-linked architecture;
- microSD + TFT/service interface;
- source-priority / protected power architecture;
- two 5V PWM fan channels.

Do not design console personality cards, the module backplane, battery-module PCB, ROM programmer/dumper, SNES DevCart, or other ecosystem hardware inside this Rev-A motherboard task.

## Capacitor reliability policy

Rev-A now has an explicit motherboard-class capacitor-quality rule:

- keep quality MLCC ceramics where they are electrically correct;
- prefer C0G/NP0 for precision/timing and reputable X7R/X7S for decoupling/power roles;
- avoid Y5V/Z5U on critical rails;
- use Murata / TDK / Yageo-class MLCC parts and prefer AEC-Q200 variants where practical;
- use conductive-polymer or conductive-polymer-hybrid aluminum capacitors for polarized bulk storage where electrically appropriate;
- avoid commodity wet aluminum electrolytics unless a control-loop/damping requirement explicitly benefits from their ESR.

Existing high-reliability bulk choices already include Panasonic EEH-series hybrid parts for USB-A VBUS, USB-C PD bulk and 5V_MAIN damping.

The remaining conventional 12V barrel output reservoir has been flagged for upgrade. Candidate:

```text
Panasonic EEHZC1V470P
47uF / 35V
conductive-polymer hybrid
-55C to +125C
60mOhm max ESR @ 100kHz
900mArms ripple @ 125C
```

This candidate is **not yet electrically frozen** because its much lower ESR requires rechecking LM74800/source-priority transient, inrush and damping behaviour before Gerber freeze.

## Current repo head at handoff creation

Latest hardware-policy/doc commits:

```text
f2b5329  Track hybrid capacitor upgrade before Gerber
693cd77  Document capacitor reliability policy
651fc01  Adopt high-reliability capacitor policy
c12a1be  Capture corrected Rev-A motherboard population baseline
88f0bb2  Advance Rev-A to functional PCB placement
97e663b  Record populated motherboard DRC baseline
1fb3e31  Advance Rev-A to populated PCB validation
c7e2081  Close corrected F8 population gate
```

A later docs-only handoff refresh commit may sit above these.

## Immediate next work

1. Pull current `main`.
2. Work from the populated motherboard committed in `c12a1be`.
3. Perform **functional block placement only**; do not route yet.
4. Placement order:
   - chassis/mechanical connectors and board-edge constraints;
   - 12V barrel/protection/source-priority/high-current power path;
   - 5V_MAIN buck and its tight high-di/dt loop;
   - Pico-A / Pico-B / microSD / service-TFT;
   - USB hub + Pico-A USB interface;
   - motherboard/front-board harness connectors;
   - fan/AUX/service connectors and remaining management logic.
5. Review whether the 160x100mm working envelope remains sensible before routing.
6. Align exact fine-pitch/thermal-via design rules with PCBWay capability and the frozen footprints.
7. Only then begin routing:
   - power/high current;
   - USB differential pairs/return paths;
   - management/SPI/I2C/GPIO;
   - planes/pours/thermal copper.
8. Close PCB DRC before Gerbers.
9. Then create/finalize the universal front USB PCB.
10. Generate fab package and get the PCBWay quote before the signup vouchers expire.

## User workflow / safety

The user is not expected to know KiCad internals. When a GUI step is required, give one action at a time and ask for screenshots when KiCad presents an unexpected dialog.

Useful validators:

```bat
py tools\render_kicad_schematics.py
py tools\render_kicad_pcb.py --expect-populated
```

Keep outputs separate:

- schematic bundle: `Downloads\kicad_fixes.zip`;
- motherboard PCB bundle: `Downloads\kicad_pcb_validation.zip`.

Long KiCad reports can be captured by Select All -> Copy -> paste into a text file. This was extremely useful for the F8 pad-map diagnosis.

## Branch / working policy

- main / dev / test only;
- current hardware work has been landing on `main`;
- prefer small, auditable batches;
- native KiCad validation after each structural/electrical change;
- do not call a gate GREEN until the returned user-side native validation proves it.


## PCB placement batch 1 — chassis-facing anchors

Commit:

```text
d4a0232  Place Rev-A chassis-facing connector anchors
```

Placed only the four safest chassis-facing anchors:

- J16 barrel input: rear edge, body extending inward;
- J17 dedicated USB-C PD power input: rear edge, exact footprint PCB-edge datum aligned to board edge;
- J7 PRIMARY front-board Micro-Fit: front edge;
- J8 EXTENDED front-board Micro-Fit: front edge.

No Picos, power-stage ICs, passives, fans, AUX, or routing were moved in this batch.

The next gate is user-side native PCB validation:

```bat
git pull --ff-only
py tools\render_kicad_pcb.py --expect-populated
```

Inspect top/bottom renders before continuing placement.


### Batch-1 validation correction

Returned native render/DRC showed J16 had been rotated the wrong direction in the initial anchor batch: its electrical pads landed outside the rear board edge. J17 and front anchors J7/J8 were mechanically correct.

Correction:
- J16 -> (165, 20) at 270 degrees, placing the jack front face on the rear y=20 edge and the jack body/pins inward.
- J17 remains aligned to rear y=20 through its exact PCB-edge datum.
- J7/J8 remain on the front y=120 edge.
- J8 currently overlaps the still-unplaced Pico-B footprint pile; this is temporary and must not be interpreted as an anchor collision.

Revalidate before freezing batch 1.


### J16 polarity catch during batch-1 freeze

The corrected mechanical orientation validated, but tracing the barrel current path exposed a stale PCB net assignment:

- source schematic: J16 pin 1 CENTER_+ -> BARREL_JACK_RAW; pin 2 SLEEVE_GND -> GND;
- project-local footprint: pad 1 is the positive/center terminal and pad 2 is sleeve;
- populated PCB baseline had those two nets reversed.

Board-only correction:
- `3aac37b Correct J16 center-positive PCB net mapping`

Validator hardening:
- `aba2484 Guard J16 center-positive PCB mapping`

Do not route the barrel block unless `render_kicad_pcb.py --expect-populated` prints:

```text
J16       : center-positive pad mapping verified (1=RAW, 2=GND)
```

The source schematic itself was already correct and was not changed.


## PCB placement batch 2 — 12V barrel protection core (native validation required)

Board commit:

```text
2ef4c27  Place Rev-A barrel protection core
```

This batch deliberately moves only the core barrel-protection/current-path parts behind the already-frozen J16 rear-edge anchor:

- F1 MINI fuse holder -> (160, 40), 180 deg;
- D29 SMBJ36CA TVS -> (160, 49), 90 deg;
- Q9 ideal-diode MOSFET -> (153.25, 52), 270 deg;
- Q10 load-disconnect MOSFET -> (144.75, 52), 90 deg;
- U6 LM74800-Q1 -> (149, 57.2), 90 deg;
- C13 barrel protected-output bulk reservoir -> (135, 52), 180 deg.

Intent:

- preserve the center-positive J16 mapping and the short raw-input path into F1;
- make Q9/Q10 a compact common-drain pair with the BARREL_MID copper facing inward;
- keep U6 directly below the MOSFET pair for short gate/control connections;
- place D29 close to the fused input/protection stage;
- place C13 on the BARREL_PROT output side while reserving physical room for the planned higher-reliability hybrid-capacitor review.

No routing was added. No other functional block was moved.

Source-level post-commit checks confirm:

- 224 footprints still exist;
- J16 remains at (165,20), 270 deg;
- J16 pad 1 remains BARREL_JACK_RAW and pad 2 remains GND;
- the six moved references retain their original nets.

This batch is **NOT GREEN yet**. Required native gate:

```bat
git pull --ff-only && ^
git log -8 --oneline && ^
py tools\render_kicad_pcb.py --expect-populated
```

Return the console output plus `kicad_pcb_validation.zip`. Inspect top/bottom renders before placing the remaining U6 support passives or moving the source-priority block.


### Batch-2 rotated-pad serialization correction

The first native validation of placement batch 2 returned the expected population and J16 polarity guards, but DRC exposed impossible same-footprint shorts inside Q9/Q10 and U6.

Root cause was **not** the manufacturer land patterns:

- Infineon PG-TDSON-8-34 source geometry matches the IAUC100N08S5N034 recommended copper/stencil drawing;
- TI DRR0012E source geometry matches drawing 4224874/C for LM7480-Q1.

The defect was introduced by direct PCB text placement: footprint-level rotation had been changed without also updating each placed pad's absolute rotation angle. In a placed `.kicad_pcb`, KiCad expects pad angles to be absolute board angles. This rotated pad centres but left non-square copper shapes at their old orientation, creating false/internal copper shorts.

Corrections:

```text
347eafd  Correct absolute pad angles for rotated PCB placements
5d7e4ed  Guard absolute pad angles on rotated PCB placements
```

Corrected references:
- J16 = 270 deg;
- J17 = 180 deg;
- F1 = 180 deg;
- D29 = 90 deg;
- Q9 = 270 deg;
- Q10 = 90 deg;
- U6 = 90 deg;
- C13 = 180 deg.

The validator now hard-fails if any of these rotated footprints has pad angles that do not match its placed board orientation.

This correction is **SOURCE-FIXED / NATIVE RETEST REQUIRED**. Do not advance placement until a returned KiCad run confirms that the Q9/Q10/U6 internal-short class disappears.


### Batch-2 native validation — GREEN

Returned user-side KiCad 10.0.8 validation after the absolute-pad-angle correction confirms the serialization defect is closed.

Guards:
- 224 total footprints;
- 220 non-scaffold motherboard footprints;
- no page-07/page-07A leakage;
- J16 center-positive mapping verified;
- rotated-placement absolute pad-angle guard passed.

DRC changed from **362 -> 312** total violations.

Most importantly:
- previous `shorting_items` count fell from **15 -> 4**;
- Q9 has **0** short/clearance violations;
- Q10 has **0** short/clearance violations;
- U6 has **0** short/clearance violations;
- the four remaining shorting findings are all the temporary J8-vs-still-piled J6 overlap and are therefore placement-pile noise.

The barrel protection core placement is therefore **NATIVE GREEN / FROZEN**.

## PCB placement batch 3 — LM7480 support network

Board commit:

```text
81604ce  Place LM7480 support network
```

Validator update:

```text
33768c1  Extend rotated placement guard to LM7480 passives
```

Placed only the seven local LM7480 support passives around U6:

- C12 BARREL_FUSED-to-GND input bypass -> (146.7, 61.3), 270 deg;
- C14 BARREL_MID-to-GND bypass -> (152.6, 57.2), 0 deg;
- C15 BARREL_CAP-to-BARREL_MID -> (145.4, 57.2), 180 deg;
- C16 BARREL_DVDT-to-GND -> (155.8, 60.0), 0 deg;
- R26 OV_TOP-to-OV -> (149.25, 61.3), 270 deg;
- R27 OV-to-GND -> (149.25, 64.5), 270 deg;
- R28 HGATE-to-DVDT -> (152.6, 60.0), 0 deg.

No routing was added and no other block was moved.

Source-level post-commit review confirms all seven references retained their original nets. The absolute-pad-angle validator now also covers C12, C15, R26 and R27.

Batch 3 is **SOURCE-PLACED / NATIVE RETEST REQUIRED**.


### Batch-3 native validation — GREEN

Returned KiCad 10.0.8 validation after the LM7480 support-network placement confirms:

- 224 total footprints / 220 non-scaffold;
- no page-07/page-07A leakage;
- J16 center-positive guard passed;
- rotated-placement absolute-pad-angle guard passed.

The seven moved LM7480 support parts (C12/C14/C15/C16/R26/R27/R28) introduced:

- **0 clearance violations**;
- **0 shorting violations**;
- **0 courtyard violations**;
- **0 hole violations**.

Their remaining findings are silkscreen/reference-field collisions plus expected unrouted connections. Those are not functional-placement blockers and will be cleaned after the major blocks are established.

The only four remaining `shorting_items` findings are still the temporary J8-versus-unplaced-J6 pile overlap.

Therefore the complete **12V barrel / automotive front end is NATIVE GREEN / FROZEN for placement**.

## PCB placement batch 4 — source-priority PowerPath core

Board commit:

```text
601790c  Place source-priority PowerPath core
```

Rotation guard:

```text
6606a00  Guard rotated source-priority MOSFET placements
```

Placed only the LTC4418 high-current/controller core:

- U4 -> (104.5, 52.25), 0 deg;
- U5 -> (104.5, 76.25), 0 deg;
- Q2 -> (113, 48), 180 deg;
- Q1 -> (121, 48), 0 deg;
- Q4 -> (113, 56.5), 180 deg;
- Q3 -> (121, 56.5), 0 deg;
- Q5 -> (113, 72), 180 deg;
- Q6 -> (121, 72), 0 deg;
- Q7 -> (113, 80.5), 180 deg;
- Q8 -> (121, 80.5), 0 deg.

Pairing/layout intent:

- U4 channel 1: Q1/Q2 = BARREL_PROT -> EXT_CHARGE_IN;
- U4 channel 2: Q3/Q4 = PD_PWR -> EXT_CHARGE_IN;
- U5 channel 1: Q5/Q6 = EXT_CHARGE_IN -> SYS_IN;
- U5 channel 2: Q7/Q8 = AUX_PWR -> SYS_IN.

For each back-to-back pair the two source sides face inward, creating a compact shared VS node; the input/output drain copper faces outward. The two U4 channels share an EXT_CHARGE_IN output side, then U5 takes that rail onward toward SYS_IN. This follows the LTC4418 layout priorities: short/wide high-current paths and local OV/UV/controller wiring.

No routing was added. No source-priority divider/timing passives were moved yet.

Q2/Q4/Q5/Q7 are intentionally rotated 180 deg and are now included in the absolute-pad-angle regression guard.

Batch 4 is **SOURCE-PLACED / NATIVE RETEST REQUIRED**.


### Batch-4 first native validation — core clean, zone conflict corrected

The first native KiCad validation of the source-priority PowerPath core returned:

- 224 total footprints / 220 non-scaffold;
- no page-07/page-07A leakage;
- J16 center-positive guard passed;
- rotated-placement absolute-pad-angle guard passed.

The Q1-Q8 / U4-U5 core itself had no internal short, clearance or courtyard violations. However, the lower half of the block had been placed into the still-unplaced service/storage pile:

- U5 overlapped J5/J6;
- Q5/Q6 overlapped J14;
- Q7/Q8 overlapped J13, including the microSD keepout.

These were placement-zone conflicts, not footprint defects and not reasons to move the service/storage parts prematurely.

Correction:

```text
67a7e3c  Shift PowerPath core clear of service pile
```

The complete PowerPath core was translated upward 20mm as a rigid group while preserving every internal spacing and rotation:

- U4 -> (104.5, 32.25);
- Q2/Q1 -> (113/121, 28);
- Q4/Q3 -> (113/121, 36.5);
- U5 -> (104.5, 56.25);
- Q5/Q6 -> (113/121, 52);
- Q7/Q8 -> (113/121, 60.5).

This keeps the U4 side near the rear BARREL/PD sources, keeps the internal back-to-back FET geometry unchanged, and clears J5/J6/J13/J14 without touching those still-unplaced service parts.

Batch 4 remains **SOURCE-CORRECTED / NATIVE RETEST REQUIRED**. Do not place U4/U5 divider/timing passives until the shifted core passes native KiCad validation.


### Batch-4 corrected native validation — GREEN

Returned KiCad 10.0.8 validation after shifting the PowerPath core upward confirms the zone correction worked.

Structural guards:
- 224 total footprints / 220 non-scaffold;
- no page-07/page-07A leakage;
- J16 center-positive guard passed;
- rotated-placement absolute-pad-angle guard passed.

Native DRC:
- total violations improved from **312 -> 298**;
- `shorting_items` remains **4**, all four still the known J8-vs-still-piled-J6 overlap;
- Q1-Q8 and U4/U5 now report **only unconnected-item entries**;
- Q1-Q8/U4/U5 have **0** short, clearance, courtyard, hole or keepout violations;
- the previous J5/J6/J13/J14 zone conflicts are gone.

Therefore the source-priority high-current/controller core is **NATIVE GREEN / FROZEN for placement**.

## PCB placement batch 5 — LTC4418 local threshold/timing networks

Board commit:

```text
c8e4331  Place LTC4418 local threshold networks
```

Placed the complete U4/U5 local divider/timing/INTVCC support set:

U4:
- R14/R15/R16 = BARREL_PROT UV1/OV1 divider row at y=28.5;
- R17/R18/R19 = PD_PWR UV2/OV2 divider row at y=34.0;
- C8 = U4 TMR capacitor at (100.5, 26.0);
- C9 = U4 INTVCC bypass at (108.5, 34.2).

U5:
- R20/R21/R22 = EXT_CHARGE_IN UV1/OV1 divider row at y=52.5;
- R23/R24/R25 = AUX_PWR UV2/OV2 divider row at y=58.0;
- C10 = U5 TMR capacitor at (100.5, 50.0);
- C11 = U5 INTVCC bypass at (108.5, 58.2).

All 16 parts remain at 0 deg rotation, so no additional absolute-pad-angle guard is required.

Source-level post-commit audit confirms every moved passive retained its original net assignments and the two three-resistor chains remain electrically ordered input -> UV -> OV -> GND.

No routing was added and no other block was moved.

Batch 5 is **SOURCE-PLACED / NATIVE RETEST REQUIRED**.
