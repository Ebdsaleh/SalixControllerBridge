# Front USB Daughterboard Interface — Rev A

Pin 10 is now BOARD_ENABLE_N, active low.

The active-low convention is deliberate: each daughterboard has a local pull-up so an unplugged, floating, uninitialized, or failed motherboard control line defaults the USB data muxes to disconnected.

Logical 20-position interface:

1  5V feed A
2  5V feed B
3  GND
4  GND
5  3V3_AUX
6  I2C SDA
7  I2C SCL
8  INT_N
9  BOARD_ID
10 BOARD_ENABLE_N
11 Bank A USB2 D-
12 Bank A USB2 D+
13 Bank A hub PRTPWR
14 Bank A hub OCS_N
15 Bank B USB2 D-
16 Bank B USB2 D+
17 Bank B hub PRTPWR
18 Bank B hub OCS_N
19 GND
20 GND

The physical connector family remains TBD; this is not the Intel/PC USB3 header pinout.


## Board-ID address straps

The daughterboard TCA9535 uses A0=BOARD_ID with A1=A2=GND.

- PRIMARY connector: BOARD_ID is strapped to GND -> TCA9535 address 0x20.
- EXTENDED connector: BOARD_ID is strapped to 3V3_AUX -> TCA9535 address 0x21.

This keeps the two otherwise-identical front boards on distinct management-I2C addresses without consuming a Pico-B GPIO.


## Motherboard management controller

Rev-A now uses a TI TCA9536DGK 4-bit I2C GPIO expander on the motherboard at fixed 7-bit address 0x41.

- P0 = PRIMARY_ENABLE_N output.
- P1 = EXTENDED_ENABLE_N output.
- P2 = PRIMARY_INT_N input.
- P3 = EXTENDED_INT_N input.

Both INT_N inputs have explicit 10k pull-ups to 3V3_AUX.

TCA9536 powers up with all ports configured as inputs. Therefore the daughterboards' existing 100k BOARD_ENABLE_N pull-ups keep USB data disconnected after reset/power-up. Pico-B must explicitly configure P0/P1 as outputs and drive LOW to enable the corresponding board.

P2/P3 remain GPIO inputs; the TCA9536 P3-as-INT special function is not used. Pico-B polls these two board-interrupt inputs over management I2C.
