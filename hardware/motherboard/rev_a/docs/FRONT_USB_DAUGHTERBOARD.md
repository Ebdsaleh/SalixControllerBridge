# Universal Front USB Dual-Bank Daughterboard — Rev A

## Hardware selection and isolation

Each bank now uses SN74LVC2G157 as the hard-isolation selector companion to TS3USB221A.

Service jumpers are active-low disable inputs implemented as active-high RUN nets:

- OPEN jumper: 10k pull-up makes RUN=1.
- SHORT jumper: shunts RUN to GND, making RUN=0.
- USB-A RUN drives TPS2553 EN directly.
- USB-C RUN drives TPS25821 EN directly.

The latching A/C selector also drives SN74LVC2G157 SEL. Input A is the A-port RUN state; input B is the C-port RUN state. The complementary Y_N output drives TS3USB221A OE.

Hub PRTPWR is active-high. A SN74LVC2G08 per bank gates PRTPWR with each physical RUN line, so both physical A/C receptacles are powered whenever the logical hub port is ON, subject to their individual service-disable jumpers. Only the mechanically selected receptacle receives USB data.

BOARD_ENABLE_N is active-low and fail-safe pulled high on the daughterboard. SN74LVC2G157 high strobe forces Y=0 and Y_N=1, so TS3USB221A disconnects data while the board is not enabled.

Result:

- Board enabled + selected port RUN=1 => TS3USB OE=0 => data connected.
- Selected port jumper short => selected RUN=0 => TS3USB OE=1 => data disconnected.
- BOARD_ENABLE_N high => TS3USB OE=1 regardless of selector/jumpers.
- Unselected port remains available for charge-only use while the logical hub port is ON.
- If the hub powers the logical port OFF, both physical receptacles in that bank lose VBUS, matching USB hub power-control semantics.

## Type-C implementation

Each Type-C port uses TPS25821:

- C30/C31/C32 for Bank A and C34/C35/C36 for Bank B: 3 x Murata GRM31CR61A476KE15L, 47uF, 10V, ±10%, X5R, 1206 at IN. This exactly follows the TPS25820/21 EVM BOM and its three-capacitor input topology.
- Use `Capacitor_SMD:C_1206_3216Metric` and place the three-capacitor bank as close as possible to the corresponding TPS25821 IN/GND pins.
- 4.7uF ceramic at OUT/VBUS (<10uF).
- 100k 0.5% REF resistor.
- 100k CHG pulldown for STD advertisement by default.
- CHG remains controllable by TCA9535 after firmware explicitly configures the GPIO.
- CC1/CC2 direct to Type-C receptacle.
- FAULT_N and SINK_N monitored by TCA9535.

## USB-A implementation

Each Type-A port uses TPS2553 with a provisional 28.7k 1% RILIM target. The jumper RUN net directly drives EN. FAULT_N is monitored by TCA9535.

Each TPS2553 now has the support capacitance called out explicitly:

- C44/C45: 100nF 25V X7R 0603 local input bypass from `5V_BOARD` to GND; place immediately at the corresponding TPS2553 IN/GND pins.
- C42/C43: Panasonic EEHZL1E221XP 220uF 25V ±20% hybrid aluminum electrolytic on the downstream VBUS net. The -20% capacitance floor is 176uF, safely above 120uF.
- C42/C43 footprint: `Capacitor_SMD:CP_Elec_6.3x7.7`; polarity is explicit, with positive to VBUS and negative to GND.

## TCA9535 map

- P00: Bank A selector
- P01: Bank B selector
- P02: Bank A USB-A FAULT_N
- P03: Bank A USB-C FAULT_N
- P04: Bank B USB-A FAULT_N
- P05: Bank B USB-C FAULT_N
- P06: Bank A USB-C SINK_N
- P07: Bank B USB-C SINK_N
- P10: Bank A USB-A LED
- P11: Bank A USB-C LED
- P12: Bank B USB-A LED
- P13: Bank B USB-C LED
- P14: Bank A selected RUN state
- P15: Bank B selected RUN state
- P16: Bank A Type-C CHG policy
- P17: Bank B Type-C CHG policy

A0=BOARD_ID; A1=A2=0. Central management-I2C pull-ups belong on the motherboard.

## Hub overcurrent handling

Each physical power controller keeps its own FAULT_N signal for Pico-B diagnostics. Four 10k pull-ups define those open-drain lines. A third SN74LVC2G08 combines the two fault signals per bank as active-low OCS_N: the hub sees OCS_N low if either the A or C receptacle faults. Type-C SINK_N and the TCA9535 INT_N also receive explicit 10k pull-ups because TCA9535 GPIOs do not provide internal pull-ups.

## Still deliberately open

- Exact latching push-push SPDT switch manufacturer/footprint.
- Exact mechanically robust USB-A and USB-C receptacle manufacturer/footprints.
- Final LED colors.


## USB shield treatment

All four USB-A/USB-C connector shield pins join a local `USB_SHIELD` copper/flood on the front daughterboard.

Default Rev-A bonding from `USB_SHIELD` to digital `GND`:
- 330 ohm resistor.
- 100nF capacitor in parallel.
- optional 0 ohm DNP footprint in parallel for EMC/ESD tuning or direct-bond experiments.

This follows Microchip hub guidance that recommends an RC shield-ground treatment while retaining the option for direct grounding. Place the shield-to-ground network near the connector/shield region and use low-inductance connections during PCB layout.
