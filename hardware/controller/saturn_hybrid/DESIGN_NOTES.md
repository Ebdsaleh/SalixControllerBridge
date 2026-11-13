# Salix Saturn-Hybrid Screen Controller — parked concept

Status: **concept / feasibility only — not fabrication ready**.

This project parks the Saturn-inspired controller concept so it can be revisited after the SalixControllerBridge motherboard reaches fabrication.

## Target layout

- Original wide, softly curved shell carrying Sega-Saturn-era ergonomic character without reproducing an official Sega shell.
- Strong D-pad position at upper-left for 2D/fighting/retro use.
- Left analog stick below the D-pad and right analog stick below the face cluster.
- Four-button Salix face-action cluster using **Π left, Ω top, Φ right, Α bottom**.
- Central 2.4-inch touchscreen.
- Modern shoulder/trigger controls, stick clicks, menu buttons and dual rumble/haptics.
- Ergonomic target: **Saturn visual language with modern deep-grip comfort**, rather than a flat historical Saturn-pad profile.

## Electrical feasibility baseline

- Same electrical core as the Screen Pro concept so firmware and future PCBs can share as much as possible.
- Prototype brain: Raspberry Pi Pico 2-class module / RP2350 family.
- Wired USB-C data + 5V.
- User-owned TF034-labelled **2.4inch RPi Display**, marked **320x240 Pixels**, as baseline display.
- Display/touch is represented as shared-SPI; **the real 2x13 header must be electrically verified before fabrication**.
- Dedicated microSD for VMU images/profiles/assets.
- Digital controls use the same abstracted I2C expansion bank as the Screen Pro concept, with the same **Π / Ω / Φ / Α** primary action mapping.
- Dual analog sticks + optional analog triggers.
- Dual rumble/haptic channels.

## Dreamcast / VMU direction

The centre display is intended to become a real controller-side VMU interface: VMU save management, game/status UI and synchronization with the SalixControllerBridge Dreamcast console module over a USB HID/vendor protocol.

The controller should remain useful on PC and other consoles even when no Dreamcast/VMU functionality is active.

## Revisit checklist

Prototype grip shape first; verify comfort against the user's preferred modern controller feel; then freeze screen placement, PCB envelope and four-button Greek-symbol spacing. After that, verify the TF034 header, choose exact sticks/switches/haptics, and replace the abstract electronics blocks with production components.
