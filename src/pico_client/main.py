# src/pico_client/main.py

import select
import sys

from machine import Pin
import rp2

# SNES standard controller serial word, bit 0 first on the wire:
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
# 12-15 Standard-controller signature: 0000
#
# Buttons are active-low: 0 = pressed, 1 = released.
SNES_BUTTON_MASK = 0x0FFF
SNES_NEUTRAL_WORD = 0x0FFF


@rp2.asm_pio(
    out_init=rp2.PIO.OUT_HIGH,
    set_init=rp2.PIO.OUT_HIGH,
    out_shiftdir=rp2.PIO.SHIFT_RIGHT,
    autopull=False,
)
def snes_piso():
    """Emulate the 16-bit serial output of a standard SNES controller."""
    wrap_target()

    # Official controllers return high after the 16-bit report until relatched.
    set(pins, 1)

    # SNES latch is GP3. in_base is GP2, so pin index 1 == GP3.
    wait(1, pin, 1)
    wait(0, pin, 1)

    # PULL NOBLOCK has exactly the behaviour we need here: when the TX FIFO
    # is empty, the PIO copies X into OSR. X therefore stores the most recent
    # controller word between polls; a newly queued word replaces it.
    pull(noblock)
    mov(x, osr)

    # Bit 0 (B) is already valid before the first clock sample.
    out(pins, 1)

    # The console samples the current bit on a falling clock edge. A real
    # controller shifts on the following rising edge, so update the data line
    # after the rise for the next sample. Fifteen bits remain after B.
    set(y, 14)
    label("clock_loop")
    wait(0, pin, 0)
    wait(1, pin, 0)
    out(pins, 1)
    jmp(y_dec, "clock_loop")

    # Bit 15 was placed on the line at the previous rising edge. Let the SNES
    # sample it on the final falling edge, then return high after the rise.
    wait(0, pin, 0)
    wait(1, pin, 0)
    set(pins, 1)

    wrap()


pin_clk = Pin(2, Pin.IN, Pin.PULL_UP)
pin_latch = Pin(3, Pin.IN, Pin.PULL_UP)
pin_data = Pin(4, Pin.OUT, value=1)

sm = rp2.StateMachine(
    0,
    snes_piso,
    freq=150_000_000,
    out_base=pin_data,
    set_base=pin_data,
    in_base=pin_clk,
)

# Seed X on the first SNES latch. SHIFT_RIGHT means bit 0 is shifted first,
# so the word is queued without the old << 16 alignment.
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

        # The PC-side mask uses 0=pressed for the 12 buttons. The SNES wire
        # protocol additionally requires bits 12-15 to be 0000 as the standard
        # controller signature.
        wire_word = raw_mask & SNES_BUTTON_MASK

        if wire_word != active_word:
            active_word = wire_word
            sm.put(active_word)
