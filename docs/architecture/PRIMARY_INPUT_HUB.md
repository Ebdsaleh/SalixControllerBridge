# Salix Primary Input Hub

## Purpose

The first physical Salix USB input module is the two-port **Primary USB-A
Input Bank**.

The stable logical slots are:

```text
PRIMARY-1
PRIMARY-2
```

These names belong to the Salix architecture and must remain independent from
whatever transport/backend currently discovers the devices.

## Physical Primary USB-A module

Prototype Rev A contains two independently wired USB-A receptacles.

Each receptacle owns its own four-conductor harness:

```text
VBUS
D-
D+
GND
```

Do not join the two data pairs together.

### Salix USB harness convention

Canonical semantic order:

```text
Pin 1 = VBUS
Pin 2 = D-
Pin 3 = D+
Pin 4 = GND
```

Preferred colours:

```text
RED   = VBUS
WHITE = D-
GREEN = D+
BLACK = GND
```

Accepted prototype fallback when green is unavailable:

```text
YELLOW = D+
```

Red remains reserved for VBUS and black remains reserved for ground.

The current Primary USB-A bank is intentionally module-first. Future LEDs,
USB-A/USB-C selector controls, and enclosure mechanics are separate later
concerns and do not change the logical slot names.

## Standalone PIO USB host wiring decision

The accepted GREEN Pico 2 W standalone host mapping is:

```text
PRIMARY-1
  D+ -> GP16
  D- -> GP17

PRIMARY-2
  D+ -> GP18
  D- -> GP19
```

The GPIO pairs are intentionally adjacent so Pico-PIO-USB can use its
`PIO_USB_PINOUT_DPDM` convention, where D- is D+ + 1.

Power is provided by the accepted prototype **USB Power Distribution Rev A**
board:

```text
GREEN Pico VBUS / source +5 V
    -> source +5 V rail
    -> removable USB +5 V jumper
    -> switched USB +5 V rail
    -> PRIMARY USB VBUS outputs

GREEN / USB ground
    -> continuous common ground rail
    -> PRIMARY USB GND outputs
```

Rev A is the 40 x 60 mm perfboard assembly previously continuity-checked on the
bench. Its source +5 V and USB-side +5 V are intentionally separated by the
removable jumper. Ground remains continuous and unswitched. The red source LED
indicates source power; the yellow USB LED indicates the post-jumper USB rail.

Rev A is accepted for prototype bring-up. Per-port current limiting/PTC
protection remains a later hardware-hardening item and is not implied by this
acceptance.

Do **not** place the DUINTECH XC4486 level shifter in either USB D+/D- pair.
USB data is handled directly by the RP2350 GPIO/PIO path.

Pico-PIO-USB upstream recommends 22 ohm series resistors on D+ and D- for
signal-integrity improvement, but describes them as preferable rather than a
hard requirement. For the current short-wire prototype, direct GP16/GP17 data
connections are accepted for first bring-up. If enumeration is flaky or the
wiring must be lengthened, add 22-27 ohm series resistors close to the GREEN
GPIO pins before changing firmware.

The existing SNES prototype signals remain reserved and untouched:

```text
GP2 = SNES CLOCK
GP3 = SNES LATCH
GP4 = SNES DATA
```

Milestone 0.2 brings up PRIMARY-1 only. PRIMARY-2 is reserved by this mapping
but is not enabled until the one-port host path is physically proven.

### PRIMARY-1 physical validation order

The controlled bench sequence is:

1. With GREEN powered down, connect Power Distribution Rev A to GREEN VBUS/GND
   and connect only PRIMARY-1 VBUS/GND to the Primary USB board. Leave the USB
   +5 V jumper removed.
2. Power GREEN from its native micro-USB connection to ERIDU. Verify source
   power is present while the post-jumper USB rail remains isolated.
3. Insert the USB +5 V jumper and verify the PRIMARY-1 socket receives the
   expected USB supply voltage.
4. Power down again.
5. Connect PRIMARY-1 D+ directly to GP16 and D- directly to GP17 for the
   current short-wire prototype. Keep the pair as short and close together as
   practical. 22-27 ohm series resistors are recommended later for additional
   signal-integrity margin, but are not a blocker for this bring-up.
6. Power GREEN, confirm the firmware still reports
   `[PRIMARY-1] host ready ...`, then attach one known-good wired HID device.
7. Accept the path only when firmware reports HID mount information and changing
   raw report bytes.

Do not connect PRIMARY-2 during this validation.

## PC-host discovery backend

The current Windows prototype still receives controllers through SDL/Pygame.

Therefore the first backend maps:

```text
PRIMARY-1 -> Pygame controller index 0
PRIMARY-2 -> Pygame controller index 1
```

This mapping is explicitly a development adapter. It does **not** prove which
physical USB receptacle a Windows controller occupies.

Inspect the current Primary bank:

```bat
py src\pc_host\bridge.py --list-inputs
```

Example output:

```text
Salix Primary USB-A Input Bank (PC-host discovery)
------------------------------------------------
PRIMARY-1: Pygame index 0 | Nintendo Switch Pro Controller
PRIMARY-2: Pygame index 1 | Xbox 360 Controller
```

Select a slot for normal pad mode:

```bat
py src\pc_host\bridge.py COM3 --input-slot PRIMARY-1
py src\pc_host\bridge.py COM3 --input-slot PRIMARY-2
```

Select a slot for controller-to-mouse emulation:

```bat
py src\pc_host\bridge.py COM3 mouse_emu --input-slot PRIMARY-1
py src\pc_host\bridge.py COM3 mouse_emu --input-slot PRIMARY-2
```

Aliases such as `1`, `2`, `P1`, `P2`, `USB1`, and `USB2` are also
accepted.

## Backward compatibility

Existing commands are deliberately unchanged:

```bat
py src\pc_host\bridge.py COM3
py src\pc_host\bridge.py COM3 mouse_emu
py src\pc_host\bridge.py COM3 mouse
py src\pc_host\snes_mouse_bridge.py COM3
```

If `--input-slot` is omitted, controller mode preserves the historical
behavior:

```text
first Pygame controller / index 0 wins
```

Physical mouse mode is not assigned to PRIMARY-1/2 by this first controller
hub backend and rejects `--input-slot`.

## Hot-plug behavior

Legacy auto mode keeps the existing hot-plug behavior.

For an explicitly selected Primary slot, the PC-host backend captures the
selected controller identity. If SDL compacts its controller indices after a
disconnect, the bridge searches for the same identity before resuming instead
of silently stealing another different controller.

Two physically identical controllers remain inherently ambiguous in the
current Pygame backend because it cannot expose Salix's future physical socket
identity.

## Standalone target

The final standalone box must replace the temporary Pygame-index backend with
real hardware-port enumeration owned by the main Pico 2 W USB host.

The intended architecture is:

```text
Primary USB-A socket 1
    -> physical host-port identity
    -> PRIMARY-1

Primary USB-A socket 2
    -> physical host-port identity
    -> PRIMARY-2
```

Everything above the discovery backend should continue to consume the same
logical slot names.

This keeps console personalities and translation code independent from whether
the source currently comes from:

```text
Windows/Pygame
PIO USB host
native USB host/hub
Bluetooth
future USB-C selector path
```
