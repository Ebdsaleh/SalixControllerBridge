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


## Generic mouse bridge / unified launcher refactor

The validated SNES Mouse path is no longer implemented as an isolated input
pipeline.

New architecture:

```text
bridge.py
  |
  +-- default/pad mode
  |
  +-- mouse_emu / mouse-emu
          |
          v
      mouse_bridge.py
          |
          +-- MouseState(dx, dy, left, right)
          +-- relative analog/D-pad movement
          +-- five-level bridge sensitivity
          +-- hot-plug/re-enumeration handling
          |
          v
      SNES Mouse output personality
          |
          +-- 32-bit logical report
          +-- physical-wire conversion
          +-- AA 56 serial framing
```

Primary command:

```bat
py src\pc_host\bridge.py COM3 mouse_emu
```

Equivalent alias:

```bat
py src\pc_host\bridge.py COM3 mouse-emu
```

Auto-detect form:

```bat
py src\pc_host\bridge.py mouse_emu
```

Normal controller mode remains backward compatible:

```bat
py src\pc_host\bridge.py COM3
```

The old direct launcher also remains valid:

```bat
py src\pc_host\snes_mouse_bridge.py COM3
```

but `snes_mouse_bridge.py` is now only a compatibility wrapper around
`mouse_bridge.py`.

This creates the intended separation for future work:

```text
input source
    -> MouseState
    -> console mouse output personality
```

Future USB/Bluetooth mouse sources can therefore produce the same `MouseState`
without knowing anything about the SNES report format, and future Saturn or
Dreamcast mouse outputs can consume the same state without duplicating the
input/sensitivity engine.


## Physical PC/USB mouse source

The generic mouse bridge now has a second input source.

Commands:

```bat
py src\pc_host\bridge.py COM3 mouse
```

or, with Pico auto-detection:

```bat
py src\pc_host\bridge.py mouse
```

Data flow:

```text
physical PC mouse
    -> PhysicalMouseSource
    -> MouseState(dx, dy, left, right)
    -> SNES Mouse output personality
    -> Pico
    -> real SNES
```

This is deliberately distinct from:

```text
controller
    -> gamepad-to-mouse translation
    -> MouseState
    -> SNES Mouse output
```

The normalized `MouseState` is shared by both.

Physical mouse details:

- SDL/Pygame relative mouse capture is used.
- a small capture window is created;
- the cursor is hidden and grabbed so relative movement continues at desktop
  edges;
- ESC releases capture and exits;
- left physical mouse button -> MouseLeft;
- right physical mouse button -> MouseRight;
- relative deltas are accumulated between 60 Hz output reports;
- button presses are latched until the next report so very short clicks are not
  lost;
- outgoing displacement is clamped to the SNES Mouse sign/magnitude range
  (-127..+127).

The first PC-host implementation sees the operating system's active mouse
stream. It does not yet bind one specific USB HID by VID/PID. Per-device USB
selection belongs to the future standalone USB-host/input-slot layer.

No Pico firmware change is required because the existing SNES Mouse output
personality already consumes normalized relative X/Y and button state.


## Razer Naga Pro physical-mouse validation and transient serial timeout

Physical mouse mode was validated with a Razer Naga Pro, model
`RZ01-03420100`, using the two-button side attachment.

Observed:

- physical mouse motion successfully controlled Mario Paint;
- physical left click successfully produced MouseLeft;
- physical right click successfully produced MouseRight;
- high DPI produced very large relative deltas and correspondingly very fast
  Mario Paint cursor movement;
- the run eventually terminated on a host serial write timeout.

The console log ended with:

```text
Serial write timed out. Releasing physical mouse bridge.
Physical mouse bridge stopped.
Bridge stopped.
```

The DPI controls are not interpreted as exit controls by Salix. Physical-mouse
mode exits only on capture-window close, ESC, Ctrl+C, or an unrecovered serial
failure. Therefore the DPI-button press may have coincided with the failure, but
the direct software cause of shutdown was the COM3 serial timeout.

### Serial robustness correction

Physical-mouse mode now:

- uses a 250 ms serial write timeout instead of 100 ms;
- retries a timed-out latest mouse state up to three attempts;
- clears stale queued output before retrying;
- preserves latest-state-wins semantics so stale mouse movement is not replayed
  after a transient USB/CDC stall;
- only terminates if the serial timeout persists through the retry budget.

Expected transient diagnostic:

```text
Transient serial write timeout; clearing stale output and retrying latest mouse state (1/2)...
```

The gamepad `mouse_emu` path is unchanged by this correction.

### Current Razer button policy

The current generic physical-mouse source consumes:

```text
left button  -> MouseLeft
right button -> MouseRight
```

The Naga Pro side buttons and hardware DPI buttons are intentionally not mapped
to Salix functions yet. Hardware DPI changes can therefore alter the raw
relative deltas reaching the bridge, but they do not directly trigger a bridge
mode change or shutdown.


