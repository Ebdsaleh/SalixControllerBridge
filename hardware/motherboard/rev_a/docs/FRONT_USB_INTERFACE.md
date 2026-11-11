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
