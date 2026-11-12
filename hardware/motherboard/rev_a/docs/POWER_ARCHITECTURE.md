# Power Architecture — Rev A

## 5V_MAIN

- Regulated 5V external system input.
- The input-current budget is **not frozen**. The current front-board policy can power both physical A/C receptacles in each logical bank.
- With four banks, nominal exposed-port demand is 5.6A at the default Type-C STD advertisement (4 x 0.9A USB-A + 4 x 0.5A Type-C), before Pico/logic/fan loads.
- If firmware enables the Type-C 1.5A advertisement on all four C ports, exposed-port demand becomes 9.6A (4 x 0.9A + 4 x 1.5A), before motherboard/fan loads.
- Therefore the older 5A/6A system-input assumption is not a valid worst-case target. Final simultaneous-port policy, PSU rating, connector rating, copper, fuse/eFuse and reverse-current strategy must be frozen together.
- TPS25947-class remains only a candidate if the final allowed system current fits its range; otherwise select a higher-current protection stage.

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
