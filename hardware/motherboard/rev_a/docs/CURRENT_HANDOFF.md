# SalixControllerBridge Rev-A — Current Hardware Handoff

Date: 2026-11-15

## Current phase

**Schematic phase: GREEN / FROZEN.**

**Motherboard PCB phase: FUNCTIONAL PLACEMENT IN PROGRESS — BATCH 10 CONNECTOR ANCHORS SOURCE-CORRECTED AGAIN / FINAL NATIVE RETEST REQUIRED.**

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


### Batch-5 first native validation — two INTVCC bypass collisions corrected

Returned KiCad 10.0.8 validation after placing the LTC4418 threshold/timing networks kept all structural guards green.

Native DRC:
- total violations improved from **298 -> 294**;
- the prior four J8-vs-J6 pile shorts remained;
- two new shorts were introduced by the first INTVCC bypass coordinates:
  - C9 GND pad touched Q4 EXT_CHARGE_IN drain copper;
  - C11 GND pad touched Q7 AUX_PWR drain copper.
- both also produced courtyard/solder-mask overlap findings.
- all other U4/U5 support passives were clean apart from expected unrouted/silkscreen findings.

Correction:

```text
fdae328  Correct LTC4418 INTVCC bypass placement
02060cd  Guard rotated LTC4418 INTVCC bypasses
```

C9 and C11 were moved inward and rotated 90 deg:
- C9 -> (107.6, 34.2), 90 deg;
- C11 -> (107.6, 58.2), 90 deg.

This keeps each capacitor local to the corresponding LTC4418 INTVCC pin while clearing the adjacent PowerPAK drain/courtyard. Their placed-pad absolute angles are now covered by the regression guard.

Batch 5 remains **SOURCE-CORRECTED / NATIVE RETEST REQUIRED**.


### Batch-5 corrected native validation — electrical GREEN, courtyard micro-adjustment

Returned KiCad 10.0.8 validation after the C9/C11 90-degree correction confirms the electrical collision is closed:

- structural/population/J16/rotation guards all pass;
- total DRC is **298**;
- `shorting_items` is back to **4**, and all four are still only the known J8-vs-still-piled-J6 collision;
- C9 and C11 have **no shorting or clearance violations**;
- the only remaining functional-block issue is a tiny courtyard overlap of C9 with U4 and C11 with U5.

The render also shows the source-priority block as a coherent physical zone in the upper-middle/rear section, clear of the service/storage pile.

Final source micro-adjustment:

```text
a28c18d  Clear LTC4418 bypass courtyards
```

C9 and C11 were each shifted +0.3mm in X while preserving their 90-degree rotation and net assignments:

- C9 -> (107.9, 34.2), 90 deg;
- C11 -> (107.9, 58.2), 90 deg.

This should clear the U4/U5 courtyard edge while retaining comfortable separation from the adjacent Q4/Q7 PowerPAK drain copper.

Batch 5 remains **SOURCE-CORRECTED / FINAL NATIVE RETEST REQUIRED** before the complete source-priority subsystem is frozen.


### Batch-5 final native validation — GREEN / source-priority subsystem frozen

Returned KiCad 10.0.8 validation after the final C9/C11 +0.3mm courtyard adjustment confirms the complete source-priority subsystem is clean for placement.

Structural guards:
- 224 total footprints / 220 non-scaffold;
- no page-07/page-07A leakage;
- J16 center-positive mapping passed;
- rotated-placement absolute-pad-angle guard passed.

Native DRC:
- total violations improved **298 -> 295**;
- C9 and C11 now have **0** short, clearance, courtyard or hole violations;
- Q1-Q8 and U4/U5 remain free of short/clearance/courtyard/keepout errors;
- the only four remaining `shorting_items` are still the known temporary J8-vs-still-piled-J6 overlap.

Therefore the entire **MAIN SOURCE PRIORITY / POWERPATH subsystem is NATIVE GREEN / FROZEN for placement**.

## PCB placement batch 6 — 5V_MAIN 12A buck power-stage core

