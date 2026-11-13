# Salix Screen Pro Controller — parked concept

Status: **concept / feasibility only — not fabrication ready**.

This project parks the modern ergonomic controller concept so it can be revisited after the SalixControllerBridge motherboard reaches fabrication.

## Target layout

- Original modern ergonomic shell inspired by the comfort goals of a Switch-Pro-style pad, not a direct copy.
- Left analog stick high, D-pad lower-left.
- Four-symbol Salix action cluster upper-right: **ا up, ب down, φ left, π right**; right analog stick lower-right.
- Central 2.4-inch touchscreen.
- Dual shoulder/trigger controls, stick clicks, menu buttons and dual rumble/haptics.

Button legends: use **ا / ب / φ / π** as the Salix face-action standard. Final shell artwork should use vector outlines, not a font dependency.

## Electrical feasibility baseline

- Prototype brain: Raspberry Pi Pico 2-class module / RP2350 family.
- Wired USB-C data + 5V.
- User-owned TF034-labelled **2.4inch RPi Display**, marked **320x240 Pixels**, used as the baseline display.
- Display/touch treated as shared-SPI in this parked schematic; **exact 26-pin header mapping must be verified on the physical unit before any PCB is made**.
- Dedicated microSD is included for VMU images, controller profiles, firmware assets and diagnostics.
- Digital buttons are abstracted behind an I2C input-expander bank to preserve MCU GPIO. The four primary action inputs use the Salix legends **ا / ب / φ / π** with the default diamond mapping **ا up, ب down, φ left, π right**.
- Dual analog sticks + optional analog triggers feed MCU ADC channels.
- Two independent rumble/haptic channels are reserved.

## Dreamcast / VMU direction

The controller should not merely imitate a VMU screen. The long-term goal is for the controller to hold real VMU save images/state locally and exchange them with SalixControllerBridge over a USB HID/vendor protocol so the Dreamcast console module can expose authentic VMU behaviour to the console.

Exact VMU storage format, LCD presentation, sound support and Dreamcast protocol ownership remain future work.

## Revisit checklist

Freeze shell ergonomics and PCB envelope; measure the real TF034 module and mounting holes; reverse-map/verify its header; select exact sticks/triggers/switches; choose haptic motors/drivers; choose USB-C/ESD/power parts; decide Pico-module prototype versus bare RP2350 production board; then convert this parked block schematic into a fabrication schematic and PCB.
