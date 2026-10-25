# PIO Input Queue / Compatibility Notes

## Why rapid fighter inputs could feel wrong

The RP2 PIO state machine has a small TX FIFO. MicroPython's
`StateMachine.put()` blocks when that FIFO is full.

Earlier firmware queued every changed host state. A fighting-stick motion can
produce several valid intermediate states inside a single SNES frame, for
example:

`Right -> Up+Right -> Up+Right+B`

If all of those are queued, the console can receive them one poll at a time
instead of receiving the latest state. That can create:

- delayed or unreliable diagonal jumps;
- stale intermediate direction/button combinations;
- apparent input lag;
- a full PIO FIFO that blocks `sm.put()`;
- serial back-pressure on COM3 and a host process that becomes difficult to
  interrupt.

The current firmware keeps at most one PIO update pending. New serial input
updates an in-memory desired state; once the pending word is consumed, only the
latest desired state is queued.

## Standard-pad physical behavior

The console input is logically inverted relative to the physical DATA pin:

- pressed button: DATA LOW;
- released button: DATA HIGH;
- standard-pad signature bits 12-15: DATA HIGH (CPU sees 0000);
- after bit 16: DATA LOW (CPU sees subsequent 1s).

The PIO now also exposes the B-button state while Latch is still high, matching
the asynchronous parallel-load behavior of a CD4021 more closely.

## Compatibility observations

Host-side diagonal construction is already correct:

- Up+Right = 0xFF6F
- Down+Right = 0xFF5F
- Down+Left = 0xFF9F
- Up+Left = 0xFFAF

The remaining compatibility work is therefore focused on exact SNES pad
electrical/timing behavior rather than Mayflash/Pygame mapping.
