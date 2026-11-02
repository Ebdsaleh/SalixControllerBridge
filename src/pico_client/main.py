# src/pico_client/main.py

import select
import sys

from machine import Pin
import rp2

# Host serial frames:
#   AA 55 <pad-low> <pad-high>
#       Existing standard-controller frame. Kept backward-compatible with the
#       current bridge and snes_test_pattern.py tools.
#
#   AA 56 <mouse-wire-b0> <b1> <b2> <b3>
#       SNES Mouse frame. Payload is the 32-bit physical DATA-wire word in
#       little-endian order; bit 0 is the first bit presented after Latch.
SYNC_1 = 0xAA
SYNC_PAD = 0x55
SYNC_MOUSE = 0x56

MODE_PAD = 0
MODE_MOUSE = 1

# Physical SNES DATA-wire word, bit 0 first for a standard pad:
#   0  B
#   1  Y
#   2  Select
#   3  Start
#   4  Up
#   5  Down
#   6  Left
#   7  Right
#   8  A
#   9  X
#  10  L
#  11  R
# 12-15 standard-pad signature stages
#
# The proven PAL-SNES interface inverts the physical DATA line at the console:
#   physical LOW  -> CPU-visible 1
#   physical HIGH -> CPU-visible 0
#
# Therefore pressed pad buttons are LOW on the wire and released buttons are
# HIGH. The mouse host encoder applies the same physical-wire convention.
SNES_BUTTON_MASK = 0x0FFF
SNES_SIGNATURE_WIRE_BITS = 0xF000
SNES_PAD_NEUTRAL_WORD = 0xFFFF

# Logical neutral SNES Mouse report is 00 01 00 00 (MSB first). After reversing
# the serial order into PIO bit 0 first and applying the proven wire inversion,
# the physical word is FFFF7FFF.
SNES_MOUSE_NEUTRAL_WIRE_WORD = 0xFFFF7FFF


@rp2.asm_pio(
    out_init=rp2.PIO.OUT_LOW,
    set_init=rp2.PIO.OUT_LOW,
    out_shiftdir=rp2.PIO.SHIFT_RIGHT,
    autopull=False,
)
def snes_pad_piso():
    """Emulate an official standard SNES pad at the physical DATA pin."""
    wrap_target()

    # Official pads return logical 1s after the 16-bit report. Because the
    # console input is inverted, that is a physical LOW level.
    set(pins, 0)

    # SNES latch is GP3. in_base is GP2, so pin index 1 == GP3.
    wait(1, pin, 1)

    # PULL NOBLOCK uses X when the FIFO is empty, so X retains the most recent
    # complete controller word between polls.
    pull(noblock)
    mov(x, osr)
    mov(osr, x)
    out(pins, 1)

    # Hold B while Latch is active.
    wait(0, pin, 1)

    # Fifteen bits remain after B.
    set(y, 14)
    label("pad_clock_loop")
    wait(0, pin, 0)
    wait(1, pin, 0)
    out(pins, 1)
    jmp(y_dec, "pad_clock_loop")

    # Let the console sample bit 15 on the final falling edge, then restore the
    # official pad's post-report LOW state after the final rising edge.
    wait(0, pin, 0)
    wait(1, pin, 0)
    set(pins, 0)

    wrap()


@rp2.asm_pio(
    out_init=rp2.PIO.OUT_LOW,
    set_init=rp2.PIO.OUT_LOW,
    out_shiftdir=rp2.PIO.SHIFT_RIGHT,
    autopull=False,
)
def snes_mouse_piso():
    """Emulate the 32-bit SNES Mouse serial report at the DATA pin."""
    wrap_target()

    # Authentic SNES mice return logical 1s after bit 32. With the proven
    # console-side inversion this is a physical LOW level.
    set(pins, 0)

    wait(1, pin, 1)

    # Load the newest 32-bit physical-wire report and expose its first bit
    # immediately while Latch is high.
    pull(noblock)
    mov(x, osr)
    mov(osr, x)
    out(pins, 1)

    wait(0, pin, 1)

    # Thirty-one bits remain after the first report bit.
    set(y, 30)
    label("mouse_clock_loop")
    wait(0, pin, 0)
    wait(1, pin, 0)
    out(pins, 1)
    jmp(y_dec, "mouse_clock_loop")

    # Let the console sample bit 31, then return the authentic post-report
    # logical 1 (physical LOW) until the next latch.
    wait(0, pin, 0)
    wait(1, pin, 0)
    set(pins, 0)

    wrap()


