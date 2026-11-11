# Universal Front USB Dual-Bank Daughterboard — Rev A

## Hardware selection and isolation

Each bank now uses SN74LVC2G157 as the hard-isolation selector companion to TS3USB221A.

Service jumpers are active-low disable inputs implemented as active-high RUN nets:

- OPEN jumper: 10k pull-up makes RUN=1.
- SHORT jumper: shunts RUN to GND, making RUN=0.
- USB-A RUN drives TPS2553 EN directly.
- USB-C RUN drives TPS25821 EN directly.

The latching A/C selector also drives SN74LVC2G157 SEL. Input A is the A-port RUN state; input B is the C-port RUN state. The complementary Y_N output drives TS3USB221A OE.

BOARD_ENABLE_N is active-low and fail-safe pulled high on the daughterboard. SN74LVC2G157 high strobe forces Y=0 and Y_N=1, so TS3USB221A disconnects data while the board is not enabled.

Result:

- Board enabled + selected port RUN=1 => TS3USB OE=0 => data connected.
- Selected port jumper short => selected RUN=0 => TS3USB OE=1 => data disconnected.
- BOARD_ENABLE_N high => TS3USB OE=1 regardless of selector/jumpers.
- Unselected port can remain powered for charging because physical VBUS enables do not depend on selector state.

## Type-C implementation

Each Type-C port uses TPS25821:

- 3 x 47uF input bulk = 141uF at IN.
- 4.7uF ceramic at OUT/VBUS (<10uF).
- 100k 0.5% REF resistor.
- 100k CHG pulldown for STD advertisement by default.
- CHG remains controllable by TCA9535 after firmware explicitly configures the GPIO.
- CC1/CC2 direct to Type-C receptacle.
- FAULT_N and SINK_N monitored by TCA9535.

## USB-A implementation

Each Type-A port uses TPS2553 with a provisional 28.7k 1% RILIM target. The jumper RUN net directly drives EN. FAULT_N is monitored by TCA9535.

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

## Still deliberately open

- Exact latching push-push SPDT switch manufacturer/footprint.
- Exact mechanically robust USB-A and USB-C receptacle manufacturer/footprints.
- Hub PRTPWR behavior with charge-only inactive receptacles.
- Hardware selected-fault combination into HUB OCS_N.
- Final LED colors.
