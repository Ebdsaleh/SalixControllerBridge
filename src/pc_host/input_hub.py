# src/pc_host/input_hub.py

"""Logical input-slot discovery for the Salix primary USB input bank.

The current PC-host prototype can only observe SDL/Pygame controller
enumeration. It cannot yet prove which physical USB receptacle on the future
standalone Salix hardware a device occupies.

This module deliberately separates the stable Salix slot names PRIMARY-1 and
PRIMARY-2 from the temporary PC-host backend. The standalone Pico 2 W USB host
can later provide physical-port identities behind the same slot model.
"""

import pygame

PRIMARY_INPUT_SLOT_COUNT = 2
PRIMARY_INPUT_SLOT_NAMES = ("PRIMARY-1", "PRIMARY-2")


def normalize_input_slot(value):
    """Return 1/2 for a user-facing primary slot, or None for legacy auto."""
    if value is None:
        return None

    normalized = str(value).strip().casefold().replace("_", "-")
    aliases = {
        "1": 1,
        "p1": 1,
        "primary1": 1,
        "primary-1": 1,
        "usb1": 1,
        "usb-1": 1,
        "2": 2,
        "p2": 2,
        "primary2": 2,
        "primary-2": 2,
        "usb2": 2,
        "usb-2": 2,
    }

    try:
        return aliases[normalized]
    except KeyError as exc:
        raise RuntimeError(
            f"Unknown input slot: {value}. Expected PRIMARY-1 or PRIMARY-2."
        ) from exc


def input_slot_label(slot):
    if slot is None:
        return "LEGACY-AUTO"

    slot = int(slot)
    if slot < 1 or slot > PRIMARY_INPUT_SLOT_COUNT:
        raise RuntimeError(f"Primary input slot out of range: {slot}")

    return PRIMARY_INPUT_SLOT_NAMES[slot - 1]


def _read_controller_info(device_index):
    joystick = pygame.joystick.Joystick(device_index)
    joystick.init()
    try:
        return {
            "device_index": int(device_index),
            "name": joystick.get_name(),
            "guid": joystick.get_guid(),
            "buttons": joystick.get_numbuttons(),
            "hats": joystick.get_numhats(),
            "axes": joystick.get_numaxes(),
        }
    finally:
        joystick.quit()


def controller_identity(joystick):
    """Capture enough identity to avoid silently jumping to another device."""
    return {
        "name": joystick.get_name(),
        "guid": joystick.get_guid(),
        "buttons": joystick.get_numbuttons(),
        "hats": joystick.get_numhats(),
        "axes": joystick.get_numaxes(),
    }


def _identity_matches(info, identity):
    if not identity:
        return False

    return all(
        info.get(key) == identity.get(key)
        for key in ("name", "guid", "buttons", "hats", "axes")
    )


def enumerate_primary_inputs():
    """Return PRIMARY-1/2 discovery records using the current PC-host backend."""
    count = pygame.joystick.get_count()
    result = []

    for slot in range(1, PRIMARY_INPUT_SLOT_COUNT + 1):
        device_index = slot - 1
        if device_index < count:
            info = _read_controller_info(device_index)
        else:
            info = None

        result.append(
            {
                "slot": slot,
                "label": input_slot_label(slot),
                "device": info,
            }
        )

    return result


def print_primary_input_bank():
    """Print the two logical primary input slots without opening the bridge."""
    print("Salix Primary USB-A Input Bank (PC-host discovery)")
    print("------------------------------------------------")

    records = enumerate_primary_inputs()
    for record in records:
        label = record["label"]
        device = record["device"]

        if device is None:
            print(f"{label}: EMPTY")
            continue

        print(
            f"{label}: Pygame index {device['device_index']} | "
            f"{device['name']}"
        )
        print(
            f"  GUID {device['guid']} | "
            f"{device['buttons']} buttons, "
            f"{device['hats']} hats, {device['axes']} axes"
        )

    extra = max(0, pygame.joystick.get_count() - PRIMARY_INPUT_SLOT_COUNT)
    if extra:
        print(
            f"Additional Pygame controllers: {extra} "
            "(outside the current Primary bank)."
        )

    print()
    print(
        "PC-host note: PRIMARY-1/2 currently map to Pygame enumeration "
        "indices 0/1. Physical USB-receptacle identity belongs to the future "
        "standalone USB-host backend."
    )


def resolve_controller_index(slot=None):
    """Resolve an initial device index while preserving legacy controller-0."""
    count = pygame.joystick.get_count()
    if count == 0:
        raise RuntimeError("No controller detected.")

    if slot is None:
        # Existing bridge behavior: first Pygame controller wins.
        return 0

    slot = int(slot)
    desired_index = slot - 1
    if desired_index >= count:
        raise RuntimeError(
            f"{input_slot_label(slot)} is empty. "
            "Run bridge.py --list-inputs to inspect the Primary input bank."
        )

    return desired_index


def find_reconnect_index(identity, preferred_slot=None):
    """Find the previously selected controller after SDL re-enumeration.

    For an explicitly selected Primary slot, first inspect the slot's current
    Pygame index and then search the remaining controller list for the same
    device identity. This avoids silently stealing a different controller when
    indices compact after a disconnect.

    Identical duplicate controllers remain inherently ambiguous on the PC-host
    backend because Pygame does not expose our future physical socket identity.
    """
    count = pygame.joystick.get_count()
    if count == 0:
        return None

    candidates = []
    if preferred_slot is not None:
        preferred_index = int(preferred_slot) - 1
        if 0 <= preferred_index < count:
            candidates.append(preferred_index)

    candidates.extend(
        index for index in range(count)
        if index not in candidates
    )

    for device_index in candidates:
        try:
            info = _read_controller_info(device_index)
        except pygame.error:
            continue

        if _identity_matches(info, identity):
            return device_index

    return None
