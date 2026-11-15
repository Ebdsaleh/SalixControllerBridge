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
