# Universal Front USB Dual-Bank Daughterboard — Rev A

One physical PCB design serves both PRIMARY and EXTENDED front panels. Motherboard BOARD_ID sets the I2C address, while LED colors are chosen at assembly/population.

## Frozen functional architecture

- Two banks per board.
- Each bank has one USB-A receptacle and one USB-C receptacle.
- One TS3USB221A per bank selects which receptacle owns USB2 D+/D-.
- Latching push-push SPDT switch directly drives the selector. Firmware cannot accidentally select both.
- Inactive receptacle remains powered for charging.
- Each physical receptacle has a hardware service-disable jumper: OPEN=RUN, SHORT=OFF.
- Each connector gets low-capacitance USB ESD protection close to the receptacle.

## USB-C

TPS25821 is the Rev-A USB-C source-controller family:

- USB2 DFP/source-only role.
- Integrated 1.5A VBUS switch.
- VBUS only applied after valid sink attachment.
- Source-to-source is not a valid Type-C connection.
- CHG defaults low for standard-current advertisement; TCA9535 can later raise CHG to 1.5A only under an explicit power-budget policy.
- REF = 100k 0.5% to GND.
- At least 120uF close to IN; <10uF near connector VBUS/OUT.

## USB-A

TPS2553 is the Rev-A power-switch family:

- Reverse input-output voltage protection.
- Open-drain FAULT output for overcurrent, overtemperature and reverse-voltage conditions.
- RILIM target approximately 28.7k 1%, giving about 0.9A nominal current-limit target before tolerance review.
- USB-A inactive charging is safe 5V power only in this revision; BC1.2 fast-charge signatures are not promised yet.

## Management / LEDs

TCA9535 provides sixteen I/O bits over Pico-B's management I2C bus:

- P00/P01: Bank A/B selector state.
- P02..P05: four physical-port fault inputs.
- P06/P07: USB-C sink-attach inputs.
- P10..P13: four connector LEDs.
- P16/P17: Type-C CHG policy control.
- A0 driven by BOARD_ID; A1/A2 grounded. PRIMARY and EXTENDED therefore use distinct addresses without different PCBs.

LED colors remain a population decision. The current intended identity palette is Blue, Amber/Yellow, Green and Purple, with Red reserved for system faults.

## Hardware-disable rule

TS3USB221A OE is active-high disconnect. The hard-disable function must remain independent of firmware:

OE = !BOARD_ENABLE OR (!SEL & DIS_A) OR (SEL & DIS_C)

A tiny LVC logic implementation is still to be frozen. The jumpers themselves are already frozen semantically as OPEN=RUN / SHORT=OFF.
