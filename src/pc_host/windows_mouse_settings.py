# src/pc_host/windows_mouse_settings.py

"""Safe temporary access to Windows pointer settings for calibration."""

from __future__ import annotations

import ctypes
import sys
from contextlib import contextmanager
from ctypes import wintypes


SPI_GETMOUSE = 0x0003
SPI_SETMOUSE = 0x0004
SPI_GETMOUSESPEED = 0x0070


def _user32():
    if sys.platform != "win32":
        raise RuntimeError("Windows mouse settings are only available on Windows.")

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.SystemParametersInfoW.argtypes = (
        wintypes.UINT,
        wintypes.UINT,
        wintypes.LPVOID,
        wintypes.UINT,
    )
    user32.SystemParametersInfoW.restype = wintypes.BOOL
    return user32


def get_windows_mouse_settings():
    user32 = _user32()

    acceleration = (ctypes.c_int * 3)()
    if not user32.SystemParametersInfoW(
        SPI_GETMOUSE,
        0,
        ctypes.byref(acceleration),
        0,
    ):
        error = ctypes.get_last_error()
        raise OSError(error, "SPI_GETMOUSE failed")

    speed = ctypes.c_int()
    if not user32.SystemParametersInfoW(
        SPI_GETMOUSESPEED,
        0,
        ctypes.byref(speed),
        0,
    ):
        error = ctypes.get_last_error()
        raise OSError(error, "SPI_GETMOUSESPEED failed")

    return {
        "threshold_1": int(acceleration[0]),
        "threshold_2": int(acceleration[1]),
        "acceleration": int(acceleration[2]),
        "pointer_speed": int(speed.value),
    }


def set_windows_mouse_acceleration(settings):
    user32 = _user32()

    acceleration = (ctypes.c_int * 3)(
        int(settings["threshold_1"]),
        int(settings["threshold_2"]),
        int(settings["acceleration"]),
    )

    if not user32.SystemParametersInfoW(
        SPI_SETMOUSE,
        0,
        ctypes.byref(acceleration),
        0,
    ):
        error = ctypes.get_last_error()
        raise OSError(error, "SPI_SETMOUSE failed")


@contextmanager
def temporarily_disable_windows_mouse_acceleration(enabled=True):
    """Disable Windows acceleration for a calibration and restore it exactly."""
    if not enabled:
        yield None
        return

    original = get_windows_mouse_settings()
    calibration = dict(original)
    calibration["acceleration"] = 0

    set_windows_mouse_acceleration(calibration)
    try:
        yield {
            "original": original,
            "calibration": calibration,
        }
    finally:
        set_windows_mouse_acceleration(original)
