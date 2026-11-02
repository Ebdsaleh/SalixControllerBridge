# src/pc_host/mouse_bridge.py

import argparse
import time
import pygame
import serial

from bridge import BAUD_RATE, HEARTBEAT_SECONDS, open_controller
from mouse_sources import PhysicalMouseSource
from mouse_state import MouseState
from serial_ports import resolve_serial_port

MOUSE_DEADZONE = 0.18
MOUSE_ANALOG_MAX_DELTA = 8
MOUSE_DPAD_DELTA = 4

SENSITIVITY_VERY_LOW = 0
SENSITIVITY_LOW = 1
SENSITIVITY_MEDIUM = 2
SENSITIVITY_HIGH = 3
SENSITIVITY_VERY_HIGH = 4
SENSITIVITY_NAMES = ("VERY LOW", "LOW", "MEDIUM", "HIGH", "VERY HIGH")

# Preserve the currently validated five-level feel.
SENSITIVITY_ANALOG_SCALE = (0.25, 0.5, 1.0, 1.5, 2.0)
SENSITIVITY_DPAD_SCALE = (0.25, 0.5, 1.0, 2.0, 3.0)
DEFAULT_SENSITIVITY = SENSITIVITY_MEDIUM

# A real mouse produces one-shot relative deltas, not a sustained velocity.
# Sample/forward at the console's normal frame cadence so accumulated desktop
# motion becomes one SNES Mouse displacement report per frame.
PHYSICAL_MOUSE_REPORT_HZ = 60.0
PHYSICAL_MOUSE_REPORT_SECONDS = 1.0 / PHYSICAL_MOUSE_REPORT_HZ


class SnesMouseOutput:
    """SNES Mouse output personality for the generic mouse-emulation bridge."""

    SYNC_1 = 0xAA
    SYNC_MOUSE = 0x56

    SIGNATURE = 0x01
    LEFT = 0x40
    RIGHT = 0x80

    # Keep the SNES hardware speed bits at the known-good compatibility value.
    # Salix bridge sensitivity is intentionally independent from the authentic
    # SNES latch/clock hardware-sensitivity command.
    WIRE_SPEED_BITS = 0

    name = "SNES Mouse"

    @staticmethod
    def _encode_sign_magnitude(delta):
        delta = max(-127, min(127, int(delta)))
        magnitude = abs(delta)
        sign = 0x80 if delta < 0 else 0x00
        return sign | magnitude

    @classmethod
    def build_logical_report(cls, state):
        second_byte = (
            cls.SIGNATURE
            | ((cls.WIRE_SPEED_BITS & 0x03) << 4)
            | (cls.LEFT if state.left else 0)
            | (cls.RIGHT if state.right else 0)
        )

        y_byte = cls._encode_sign_magnitude(state.dy)
        x_byte = cls._encode_sign_magnitude(state.dx)

        return (
            (0x00 << 24)
            | (second_byte << 16)
            | (y_byte << 8)
            | x_byte
        )

    @staticmethod
    def logical_report_to_wire_word(logical_report):
        wire_word = 0

        for serial_index in range(32):
            logical_bit = (logical_report >> (31 - serial_index)) & 1

            # The proven PAL-SNES adapter path presents logical 1 as physical
            # LOW and logical 0 as physical HIGH at the Pico-side DATA output.
            physical_bit = 0 if logical_bit else 1
            wire_word |= physical_bit << serial_index

        return wire_word

    @classmethod
    def build_packet(cls, wire_word):
        return bytes((
            cls.SYNC_1,
            cls.SYNC_MOUSE,
            wire_word & 0xFF,
            (wire_word >> 8) & 0xFF,
            (wire_word >> 16) & 0xFF,
            (wire_word >> 24) & 0xFF,
        ))

    def send(self, serial_port, state):
        logical_report = self.build_logical_report(state)
        wire_word = self.logical_report_to_wire_word(logical_report)
        packet = self.build_packet(wire_word)
        bytes_written = serial_port.write(packet)

        if bytes_written != len(packet):
            raise serial.SerialException(
                f"Short serial write: expected {len(packet)} bytes, "
                f"wrote {bytes_written}"
            )

        serial_port.flush()
        return logical_report, wire_word, packet

    def send_neutral(self, serial_port):
        neutral = MouseState()
        for _ in range(5):
            self.send(serial_port, neutral)
            time.sleep(0.005)


