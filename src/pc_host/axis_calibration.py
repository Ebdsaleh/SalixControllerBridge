# src/pc_host/axis_calibration.py

"""Backend-neutral analog-axis normalization helpers."""


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def normalize_axis(value, calibration=None):
    """Recenter/rescale one raw joystick axis to the canonical -1..+1 range."""
    value = float(value)
    if not calibration:
        return clamp(value, -1.0, 1.0)

    center = float(calibration.get("center", 0.0))
    minimum = float(calibration.get("minimum", -1.0))
    maximum = float(calibration.get("maximum", 1.0))

    if value >= center:
        span = max(0.001, maximum - center)
        normalized = (value - center) / span
    else:
        span = max(0.001, center - minimum)
        normalized = (value - center) / span

    return clamp(normalized, -1.0, 1.0)


def apply_deadzone(value, deadzone):
    """Apply a radial-component style deadzone while preserving full-scale 1.0."""
    value = float(value)
    deadzone = clamp(float(deadzone), 0.0, 0.95)

    magnitude = abs(value)
    if magnitude <= deadzone:
        return 0.0

    scaled = (magnitude - deadzone) / (1.0 - deadzone)
    return -scaled if value < 0.0 else scaled
