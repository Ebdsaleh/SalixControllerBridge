# src/pico_client/main.py

import select
import sys

from machine import Pin
import rp2

# Physical SNES DATA-wire word, bit 0 first:
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
# The console input inverts the physical DATA line:
#   physical LOW  -> CPU-visible 1
#   physical HIGH -> CPU-visible 0
#
# Therefore:
# - pressed buttons are LOW on the wire;
# - released buttons are HIGH;
# - the CPU-visible 0000 standard-pad signature is HIGH on the wire;
# - official pads return CPU-visible 1s after the first 16 bits, so DATA is
#   LOW after the report until the next latch.
SNES_BUTTON_MASK = 0x0FFF
SNES_SIGNATURE_WIRE_BITS = 0xF000
SNES_NEUTRAL_WORD = 0xFFFF


@rp2.asm_pio(
    out_init=rp2.PIO.OUT_LOW,
    set_init=rp2.PIO.OUT_LOW,
    out_shiftdir=rp2.PIO.SHIFT_RIGHT,
    autopull=False,
)
def snes_piso():
    """Emulate an official standard SNES pad at the physical DATA pin."""
    wrap_target()

    # Official pads return logical 1s after the 16-bit report. Because the
    # console input is inverted, that is a physical LOW level.
    set(pins, 0)

    # SNES latch is GP3. in_base is GP2, so pin index 1 == GP3.
    wait(1, pin, 1)

    # Latch on a real CD4021 is asynchronous. Load the freshest available
    # controller word as soon as Latch goes high and expose B immediately,
    # rather than waiting for Latch to fall.
    #
    # PULL NOBLOCK uses X when the FIFO is empty, so X retains the most recent
    # complete controller word between polls.
    pull(noblock)
    mov(x, osr)
    mov(osr, x)
    out(pins, 1)

    # Hold B while Latch is active.
    wait(0, pin, 1)

    # The console samples DATA on Clock falling edges. The 4021 shifts on the
    # following low-to-high Clock edge. Fifteen bits remain after B.
    set(y, 14)
    label("clock_loop")
    wait(0, pin, 0)
    wait(1, pin, 0)
    out(pins, 1)
    jmp(y_dec, "clock_loop")

    # Bit 15 was placed on DATA at the previous rising edge. Let the console
    # sample it on the final falling edge, then restore the official pad's
    # post-report LOW state after the final rising edge.
    wait(0, pin, 0)
    wait(1, pin, 0)
    set(pins, 0)

    wrap()


pin_clk = Pin(2, Pin.IN, Pin.PULL_UP)
pin_latch = Pin(3, Pin.IN, Pin.PULL_UP)
pin_data = Pin(4, Pin.OUT, value=0)

sm = rp2.StateMachine(
    0,
    snes_piso,
    freq=150_000_000,
    out_base=pin_data,
    set_base=pin_data,
    in_base=pin_clk,
)

# Seed the PIO's retained state. The first console poll consumes this word.
sm.put(SNES_NEUTRAL_WORD)
sm.active(1)

poller = select.poll()
poller.register(sys.stdin, select.POLLIN)

# active_word is always the newest host state.
# last_enqueued_word tracks what is currently pending in the PIO FIFO.
#
# Crucially, we keep at most ONE pending update. A fighting-stick motion can
# produce several intermediate states in a few milliseconds. Queueing all of
# them would make the console replay stale states one frame at a time and can
# fill the PIO FIFO, causing sm.put() to block and COM3 to back up.
active_word = SNES_NEUTRAL_WORD
last_enqueued_word = SNES_NEUTRAL_WORD

parser_state = 0
payload_low = 0


def queue_latest_if_possible():
    global last_enqueued_word

    if active_word == last_enqueued_word:
        return

    # Never call sm.put() while a word is already pending. StateMachine.put()
    # is blocking if the TX FIFO fills. Waiting for an empty FIFO makes
    # "latest state wins" instead of accumulating stale intermediate inputs.
    if sm.tx_fifo() == 0:
        sm.put(active_word)
        last_enqueued_word = active_word


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
        if value == 0xAA:
            parser_state = 1

    elif parser_state == 1:
        if value == 0x55:
            parser_state = 2
        elif value != 0xAA:
            parser_state = 0

    elif parser_state == 2:
        payload_low = value
        parser_state = 3

    else:
        raw_mask = payload_low | (value << 8)
        parser_state = 0

        # Host mask uses 0=pressed / 1=released for the twelve buttons.
        # Force physical wire bits 12-15 HIGH so the SNES sees the standard
        # controller's CPU-visible 0000 signature.
        active_word = (
            (raw_mask & SNES_BUTTON_MASK)
            | SNES_SIGNATURE_WIRE_BITS
        )

        queue_latest_if_possible()
