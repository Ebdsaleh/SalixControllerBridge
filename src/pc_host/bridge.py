# src/pc_host/bridge.py

import sys
import time

import pygame
import serial

SERIAL_PORT = "COM3"
BAUD_RATE = 115200

SYNC_1 = 0xAA
SYNC_2 = 0x55
SNES_NEUTRAL_MASK = 0xFFFF

# Mayflash F300, PS3/DINPUT mode, measured on Windows Server 2022 x64.
#
# SNES bit order:
#   0 B, 1 Y, 2 Select, 3 Start,
#   4 Up, 5 Down, 6 Left, 7 Right,
#   8 A, 9 X, 10 L, 11 R
#
# F300 Pygame button indices measured 2026-10-25:
#   Square=0, Cross=1, R1=2, Triangle=3, Circle=4, R2=5,
#   L1=6, L2=7, Home=9, Select=10, Start=11.
F300_BUTTON_TO_SNES_BIT = {
    0: 1,    # Square/X   -> SNES Y
    1: 0,    # Cross/A    -> SNES B
    2: 11,   # R1         -> SNES R
    3: 9,    # Triangle/Y -> SNES X
    4: 8,    # Circle/B   -> SNES A
    5: 11,   # R2         -> SNES R
    6: 10,   # L1         -> SNES L
    7: 10,   # L2         -> SNES L
    9: 3,    # Home/PS    -> SNES Start
    10: 2,   # Select     -> SNES Select
    11: 3,   # Start      -> SNES Start
}


def init_controller():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No arcade stick detected.")
        sys.exit(1)

    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    print(f"Controller: {joystick.get_name()}")
    print(
        "Inputs: "
        f"{joystick.get_numbuttons()} buttons, "
        f"{joystick.get_numhats()} hats, "
        f"{joystick.get_numaxes()} axes"
    )
    return joystick


def build_snes_mask(joystick):
    pygame.event.pump()
    mask = SNES_NEUTRAL_MASK

    num_buttons = joystick.get_numbuttons()
    for button_index, snes_bit in F300_BUTTON_TO_SNES_BIT.items():
        if button_index < num_buttons and joystick.get_button(button_index):
            mask &= ~(1 << snes_bit)

    if joystick.get_numhats() > 0:
        hat_x, hat_y = joystick.get_hat(0)

        if hat_y == 1:
            mask &= ~(1 << 4)   # Up
        elif hat_y == -1:
            mask &= ~(1 << 5)   # Down

        if hat_x == -1:
            mask &= ~(1 << 6)   # Left
        elif hat_x == 1:
            mask &= ~(1 << 7)   # Right

    return mask


def build_packet(mask):
    return bytes((SYNC_1, SYNC_2, mask & 0xFF, (mask >> 8) & 0xFF))


def send_neutral(serial_port):
    packet = build_packet(SNES_NEUTRAL_MASK)
    for _ in range(5):
        serial_port.write(packet)
        time.sleep(0.005)


def main():
    joystick = init_controller()

    try:
        serial_port = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0)
    except serial.SerialException as err:
        pygame.quit()
        print(f"Error opening {SERIAL_PORT}: {err}")
        sys.exit(1)

    print(f"Bridge streaming to {SERIAL_PORT}. Press Ctrl+C to exit.")
    last_mask = None

    try:
        while True:
            mask = build_snes_mask(joystick)
            serial_port.write(build_packet(mask))

            if mask != last_mask:
                active_bits = bin(~mask & 0x0FFF)[2:].zfill(12)
                print(f"Mask: 0x{mask:04X} | SNES (R->B): {active_bits}")
                last_mask = mask

            time.sleep(0.005)

    except KeyboardInterrupt:
        print("\nReleasing all SNES inputs...")

    finally:
        try:
            send_neutral(serial_port)
        finally:
            serial_port.close()
            pygame.quit()


if __name__ == "__main__":
    main()
