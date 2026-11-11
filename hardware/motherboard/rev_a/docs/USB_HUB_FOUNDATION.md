# USB Hub Foundation — Rev A

## Frozen hub choice

- Microchip USB2514B/M2-class 4-port USB 2.0 hub, preferred 36-pin SQFN family.
- One upstream USB2 pair connects to Pico-A's PIO-USB host root.
- Pico-A GP16 = hub upstream D+; GP17 = hub upstream D−.
- 22Ω series resistors remain close to Pico-A; explicit 15k host pulldowns are provided on D+ and D−.
- Important capability boundary: the USB2514B itself is Hi-Speed capable, but the Rev-A Pico-PIO-USB host root is Full-/Low-Speed. Do not claim a 480Mbps end-to-end host path.

## Downstream deterministic mapping

- Hub DN1 → PRIMARY-1
- Hub DN2 → PRIMARY-2
- Hub DN3 → EXTENDED-3
- Hub DN4 → EXTENDED-4

PRIMARY and EXTENDED each use one dual-bank motherboard interface carrying two USB2 channels. Each logical hub PRTPWR output gates both physical A/C VBUS paths in that bank through hardware AND logic; only the mechanically selected receptacle owns USB data. Either physical FAULT_N can assert the logical bank OCS_N while Pico-B still sees individual fault status.

## Configuration and supervision

- Hub configuration is via Pico-B management I²C / SMBus.
- CFG_SEL0/SCL is pulled high and CFG_SEL1/HS_IND is pulled low, selecting MCU/SoC configuration mode.
- Pico-B GP22 is dedicated to USB2514B RESET_N.
- RESET_N has 10k pull-up to 3V3_AUX and 1uF to GND for power-up delay; Pico-B may assert reset low.
- VBUS_DET uses a 100k/100k divider from 5V_MAIN.
- The bridge is self-powered; the internal Pico-A PIO root has no separate upstream connector VBUS source.

## Hub support network

- RBIAS: 12.0kΩ ±1% to GND.
- Reference clock: 24.000MHz, ±350ppm or better.
- Crystal load capacitors remain value-TBD until the exact crystal and its CL are selected.
- VDDA33: one 100nF at each of four power pins plus shared 1uF bulk.
- VDD33: one 100nF at each of two power pins.
- CRFILT: 10nF + 100nF low-ESR to GND.
- PLLFILT: 10nF + 100nF low-ESR to GND.
- CRFILT and PLLFILT are separate networks and must never be tied together.
- TEST → GND.
- Exposed VSS pad → solid ground plane with multiple vias.

## Cross-sheet connectivity

Shared motherboard signals are KiCad global nets:
- 5V_MAIN
- 3V3_AUX
- GND
- MGMT_I2C_SDA / MGMT_I2C_SCL
- HUB_RESET_N
- PICO_A_GP16_USB_DP / PICO_A_GP17_USB_DM

## Still deliberately open

- Exact 24MHz crystal manufacturer/package and calculated load-cap values.
- Exact reset supervisor part, only if measured power sequencing requires one.
- Exact J7/J8 keyed locking connector family.
- Final PCB placement/routing constraints and USB differential-pair tuning.

## Capability boundary

Front USB-A/USB-C receptacles may use mechanically 5Gbps-capable connector parts. Rev A does not route SuperSpeed lanes. Controller traffic reaches Pico-A through a Full-/Low-Speed PIO host root.
