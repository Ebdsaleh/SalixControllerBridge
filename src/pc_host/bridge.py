# src/pc_host/bridge.py

import argparse
import sys
import time

import pygame
import serial

SERIAL_PORT = "COM3"
BAUD_RATE = 115200
HEARTBEAT_SECONDS = 0.100
RECONNECT_POLL_SECONDS = 0.050

SYNC_1 = 0xAA
SYNC_2 = 0x55
SNES_NEUTRAL_MASK = 0xFFFF

F300_DINPUT_GUID = "0300b697bc2000000155000000000000"
F300_GAMEPAD_GUID = "0300dc99790000001c18000000000000"
F300_XINPUT_GUID = "0300383c790000003218000000007200"
GAMESIR_C2_XINPUT_GUID = "030003f05e0400008e02000000007200"

SNES_TEST_BITS = {
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

# Canonical SNES layout. The physical F300 controls must produce these same
# SNES actions regardless of which USB personality the F300 exposes.
#
# SNES bits: 0=B, 1=Y, 2=Select, 3=Start, 4=Up, 5=Down,
#            6=Left, 7=Right, 8=A, 9=X, 10=L, 11=R.
#
# PS3/DINPUT mode is the known-good reference mapping and must not change.
F300_DINPUT_BUTTON_TO_SNES_BIT = {
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

# Middle "Gamepad/Controller" mode enumerates the face buttons differently.
# These four remaps normalize the physical face positions back to the exact
# same SNES actions as the known-good PS3/DINPUT profile.
F300_GAMEPAD_BUTTON_TO_SNES_BIT = {
    0: 0,    # Cross/A    -> SNES B
    1: 8,    # Circle/B   -> SNES A
    2: 11,   # R1/RB      -> SNES R
    3: 1,    # Square/X   -> SNES Y
    4: 9,    # Triangle/Y -> SNES X
    5: 11,
    6: 10,   # L1/LB      -> SNES L
    7: 10,
    9: 3,
    10: 2,
    11: 3,
}

# XInput/NS raw mapping, calibrated on Windows Server 2022 with the F300 in
# the far-left switch's top XInput/NS position. Normalize the physical controls
# back to the same canonical SNES actions as PS3/DINPUT.
F300_XINPUT_BUTTON_TO_SNES_BIT = {
    0: 0,    # A / Cross     -> SNES B
    1: 8,    # B / Circle    -> SNES A
    2: 1,    # X / Square    -> SNES Y
    3: 9,    # Y / Triangle  -> SNES X
    4: 10,   # LB / L1       -> SNES L
    5: 11,   # RB / R1       -> SNES R
    6: 2,    # Select / Back -> SNES Select
    7: 3,    # Start         -> SNES Start
    # 10 = PS/Home, intentionally unmapped.
}

# GameSir C2 XInput mapping, calibrated on Windows Server 2022. The C2
# enumerates as "Xbox 360 Controller" and exposes the same standard XInput
# face/shoulder/start/back indices as the F300 XInput profile. Home (10),
# L3 (8), R3 (9), and trigger axes 4/5 are intentionally unmapped for SNES.
GAMESIR_C2_XINPUT_BUTTON_TO_SNES_BIT = {
    0: 0,    # A / Cross      -> SNES B
    1: 8,    # B / Circle     -> SNES A
    2: 1,    # X / Square     -> SNES Y
    3: 9,    # Y / Triangle   -> SNES X
    4: 10,   # LB / L1        -> SNES L
    5: 11,   # RB / R1        -> SNES R
    6: 2,    # Share / Back   -> SNES Select
    7: 3,    # Options / Start-> SNES Start
}

# X/Y lever mode is exposed on axes 0/1 in both Gamepad/Controller and
# XInput/NS profiles. The measured polarity is:
#   axis 0: -1 left, +1 right
#   axis 1: -1 up,   +1 down
#
# In Gamepad/Controller mode axis 2 mirrors axis 1 for the vertical lever
# movement; axis 1 alone is sufficient and avoids double-counting the same
# physical direction. DPAD lever mode continues to arrive through hat 0.
F300_XY_AXIS_DEADZONE = 0.50


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--probe-inputs",
        action="store_true",
        help=(
            "Print raw button, hat and axis changes for controller calibration. "
            "COM3 is not opened and nothing is sent to the SNES."
        ),
    )
    parser.add_argument(
        "--serial-test",
        choices=tuple(SNES_TEST_BITS),
        help=(
            "Diagnostic mode: initialise Pygame/XInput normally, then ignore "
            "live input and continuously send one fixed SNES state every 5 ms."
        ),
    )
    return parser.parse_args()


def detect_controller_profile(joystick):
    guid = joystick.get_guid()
    name = joystick.get_name()
    button_count = joystick.get_numbuttons()

    if guid == F300_DINPUT_GUID or (name == "JJ" and button_count == 16):
        return (
            "PS3/DInput",
            F300_DINPUT_BUTTON_TO_SNES_BIT,
            False,
            (),
        )

    if guid == F300_GAMEPAD_GUID or (
        name == "MAYFLASH Arcade Fightstick F300" and button_count == 15
    ):
        return (
            "Gamepad/Controller",
            F300_GAMEPAD_BUTTON_TO_SNES_BIT,
            False,
            ((0, 1),),
        )

    if guid == F300_XINPUT_GUID or (
        name == "Controller (MAYFLASH Arcade Fightstick F300)"
        and button_count == 11
    ):
        return (
            "F300 XInput/NS",
            F300_XINPUT_BUTTON_TO_SNES_BIT,
            False,
            ((0, 1),),
        )

    if guid == GAMESIR_C2_XINPUT_GUID:
        return (
            "GameSir C2 XInput",
            GAMESIR_C2_XINPUT_BUTTON_TO_SNES_BIT,
            False,
            ((0, 1), (2, 3)),
        )

    return (
        "Unknown/Fallback",
        F300_DINPUT_BUTTON_TO_SNES_BIT,
        True,
        (),
    )


def open_controller(device_index):
    joystick = pygame.joystick.Joystick(device_index)
    joystick.init()

    print(f"Controller: {joystick.get_name()}")
    print(f"GUID: {joystick.get_guid()}")
    print(
        "Inputs: "
        f"{joystick.get_numbuttons()} buttons, "
        f"{joystick.get_numhats()} hats, "
        f"{joystick.get_numaxes()} axes"
    )

    profile_name, button_map, provisional, directional_axis_pairs = detect_controller_profile(joystick)
    print(f"Controller profile: {profile_name}")
    if provisional:
        print(
            "WARNING: this profile is not fully calibrated; "
            "F300 PS3/DInput remains the canonical SNES reference."
        )

    return joystick, button_map, directional_axis_pairs


def init_controller():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        raise RuntimeError("No arcade stick detected.")

    return open_controller(0)


def probe_controller_inputs(joystick):
    button_count = joystick.get_numbuttons()
    hat_count = joystick.get_numhats()
    axis_count = joystick.get_numaxes()

    last_buttons = [joystick.get_button(i) for i in range(button_count)]
    last_hats = [joystick.get_hat(i) for i in range(hat_count)]
    last_axes = [joystick.get_axis(i) for i in range(axis_count)]

    print("Raw input probe active. COM3 will NOT be opened.")
    print("Initial axes: " + ", ".join(
        f"{index}={value:+.3f}" for index, value in enumerate(last_axes)
    ))
    print("Press/move one physical control at a time. Ctrl+C to exit.")

    while True:
        pygame.event.pump()

        for index in range(button_count):
            value = joystick.get_button(index)
            if value != last_buttons[index]:
                state = "DOWN" if value else "UP"
                print(f"BUTTON {index}: {state}")
                last_buttons[index] = value

        for index in range(hat_count):
            value = joystick.get_hat(index)
            if value != last_hats[index]:
                print(f"HAT {index}: {value}")
                last_hats[index] = value

        for index in range(axis_count):
            value = joystick.get_axis(index)
            if abs(value - last_axes[index]) >= 0.20:
                print(f"AXIS {index}: {value:+.3f}")
                last_axes[index] = value

        time.sleep(0.005)


def build_snes_mask(joystick, button_map, directional_axis_pairs):
    pygame.event.pump()
    mask = SNES_NEUTRAL_MASK

    num_buttons = joystick.get_numbuttons()
    for button_index, snes_bit in button_map.items():
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

    # Some controllers can route the same physical lever to analog stick axes
    # instead of hat 0. Merge every calibrated directional axis pair into the
    # canonical SNES direction bits. F300 X/Y uses (0,1); GameSir C2 LS uses
    # (0,1) and RS uses (2,3). Inactive pairs remain centered and contribute
    # no direction.
    num_axes = joystick.get_numaxes()
    for axis_x_index, axis_y_index in directional_axis_pairs:
        if axis_x_index >= num_axes or axis_y_index >= num_axes:
            continue

        axis_x = joystick.get_axis(axis_x_index)
        axis_y = joystick.get_axis(axis_y_index)

        if axis_y <= -F300_XY_AXIS_DEADZONE:
            mask &= ~(1 << 4)
        elif axis_y >= F300_XY_AXIS_DEADZONE:
            mask &= ~(1 << 5)

        if axis_x <= -F300_XY_AXIS_DEADZONE:
            mask &= ~(1 << 6)
        elif axis_x >= F300_XY_AXIS_DEADZONE:
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

    # write() returning 4 only proves Windows accepted the bytes. Force the
    # host serial stack to drain so this diagnostic distinguishes an OS-side
    # queued write from data actually handed to the Pico's USB CDC endpoint.
    serial_port.flush()
    return packet, bytes_written, serial_port.out_waiting


def send_neutral(serial_port):
    for _ in range(5):
        send_mask(serial_port, SNES_NEUTRAL_MASK)
        time.sleep(0.005)


def main():
    args = parse_args()
    joystick = None
    serial_port = None

    try:
        joystick, button_map, directional_axis_pairs = init_controller()

        if args.probe_inputs:
            probe_controller_inputs(joystick)
            return

        serial_port = serial.Serial(
            SERIAL_PORT,
            BAUD_RATE,
            timeout=0,
            write_timeout=0.100,
        )

        if args.serial_test is not None:
            test_mask = SNES_NEUTRAL_MASK & ~(1 << SNES_TEST_BITS[args.serial_test])
            test_packet = build_packet(test_mask)
            packet_hex = " ".join(f"{byte:02X}" for byte in test_packet)
            print(
                f"Serial diagnostic: holding {args.serial_test.upper()} "
                f"mask=0x{test_mask:04X} packet={packet_hex}"
            )
            print("Pygame/XInput remains initialised. Press Ctrl+C to exit.")

            while True:
                send_mask(serial_port, test_mask)
                time.sleep(0.005)

        print(f"Bridge streaming to {SERIAL_PORT}. Press Ctrl+C to exit.")
        print("Controller USB hot-switching enabled.")

        active_instance_id = joystick.get_instance_id()
        last_mask = None
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
                        "Sending SNES neutral and waiting for controller..."
                    )
                    send_neutral(serial_port)

                    try:
                        joystick.quit()
                    except pygame.error:
                        pass

                    joystick = None
                    button_map = None
                    directional_axis_pairs = False
                    active_instance_id = None
                    last_mask = SNES_NEUTRAL_MASK
                    last_send_time = time.monotonic()
                    last_reconnect_poll = 0.0

                elif event.type == pygame.JOYDEVICEADDED and joystick is None:
                    try:
                        joystick, button_map, directional_axis_pairs = open_controller(
                            event.device_index
                        )
                        active_instance_id = joystick.get_instance_id()
                        last_mask = None
                        last_send_time = 0.0
                        print("Controller re-enumerated. Live bridge resumed.")
                    except pygame.error as err:
                        print(f"Controller re-open deferred: {err}")
                        joystick = None

            if joystick is None:
                now = time.monotonic()

                # Fallback in case Windows/SDL re-enumerates the device before
                # the hotplug event is observed. Keep COM3 open throughout.
                if (now - last_reconnect_poll) >= RECONNECT_POLL_SECONDS:
                    last_reconnect_poll = now
                    if pygame.joystick.get_count() > 0:
                        try:
                            joystick, button_map, directional_axis_pairs = open_controller(0)
                            active_instance_id = joystick.get_instance_id()
                            last_mask = None
                            last_send_time = 0.0
                            print("Controller rediscovered. Live bridge resumed.")
                        except pygame.error:
                            joystick = None

                # Keep the console-side state explicitly neutral while the USB
                # personality is between disconnect and re-enumeration.
                if (
                    joystick is None
                    and (now - last_send_time) >= HEARTBEAT_SECONDS
                ):
                    send_mask(serial_port, SNES_NEUTRAL_MASK)
                    last_send_time = now

                if joystick is None:
                    time.sleep(0.005)
                    continue

            try:
                mask = build_snes_mask(joystick, button_map, directional_axis_pairs)
            except pygame.error:
                # Defensive race handling: the physical mode switch can remove
                # the old joystick between event processing and state sampling.
                print(
                    "Controller vanished during sampling. "
                    "Sending SNES neutral and waiting for controller..."
                )
                send_neutral(serial_port)
                try:
                    joystick.quit()
                except pygame.error:
                    pass
                joystick = None
                button_map = None
                directional_axis_pairs = False
                active_instance_id = None
                last_mask = SNES_NEUTRAL_MASK
                last_send_time = time.monotonic()
                last_reconnect_poll = 0.0
                continue

            now = time.monotonic()

            # Send immediately on every state change. While held, refresh at
            # 10 Hz only. The Pico keeps the latest state between SNES polls,
            # so flooding COM3 every 5 ms is unnecessary.
            if mask != last_mask or (now - last_send_time) >= HEARTBEAT_SECONDS:
                packet, bytes_written, out_waiting = send_mask(serial_port, mask)
                last_send_time = now
            else:
                packet = None
                bytes_written = 0
                out_waiting = 0

            if mask != last_mask:
                active_bits = bin(~mask & 0x0FFF)[2:].zfill(12)
                packet_hex = " ".join(f"{byte:02X}" for byte in packet)
                print(
                    f"Mask: 0x{mask:04X} | SNES (R->B): {active_bits} "
                    f"| TX: {packet_hex} | wrote={bytes_written} "
                    f"| pending={out_waiting}"
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