Board commit:

```text
cfd4a64  Place 5V_MAIN buck power-stage core
```

Placed the high-current/switching skeleton in actual power-flow order:

- C70 bulk input hybrid -> (129, 66.5);
- L70 SYS_IN input/filter inductor -> (127.5, 76);
- C71/C72/C73/C74 BUCK_VIN ceramics -> (134/139, 74/78);
- Q70 high-side MOSFET -> (145, 77.8);
- Q71 low-side MOSFET -> (145, 86.4);
- U70 LM25149-Q1 controller -> (138.5, 82.2);
- L71 output inductor -> (155.5, 82.2);
- R70 3mR current shunt -> (162.5, 82.2);
- C90-C97 47uF 5V output bank -> two columns at x=167/172 and y=74/78/82/86.

Placement intent follows the electrical path:

```text
SYS_IN -> L70 -> BUCK_VIN/input capacitors
                    |
                    v
              Q70 / Q71 half-bridge
                    |
                 BUCK_SW
                    |
                   L71
                    |
               BUCK_ISNS_PLUS
                    |
                   R70
                    |
                 5V_MAIN
                    |
                C90-C97
```

Important geometry:
- Q70 and Q71 are vertically stacked with a deliberate courtyard gap; Q70 source/SW side faces Q71 drain/SW side;
- L71 pad 1 (BUCK_SW) faces the FET pair and pad 2 (BUCK_ISNS_PLUS) faces R70;
- R70 pad 2 (5V_MAIN) faces the output-capacitor bank;
- the four ceramic VIN capacitors sit immediately upstream of Q70;
- C70 provides bulk energy storage but is kept out of the tight switching-loop geometry;
- U70 is placed immediately left of the half-bridge for short HO/LO/SW control paths.

No component in this batch was rotated; no absolute-pad-angle update was required.

Source-level post-commit audit confirms:
- all 19 moved footprints retained their original net assignments;
- no target-target courtyard rectangles overlap;
- all target courtyards remain inside the 160x100mm working board envelope.

No routing was added. Compensation, bootstrap, VCC/VDDA, enable/FB/RT/CNFG, PGOOD and AEF parts remain unplaced.

Batch 6 is **SOURCE-PLACED / NATIVE RETEST REQUIRED** before any small-signal buck support parts move.


### Batch-6 first native validation — buck core topology good, VIN ceramic row corrected

Returned KiCad 10.0.8 validation after the first 5V_MAIN power-stage placement kept all global guards green:

- 224 total footprints / 220 non-scaffold;
- no page-07/page-07A leakage;
- J16 center-positive guard passed;
- rotated-placement absolute-pad-angle guard passed.

The raw DRC count rose because the newly placed buck core occupies the same coordinates as many still-unplaced page-11 small-signal parts and page-04 service/storage parts. Those pile collisions are not evidence that the power-stage zone itself is wrong; the right-center zone is intentionally retained because it keeps the SYS_IN handoff from the frozen source-priority stage short and avoids the permanent Pico-B socket corridor at J5/J6.

One genuine internal batch-6 defect was identified:

- C74 BUCK_VIN pad overlapped U70 GND, creating a real BUCK_VIN-to-GND short;
- C73/C74 courtyards also crowded U70.

Correction:

```text
c85956e  Clear buck VIN ceramic bank from controller
```

C71-C74 were reorganized into one horizontal ceramic row directly above Q70:

- C71 -> (136, 70.5);
- C72 -> (141, 70.5);
- C73 -> (146, 70.5);
- C74 -> (151, 70.5).

All remain at 0 degrees.

This placement is intentional:
- the ceramic bank is now immediately adjacent to the high-side switching FET region;
- C70 remains the bulk hybrid reservoir and is not forced into the high-frequency loop;
- the row is mechanically separated from U70 and Q70;
- source-level courtyard audit reports **0 target-target overlaps** among the buck power-stage footprints after the correction.

