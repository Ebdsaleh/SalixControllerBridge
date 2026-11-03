# Controller Calibration Milestone — 2026-11-03

## Status

```text
[COMPLETE] Generic controller calibration milestone

[PASS / USER ACCEPTED] Nintendo Switch Pro Controller
[PASS / USER ACCEPTED] MAYFLASH Arcade Stick F300
[PASS / USER ACCEPTED] GameSir C2 Universal Arcade Fightstick
```

This milestone establishes reusable source calibration for both analog gamepads
and arcade/fightstick-style controllers before the project moves into generic
button mapping, layout presets, game profiles, and additional console modules.

## Nintendo Switch Pro Controller

Accepted SNES mouse-emulation preference:

```text
axis_pair = [0, 1]
base_analog_speed = 8.0
deadzone = 0.15847863938809773
```

The post-exercise return-to-center phase exposed real axis-0 center movement
that the original initial-neutral-only calibration could not see.

The user reported substantially improved left-stick accuracy and completed the
first Gnat Attack stage with minimal trouble.

See:

```text
docs/validation/SWITCH_PRO_CONTROLLER_2026-11-03.md
```

## MAYFLASH Arcade Stick F300

Profile:

```text
profile_name = MAYFLASH Arcade Stick F300
device label = Mayflash F300
SDL name = Controller (MAYFLASH Arcade Fightstick F300)
GUID = 0300383c790000003218000000007200
buttons = 11
hats = 1
axes = 6
```

Accepted SNES mouse-emulation preference:

```text
axis_pair = [0, 1]
base_analog_speed = 7.0
deadzone = 0.05
measured_recommended_deadzone = 0.05
```

Primary axes were effectively ideal:

```text
axis 0:
  initial_center = +0.00390625
  return_center  = +0.00390625
  center_shift   = 0
  resting_excursion = 0
  minimum = -1
  maximum ~= +1

axis 1:
  initial_center = -0.003936767578125
  return_center  = -0.003936767578125
  center_shift   = 0
  resting_excursion = 0
  minimum = -1
  maximum ~= +1
```

This is expected for an arcade lever represented as stable directional axes.

## GameSir C2 Universal Arcade Fightstick

Profile:

```text
profile_name = GameSir C2 Universal Arcade Fightstick
device label = GamerSir C2
SDL name = Xbox 360 Controller
GUID = 030003f05e0400008e02000000007200
buttons = 11
hats = 1
axes = 6
```

Note: the saved device label currently says `GamerSir C2`. This is cosmetic
profile metadata only; the intended product name is GameSir C2.

Accepted SNES mouse-emulation preference:

```text
axis_pair = [0, 1]
base_analog_speed = 7.0
deadzone = 0.05
measured_recommended_deadzone = 0.05
```

Primary axes were also effectively ideal:

```text
axis 0:
  initial_center = +0.00390625
  return_center  = +0.00390625
  center_shift   = 0
  resting_excursion = 0
  minimum = -1
  maximum ~= +1

axis 1:
  initial_center = -0.003936767578125
  return_center  = -0.003936767578125
  center_shift   = 0
  resting_excursion = 0
  minimum = -1
  maximum ~= +1
```

## Cross-device result

The three accepted devices demonstrate the intended calibration architecture:

```text
physical controller
    -> measured source baseline
    -> normalized directional axes
    -> measured/accepted deadzone
    -> accepted MEDIUM/base analog speed
    -> SNES mouse-emulation module
```

Observed device preferences:

```text
Switch Pro
  base speed 8.0
  deadzone ~0.158479
  meaningful mechanical return-to-center variation

MAYFLASH F300
  base speed 7.0
  deadzone 0.05
  zero measured return-center wander on primary pair

GameSir C2
  base speed 7.0
  deadzone 0.05
  zero measured return-center wander on primary pair
```

This validates that profile values are device-specific rather than arbitrary
global defaults.

## Axis-semantics follow-up

The generic worker still treats every Pygame axis with a centered-axis
statistical model.

The accepted profiles show several categories:

```text
centered bidirectional directional axes
inactive/constant axes
one-sided axes resting at -1
other controller-specific full-range axes
```

This does not block the completed milestone because the active SNES
mouse-emulation pair is explicitly [0, 1] on all three accepted devices.

Before broader controller mapping and future console modules depend on all axes,
add axis classification/semantics so the application can distinguish:

```text
centered stick/lever axes
one-sided trigger axes
inactive axes
hat/digital directions
```

## Next milestone

Controller calibration is no longer the priority.

The next major direction is the configuration/mapping architecture already
recorded in the private handoff:

```text
HardwareProfile
    -> physical device facts and calibration

ConsoleModule
    -> console capabilities/default interpretation

LayoutPreset
    -> reusable physical layouts such as HORI Fighting Stick SS

GameProfile
    -> optional per-game association/overrides

RuntimeSession
    -> active devices/mappings for final-box touchscreen display
```

The desktop Hardware Profiler should evolve into the broader Salix Controller
Bridge configuration application rather than remain calibration-only.
