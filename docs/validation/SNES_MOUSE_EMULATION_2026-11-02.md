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


## Click regression after bridge sensitivity controls

Physical testing showed the new LOW/MEDIUM/HIGH cursor-speed controls worked and
the host continued detecting both mouse-button inputs, but Mario Paint no longer
responded to MouseLeft/MouseRight after the host also began changing the SNES
Mouse on-wire speed bits.

The host log proved the controller mapping itself was still intact: left and
right click states were still being emitted by the PC bridge.

Correction:

- keep LOW/MEDIUM/HIGH as **bridge-side movement scaling** only;
- restore the exact known-good SNES Mouse first-16-bit report pattern used during
  the successful click bring-up;
- preserve B-position -> MouseLeft and A-position -> MouseRight;
- defer authentic SNES hardware-mouse sensitivity selection until its
  Latch/Clock command sequence is implemented independently.

Known-good SNES-facing second-byte values are therefore restored to:

```text
neutral     0x01
MouseLeft   0x41
MouseRight  0x81
```

Bridge sensitivity still remains:

```text
LOW     0.5x
MEDIUM  1.0x
HIGH    2.0x
```

with L/Y decreasing and R/X increasing.

This correction is PC-side only; no Pico firmware update is required.


## Five-tier bridge sensitivity refinement

Physical Mario Paint testing confirmed that:

- the restored MouseLeft/MouseRight report works;
- MEDIUM analog movement is a good default;
- the previous HIGH analog rate is useful but somewhat fast;
- the D-pad benefits from more speed in the upper sensitivity levels.

The bridge therefore now exposes five edge-triggered sensitivity states:

| State | Analog scale | Default analog max | D-pad scale | Default D-pad delta |
| --- | ---: | ---: | ---: | ---: |
| VERY LOW | 0.25x | 2 | 0.25x | 1 |
| LOW | 0.5x | 4 | 0.5x | 2 |
| MEDIUM | 1.0x | 8 | 1.0x | 4 |
| HIGH | 1.5x | 12 | 2.0x | 8 |
| VERY HIGH | 2.0x | 16 | 3.0x | 12 |

This deliberately preserves the previously validated MEDIUM rate exactly.

The old three-tier HIGH analog rate (16) becomes the new VERY HIGH analog rate.
A new HIGH analog tier (12) is inserted between MEDIUM and VERY HIGH.

The D-pad is intentionally more aggressive at the upper levels:

- HIGH = 8 per poll;
- VERY HIGH = 12 per poll.

Controls remain unchanged:

```text
L or Y -> decrease one sensitivity step
R or X -> increase one sensitivity step
```

The bridge starts at MEDIUM and clamps at VERY LOW / VERY HIGH.

The SNES-facing mouse button report remains in known-good compatibility mode:

```text
neutral     0x01
MouseLeft   0x41
MouseRight  0x81
```

This refinement is PC-side only; no Pico firmware update is required.


## Mayflash F300 Gamepad/Controller shoulder correction

Physical testing of the F300 across its USB personalities found:

- XInput/NS: shoulder sensitivity controls correct.
- PS3/DInput: shoulder sensitivity controls correct.
- Gamepad/Controller: physical RB/R1 incorrectly behaved as LB/L1 and repeatedly
  decreased bridge sensitivity.

The Gamepad/Controller profile uses GUID:

```text
0300dc99790000001c18000000000000
```

The profile table contained the misalignment directly:

```text
button 6 -> SNES L
button 7 -> SNES L   (incorrect)
```

The correction is:

```text
button 6 -> SNES L
button 7 -> SNES R
```

No SNES Mouse protocol or Pico firmware changes are involved. Face-button
clicks, X/Y lever mode, D-pad lever mode, and the five-tier bridge sensitivity
curve are unchanged.