TI LM25149-Q1 layout guidance explicitly recommends minimizing the high-di/dt loop area and placing the ceramic input capacitors as close as possible to the high-side MOSFET / low-side MOSFET switching loop.

Batch 6 remains **SOURCE-CORRECTED / NATIVE RETEST REQUIRED**. The next native run should be evaluated by filtering out still-unplaced pile collisions; do not move U70 support/AEF/compensation parts until the corrected core itself is confirmed free of internal short/clearance/courtyard faults.


### Batch-6 corrected native validation — GREEN / buck power skeleton frozen

Returned KiCad 10.0.8 validation after moving C71-C74 into the corrected VIN ceramic row confirms the 5V_MAIN high-current power skeleton is internally clean.

Structural guards:
- 224 total footprints / 220 non-scaffold;
- no page-07/page-07A leakage;
- J16 center-positive guard passed;
- rotated-placement absolute-pad-angle guard passed.

Native DRC report contains **504 total violations**, but that raw number is dominated by still-unplaced page-11/page-04 pile parts occupying the same coordinates as already placed buck parts.

When filtered to the frozen buck power-stage target set:
- C70, L70, C71-C74, Q70, Q71, U70, L71, R70 and C90-C97 have **0 internal shorting violations**;
- **0 internal copper-clearance violations**;
- **0 internal courtyard / hole / solder-mask violations**;
- remaining target-target items are only expected unrouted connections and silkscreen/reference-field warnings.

Therefore the **5V_MAIN high-current buck power skeleton is NATIVE GREEN / FROZEN for placement**. Unplaced-pile collisions remain temporary until those page-11/page-04 parts are extracted into their final zones.

## PCB placement batch 7 — LM25149 controller-local support network

Initial placement commit:

```text
a8c475e  Place LM25149 controller support network
```

Rotation guard:

```text
1f2c6fa  Guard rotated LM25149 support placements
```

Source-level geometry refinement:

```text
80579be  Refine LM25149 support spacing
```

Placed only the controller-local non-AEF support set:

- R75 CNFG -> (133.0, 75.2), 180 deg;
- R74 RT -> (133.0, 77.2), 180 deg;
- C76 22pF DNP compensation HF capacitor -> (129.5, 81.0), 180 deg;
- R73 FB network -> (133.0, 81.0), 0 deg;
- C75 COMP_RC capacitor -> (129.5, 83.5), 180 deg;
- R76 compensation resistor -> (133.0, 83.5), 180 deg;
- C77 VCC bypass -> (133.0, 85.8), 180 deg;
- C78 VDDA bypass -> (133.0, 88.1), 180 deg;
- C79 bootstrap capacitor -> (139.5, 86.8), 180 deg;
- R71/R72 EN divider -> (129.5/133.0, 90.5), 0 deg;
- R78 PGOOD pull-up -> (133.0, 93.0), 0 deg.

Placement intent:
- analog/configuration and compensation components form a narrow strip immediately left of U70, separated from the SW node and Q70/Q71;
- VCC and VDDA bypass capacitors remain local to U70;
- C79 is isolated just below/right of U70 to keep the CBOOT-to-SW loop short without entering Q71's courtyard;
- EN and PGOOD support parts sit below the analog strip;
- the active EMI filter parts C81-C86 and R79-R83 remain unplaced for a separate sensitive-analog batch.

TI LM25149-Q1 guidance places CVCC, CVDDA and CBOOT locally at their associated pins and keeps sensitive small-signal circuitry away from the high-dv/dt SW region.

Eight deliberately rotated 0603 parts are added to the absolute-pad-angle regression guard:
R75, R74, C76, C75, R76, C77, C78 and C79.

The first source placement briefly overlapped R75/C76 with L70's courtyard; commit 80579be reorganized the support parts into the current narrow strip. Post-refinement source audit reports **0 courtyard-box overlaps** among the buck power skeleton and all batch-7 support footprints.

No routing was added.

Batch 7 is **SOURCE-PLACED / NATIVE RETEST REQUIRED** before the AEF network is moved.


### Batch-7 native validation — GREEN / LM25149 local support frozen

