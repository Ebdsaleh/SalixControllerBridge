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
