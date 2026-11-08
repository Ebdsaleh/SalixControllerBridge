# src/pc_host/pico_monitor.py

"""Simple Pico CDC monitor with a reliable Ctrl+C exit path on Windows."""

import argparse
import sys

import serial

from serial_ports import resolve_serial_port


DEFAULT_BAUD_RATE = 115200
READ_TIMEOUT_SECONDS = 0.100


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Monitor Salix/Pico USB CDC output. Ctrl+C always exits and closes "
            "the serial port."
        )
    )
    parser.add_argument(
        "serial_port",
        nargs="?",
        metavar="COM_PORT",
        help=(
            "Optional Pico serial port override, for example COM6. "
            "If omitted, the active Pico is auto-detected."
        ),
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=DEFAULT_BAUD_RATE,
        help=f"Serial baud rate (default: {DEFAULT_BAUD_RATE}).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        port = resolve_serial_port(args.serial_port)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        f"Monitoring {port} at {args.baud} baud. "
        "Press Ctrl+C to exit."
    )

    try:
        with serial.Serial(
            port,
            baudrate=args.baud,
            timeout=READ_TIMEOUT_SECONDS,
            write_timeout=READ_TIMEOUT_SECONDS,
        ) as connection:
            while True:
                pending = connection.in_waiting
                data = connection.read(pending if pending > 0 else 1)

                if not data:
                    continue

                sys.stdout.write(data.decode("utf-8", errors="replace"))
                sys.stdout.flush()

    except KeyboardInterrupt:
        print("\nMonitor stopped.")
        return 0
    except serial.SerialException as exc:
        print(f"\nSerial monitor error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