Returned KiCad 10.0.8 validation after the controller-local support placement confirms all structural guards still pass.

When the native DRC is filtered to the frozen buck power skeleton plus batch-7 support references (R71-R76, R78, C75-C79):
- **0 internal shorting violations**;
- **0 internal copper-clearance violations**;
- **0 internal courtyard / solder-mask / hole violations**;
- only expected unrouted connections and silkscreen/reference-field findings remain inside the block.

The raw board DRC count is still dominated by page-11/page-04 components that remain in the import pile and temporarily overlap already placed buck parts.

Therefore the **LM25149 controller-local support network is NATIVE GREEN / FROZEN for placement**.

## PCB placement batch 8 — LM25149 active EMI filter network

Board commit:

```text
9062958  Place LM25149 active EMI filter network
```

Placed the remaining page-11 AEF network as a quiet small-signal cluster below/left of U70 and away from Q70/Q71/L71/SW copper.

Local AEFVDDA supply pair:
- R83 BUCK_VCC -> BUCK_AEFVDDA -> (136.2, 88.8), 0 deg;
- C86 BUCK_AEFVDDA -> GND -> (139.5, 90.0), 0 deg.

Signal-flow rows:
- C81 SYS_IN -> BUCK_SEN -> (134.0, 96.0), 0 deg;
- R81 BUCK_SEN -> BUCK_INJ -> (137.5, 96.0), 0 deg;

- C84 BUCK_SEN -> AEF_COMP_MID -> (134.0, 98.5), 0 deg;
- R80 AEF_COMP_MID -> BUCK_INJ -> (137.5, 98.5), 0 deg;

- C82 SYS_IN -> AEF_DAMP_TOP -> (134.0, 101.0), 0 deg;
- R79 AEF_DAMP_TOP -> BUCK_INJ -> (137.5, 101.0), 0 deg;
- C83 AEF_DAMP_TOP -> BUCK_INJ -> (137.5, 103.5), 0 deg;

- C85 SYS_IN -> AEF_RINC_MID -> (134.0, 106.0), 0 deg;
- R82 AEF_RINC_MID -> GND -> (137.5, 106.0), 0 deg.

Placement intent:
- all AEF parts remain at 0 deg, so no new absolute-pad-angle guard entries are required;
- each two-part row is arranged so the intermediate net faces inward, minimizing local analog interconnect;
- R83/C86 are kept closer to U70 because AEFVDDA is a local controller supply;
- the SEN/INJ shaping network is kept below the controller-local support strip and physically separated from the high-dv/dt SW side;
- no routing was added.

Source-level post-placement audit reports **0 courtyard-box overlaps** among the complete buck power skeleton, controller-support network, and all batch-8 AEF footprints.

Batch 8 is **SOURCE-PLACED / NATIVE RETEST REQUIRED** before any further functional block is moved.


### Batch-8 native validation — GREEN / complete 5V_MAIN buck frozen

Returned user-side KiCad 10.0.8 validation for commit `671da22` confirms the LM25149 active-EMI-filter placement is clean inside the actual page-11 subsystem.

Structural guards remain GREEN:

- 224 total footprints / 220 non-scaffold motherboard footprints;
- no page-07/page-07A front-board leakage;
- J16 center-positive mapping verified;
- absolute-pad-angle guard verified for all rotated anchors/blocks.

Native DRC reports **475 total violations**, but the hard findings involving batch-8 AEF parts are all collisions with still-unplaced service/storage pile parts:

- C81 BUCK_SEN against C212 3V3_AUX;
- R81 BUCK_SEN against C212 GND;
- C84 clearance against J12 mechanical pad.

These are not AEF-to-AEF or AEF-to-buck faults. Within the complete page-11 buck target set there are:

- **0 internal shorting violations**;
- **0 internal copper-clearance violations**;
- **0 internal courtyard / hole / solder-mask functional faults**;
- only expected unrouted connections and silkscreen/reference-field noise remain internally.

All 42 page-11 references are now extracted from the import pile and placed:

