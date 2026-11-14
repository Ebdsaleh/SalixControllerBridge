# Rev-A Design Completion Checklist

Snapshot: 2026-11-14, remote `main` at `0cc0ba3`.

## How to read this

- `[x]` complete / frozen for Rev A
- `[~]` intentionally provisional or waiting on a later physical measurement
- `[ ]` still blocks the next release stage

Two finish lines are tracked separately:

1. **Design complete / quote-ready** — exact parts/mechanics, PCB layout, clean DRC, fabrication outputs and BOM are ready for a real quote / first article.
2. **Production-ready** — the manufactured first article has passed electrical, USB, thermal, transient and EMI validation and any resulting fixes are folded back into the design.

## Current snapshot

- [x] 13 logical schematic sheets render natively in KiCad 10.0.8
- [x] 18 project-local footprints export natively
- [x] ERC at **0 errors**
- [x] USB-A + USB-C per-port presence telemetry native-green
- [x] Barrel front end native-green and physically footprinted
- [x] USB-C PD input native-green
- [x] Source-priority / AUX recharge control native-green
- [x] 5V_MAIN buck schematic native-green
- [x] Front USB data/power architecture frozen
- [x] SW1/SW2 and D25-D28 exact parts/footprints plus R110-R113 LED current-limit networks are native-green; J12 remains unassigned
- [ ] No fabrication `.kicad_pcb` exists yet

Useful scale reference:

```text
264 unique schematic reference designators
219 are resistors/capacitors
13 logical schematic sheets
18 project-local footprint definitions
```

## Progress gauge

These are engineering-stage ranges, not artificial precision:

- **Electrical / schematic architecture:** ~95%
- **Exact part / footprint / mechanics definition:** ~90%
- **PCB layout / routing:** ~0-5%
- **Fabrication package:** 0%
- **Physical first-article validation:** 0%
- **Overall quote-ready hardware design:** ~55-60%
- **Overall production-ready hardware:** ~35-40%

The apparent mismatch is expected: most circuit decisions are done, but PCB layout and first-article validation are large remaining phases.

## Phase A — architecture and electrical design

- [x] Main Pico-A real-time role defined
- [x] Service Pico-B role defined
- [x] Rev-A scope frozen as 8 physical USB receptacles presenting 4 logical/concurrent controller inputs across the Primary + Extended front boards
- [x] Dual-Pico soft-linked architecture retained: Pico-A realtime/USB-host role + Pico-B service/storage/update role
- [x] Dual-bank-per-front-board USB architecture defined
- [x] One data-active A/C receptacle per bank
- [x] Inactive receptacle may remain power-only
- [x] Per-port service disable concept retained
- [x] USB-A fault telemetry
- [x] USB-C fault telemetry
- [x] USB-C attach presence via TPS25821 SINK_N
- [x] USB-A attach presence via high-impedance filtered sensing
- [x] Front-board management I2C addressing
- [x] Stage-1 source priority: BARREL_PROT > PD_PWR -> EXT_CHARGE_IN
- [x] Stage-2 source priority: EXT_CHARGE_IN > AUX_PWR -> SYS_IN
- [x] AUX recharge hardware-default OFF
- [x] 5V_MAIN 12A-capability synchronous buck architecture
- [x] Active EMI filter first-pass network
- [x] PGOOD pull-up defined
- [~] Final PGOOD receiving GPIO / firmware policy
- [~] Final F1 fuse amperage; current candidate 7.5A
- [~] Final load-shed thresholds depend on measured source/harness behaviour

## Phase B — exact components, footprints and mechanics

### Frozen / closed