def create_output_personality(name):
    normalized = name.strip().lower().replace("-", "_")

    if normalized in ("snes", "snes_mouse"):
        return SnesMouseOutput()

    raise RuntimeError(f"Unsupported mouse output personality: {name}")


def clamp_speed(value, name):
    if value < 1 or value > 32:
        raise RuntimeError(f"{name} must be between 1 and 32.")
    return value


def snes_bit_is_pressed(joystick, button_map, target_bit):
    """Current gamepad-source adapter using the canonical profile positions."""
    num_buttons = joystick.get_numbuttons()
    for button_index, snes_bit in button_map.items():
        if snes_bit != target_bit or button_index >= num_buttons:
            continue
        if joystick.get_button(button_index):
            return True
    return False


def read_sensitivity_controls(joystick, button_map):
    decrease = (
        snes_bit_is_pressed(joystick, button_map, 10)  # L shoulder
        or snes_bit_is_pressed(joystick, button_map, 1)  # Y face
    )
    increase = (
        snes_bit_is_pressed(joystick, button_map, 11)  # R shoulder
        or snes_bit_is_pressed(joystick, button_map, 9)  # X face
    )
    return decrease, increase


def scaled_speed(base_speed, sensitivity, scale_table):
    scale = scale_table[sensitivity]
    return max(1, int(round(base_speed * scale)))


def read_dpad(joystick, button_map):
    up = snes_bit_is_pressed(joystick, button_map, 4)
    down = snes_bit_is_pressed(joystick, button_map, 5)
    left = snes_bit_is_pressed(joystick, button_map, 6)
    right = snes_bit_is_pressed(joystick, button_map, 7)

    if joystick.get_numhats() > 0:
        hat_x, hat_y = joystick.get_hat(0)
        up = up or hat_y == 1
        down = down or hat_y == -1
        left = left or hat_x == -1
        right = right or hat_x == 1

    x = (-1 if left else 0) + (1 if right else 0)
    y = (-1 if up else 0) + (1 if down else 0)
    return x, y


def axis_to_delta(value, max_delta):
    magnitude = abs(value)
    if magnitude <= MOUSE_DEADZONE:
        return 0

    normalized = (magnitude - MOUSE_DEADZONE) / (1.0 - MOUSE_DEADZONE)
    delta = max(1, int(round(normalized * max_delta)))
    return -delta if value < 0.0 else delta


def read_analog_motion(joystick, directional_axis_pairs, max_delta):
    if not directional_axis_pairs:
        return 0, 0

    # The first calibrated pair is the primary mouse-motion source. This works
    # for analog sticks and for arcade sticks exposing X/Y lever axes.
    axis_x_index, axis_y_index = directional_axis_pairs[0]
    if (
        axis_x_index >= joystick.get_numaxes()
        or axis_y_index >= joystick.get_numaxes()
    ):
        return 0, 0

    return (
        axis_to_delta(joystick.get_axis(axis_x_index), max_delta),
        axis_to_delta(joystick.get_axis(axis_y_index), max_delta),
    )


def build_mouse_state(
    joystick,
    button_map,
    directional_axis_pairs,
    max_speed,
    dpad_speed,
    sensitivity,
):
    pygame.event.pump()

    analog_speed = scaled_speed(
        max_speed,
        sensitivity,
        SENSITIVITY_ANALOG_SCALE,
    )
    digital_speed = scaled_speed(
        dpad_speed,
        sensitivity,
        SENSITIVITY_DPAD_SCALE,
    )

    analog_x, analog_y = read_analog_motion(
        joystick,
        directional_axis_pairs,
        analog_speed,
    )
    dpad_x, dpad_y = read_dpad(joystick, button_map)

    dx = max(-127, min(127, analog_x + (dpad_x * digital_speed)))
    dy = max(-127, min(127, analog_y + (dpad_y * digital_speed)))

    # Source adapter convention retained from the validated SNES mapping:
    # B-position -> MouseLeft, A-position -> MouseRight.
    left_pressed = snes_bit_is_pressed(joystick, button_map, 0)
    right_pressed = snes_bit_is_pressed(joystick, button_map, 8)

    return (
        MouseState(
            dx=dx,
            dy=dy,
            left=left_pressed,
            right=right_pressed,
        ),
        analog_speed,
        digital_speed,
    )