pin_clk = Pin(2, Pin.IN, Pin.PULL_UP)
pin_latch = Pin(3, Pin.IN, Pin.PULL_UP)
pin_data = Pin(4, Pin.OUT, value=0)

# Keep pad and mouse programs in separate PIO instruction memories.
# StateMachine 0 is PIO0/SM0; StateMachine 4 is PIO1/SM0. Each PIO block has
# its own 32-instruction program memory, avoiding ENOMEM when both personalities
# are present in one firmware image.
pad_sm = rp2.StateMachine(0)
mouse_sm = rp2.StateMachine(4)
active_sm = pad_sm
current_mode = None
active_word = SNES_PAD_NEUTRAL_WORD
last_enqueued_word = SNES_PAD_NEUTRAL_WORD


def init_state_machine(mode, initial_word):
    """Switch between pad and mouse PIO blocks without sharing program memory."""
    global active_sm, current_mode, active_word, last_enqueued_word

    pad_sm.active(0)
    mouse_sm.active(0)

    if mode == MODE_MOUSE:
        target_sm = mouse_sm
        program = snes_mouse_piso
    else:
        target_sm = pad_sm
        program = snes_pad_piso

    # Re-initialising the selected SM resets its execution/FIFO state. Because
    # each personality lives in a different PIO block, the two programs no
    # longer compete for the same 32-instruction memory.
    target_sm.init(
        program,
        freq=150_000_000,
        out_base=pin_data,
        set_base=pin_data,
        in_base=pin_clk,
    )

    active_sm = target_sm
    active_word = initial_word
    last_enqueued_word = initial_word
    active_sm.put(initial_word)
    active_sm.active(1)
    current_mode = mode

def queue_latest_if_possible():
    global last_enqueued_word

    if active_word == last_enqueued_word:
        return

    # Keep at most one pending report. Latest state wins rather than allowing
    # stale controller/mouse reports to accumulate in the PIO TX FIFO.
    if active_sm.tx_fifo() == 0:
        active_sm.put(active_word)
        last_enqueued_word = active_word


def apply_pad_word(raw_mask):
    global active_word

    pad_word = (
        (raw_mask & SNES_BUTTON_MASK)
        | SNES_SIGNATURE_WIRE_BITS
    )

    if current_mode != MODE_PAD:
        init_state_machine(MODE_PAD, pad_word)
        return

    active_word = pad_word
    queue_latest_if_possible()


def apply_mouse_wire_word(mouse_word):
    global active_word

    mouse_word &= 0xFFFFFFFF

    if current_mode != MODE_MOUSE:
        init_state_machine(MODE_MOUSE, mouse_word)
        return

    active_word = mouse_word
    queue_latest_if_possible()


# Start in the existing, known-good standard-controller mode.
init_state_machine(MODE_PAD, SNES_PAD_NEUTRAL_WORD)

poller = select.poll()
poller.register(sys.stdin, select.POLLIN)

parser_state = 0
frame_kind = None
payload = bytearray(4)
payload_index = 0

while True:
    # If the previous pending word was consumed by the SNES, immediately queue
    # the newest desired state. This runs even when no new serial byte arrived.
    queue_latest_if_possible()

    if not poller.poll(0):
        continue

    incoming = sys.stdin.buffer.read(1)
    if not incoming:
        continue

    value = incoming[0]

    if parser_state == 0:
        if value == SYNC_1:
            parser_state = 1

    elif parser_state == 1:
        if value == SYNC_PAD:
            frame_kind = MODE_PAD
            payload_index = 0
            parser_state = 2
        elif value == SYNC_MOUSE:
            frame_kind = MODE_MOUSE
            payload_index = 0
            parser_state = 2
        elif value != SYNC_1:
            parser_state = 0

    else:
        payload[payload_index] = value
        payload_index += 1

        expected = 2 if frame_kind == MODE_PAD else 4
        if payload_index < expected:
            continue

        parser_state = 0

        if frame_kind == MODE_PAD:
            raw_mask = payload[0] | (payload[1] << 8)
            apply_pad_word(raw_mask)
        else:
            mouse_word = (
                payload[0]
                | (payload[1] << 8)
                | (payload[2] << 16)
                | (payload[3] << 24)
            )
            apply_mouse_wire_word(mouse_word)