- [x] Barrel jack J16 exact Kycon footprint
- [x] Barrel fuse holder F1 exact Littelfuse footprint
- [x] Barrel ideal-diode MOSFET Q9/Q10 exact PG-TDSON-8-34 footprint
- [x] LM74800-Q1 package
- [x] USB-C PD input physical parts
- [x] USB-A and USB-C receptacle footprints
- [x] USB mux exact package
- [x] Fan headers
- [x] AUX module power header
- [x] microSD / service-TFT headers
- [x] 5V_MAIN power MOSFET footprints
- [x] Buck inductors / shunt / hybrid bulk exact footprints
- [x] USB presence U80/U81 stock exact packages

### Still open

- [x] SW1 exact latching selector MPN — E-Switch LC1258EENP1RBLK
- [x] SW1 exact project footprint native-green
- [x] SW2 exact latching selector MPN — E-Switch LC1258EENP1RBLK
- [x] SW2 exact project footprint native-green
- [x] D25 exact Kingbright InGaN right-angle family/population native-green
- [x] D26 Kingbright APDA3020LVBC/D blue native-green
- [x] D27 Kingbright AlGaInP yellow/red population native-green
- [x] D28 Kingbright APDA3020LSYCK/J3-PF yellow native-green
- [x] Keep independent per-port LEDs; selected E-Switch LC1258 is non-illuminated and preserves four-port identity/status semantics
- [x] R110-R113 = 1k 1% 0603 LED current-limit networks restored and native-green
- [ ] J12 spring/pogo SWD contact geometry
- [ ] Freeze Pico-A socket / standoff / mounting height before J12
- [ ] Freeze front-panel mechanical relationship to selector actuators and LEDs
- [ ] Freeze harness wire gauge and exact crimp/contact population for high-current 5V/GND paths

## Phase C — schematic release hygiene

- [x] ERC errors = 0
- [ ] Reduce or explicitly disposition endpoint-off-grid warnings
- [ ] Reduce or explicitly disposition library-symbol-mismatch warnings
- [ ] Retain documented disposition for established USB-C PD pin-to-pin warning
- [ ] Verify every fabricated BOM line has an exact MPN or explicitly approved generic class
- [ ] Remove stale `SCHEMATIC PENDING` / `NATIVE VALIDATION PENDING` labels where the corresponding block is already frozen
- [ ] Final schematic visual-review pass on every sheet

Current warning baseline:

```text
1111 endpoint_off_grid
 251 lib_symbol_mismatch
   4 isolated_pin_label
   4 lib_symbol_issues
   1 pin_to_pin
-----------------------
1371 warnings / 0 errors
```

## Phase D — create the actual PCBs

No fabrication PCB exists yet, so every item below is still open.

### Motherboard

- [ ] Create `.kicad_pcb`
- [ ] Freeze board dimensions / outline
- [ ] Freeze mounting-hole locations
- [ ] Freeze connector positions relative to enclosure
- [ ] Choose PCB stack-up / copper weight
- [ ] Place Pico-A / Pico-B / SD / TFT / module connectors
- [ ] Place source-priority and power-conversion blocks
- [ ] Place fans / airflow-sensitive parts
- [ ] Place high-current input and 5V_MAIN components
- [ ] Place USB hub / interface circuitry
- [ ] Define high-current plane/trace widths
- [ ] Define grounding / return strategy
- [ ] Route USB differential pairs
- [ ] Route management / GPIO
- [ ] Route power
- [ ] Add thermal copper / vias
- [ ] Add keepouts
- [ ] Add test points where useful
- [ ] Silkscreen / polarity / connector labels
- [ ] PCB DRC clean

### Universal front USB daughterboard

- [ ] Create/finalize physical PCB corresponding to schematic pages 07 + 07a
- [ ] Freeze physical front-panel connector spacing
- [ ] Place A/C receptacles
- [ ] Place selector switch(es)
- [ ] Place status LEDs
- [ ] Place ESD devices directly at receptacles
- [ ] Place TPS2553 / TPS25821 close to VBUS paths
- [ ] Place USB presence taps with minimal data-line stub loading
- [ ] Route USB differential pairs / return paths
- [ ] Route VBUS current paths
- [ ] Verify Primary and Extended population/BOARD_ID strategy
- [ ] PCB DRC clean

