"""Send a fixed SNES controller state to the Pico for hardware validation."""

import argparse
import time

import serial

SYNC_1 = 0xAA
SYNC_2 = 0x55
BAUD_RATE = 115200

SNES_BITS = {
    "b": 0,
    "y": 1,
    "select": 2,
    "start": 3,
    "up": 4,
    "down": 5,
    "left": 6,
    "right": 7,
    "a": 8,
    "x": 9,
    "l": 10,
    "r": 11,
}


def build_mask(button_name):
    mask = 0xFFFF
    if button_name != "neutral":
        mask &= ~(1 << SNES_BITS[button_name])
    return mask


def packet_for(mask):
    return bytes((SYNC_1, SYNC_2, mask & 0xFF, (mask >> 8) & 0xFF))


def main():
    parser = argparse.ArgumentParser(
        description="Continuously send one known SNES button state to the Pico."
    )
    parser.add_argument("--port", default="COM3", help="Pico serial port (default: COM3)")
    parser.add_argument(
        "--button",
        default="neutral",
        choices=("neutral",) + tuple(SNES_BITS),
        help="SNES state to hold (default: neutral)",
    )
    args = parser.parse_args()

    mask = build_mask(args.button)
    packet = packet_for(mask)
    neutral_packet = packet_for(0xFFFF)

    print(f"Opening {args.port} at {BAUD_RATE} baud")
    print(f"Holding SNES state: {args.button.upper()}  logical mask=0x{mask:04X}")
    print("Press Ctrl+C to release and exit.")

    with serial.Serial(args.port, BAUD_RATE, timeout=0) as ser:
        try:
            while True:
                ser.write(packet)
                time.sleep(0.005)
        except KeyboardInterrupt:
            pass
        finally:
            for _ in range(5):
                ser.write(neutral_packet)
                time.sleep(0.005)


if __name__ == "__main__":
    main()