- power skeleton: C70-C74, C90-C97, L70/L71, Q70/Q71, R70, U70;
- controller-local support: C75-C79, R71-R76, R78;
- AEF network: C81-C86, R79-R83.

Therefore the entire **5V_MAIN 12A synchronous buck subsystem is NATIVE GREEN / FROZEN for placement**.

## Handoff freshness invariant — required from this point onward

The project handoff must be updated on **every hardware work batch / pull request / push that advances placement or validation**.

Each handoff update must record, at minimum:

- current repo head / relevant commits;
- latest returned native KiCad validation result;
- which functional blocks are GREEN/FROZEN;
- which block is currently active or source-placed;
- known temporary import-pile collisions that must not be mistaken for real layout defects;
- the exact next user command/action.

Do not leave `CURRENT_HANDOFF.md` one batch behind the PCB state.

## Immediate next work after Batch 8

Continue **functional placement only; do not route yet**.

Next placement zone is:

1. Pico-A / Pico-B socket-pair mechanical geometry and their local breakout/debug access;
2. microSD and service/TFT interface;
3. USB hub + Pico-A USB interface;
4. motherboard/front-board harness connectors;
5. fan/AUX/service connectors and remaining management logic.

Before moving the Pico socket pairs, preserve the already-frozen barrel, source-priority and complete 5V_MAIN buck zones. The remaining raw DRC noise is expected to change significantly as the service/storage import pile is extracted into its final locations.


## PCB placement batch 9 — dual Pico socket / breakout geometry

Board commit:

```text
5a943e9  Place dual Pico socket and breakout geometry
```

Batch 9 moves only the removable-Pico socket/breakout rails. No routing was added and no frozen power component was moved.

Pico-A / realtime module:
- J1 socket left 1-20 -> (48.00, 46.50), 0 deg;
- J2 socket right 21-40 -> (65.78, 46.50), 0 deg;
- J3 raw breakout 1-20 -> (43.50, 46.50), 0 deg;
- J4 raw breakout 21-40 -> (70.28, 46.50), 0 deg.

Pico-B / service module:
- J5 socket left 1-20 -> (79.00, 64.00), 0 deg;
- J6 socket right 21-40 -> (96.78, 64.00), 0 deg.

Mechanical intent:
- both socket pairs use the 17.78mm Pico row spacing;
- Pico-A uses the official Raspberry Pi Pico 2 W mechanical baseline already frozen in the project;
- Pico-A's wireless antenna end faces the front/bottom side of its module zone, with the area beyond it reserved from metal/copper placement so the antenna is not boxed in by the motherboard layout;
- J3/J4 sit 4.5mm outboard from the corresponding Pico-A socket rows, keeping the raw breakout accessible without consuming the module body area;
- Pico-B is staggered lower than Pico-A so its body clears the frozen U5 threshold/support row and remains between the J7/J8 front-connector corridors rather than overlapping them.

Source-level audit after the edit confirms:
- J1-J2 spacing = exactly 17.78mm;
- J5-J6 spacing = exactly 17.78mm;
- J3/J4 remain exactly 4.5mm outboard of J1/J2;
- all six placements remain 0 degrees, so no new absolute-pad-angle guard entries are required;
- barrel, source-priority and complete 5V_MAIN buck coordinates are untouched.

Batch 9 is **SOURCE-PLACED / NATIVE RETEST REQUIRED**.

Do not move J12, J13, J14 or their local service/storage passives until this socket geometry has been returned through native KiCad validation. The current service/storage pile is expected to continue generating temporary DRC collisions until those parts are extracted.

Next user action:

```bat
git pull --ff-only && ^
git log -8 --oneline && ^
py tools\render_kicad_pcb.py --expect-populated
```

Return the fresh console output and `kicad_pcb_validation.zip`. If Batch 9 is clean, freeze the Pico socket geometry, then place J12/J13/J14 plus their local service/storage support as the next small functional batch.


### Batch-9 native validation — GREEN / dual-Pico geometry frozen

