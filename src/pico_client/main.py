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
# 12-15 Unused standard-pad stages
#
# IMPORTANT:
# The controller DATA wire is active-low. A pressed button drives LOW.
# The SNES CPU-side controller bits are therefore the logical inverse of the
# wire level. A standard controller's CPU-visible signature is 0000, which
# means the physical DATA wire must be HIGH for clocks 13-16.
#
# After the 16-bit report an official controller drives DATA LOW. A subsequent
# (17th) manual read therefore reports 1 to the CPU, which Nintendo documents
# as "standard controller connected".
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
    """Emulate the physical DATA output of an official standard SNES pad."""
    wrap_target()

    # Official standard pads idle DATA low after the 16th bit. This also makes
    # the 17th manual read identify a connected standard controller.
    set(pins, 0)

    # SNES latch is GP3. in_base is GP2, so pin index 1 == GP3.
    wait(1, pin, 1)
    wait(0, pin, 1)

    # PULL NOBLOCK keeps the most recent controller word in X when no new host
    # update is queued. A newly queued word replaces it at each latch.
    pull(noblock)
    mov(x, osr)

    # B (bit 0) must be valid at the falling edge of Latch, before the first
    # falling Clock edge at which the console samples it.
    out(pins, 1)

    # The SNES samples DATA on Clock falling edges. The pad shifts to the next
    # bit on the following rising edge. Fifteen bits remain after B.
    set(y, 14)
    label("clock_loop")
    wait(0, pin, 0)
    wait(1, pin, 0)
    out(pins, 1)
    jmp(y_dec, "clock_loop")

    # Bit 15 was placed on DATA at the previous rising edge. Let the console
    # sample it on the final falling edge, then reproduce an official pad's
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

# SHIFT_RIGHT outputs bit 0 first.
sm.put(SNES_NEUTRAL_WORD)
sm.active(1)

poller = select.poll()
poller.register(sys.stdin, select.POLLIN)

active_word = SNES_NEUTRAL_WORD
parser_state = 0
payload_low = 0

while True:
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

        # Host mask: 0=pressed, 1=released for the 12 SNES buttons.
        # Force physical wire bits 12-15 HIGH. The SNES input circuitry
        # interprets these as the standard controller's CPU-visible 0000
        # signature.
        wire_word = (raw_mask & SNES_BUTTON_MASK) | SNES_SIGNATURE_WIRE_BITS

        if wire_word != active_word:
            active_word = wire_word
            sm.put(active_word)
