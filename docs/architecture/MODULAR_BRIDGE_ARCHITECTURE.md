# SalixControllerBridge modular architecture

## Core rule

The user-facing `bridge.py` entry point is an orchestrator.

It should select and connect modules; it should not become the implementation
of every input device or every console protocol.

The intended data flow is:

```text
physical input
    |
    v
input-source module
    |
    v
normalized state
    |
    v
optional translation personality
    |
    v
console-output module
    |
    v
physical console
```

## Normalized states

Normalized states preserve source semantics before any console-specific
encoding occurs.

Current mouse state:

```text
MouseState
  dx
  dy
  left
  right
```

Other families can later expose their own normalized states:

```text
GamepadState
KeyboardState
MouseState
WheelState
FlightStickState
```

## Current mouse paths

Gamepad/arcade-stick mouse emulation:

```text
controller
    -> controller profile
    -> gamepad-to-mouse translation
    -> MouseState
    -> SNES Mouse output
```

Physical PC/USB mouse translation:

```text
PC mouse
    -> PhysicalMouseSource
    -> MouseState
    -> SNES Mouse output
```

Both therefore share the same console-facing mouse state and encoder.

## Orchestrator commands

Normal controller bridge:

```bat
py src\pc_host\bridge.py COM3
```

Gamepad emulating a mouse:

```bat
py src\pc_host\bridge.py COM3 mouse_emu
```

Physical PC mouse translated to a console mouse:

```bat
py src\pc_host\bridge.py COM3 mouse
```

## Console modules

The long-term console side should be grouped by console family, for example:

```text
SNES
  Standard Controller
  Mouse

Saturn
  Digital Pad
  Analog Pad
  Mouse
  Keyboard
  Virtua Gun / timing-dependent peripherals

Dreamcast
  Controller
  Mouse
  Keyboard
  other Maple devices
```

The source should not need to know which console consumes the normalized state.

Examples:

```text
USB mouse       -> MouseState -> SNES Mouse
USB mouse       -> MouseState -> Saturn Mouse
USB mouse       -> MouseState -> Dreamcast Mouse

Switch Pro      -> MouseState -> SNES Mouse
Switch Pro      -> GamepadState -> SNES Pad

USB keyboard    -> KeyboardState -> Dreamcast Keyboard
```

## Current host limitation

The first `mouse` source uses SDL/Pygame's PC mouse input. It therefore sees
the operating system's active mouse stream rather than selecting one specific
USB HID by VID/PID.

That is appropriate for the current PC-host proof.

The future standalone Salix box should enumerate USB/Bluetooth devices itself
and bind individual physical devices to input slots before producing normalized
states.


## Physical mouse transport resilience

Input-source modules and console-output modules remain independent from host
transport reliability.

A transient serial timeout must not destroy the normalized input source. For
physical mouse mode, the bridge retries the latest `MouseState` after clearing
stale queued serial bytes. This follows the same latest-state-wins rule already
used throughout the controller bridge: old motion reports are less valuable
than the newest state.

Device-specific controls such as mouse DPI buttons remain source-specific and
must not leak into console-output personalities unless an explicit translation
profile chooses to use them.
