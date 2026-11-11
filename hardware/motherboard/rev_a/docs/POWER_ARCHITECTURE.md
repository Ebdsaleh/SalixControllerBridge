# Power Architecture — Rev A

## 5V_MAIN

- Regulated 5V external system input.
- Budget target: 5A minimum, 6A recommended if all eight physical front receptacles may be powered/charging simultaneously.
- Exact input connector and eFuse are not frozen yet.
- TPS25947-class is a candidate only if the final current limit is within its 5.5A range; otherwise select a higher-current part.

5V_MAIN feeds both Pico VSYS inputs, both USB front-board power feeds, fan power, and the 3V3_AUX regulator.

## 3V3_AUX

Frozen regulator family: TI TLV62569P, 2A synchronous buck.

- VIN: 5V_MAIN
- L1: 2.2uH
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
