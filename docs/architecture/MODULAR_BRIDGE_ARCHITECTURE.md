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


## Output-personality lifecycle

Console-output personalities may require an explicit activation boundary, not
only data packets.

For the current SNES Mouse/Pico transport, a host restart must not assume that
the previous PIO execution phase is reusable merely because the Pico still
reports the same logical mode.

Physical-mouse mode therefore re-arms the SNES Mouse output through:

```text
PAD neutral -> MOUSE neutral
```

before live normalized `MouseState` data is emitted.

This lifecycle behavior belongs to the SNES output personality, not to
`PhysicalMouseSource`.


## Physical mouse source motion envelope

Normalized states are allowed to apply source-specific safety/normalization
before entering a console personality.

For the PC physical-mouse source, Windows/SDL can produce relative motion far
larger than an authentic SNES Mouse normally produces. The source therefore
limits each 60 Hz motion vector to a maximum largest-axis magnitude of 28 while
preserving direction proportionally.

This is intentionally a source normalization rule, not an SNES screen-position
rule:

```text
desktop relative motion
    -> source motion envelope
    -> MouseState
    -> SNES Mouse encoder
```

The SNES Mouse remains a relative device; cursor bounds remain owned by the
game.


## Source-local software gain

Physical input hardware should remain configured for the environment that owns
it. A high-DPI desktop mouse should not need to be crippled at the device level
just to feed a low-resolution legacy console peripheral.

The physical PC-mouse source therefore has its own software gain before console
normalization:

```text
desktop mouse
    -> source gain
    -> fractional residual carry
    -> source throw envelope
    -> MouseState
    -> console output
```

This is another example of why source normalization and console output must
remain separate modules.


## PC-host mouse compensation versus final standalone USB host

The current `bridge.py ... mouse` path is a PC-host proof adapter. Its input
comes from SDL/Pygame after the operating system has already claimed the mouse.

That means host pointer settings, desktop integration, and device DPI can affect
the relative motion observed by the bridge.

The final standalone Salix box should not reproduce that dependency.

Final intended path:

```text
physical USB/Bluetooth mouse
    -> Salix raw HID host
    -> device/profile normalization
    -> MouseState
    -> selected console mouse personality
```

There is no Windows desktop cursor or Windows pointer-acceleration stage in that
path.

Therefore the current `--mouse-gain` control must be understood primarily as
a PC-host/source-normalization aid, not as part of the SNES Mouse protocol.

One nuance remains: raw HID bypasses OS acceleration, but a high-DPI mouse still
produces more raw counts per unit of physical movement than a low-DPI mouse.
The standalone box may therefore still need per-device/profile scaling. That
scaling belongs to the input-source/profile layer.

The SNES-oriented per-report throw envelope is a separate concern: it limits the
relative motion presented to the emulated console peripheral and may remain
useful even when the source is raw HID.