def run_gamepad_mouse_bridge(
    serial_port_override=None,
    output_personality="snes",
    max_speed=MOUSE_ANALOG_MAX_DELTA,
    dpad_speed=MOUSE_DPAD_DELTA,
):
    joystick = None
    serial_port = None
    output = create_output_personality(output_personality)

    try:
        max_speed = clamp_speed(max_speed, "--max-speed")
        dpad_speed = clamp_speed(dpad_speed, "--dpad-speed")

        sensitivity = DEFAULT_SENSITIVITY
        previous_decrease = False
        previous_increase = False

        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            raise RuntimeError("No controller detected.")

        joystick, button_map, directional_axis_pairs = open_controller(0)

        serial_device = resolve_serial_port(serial_port_override)
        serial_port = serial.Serial(
            serial_device,
            BAUD_RATE,
            timeout=0,
            write_timeout=0.100,
        )

        print(
            f"Mouse emulation -> {output.name} streaming to {serial_device}. "
            "Press Ctrl+C to exit."
        )
        print(
            "Mapping: left stick/lever or D-pad -> mouse motion; "
            "SNES B position -> LEFT click; SNES A position -> RIGHT click."
        )
        print(
            f"Motion tuning base: analog max={max_speed}, "
            f"D-pad speed={dpad_speed}, deadzone={MOUSE_DEADZONE:.2f}"
        )
        print(
            "Sensitivity controls: L or Y = decrease; R or X = increase. "
            "Five levels, one step per press."
        )
        print(
            f"Bridge sensitivity: {SENSITIVITY_NAMES[sensitivity]} "
            f"({sensitivity})"
        )
        print(
            "SNES Mouse button report: known-good compatibility mode; "
            "B=MouseLeft, A=MouseRight."
        )

        active_instance_id = joystick.get_instance_id()
        last_state = None
        last_send_time = 0.0
        last_reconnect_poll = 0.0

        while True:
            now = time.monotonic()

            for event in pygame.event.get():
                if (
                    event.type == pygame.JOYDEVICEREMOVED
                    and joystick is not None
                    and event.instance_id == active_instance_id
                ):
                    print(
                        "Controller disconnected/re-enumerating. "
                        f"Sending neutral {output.name} state and waiting..."
                    )
                    output.send_neutral(serial_port)

                    try:
                        joystick.quit()
                    except pygame.error:
                        pass

                    joystick = None
                    button_map = None
                    directional_axis_pairs = ()
                    active_instance_id = None
                    previous_decrease = False
                    previous_increase = False
                    last_state = MouseState()
                    last_send_time = time.monotonic()
                    last_reconnect_poll = 0.0

                elif event.type == pygame.JOYDEVICEADDED and joystick is None:
                    try:
                        joystick, button_map, directional_axis_pairs = open_controller(
                            event.device_index
                        )
                        active_instance_id = joystick.get_instance_id()
                        last_state = None
                        last_send_time = 0.0
                        print("Controller re-enumerated. Mouse emulation resumed.")
                    except pygame.error as err:
                        print(f"Controller re-open deferred: {err}")
                        joystick = None

            if joystick is None:
                if (now - last_reconnect_poll) >= 0.050:
                    last_reconnect_poll = now
                    if pygame.joystick.get_count() > 0:
                        try:
                            joystick, button_map, directional_axis_pairs = open_controller(0)
                            active_instance_id = joystick.get_instance_id()
                            last_state = None
                            last_send_time = 0.0
                            print("Controller rediscovered. Mouse emulation resumed.")
                        except pygame.error:
                            joystick = None

                if joystick is None and (now - last_send_time) >= HEARTBEAT_SECONDS:
                    output.send(serial_port, MouseState())
                    last_send_time = now

                if joystick is None:
                    time.sleep(0.005)
                    continue

            try:
                decrease_pressed, increase_pressed = read_sensitivity_controls(
                    joystick,
                    button_map,
                )

                decrease_edge = decrease_pressed and not previous_decrease
                increase_edge = increase_pressed and not previous_increase

                if decrease_edge and not increase_edge:
                    old_sensitivity = sensitivity
                    sensitivity = max(SENSITIVITY_VERY_LOW, sensitivity - 1)
                    if sensitivity != old_sensitivity:
                        print(
                            f"Sensitivity: {SENSITIVITY_NAMES[old_sensitivity]} "
                            f"-> {SENSITIVITY_NAMES[sensitivity]}"
                        )
                    else:
                        print("Sensitivity already at VERY LOW.")

                elif increase_edge and not decrease_edge:
                    old_sensitivity = sensitivity
                    sensitivity = min(SENSITIVITY_VERY_HIGH, sensitivity + 1)
                    if sensitivity != old_sensitivity:
                        print(
                            f"Sensitivity: {SENSITIVITY_NAMES[old_sensitivity]} "
                            f"-> {SENSITIVITY_NAMES[sensitivity]}"
                        )
                    else:
                        print("Sensitivity already at VERY HIGH.")

                previous_decrease = decrease_pressed
                previous_increase = increase_pressed

                state, analog_speed, digital_speed = build_mouse_state(
                    joystick,
                    button_map,
                    directional_axis_pairs,
                    max_speed,
                    dpad_speed,
                    sensitivity,
                )
            except pygame.error:
                print(
                    "Controller vanished during sampling. "
                    f"Sending neutral {output.name} state and waiting..."
                )
                output.send_neutral(serial_port)

                try:
                    joystick.quit()
                except pygame.error:
                    pass

                joystick = None
                button_map = None
                directional_axis_pairs = ()
                active_instance_id = None
                previous_decrease = False
                previous_increase = False
                last_state = MouseState()
                last_send_time = time.monotonic()
                last_reconnect_poll = 0.0
                continue

            now = time.monotonic()
            if state != last_state or (now - last_send_time) >= HEARTBEAT_SECONDS:
                logical_report, wire_word, packet = output.send(serial_port, state)
                last_send_time = now
            else:
                logical_report = None
                wire_word = None
                packet = None

            if state != last_state:
                packet_hex = " ".join(f"{byte:02X}" for byte in packet)
                print(
                    f"Mouse dx={state.dx:+d} dy={state.dy:+d} "
                    f"L={int(state.left)} R={int(state.right)} "
                    f"bridge-sens={SENSITIVITY_NAMES[sensitivity]}"
                    f"({sensitivity}) speed={analog_speed}/{digital_speed} "
                    f"report=0x{logical_report:08X} "
                    f"wire=0x{wire_word:08X} TX={packet_hex}"
                )
                last_state = state

            time.sleep(0.001)

    except KeyboardInterrupt:
        print(f"\nCtrl+C received. Releasing {output.name} state...")

    except serial.SerialTimeoutException:
        print("\nSerial write timed out. Releasing mouse bridge.")

    except (serial.SerialException, RuntimeError) as err:
        print(f"Mouse bridge error: {err}")

    finally:
        if serial_port is not None:
            try:
                output.send_neutral(serial_port)
            except (serial.SerialException, serial.SerialTimeoutException):
                pass
            try:
                serial_port.close()
            except serial.SerialException:
                pass

        pygame.quit()
        print("Mouse bridge stopped.")