## Physical-mouse restart produced host traffic but no SNES response

After the serial-timeout recovery batch, a new physical test showed:

- `bridge.py COM3 mouse` started normally;
- the PC continued generating valid `AA 56` SNES Mouse frames;
- MouseLeft/MouseRight reports were present in the host log;
- no serial timeout occurred during the run;
- the real SNES/Mario Paint did not respond to the mouse at all.

The host therefore still had valid input and packet generation. The failure was
downstream of host report construction.

### Pico mode-state observation

The Pico only reinitializes the mouse PIO state machine when the incoming frame
kind changes from PAD to MOUSE.

If a previous host session ends while the Pico already believes it is in
`MODE_MOUSE`, a subsequent host process can send more `AA 56` frames without
forcing the mouse PIO state machine through a fresh initialization boundary.

This can leave a restart dependent on whatever PIO phase/state the previous
session left behind.

### Physical-mouse startup re-arm

Physical-mouse mode now explicitly forces:

```text
PAD neutral
    ->
MOUSE neutral
    ->
live physical-mouse reports
```

on every launch.

This deliberately causes the Pico to execute:

```text
MODE_MOUSE -> MODE_PAD -> MODE_MOUSE
```

and therefore re-run the known-good PIO initialization path before live mouse
traffic begins.

Startup diagnostic:

```text
Re-arming SNES Mouse output: PAD neutral -> MOUSE neutral...
```

On physical-mouse shutdown, the bridge now:

```text
mouse neutral -> pad neutral
```

so the Pico is returned to its default pad personality.

The already validated gamepad `mouse_emu` path remains on its previous
startup/shutdown behavior and was intentionally excluded from this lifecycle
change.


## Physical mouse throw clamp

A later Razer Naga Pro run confirmed the physical mouse path can produce very
large Windows/SDL deltas, including reports that hit the protocol encoder's
previous +/-127 clamp.

The SNES Mouse report is relative, not an absolute screen coordinate. The game
owns the cursor position and screen bounds.

The physical PC-mouse source now applies an authentic-ish per-report motion
envelope before producing `MouseState`:

```text
PHYSICAL_MOUSE_MAX_THROW = 28
```

The largest axis is limited to +/-28 and the other axis is scaled by the same
factor so direction is preserved.

Example:

```text
raw +127 / +54
    ->
limited +28 / +12
```

This does not clamp Mario Paint to a specific pixel coordinate. It limits the
largest relative displacement that can be injected during one 60 Hz report.

The gamepad `mouse_emu` source is unchanged.

When limiting occurs the host prints:

```text
Physical mouse throw limited: raw=+127/+54 -> +28/+12
```

Rationale:

- authentic SNES Mouse motion is normally much smaller than the full 7-bit
  sign/magnitude field;
- low-sensitivity authentic motion values above roughly 25 are difficult to
  produce;
- higher authentic sensitivity modes saturate around roughly 21/28;
- preserving the majority of normal Naga motion while suppressing extreme
  accelerated spikes is therefore closer to real hardware behavior.


## High-DPI physical mouse software gain

The Razer Naga Pro test exposed a second issue distinct from the per-report
throw spike.

Lowering the mouse's hardware DPI enough to make Mario Paint comfortable made
normal Windows pointer use unacceptably slow.

Physical mouse mode now therefore applies a source-specific software gain before
the SNES throw limit:

```text
PHYSICAL_MOUSE_GAIN = 0.50
```

Default data flow:

```text
Windows / SDL relative delta
    -> 0.50x physical-mouse gain
    -> preserve fractional residual motion
    -> +/-28 proportional throw envelope
    -> MouseState
    -> SNES Mouse
```

Fractional residuals are carried across reports so small source movements are
not discarded merely because the gain is below 1.0.

The normal command:

```bat
py src\pc_host\bridge.py COM3 mouse
```

uses the default 0.50x gain.

For tuning without changing hardware DPI:

```bat
py src\pc_host\bridge.py COM3 mouse --mouse-gain 0.35
py src\pc_host\bridge.py COM3 mouse --mouse-gain 0.75
```

Valid gain range is greater than 0 through 4.0.

This setting affects only the physical PC-mouse source. Gamepad mouse emulation
remains unchanged.


## PC-host-only nature of current physical mouse tuning

The current physical mouse path runs inside Windows through SDL/Pygame.

Its software gain is therefore a host-side compensation/normalization tool for
the PC proof environment.

The final standalone bridge will instead host the mouse directly:

```text
USB mouse
    -> Salix USB host
    -> raw HID counts
    -> source/profile normalization
    -> MouseState
    -> SNES Mouse
```

Windows pointer acceleration and desktop cursor behavior will not exist in that
final path.

Raw HID does not eliminate hardware DPI differences, however. A high-DPI mouse
still reports more raw counts for the same physical travel. Any compensation for
that belongs to the source/profile layer, not to the SNES Mouse encoder.