Returned KiCad 10.0.8 validation for head `cdc4828` confirms the dual-Pico socket/breakout placement is mechanically and electrically clean for placement.

Structural guards:
- 224 total footprints / 220 non-scaffold motherboard footprints;
- no page-07/page-07A front-board leakage;
- J16 center-positive mapping guard passed;
- rotated-placement absolute-pad-angle guard passed.

Native DRC:
- raw board total: **413** findings, still dominated by unrouted nets and the remaining import/service pile;
- filtering to J1-J6 finds **0 shorting violations**;
- **0 copper-clearance violations**;
- **0 courtyard / hole / keepout / solder-mask faults**;
- only expected unrouted connections plus two silkscreen-over-copper warnings involving still-piled nearby resistors.

The top/bottom native renders also show the three socket/breakout pairs separated correctly with no mechanical collision.

Therefore the complete **Pico-A / Pico-B socket and breakout geometry is NATIVE GREEN / FROZEN for placement**.

## PCB placement batch 10 — service connector anchors

Board commit:

```text
34726bc  Place service connector anchors
```

Moved only the three mechanically constrained service connectors:

- J12 Pico-A SWD JST-SH -> **(56.9, 39.5), 0 deg**;
- J13 Hirose DM3AT-SF-PEJM5 microSD -> **(149.0, 111.0), 0 deg**;
- J14 12-pin JST PH TFT/service connector -> **(173.0, 102.0), 0 deg**.

Placement intent:
- J12 sits above the Pico-A socket pair at the USB/debug end, leaving the opposite Pico 2 W antenna end unobstructed;
- J13 is placed at the lower board edge so the push-push microSD card slot is physically accessible instead of buried in the board interior;
- J14 occupies the lower-right service/UI zone, clear of the frozen buck output bank and clear of J13 while keeping the TFT/service harness out of the Pico socket corridor;
- all three remain at 0 deg, so no new absolute-pad-angle guard entry is required.

Source-level courtyard audit after the move reports:
- **0 J12/J13/J14 target-target overlaps**;
- **0 overlaps with the frozen Pico socket/breakout blocks**;
- **0 overlaps with the frozen 5V_MAIN buck power-stage anchors**;
- all three courtyards remain inside the 160 x 100 mm working board envelope.

No routing was added. No sheet-04 support passives were moved yet. The SD/TFT pull-ups, SPI series resistors, SWD series resistors and local decoupling remain in the import pile for the next small placement batch.

Batch 10 is **SOURCE-PLACED / NATIVE RETEST REQUIRED**.

### Exact next action

```bat
git pull --ff-only && ^
git log -8 --oneline && ^
py tools\render_kicad_pcb.py --expect-populated
```

Return the fresh console output and `kicad_pcb_validation.zip`.

If Batch 10 is native-clean, freeze J12/J13/J14 and place the remaining sheet-04 support network around those anchors:
- microSD pulls/decoupling;
- shared SPI series network;
- TFT logic/pull network;
- Pico-A SWD series pair;
- local 3V3_AUX / 5V_AUX decoupling.

Do not route yet and do not manually move the remaining import pile.


### Batch-10 first native validation — J12/J13 GREEN, J14 edge fault corrected

Returned KiCad 10.0.8 validation for head `e98453c` kept every global structural guard green:

- 224 total footprints / 220 non-scaffold motherboard footprints;
- no page-07/page-07A front-board leakage;
- J16 center-positive mapping guard passed;
- existing rotated-placement absolute-pad-angle guard passed.

Connector-specific native DRC:

**J12 Pico-A SWD**
- 0 shorting violations;
- 0 copper-clearance violations;
- 0 courtyard / hole / keepout / edge violations;
- only expected unrouted connections.

**J13 microSD**
- 0 shorting violations;
- 0 copper-clearance violations;
- 0 courtyard / hole / keepout / board-edge violations;
- only expected unrouted connections plus the already-known project-local library-copy warning.

