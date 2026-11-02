# Hardware Profiles and Calibration Utility

## Purpose

SalixControllerBridge uses one versioned hardware profile per physical input
device. The profile records the device baseline once, then stores every
compatible console/module calibration beneath that same identity.

The DearPyGui calibration utility is an application shell only. It is modeled
after SalixTorrent's desktop application style, but the bridge/profile backend
does not depend on SalixTorrent or DearPyGui.

## Architecture

```text
DearPyGui calibration utility
        |
        +-- profile editor / saved profiles
        |
        +-- launches SDL/Pygame calibration worker
                    |
                    +-- Windows Raw Input mouse baseline
                    +-- controller axis baseline
                    +-- console-sized test environment
        |
        v
versioned HardwareProfile
        |
        +-- identity
        +-- host_environment
        +-- source_calibration
        +-- consoles
              +-- snes
              |    +-- mouse
              |    +-- mouse_emu
              |    +-- pad
              +-- saturn
              |    +-- mouse
              |    +-- ...
              +-- dreamcast
                   +-- mouse
                   +-- ...
```

The runtime asks the profile only for the module required by the selected
bridge route.

## Storage

Profiles are user/application state, not repository source.

Windows default:

```text
%LOCALAPPDATA%\SalixControllerBridge\profiles\hardware\
```

Override:

```text
SALIX_CONTROLLER_BRIDGE_STATE_DIR
```

Profiles use schema version 1 and JSON.

## Mouse calibration

The current SNES mouse workflow uses a 256x224 logical test environment.

The user is instructed to keep the mouse at the normal daily-driver hardware
setting.

The utility records four comfortable full throws:

```text
RIGHT
LEFT
DOWN
UP
```

Movement is measured with Win32 Raw Input (`WM_INPUT`), not ordinary
accelerated desktop cursor movement.

The four throws produce:

- horizontal raw-count span;
- vertical raw-count span;
- independent measured axis gains;
- one scalar recommended gain using the geometric mean;
- a live console-sized test where +/- adjusts the gain by 5 percent;
- the accepted gain stored under `consoles.snes.modules.mouse`.

The scalar gain is deliberate: applying different X/Y gains to a mouse would
distort diagonal direction.

The SNES module also stores:

```text
logical environment: 256x224
report rate: 60 Hz
maximum throw: 28
```

The 256x224 environment is the current standard low-resolution SNES baseline.
The profile format permits future game/console environment variants.

## Windows pointer acceleration

The utility can temporarily disable Windows mouse acceleration while the
interactive test is running.

Before changing anything it records the current:

- threshold 1;
- threshold 2;
- acceleration state;
- pointer speed.

The original acceleration settings are restored in a `finally` path on
success, cancellation or error.

Raw Input remains the authoritative measurement. Windows acceleration affects
the ordinary pointer path, not the raw `WM_INPUT` counts. The toggle exists
to make the visible Windows-host test environment repeatable and to record the
host conditions.

## Mouse DPI

Generic HID does not reliably provide a vendor mouse's currently selected DPI.

Therefore:

- current DPI is optional user/profile metadata;
- VID/PID and Raw Input device path are captured when available;
- measured raw counts remain authoritative;
- vendor-specific DPI interrogation can be added later as an optional device
  adapter without changing the profile schema.

## Controller calibration

The controller worker currently records:

- Pygame name and GUID;
- button/hat/axis counts;
- 2.5 seconds of neutral samples;
- per-axis center;
- center noise;
- minimum/maximum range;
- negative/positive span;
- recommended deadzone;
- provisional primary directional axis pair.

For SNES mouse emulation, the primary pair and recommended deadzone are stored
under:

```text
consoles.snes.modules.mouse_emu
```

Future console modules can reuse the same generic source axis calibration.

## Runtime profile use

Physical mouse:

```bat
py src\pc_host\bridge.py COM3 mouse --hardware-profile "Razer Naga Pro"
```

