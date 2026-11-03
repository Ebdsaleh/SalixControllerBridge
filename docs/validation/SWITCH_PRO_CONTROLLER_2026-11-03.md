# Nintendo Switch Pro Controller Calibration Validation — 2026-11-03

## Status

```text
[PASS PHYSICAL / USER ACCEPTED] Switch Pro controller calibration
[PASS PHYSICAL] MEDIUM/base analog speed = 8.0
[PASS PHYSICAL] Gnat Attack stage 1 completed with minimal trouble
[PASS] calibrated hardware profile saved and applied
[PENDING ONE FINAL RUNTIME CHECK] exact saved 0.1584786394 deadzone loaded by bridge
```

The distinction in the final line is intentional.

The user accepted the new controller calibration and reported materially better
left-stick control. The saved hardware profile contains the measured/accepted
SNES mouse-emulation calibration, including:

```text
axis_pair = [0, 1]
base_analog_speed = 8.0
deadzone = 0.15847863938809773
measured_recommended_deadzone = 0.15847863938809773
```

However, the gameplay log supplied immediately after acceptance shows the
runtime session launched with the legacy/fallback:

```text
analog max=8
D-pad speed=4
deadzone=0.180
```

and does not show a hardware profile/default-controller load line.

Therefore the accepted calibration is locked in as the user's preferred Switch
Pro profile, but the exact saved deadzone must not be falsely described as
physically runtime-validated until one bridge launch explicitly/default-loads
the saved hardware profile.

## Calibration result

Primary directional pair:

```text
axis 0 / axis 1
```

Axis 0 exposed the value of the post-exercise return-to-center phase:

```text
initial_center                  -0.01849365234375
return_center                   +0.024322509765625
center_shift                    0.042816162109375
normalized_resting_excursion    0.079130651078913
recommended_deadzone            0.15847863938809773
```

Axis 1 was substantially tighter:

```text
initial_center                  +0.029052734375
return_center                   +0.03851318359375
center_shift                    0.00946044921875
normalized_resting_excursion    0.014961496149614962
recommended_deadzone            0.05
```

The pair uses the larger measured requirement:

```text
0.15847863938809773
```

This is expected because one shared paired deadzone must cover the less stable
axis.

## User acceptance

The user reported that the new calibration:

- felt substantially more accurate on the left stick;
- felt calibrated to their personal preference;
- allowed completion of the first Gnat Attack stage with minimal trouble.

This is sufficient to mark the calibration itself as physically accepted by the
user.

## Non-centered axes

Axes 4 and 5 still illustrate a generic-calibration limitation:

```text
initial center = 0
return center  = -1
```

They are not part of the active SNES mouse-emulation axis pair and therefore do
not affect this accepted Switch Pro profile.

Future generic controller calibration should classify axis semantics so
centered thumbsticks and one-sided trigger-style axes are not evaluated with the
same neutral model.

## Final exact-profile runtime check

Before describing the saved 0.1584786394 value as physically validated in the
runtime bridge, set the Nintendo Switch Pro profile as the default controller
(or pass it explicitly) and launch:

```bat
py src\pc_host\bridge.py COM3 mouse_emu
```

Expected startup should identify the hardware profile/default controller and
report a deadzone of approximately:

```text
0.158479
```

The current acceptance remains valid regardless: the profile is saved and
accepted; this final check is only to verify that runtime profile selection is
using the saved values rather than the legacy fallback.