**J14 TFT/service**
- no short or inter-component clearance fault;
- one real board-edge placement defect:
  - pad 10 touched the board edge at x=180.0 mm;
  - J14 silkscreen was clipped by the board edge.

This is a genuine Batch-10 placement error, not import-pile noise. J12 and J13 are therefore individually clean, but Batch 10 is not frozen until corrected J14 passes native KiCad.

Correction commits:

```text
25d4c1c  Rotate TFT service connector clear of board edge
27dde82  Guard rotated TFT service connector placement
```

Corrected J14 placement:
- J14 -> **(174.0, 104.0), 90 deg**.

The 90-degree orientation turns the long 12-pin connector body into the vertical lower-right service corridor rather than extending it through the right board edge.

Source-level post-correction geometry audit:
- J14 courtyard bbox = x **168.9 .. 179.1 mm**, y **89.4 .. 118.6 mm**;
- right-board courtyard margin = **0.9 mm**;
- bottom-board courtyard margin = **1.4 mm**;
- 0 courtyard-box overlaps with J13;
- 0 overlaps with the frozen Pico socket/breakout blocks;
- 0 overlaps with the frozen 5V_MAIN output bank / L71 / R70;
- all fourteen J14 pads/mechanical pads now carry the correct absolute **90-degree** placed-pad angle;
- `tools/render_kicad_pcb.py` now guards J14 at 90 degrees.

No routing was added and no sheet-04 support passives were moved.

Batch 10 is **SOURCE-CORRECTED / FINAL NATIVE RETEST REQUIRED**.

### Exact next action after J14 correction

```bat
git pull --ff-only && ^
git log -8 --oneline && ^
py tools\render_kicad_pcb.py --expect-populated
```

Return the fresh console output and `kicad_pcb_validation.zip`.

If the corrected J14 gate is native-clean, freeze J12/J13/J14 and place the remaining sheet-04 local support network around those anchors. Do not route yet and do not manually move the remaining import pile.


### Batch-10 second native validation — board edge fixed, H4 conflict found and corrected

Returned KiCad 10.0.8 validation for head `2b46e33` confirms the previous J14 board-edge defect is closed, and all global structural guards remain green:

- 224 total footprints / 220 non-scaffold motherboard footprints;
- no page-07/page-07A front-board leakage;
- J16 center-positive mapping guard passed;
- rotated-placement absolute-pad-angle guard passed, including J14 at 90 degrees.

Native DRC reports **373 total findings**, still dominated by unrouted nets and the untouched sheet-04 import pile.

J12 and J13 remain clean for placement.

The corrected J14 no longer touches the board edge, but native KiCad exposed a second genuine mechanical conflict:
- J14 mounting pad MP at approximately (176.9, 117.35) was only **0.0539 mm** from H4's NPTH;
- J14 and H4 courtyards overlapped;
- H4's NPTH was inside J14's courtyard.

This is a real placement blocker, not import-pile noise.

Correction:

```text
bbad511  Shift TFT service connector clear of H4
```

J14 remains rotated 90 degrees but is shifted left:

- J14 -> **(165.0, 104.0), 90 deg**.

Source-level post-correction geometry audit:
- J14 courtyard bbox = x **159.9 .. 170.1 mm**, y **89.4 .. 118.6 mm**;
- no courtyard overlap with J13;
- no courtyard overlap with H4;
- no overlap with C90-C97, L71 or R70;
- no overlap with J5/J6;
- J14 remains completely inside the board envelope;
- all J14 pads retain their guarded absolute 90-degree orientation.

No routing was added and no sheet-04 support passives were moved.

Batch 10 remains **SOURCE-CORRECTED / FINAL NATIVE RETEST REQUIRED**.

### Exact next action after H4 correction

```bat
git pull --ff-only && ^
git log -8 --oneline && ^
py tools\render_kicad_pcb.py --expect-populated
```

Return the fresh console output and `kicad_pcb_validation.zip`.

If this corrected J14 position is native-clean, freeze J12/J13/J14 and proceed immediately with the sheet-04 local support network. Do not route yet and do not manually move the remaining import pile.
