"""Send a fixed SNES controller state to the Pico for hardware validation."""

import argparse
import time

import serial

from serial_ports import resolve_serial_port

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
    parser.add_argument(
        "serial_port",
        nargs="?",
        metavar="COM_PORT",
        help="Optional Pico serial port override, e.g. COM4; otherwise auto-detect.",
    )
    parser.add_argument(
        "--port",
        dest="port_override",
        metavar="COM_PORT",
        help="Explicit Pico serial port override (same as positional COM_PORT).",
    )
    parser.add_argument(
        "--button",
        default="neutral",
        choices=("neutral",) + tuple(SNES_BITS),
        help="SNES state to hold (default: neutral)",
    )
    args = parser.parse_args()

    if (
        args.serial_port
        and args.port_override
        and args.serial_port.casefold() != args.port_override.casefold()
    ):
        parser.error(
            "conflicting serial ports supplied: "
            f"{args.serial_port} and {args.port_override}"
        )

    serial_device = resolve_serial_port(args.port_override or args.serial_port)

    mask = build_mask(args.button)
    packet = packet_for(mask)
    neutral_packet = packet_for(0xFFFF)

    print(f"Opening {serial_device} at {BAUD_RATE} baud")
    print(f"Holding SNES state: {args.button.upper()}  logical mask=0x{mask:04X}")
    print("Press Ctrl+C to release and exit.")

    with serial.Serial(serial_device, BAUD_RATE, timeout=0) as ser:
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
