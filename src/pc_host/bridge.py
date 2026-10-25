# src/pc_host/bridge.py


import sys
import time
import serial
import pygame

SERIAL_PORT = "COM3"
BAUD_RATE = 115200

def init_controller():
    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        print("No arcade stick detected.")
        sys.exit(1)
    js = pygame.joystick.Joystick(0)
    js.init()
    return js

def build_snes_mask(js):
    pygame.event.pump()
    mask = 0xFFFF

    button_map = {
        0: 1,   # Square/X    -> SNES Y (Bit 1)
        1: 0,   # Cross/A     -> SNES B (Bit 0)
        2: 8,   # Circle/B    -> SNES A (Bit 8)
        3: 9,   # Triangle/Y  -> SNES X (Bit 9)
        4: 10,  # LB/L1       -> SNES L (Bit 10)
        5: 11,  # RB/R1       -> SNES R (Bit 11)
        6: 10,  # LT/L2       -> SNES L (Bit 10)
        7: 11,  # RT/R2       -> SNES R (Bit 11)
        8: 2,   # Select      -> SNES Select (Bit 2)
        9: 3,   # Start       -> SNES Start (Bit 3)
        10: 2,  # Alt Select  -> SNES Select (Bit 2)
        11: 3,  # Alt Start   -> SNES Start (Bit 3)
        12: 3   # Home        -> SNES Start (Bit 3)
    }

    num_buttons = js.get_numbuttons()
    for btn_idx, snes_bit in button_map.items():
        if btn_idx < num_buttons and js.get_button(btn_idx):
            mask &= ~(1 << snes_bit)

    if js.get_numhats() > 0:
        hat_x, hat_y = js.get_hat(0)
        if hat_y == 1:
            mask &= ~(1 << 4)
        elif hat_y == -1:
            mask &= ~(1 << 5)
        if hat_x == -1:
            mask &= ~(1 << 6)
        elif hat_x == 1:
            mask &= ~(1 << 7)

    return mask

def main():
    js = init_controller()
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0)
    except serial.SerialException as err:
        print(f"Error opening {SERIAL_PORT}: {err}")
        sys.exit(1)

    print("Bridge streaming. Press Ctrl+C to exit.")
    last_mask = None

    try:
        while True:
            mask = build_snes_mask(js)
            packet = bytearray([0xAA, 0x55, mask & 0xFF, (mask >> 8) & 0xFF])
            ser.write(packet)

            if mask != last_mask:
                active_bits = bin(~mask & 0x0FFF)[2:].zfill(12)
                print(f"Mask: 0x{mask:04X} | SNES (R->B): {active_bits}")
                last_mask = mask

            time.sleep(0.005)
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()
        pygame.quit()

if __name__ == "__main__":
    main()