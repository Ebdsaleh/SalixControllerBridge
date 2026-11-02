# SNES Mouse Emulation Bring-Up — 2026-11-02

## Goal

Prove that the existing SalixControllerBridge SNES electrical interface can present a genuine SNES Mouse personality to a physical PAL SNES before adding USB-mouse input support.

The initial input source is a Nintendo Switch Pro Controller because its left analog stick and face buttons are already calibrated in the PC bridge.

## Scope of this batch

- Existing standard-pad serial frame remains unchanged: `AA 55 <low> <high>`.
- New mouse frame: `AA 56 <wire0> <wire1> <wire2> <wire3>`.
- Pico firmware can switch between 16-bit standard-pad and 32-bit SNES Mouse PIO personalities.
- Mouse movement source:
  - left analog stick / calibrated first XY pair;
  - D-pad as a fixed-speed fallback/additional source.
- SNES B face position -> SNES Mouse left button.
- SNES A face position -> SNES Mouse right button.
- Mouse sensitivity field is fixed at level 0 for this first physical proof.
- Software-driven sensitivity cycling while Latch is high is intentionally deferred.

## Hardware

Use one already-proven SNES adapter only.

For Mario Paint, connect that adapter to **SNES controller port 1**.

Do not modify the level-shifter/perfboard wiring for this test.

## Pico update

Copy the updated:

`src/pico_client/main.py`

to the selected Pico as:

`main.py`

and reset the Pico.

## Host test

With the Nintendo Switch Pro Controller connected to Windows:

```bat
py src\pc_host\snes_mouse_bridge.py COM3
```

Replace `COM3` with the Pico attached to SNES controller port 1.

The tool can also auto-detect the Pico when only one likely Pico serial device is connected:

```bat
py src\pc_host\snes_mouse_bridge.py
```

Optional tuning:

```bat
py src\pc_host\snes_mouse_bridge.py COM3 --max-speed 6 --dpad-speed 3
```

Defaults are:

- analog deadzone: 0.18
- full-stick maximum displacement: 8
- D-pad displacement: 4

## Expected mapping

| Physical/normalized input | SNES Mouse output |
| --- | --- |
| Left stick X/Y | Relative mouse motion |
| D-pad | Relative mouse motion |
| SNES B face position | Left mouse button |
| SNES A face position | Right mouse button |

For the calibrated Nintendo Switch Pro profile, this preserves the existing canonical SNES face-position mapping rather than hard-coding raw Pygame button numbers.

## Acceptance checkpoints

1. Mario Paint boots with the adapter in controller port 1.
2. Mario Paint recognizes the bridge as a mouse rather than a standard pad.
3. Left-stick motion moves the Mario Paint cursor.
4. D-pad motion also moves the cursor.
5. SNES B-position button performs left click.
6. SNES A-position button performs right click.
7. Returning the stick to center stops cursor movement.
8. Ctrl+C releases mouse buttons/motion and stops the host bridge cleanly.

## First-run console output

The host should print a line similar to:

```text
SNES Mouse bridge streaming to COM3. Press Ctrl+C to exit.
Mapping: left stick/lever or D-pad -> mouse motion; SNES B position -> LEFT click; SNES A position -> RIGHT click.
```

State changes print the logical mouse report, the physical-wire word, and the serial packet. A neutral report is logically `0x00010000`.

## Known limitation

The authentic SNES Mouse can cycle sensitivity when the console clocks the mouse while Latch is active. This first batch reports sensitivity level 0 and does not yet emulate the sensitivity-cycle command.

If Mario Paint recognition/motion works, sensitivity cycling becomes the next protocol-accuracy refinement rather than being mixed into the first proof.


## Bring-up note: PIO ENOMEM on first paste

The first physical paste of the dual-personality Pico firmware failed during
startup with:

```text
OSError: [Errno 12] ENOMEM
```

at the state-machine initialisation step.

Cause: both the 16-bit standard-pad and 32-bit mouse PIO programs were being
loaded into the same PIO block. A PIO block has only 32 shared instruction
slots, so keeping both programs there exhausted its instruction memory.

Fix: the standard-pad personality now uses StateMachine 0 (PIO0/SM0) and the
mouse personality uses StateMachine 4 (PIO1/SM0). Only the selected personality
is active on the shared DATA pin at any time.

Physical retest should use commit `3a12dcc` or later.


## Sensitivity controls — controller-driven follow-up

After the first successful gamepad-to-SNES-Mouse bring-up, the host bridge gained
three user-selectable sensitivity states:

| State | SNES report value | Movement scale |
| --- | ---: | ---: |
| LOW | 0 | 0.5x |
| MEDIUM | 1 | 1.0x |
| HIGH | 2 | 2.0x |

The bridge starts at **MEDIUM**, preserving the movement rate used during the
first successful physical test.

Sensitivity is changed from canonical SNES control positions:

- **L shoulder** or **Y face position**: decrease one step.
- **R shoulder** or **X face position**: increase one step.

Changes are edge-triggered: holding a sensitivity button does not repeatedly
cycle through every level. The setting clamps at LOW and HIGH.

The selected value is written into the SNES Mouse sensitivity bits in every
32-bit report as well as being used to scale generated analog-stick/D-pad
displacement.

Expected console diagnostics include:

```text
Sensitivity: MEDIUM -> LOW
Sensitivity: LOW -> MEDIUM
Sensitivity: MEDIUM -> HIGH
```

and state reports include the active level and generated movement speeds.

No Pico firmware change is required for this host-side sensitivity-control
batch; the existing 32-bit mouse personality already transports the sensitivity
bits.
