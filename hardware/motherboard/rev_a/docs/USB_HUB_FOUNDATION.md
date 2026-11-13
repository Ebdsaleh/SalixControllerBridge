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
- U1 pin 28 (`SUSP_IND/LOCAL_PWR/NON_REM0`) is intentionally left unconnected in Rev A. `CFG_SEL[1:0]=01` selects SMBus configuration, which disables the hardware strap options, so `NON_REM0` is not sampled as a configuration strap.
- Pico-B hub configuration must explicitly use fixed self-powered operation: `CONFIG_BYTE_1.SELF_BUS_PWR=1`, `CONFIG_BYTE_2.DYNAMIC=0`, and `NR_DEVICE=0x00` for the four removable front-panel ports. With dynamic power switching disabled, `LOCAL_PWR` is not required; Rev A also does not use the optional `SUSP_IND` status LED, so pin 28 has no electrical job and the KiCad no-connect marker is intentional.
- U1 pins 25 and 28 are modeled as bidirectional in the custom symbol because both are sampled as inputs during configuration/reset in some modes and can act as status outputs afterward.

## Hub support network

- RBIAS: 12.0kΩ ±1% to GND.
- Reference clock: CTS 445I25A24M00000, 24.000MHz, 10pF load, ±20ppm tolerance, ±50ppm stability, 40Ω ESR, -40°C to +85°C, two-pad 5.0x3.2mm SMD.
- Y1 footprint: `Crystal:Crystal_SMD_5032-2Pin_5.0x3.2mm`.
- C62/C63: Yageo CC0603JRNPO9BN180, 18pF ±5%, 50V, C0G/NP0, 0603.
- Load check: with equal 18pF physical caps and approximately 1-2pF stray capacitance per side, Microchip's load relation gives about 9.5-10pF effective load, matching Y1's 10pF CL. Keep crystal traces short/symmetric and verify oscillation frequency/stability on hardware.
- VDDA33: one 100nF at each of four power pins plus shared 1uF bulk.
- VDD33: one 100nF at each of two power pins.
- CRFILT: 100nF low-ESR to GND. Optional parallel tuning pad is DNP by default.
- PLLFILT: 100nF low-ESR to GND. Optional parallel tuning pad is DNP by default.
- CRFILT and PLLFILT are separate networks and must never be tied together. Keep each fitted filter capacitance at or below 0.1uF.
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

- Exact reset supervisor part, only if measured power sequencing requires one.
- Exact J7/J8 keyed locking connector family.
- Final PCB placement/routing constraints and USB differential-pair tuning.

## Capability boundary

Front USB-A/USB-C receptacles may use mechanically 5Gbps-capable connector parts. Rev A does not route SuperSpeed lanes. Controller traffic reaches Pico-A through a Full-/Low-Speed PIO host root.