def run_mouse_bridge(
    serial_port_override=None,
    output_personality="snes",
    max_speed=MOUSE_ANALOG_MAX_DELTA,
    dpad_speed=MOUSE_DPAD_DELTA,
):
    """Backward-compatible name for the gamepad mouse-emulation source."""
    return run_gamepad_mouse_bridge(
        serial_port_override=serial_port_override,
        output_personality=output_personality,
        max_speed=max_speed,
        dpad_speed=dpad_speed,
    )


def run_physical_mouse_bridge(
    serial_port_override=None,
    output_personality="snes",
):
    """Translate the PC's physical mouse into a console mouse personality."""
    serial_port = None
    source = PhysicalMouseSource()
    output = create_output_personality(output_personality)

    try:
        source.start()

        serial_device = resolve_serial_port(serial_port_override)
        serial_port = serial.Serial(
            serial_device,
            BAUD_RATE,
            timeout=0,
            write_timeout=0.100,
        )

        print(
            f"Physical mouse -> {output.name} streaming to {serial_device}. "
            "Press ESC in the capture window or Ctrl+C to exit."
        )
        print(
            "Mapping: physical mouse motion -> relative console mouse motion; "
            "left button -> MouseLeft; right button -> MouseRight."
        )
        print(
            f"Physical mouse report cadence: {PHYSICAL_MOUSE_REPORT_HZ:.0f} Hz. "
            "Mouse deltas are accumulated between reports."
        )

        accumulated_dx = 0
        accumulated_dy = 0
        current_left = False
        current_right = False
        latched_left = False
        latched_right = False
        last_report_time = time.monotonic()

        while True:
            sample, stop_requested = source.poll()
            if stop_requested:
                break

            accumulated_dx += sample.dx
            accumulated_dy += sample.dy
            current_left = sample.left
            current_right = sample.right

            # Preserve short clicks that begin and end between two 60 Hz
            # console reports. Held buttons remain asserted every report.
            latched_left = latched_left or current_left
            latched_right = latched_right or current_right

            now = time.monotonic()
            if (now - last_report_time) < PHYSICAL_MOUSE_REPORT_SECONDS:
                time.sleep(0.001)
                continue

            state = MouseState(
                dx=max(-127, min(127, accumulated_dx)),
                dy=max(-127, min(127, accumulated_dy)),
                left=latched_left,
                right=latched_right,
            )

            logical_report, wire_word, packet = output.send(serial_port, state)
            packet_hex = " ".join(f"{byte:02X}" for byte in packet)

            if state.dx or state.dy or state.left or state.right:
                print(
                    f"Mouse dx={state.dx:+d} dy={state.dy:+d} "
                    f"L={int(state.left)} R={int(state.right)} "
                    f"report=0x{logical_report:08X} "
                    f"wire=0x{wire_word:08X} TX={packet_hex}"
                )

            accumulated_dx = 0
            accumulated_dy = 0
            latched_left = current_left
            latched_right = current_right
            last_report_time = now

            time.sleep(0.001)

    except KeyboardInterrupt:
        print(f"\nCtrl+C received. Releasing {output.name} state...")

    except serial.SerialTimeoutException:
        print("\nSerial write timed out. Releasing physical mouse bridge.")

    except (serial.SerialException, RuntimeError, pygame.error) as err:
        print(f"Physical mouse bridge error: {err}")

    finally:
        if serial_port is not None:
            try:
                output.send_neutral(serial_port)
            except (serial.SerialException, serial.SerialTimeoutException):
                pass
            try:
                serial_port.close()
            except serial.SerialException:
                pass

        source.stop()
        pygame.quit()
        print("Physical mouse bridge stopped.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Translate a connected input device into a console mouse personality."
    )
    parser.add_argument(
        "serial_port",
        nargs="?",
        metavar="COM_PORT",
        help=(
            "Optional Pico serial port override, for example COM3. "
            "If omitted, the active Pico is auto-detected."
        ),
    )
    parser.add_argument(
        "--port",
        dest="port_override",
        metavar="COM_PORT",
        help="Explicit Pico serial port override (same as positional COM_PORT).",
    )
    parser.add_argument(
        "--output",
        default="snes",
        choices=("snes",),
        help="Console mouse output personality (currently: snes).",
    )
    parser.add_argument(
        "--source",
        default="gamepad",
        choices=("gamepad", "mouse"),
        help=(
            "Input source for MouseState: gamepad for controller/arcade-stick "
            "emulation, or mouse for the PC's physical mouse."
        ),
    )
    parser.add_argument(
        "--max-speed",
        type=int,
        default=MOUSE_ANALOG_MAX_DELTA,
        metavar="1..32",
        help="Base maximum analog displacement (default: 8).",
    )
    parser.add_argument(
        "--dpad-speed",
        type=int,
        default=MOUSE_DPAD_DELTA,
        metavar="1..32",
        help="Base D-pad displacement (default: 4).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if (
        args.serial_port
        and args.port_override
        and args.serial_port.casefold() != args.port_override.casefold()
    ):
        raise RuntimeError(
            "Conflicting serial ports supplied: "
            f"{args.serial_port} and {args.port_override}"
        )

    serial_device = args.port_override or args.serial_port

    if args.source == "mouse":
        run_physical_mouse_bridge(
            serial_port_override=serial_device,
            output_personality=args.output,
        )
    else:
        run_gamepad_mouse_bridge(
            serial_port_override=serial_device,
            output_personality=args.output,
            max_speed=args.max_speed,
            dpad_speed=args.dpad_speed,
        )


if __name__ == "__main__":
    main()