## Phase E — enclosure and harness

- [ ] Freeze enclosure internal dimensions
- [ ] Freeze front USB cutouts
- [ ] Freeze selector actuator holes/cutouts
- [ ] Freeze LED light-pipe / direct-LED approach
- [ ] Freeze rear console-module bay geometry
- [ ] Freeze fan size / locations / airflow direction
- [ ] Freeze motherboard standoffs
- [ ] Freeze front-board standoffs
- [ ] Freeze cable lengths
- [ ] Freeze high-current harness wire gauge
- [ ] Freeze USB differential twisted-pair harness construction
- [ ] Verify service-access / debug-access clearances

## Phase F — fabrication / quote package

This is the **design-complete / quote-ready gate**.

- [ ] Exact costed BOM
- [ ] PCB fabrication files
- [ ] Gerber copper layers
- [ ] Solder mask layers
- [ ] Silkscreen layers
- [ ] Board outline
- [ ] Excellon drill files
- [ ] Pick-and-place / centroid files if assembled
- [ ] Assembly drawing
- [ ] Fab notes / stack-up
- [ ] GerbView final visual inspection
- [ ] Mechanical fit review against enclosure
- [ ] Real PCBWay / assembler quote
- [ ] Australian landed-cost estimate

When all Phase A-F blockers are closed, Rev A is **design complete / quote-ready**.

## Phase G — first article bring-up

- [ ] Visual inspection / continuity before power
- [ ] Current-limited first power-up
- [ ] Validate all rails
- [ ] Validate source priority
- [ ] Validate barrel reverse/OV protection
- [ ] Validate USB-C PD negotiation
- [ ] Validate AUX admission / recharge default-off behaviour
- [ ] Validate 5V_MAIN no-load / load regulation
- [ ] Validate hard-short / current limit
- [ ] Measure buck switch-node ringing
- [ ] Measure loop/Bode response
- [ ] Thermal test at sustained load
- [ ] Load-transient test
- [ ] USB-A controller enumeration
- [ ] USB-C controller enumeration
- [ ] Multi-controller / both-bank testing
- [ ] Presence detection: empty / inactive / selected / unplug transitions
- [ ] Fault telemetry / overcurrent behaviour
- [ ] Verify service Pico / SD / TFT paths
- [ ] Verify fan control / airflow

## Phase H — signal integrity / compliance-oriented validation

- [ ] USB D+/D- eye/signal-integrity sanity at target Full-/Low-Speed use
- [ ] Harness sensitivity test
- [ ] ESD robustness sanity testing
- [ ] Conducted-noise check
- [ ] Radiated-noise check
- [ ] Buck active-EMI-filter tuning if required
- [ ] Thermal margin review at worst ambient
- [ ] Fuse selection finalized from real measurements

## Phase I — quote-driven cost-down

Only begin this after the first real quote.

- [ ] Rank BOM items by extended cost
- [ ] Rank assembly operations by cost
- [ ] Rank PCB area/layer/stack-up drivers
- [ ] Identify expensive connectors/mechanics
- [ ] Identify optional telemetry with meaningful cost impact
- [ ] Consider equivalent parts only where risk is acceptable
- [ ] Requote
- [ ] Compare against eventual AUD$150 target
- [ ] Preserve feature-complete reference design even if a reduced-cost variant is made

## Next five milestones

1. **Freeze Pico-A mechanical stack and J12 spring-contact geometry.**
2. **Create the first real motherboard/front-board PCB outlines and mounting geometry.**
3. **Place and route the boards; close DRC.**
4. **Generate the fab package and perform GerbView/fabrication review.**
5. **Obtain the first real PCBWay quote / first-article fabrication decision.**

After milestone 5, the project moves from “designing the hardware” to “building and validating the first article.”