Accordingly:

- `--mouse-gain` is currently a PC-host/source tuning knob;
- the SNES report encoder remains unchanged;
- the +/-28 throw envelope is conceptually separate and protects the console
  personality from implausibly large one-frame movement.


## Physical mouse gain/throw validation before hardware-profiler work

A later Razer Naga Pro run physically validated the 0.50x host gain and +/-28
throw envelope on the real SNES. The user reported the motion was substantially
better.

The host startup showed:

```text
Re-arming SNES Mouse output: PAD neutral -> MOUSE neutral...
Physical mouse software gain: 0.50x (fractional motion preserved).
Physical mouse throw limit: +/-28 per report (direction preserved).
```

The diagnostic log also showed the expected pipeline:

```text
raw movement -> 0.50x scaled movement -> proportional +/-28 clamp
```

MouseLeft and MouseRight reports remained correct.

A physical recovery observation remains important: before this successful run,
the user had to copy/re-paste the current `src/pico_client/main.py` onto the
Pico again. If future host logs show valid continuous `AA 56` packets while
the real SNES remains completely silent, verify the Pico firmware/runtime state
before changing the host mouse translation.

This successful high-DPI experiment directly motivated the new hardware-profile
calibration subsystem. Fixed host defaults remain useful as safe fallbacks, but
device-specific calibration is now the intended long-term path.


## First Hardware Profiler mouse-calibration pilot

The first DearPyGui/SDL calibration pilot completed successfully with the
Razer Naga Pro Raw Input device:

```text
VID 1532
PID 008F
```

The worker recorded Windows pointer settings before calibration as:

```text
acceleration = 1
pointer speed = 10
threshold 1 = 6
threshold 2 = 10
```

and used acceleration 0 during the calibration while retaining pointer speed 10.

The pilot produced a recommended/accepted gain of approximately:

```text
0.197171x
```

but the user explicitly did NOT accept this as a finished profile calibration.

The pilot exposed two important calibration-tool issues:

1. the original 256x224 physical window made text too small to read comfortably;
2. the RIGHT throw was visibly contaminated:
   ```text
   RIGHT raw = +173 / -209, events = 4309
   LEFT  raw = -823 /  -30, events = 212
   DOWN  raw =  +53 / +474, events = 229
   UP    raw =  +47 / -626, events = 312
   ```

The RIGHT sample had more off-axis movement than primary movement and should
never have been accepted into a production calibration.

Corrections:

- render the native 256x224 SNES surface at 3x physical scale;
- place instructions/telemetry in a dedicated side panel;
- reject wrong-direction/small/excessive-off-axis throws and repeat them;
- report opposite-direction consistency warnings;
- stage successful calibration results without mutating or saving the profile;
- require explicit Apply, then explicit Save Profile.


## Mario Paint hardware-sensitivity selector can break current emulation state

During physical Razer Naga Pro testing, Mario Paint started in its own SLOW
mouse-sensitivity setting and the mouse initially worked.

When the user changed Mario Paint's mouse sensitivity through the game's own
menu, the real SNES stopped responding to MouseLeft/MouseRight until the console
was reset.

The host log continued to generate valid button reports afterward, including:

```text
MouseLeft:
report 0x0041....

MouseRight:
report 0x0081....
```

Therefore the physical Windows mouse buttons and host report encoder were still
working. The failure is downstream of host report construction.

Interpretation:

```text
Mario Paint sensitivity selector
    -> authentic SNES Mouse console-side sensitivity command
    -> latch/clock interaction with the mouse peripheral
```

That command path is still intentionally unimplemented in the current
SNES-Mouse/Pico transport. Bridge-side sensitivity must remain independent from
the SNES hardware-sensitivity bits/command until the authentic console-driven
cycle is implemented.

For current validation:

```text
DO NOT use Mario Paint's SLOW/NORMAL/FAST selector to tune Salix sensitivity.
```

Use Salix source-side sensitivity instead.

## Razer Naga Pro side-button probe

The physical mouse runtime currently samples:

```text
pygame.mouse.get_pressed(3)
```

which exposes only:

```text
left
middle
right
```

The two-button Naga Pro side plate therefore has no Salix mapping yet.

New diagnostic:

```bat
py src\pc_host\mouse_button_probe.py
```

The probe:

- does not open COM3;
- does not communicate with the Pico or SNES;
- prints Pygame MOUSEBUTTONDOWN / MOUSEBUTTONUP event.button values;
- prints MOUSEWHEEL events;
- reports the current 3/5-button Pygame pressed state when available.

Probe controls in this order:

```text
Left
Right
Middle
Side Front
Side Rear
DPI Down
DPI Up
Wheel Up
Wheel Down
```

The resulting event indices should be recorded into the Naga hardware profile
before assigning the two side buttons to Salix sensitivity down/up.
