"""Shared Pico serial-port discovery for the PC-side bridge tools."""

from serial.tools import list_ports


PICO_USB_VID = 0x2E8A
PICO_TEXT_HINTS = (
    "raspberry pi",
    "pico",
    "rp2040",
    "rp2350",
    "micropython",
    "board in fs mode",
)


def _port_description(port):
    description = getattr(port, "description", None) or "no description"
    return f"{port.device} ({description})"


def _looks_like_pico(port):
    if getattr(port, "vid", None) == PICO_USB_VID:
        return True

    fields = (
        getattr(port, "device", None),
        getattr(port, "description", None),
        getattr(port, "manufacturer", None),
        getattr(port, "product", None),
        getattr(port, "hwid", None),
    )
    text = " ".join(str(value) for value in fields if value).casefold()
    return any(hint in text for hint in PICO_TEXT_HINTS)


def resolve_serial_port(requested=None):
    """Return the selected serial device name without guessing when ambiguous."""
    ports = sorted(list(list_ports.comports()), key=lambda port: port.device.casefold())

    if requested:
        requested = requested.strip()
        for port in ports:
            if port.device.casefold() == requested.casefold():
                print(f"Using requested Pico serial port: {_port_description(port)}")
                return port.device

        available = ", ".join(_port_description(port) for port in ports) or "none"
        raise RuntimeError(
            f"Requested serial port {requested!r} was not found. "
            f"Available serial ports: {available}"
        )

    pico_ports = [port for port in ports if _looks_like_pico(port)]

    if len(pico_ports) == 1:
        port = pico_ports[0]
        print(f"Auto-detected Pico serial port: {_port_description(port)}")
        return port.device

    if len(pico_ports) > 1:
        choices = ", ".join(_port_description(port) for port in pico_ports)
        raise RuntimeError(
            "Multiple likely Pico serial ports were detected: "
            f"{choices}. Specify one explicitly, for example: python bridge.py COM4"
        )

    if len(ports) == 1:
        port = ports[0]
        print(
            "No Pico-specific USB metadata was found; "
            f"using the only available serial port: {_port_description(port)}"
        )
        return port.device

    if not ports:
        raise RuntimeError(
            "No serial ports were detected. Connect the Pico and try again, "
            "or specify its COM port explicitly."
        )

    choices = ", ".join(_port_description(port) for port in ports)
    raise RuntimeError(
        "Multiple serial ports are present and no Pico can be identified uniquely: "
        f"{choices}. Specify one explicitly, for example: python bridge.py COM4"
    )
