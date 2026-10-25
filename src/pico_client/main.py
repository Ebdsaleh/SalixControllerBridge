# src/pico_client/main.py

import sys
import select
from machine import Pin
import rp2

@rp2.asm_pio(
    out_init=rp2.PIO.OUT_HIGH,
    set_init=rp2.PIO.OUT_HIGH,
    out_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopull=False
)
def snes_piso():
    wrap_target()
    set(pins, 1)

    # Wait for Latch pulse from SNES (GP3)
    wait(1, pin, 1)
    wait(0, pin, 1)

    # Check FIFO: only update Y if host pushed new data, otherwise preserve Y
    mov(osr, y)
    pull(noblock)
    mov(x, osr)
    jmp(not_x, "use_old")
    mov(y, osr)
    label("use_old")
    mov(osr, y)

    # Present Bit 0 (B) immediately on GP4
    out(pins, 1)

    # Clock out remaining 15 bits on falling Clock edges (GP2)
    set(x, 14)
    label("clock_loop")
    wait(0, pin, 0)
    out(pins, 1)
    wait(1, pin, 0)
    jmp(x_dec, "clock_loop")

    set(pins, 1)
    wrap()

pin_clk   = Pin(2, Pin.IN, Pin.PULL_UP)
pin_latch = Pin(3, Pin.IN, Pin.PULL_UP)
pin_data  = Pin(4, Pin.OUT, value=1)

sm = rp2.StateMachine(
    0,
    snes_piso,
    freq=150_000_000,
    out_base=pin_data,
    set_base=pin_data,
    in_base=pin_clk
)

sm.put(0xFFFF << 16)
sm.active(1)

poller = select.poll()
poller.register(sys.stdin, select.POLLIN)

active_mask = 0xFFFF

while True:
    if poller.poll(0):
        b1 = sys.stdin.buffer.read(1)
        if b1 and b1[0] == 0xAA:
            b2 = sys.stdin.buffer.read(1)
            if b2 and b2[0] == 0x55:
                payload = sys.stdin.buffer.read(2)
                if len(payload) == 2:
                    raw_mask = payload[0] | (payload[1] << 8)
                    if raw_mask != active_mask:
                        active_mask = raw_mask
                        sm.put(active_mask << 16)