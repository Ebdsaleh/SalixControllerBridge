# src/pc_host/bridge.py

import sys
import time

import pygame
import serial

SERIAL_PORT = "COM3"
BAUD_RATE = 115200
HEARTBEAT_SECONDS = 0.100

SYNC_1 = 0xAA
SYNC_2 = 0x55
SNES_NEUTRAL_MASK = 0xFFFF

# Mayflash F300, PS3/DINPUT mode, measured on Windows Server 2022 x64.
# SNES bits: 0=B, 1=Y, 2=Select, 3=Start, 4=Up, 5=Down,
#            6=Left, 7=Right, 8=A, 9=X, 10=L, 11=R.
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
        raise RuntimeError("No arcade stick detected.")

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
            mask &= ~(1 << 4)
        elif hat_y == -1:
            mask &= ~(1 << 5)

        if hat_x == -1:
            mask &= ~(1 << 6)
        elif hat_x == 1:
            mask &= ~(1 << 7)

    return mask


def build_packet(mask):
    return bytes((SYNC_1, SYNC_2, mask & 0xFF, (mask >> 8) & 0xFF))


def send_mask(serial_port, mask):
    packet = build_packet(mask)
    bytes_written = serial_port.write(packet)

    if bytes_written != len(packet):
        raise serial.SerialException(
            f"Short serial write: expected {len(packet)} bytes, wrote {bytes_written}"
        )

    return packet, bytes_written


def send_neutral(serial_port):
    for _ in range(5):
        send_mask(serial_port, SNES_NEUTRAL_MASK)
        time.sleep(0.005)


def main():
    joystick = None
    serial_port = None

    try:
        joystick = init_controller()
        serial_port = serial.Serial(
            SERIAL_PORT,
            BAUD_RATE,
            timeout=0,
            write_timeout=0.100,
        )

        print(f"Bridge streaming to {SERIAL_PORT}. Press Ctrl+C to exit.")

        last_mask = None
        last_send_time = 0.0

        while True:
            mask = build_snes_mask(joystick)
            now = time.monotonic()

            # Send immediately on every state change. While held, refresh at
            # 10 Hz only. The Pico keeps the latest state between SNES polls,
            # so flooding COM3 every 5 ms is unnecessary.
            if mask != last_mask or (now - last_send_time) >= HEARTBEAT_SECONDS:
                packet, bytes_written = send_mask(serial_port, mask)
                last_send_time = now
            else:
                packet = None
                bytes_written = 0

            if mask != last_mask:
                active_bits = bin(~mask & 0x0FFF)[2:].zfill(12)
                packet_hex = " ".join(f"{byte:02X}" for byte in packet)
                print(
                    f"Mask: 0x{mask:04X} | SNES (R->B): {active_bits} "
                    f"| TX: {packet_hex} | wrote={bytes_written}"
                )
                last_mask = mask

            # 1 ms input sampling keeps the F300 responsive while leaving
            # Windows plenty of opportunities to deliver Ctrl+C.
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\nCtrl+C received. Releasing all SNES inputs...")

    except serial.SerialTimeoutException:
        print("\nSerial write timed out. Releasing bridge.")

    except (serial.SerialException, RuntimeError) as err:
        print(f"Bridge error: {err}")

    finally:
        if serial_port is not None:
            try:
                send_neutral(serial_port)
            except (serial.SerialException, serial.SerialTimeoutException):
                pass
            try:
                serial_port.close()
            except serial.SerialException:
                pass

        pygame.quit()
        print("Bridge stopped.")


if __name__ == "__main__":
    main()