The bridge reads:

```text
consoles.snes.modules.mouse
```

and applies its gain, throw limit and report rate.

Gamepad mouse emulation:

```bat
py src\pc_host\bridge.py COM3 mouse_emu --hardware-profile "Switch Pro"
```

The bridge reads:

```text
consoles.snes.modules.mouse_emu
```

and applies its axis-pair/deadzone calibration.

An explicit JSON path can be supplied instead of the profile name.

## PC host versus final Salix box

Current Windows proof:

```text
mouse/controller
    -> Windows host
    -> Raw Input / Pygame source adapter
    -> normalized state
    -> console module
```

Final standalone box:

```text
USB/Bluetooth hardware
    -> Salix USB/Bluetooth host
    -> device profile normalization
    -> normalized state
    -> console module
```

The final box does not contain Windows pointer acceleration. Hardware DPI and
device-specific response still exist, which is why device profiles remain
valuable even after Windows is removed from the path.

## Utility launch

Install/update dependencies:

```bat
py -m pip install -r requirements.txt
```

Launch:

```bat
py src\pc_host\calibration_app.py
```

The DearPyGui app launches the SDL/Pygame calibration surface as a separate
worker process so the two GUI/render loops remain isolated.


## Calibrated analog controller runtime

Controller calibration now has two layers.

Source/device normalization stores per axis:

```text
center
center_noise
minimum
maximum
negative_span
positive_span
recommended_deadzone
```

At runtime, the selected axis is recentered around its measured center and each
side is independently rescaled to the canonical -1..+1 range before the
deadzone is applied.

The SNES `mouse_emu` console module separately stores:

```text
axis_pair
deadzone
base_analog_speed
axis_calibration
```

`base_analog_speed` is the MEDIUM sensitivity speed accepted in the live
256x224 SNES analog-cursor test. The existing five-tier sensitivity curve then
scales around that calibrated device/console baseline.

This keeps reusable device geometry separate from console-personality tuning:

```text
controller raw axis
    -> measured center/range normalization
    -> measured deadzone
    -> normalized stick
    -> SNES mouse_emu base speed / sensitivity tiers
```

A future Saturn or Dreamcast module can reuse the same source axis calibration
while choosing its own response/deadzone/output behavior.


## Calibration result staging

A calibration run is an experiment, not an automatic profile mutation.

The DearPyGui utility now follows this lifecycle:

```text
run calibration
    -> inspect pending result
    -> Apply Pending Result
    -> inspect in-memory profile
    -> Save Profile
```

Until `Apply Pending Result` is pressed, the hardware profile is unchanged.

Applying a result changes only the in-memory profile. The user must separately
press `Save Profile` before JSON is written to persistent profile storage.

This allows repeated calibration attempts without polluting a known-good
hardware profile.

## Scaled console calibration presentation

The SNES calibration math remains exactly:

```text
256 x 224 logical coordinates
```

The SDL calibration worker now renders that logical surface at 3x physical
scale:

```text
768 x 672 rendered SNES area
    +
420 px instruction/telemetry panel
```

The larger presentation is purely visual. Raw Input counts, logical cursor
coordinates, target distances and derived gain calculations remain based on the
native 256x224 environment.

Instructions and telemetry are placed beside the console surface rather than
inside it.

## Mouse throw quality validation

Each directional mouse throw is now validated before it can contribute to the
calibration result.

A throw is automatically rejected and repeated when:

- it moves in the wrong primary direction;
- primary movement is too small;
- off-axis movement exceeds 45 percent of the primary movement.

Accepted throws store quality data including:

```text
primary_counts
secondary_counts
primary_abs
secondary_abs
off_axis_ratio
event_count
attempt
```

The final derived result also compares opposite-direction throw magnitudes.
Horizontal or vertical opposite-direction measurements differing by more than
2x produce a `quality.status = review` warning rather than being silently
presented as equally trustworthy.
