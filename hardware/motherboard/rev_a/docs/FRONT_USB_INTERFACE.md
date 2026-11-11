# Front USB Daughterboard Interface — Rev A

PRIMARY and EXTENDED are intended to use the same PCB.

Each motherboard-to-front-board interface now reserves 20 logical positions:

1. 5V feed A
2. 5V feed B
3. GND
4. GND
5. 3V3_AUX
6. I2C SDA
7. I2C SCL
8. INT_N
9. BOARD_ID
10. BOARD_ENABLE
11. Bank A USB2 D-
12. Bank A USB2 D+
13. Bank A hub PRTPWR
14. Bank A hub OCS_N
15. Bank B USB2 D-
16. Bank B USB2 D+
17. Bank B hub PRTPWR
18. Bank B hub OCS_N
19. GND
20. GND

The physical connector family is not frozen. These are logical electrical positions only. Do not assume the eventual connector uses the PC USB3 20-pin pinout.

BOARD_ID lets an otherwise identical PCB distinguish PRIMARY from EXTENDED. I2C/INT lets Pico-B read selector/fault state and later manage LEDs or diagnostics without dedicating many direct GPIOs.

PRTPWR/OCS are retained per logical hub port so the USB2514B still has proper logical-port power/overcurrent semantics while the daughterboard independently keeps an inactive A/C receptacle available for charging.
