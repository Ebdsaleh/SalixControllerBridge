# src/pc_host/windows_raw_mouse.py

"""Minimal Win32 Raw Input capture used by the calibration utility.

This module intentionally avoids third-party Win32 dependencies. It subclasses
an existing SDL/Pygame HWND so WM_INPUT can be observed while the normal Pygame
event loop continues to own the window.
"""

from __future__ import annotations

import ctypes
import re
import sys
import threading
from ctypes import wintypes


WM_INPUT = 0x00FF
GWLP_WNDPROC = -4

RIM_TYPEMOUSE = 0
RID_INPUT = 0x10000003
RIDI_DEVICENAME = 0x20000007

RIDEV_REMOVE = 0x00000001

HID_USAGE_PAGE_GENERIC = 0x01
HID_USAGE_GENERIC_MOUSE = 0x02

MOUSE_MOVE_ABSOLUTE = 0x0001


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = (
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND),
    )


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = (
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", wintypes.WPARAM),
    )


class _RAWMOUSE_BUTTONS(ctypes.Structure):
    _fields_ = (
        ("usButtonFlags", wintypes.USHORT),
        ("usButtonData", wintypes.USHORT),
    )


class _RAWMOUSE_BUTTON_UNION(ctypes.Union):
    _anonymous_ = ("buttons",)
    _fields_ = (
        ("ulButtons", wintypes.ULONG),
        ("buttons", _RAWMOUSE_BUTTONS),
    )


class RAWMOUSE(ctypes.Structure):
    _anonymous_ = ("button_union",)
    _fields_ = (
        ("usFlags", wintypes.USHORT),
        ("button_union", _RAWMOUSE_BUTTON_UNION),
        ("ulRawButtons", wintypes.ULONG),
        ("lLastX", wintypes.LONG),
        ("lLastY", wintypes.LONG),
        ("ulExtraInformation", wintypes.ULONG),
    )


class _RAWINPUT_DATA(ctypes.Union):
    _fields_ = (
        ("mouse", RAWMOUSE),
    )


class RAWINPUT(ctypes.Structure):
    _anonymous_ = ("data",)
    _fields_ = (
        ("header", RAWINPUTHEADER),
        ("data", _RAWINPUT_DATA),
    )


def parse_vid_pid(device_path):
    match = re.search(
        r"VID_([0-9A-Fa-f]{4}).*PID_([0-9A-Fa-f]{4})",
        device_path or "",
    )
    if not match:
        return None, None

    return match.group(1).upper(), match.group(2).upper()


class WindowsRawMouseCapture:
    """Collect unaccelerated relative mouse counts from WM_INPUT."""

    def __init__(self):
        if sys.platform != "win32":
            raise RuntimeError("Windows Raw Input is only available on Windows.")

        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._hwnd = None
        self._old_wndproc = None
        self._callback = None
        self._lock = threading.Lock()

        self._dx = 0
        self._dy = 0
        self._event_count = 0
        self._last_device = None
        self._device_names = {}

        self._configure_functions()

    def _configure_functions(self):
        self._user32.RegisterRawInputDevices.argtypes = (
            ctypes.POINTER(RAWINPUTDEVICE),
            wintypes.UINT,
            wintypes.UINT,
        )
        self._user32.RegisterRawInputDevices.restype = wintypes.BOOL

        self._user32.GetRawInputData.argtypes = (
            wintypes.HANDLE,
            wintypes.UINT,
            wintypes.LPVOID,
            ctypes.POINTER(wintypes.UINT),
            wintypes.UINT,
        )
        self._user32.GetRawInputData.restype = wintypes.UINT

        self._user32.GetRawInputDeviceInfoW.argtypes = (
            wintypes.HANDLE,
            wintypes.UINT,
            wintypes.LPVOID,
            ctypes.POINTER(wintypes.UINT),
        )
        self._user32.GetRawInputDeviceInfoW.restype = wintypes.UINT

        self._user32.CallWindowProcW.argtypes = (
            ctypes.c_void_p,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )
        self._user32.CallWindowProcW.restype = ctypes.c_ssize_t

        set_wndproc = getattr(
            self._user32,
            "SetWindowLongPtrW",
            self._user32.SetWindowLongW,
        )
        set_wndproc.argtypes = (
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_void_p,
        )
        set_wndproc.restype = ctypes.c_void_p
        self._set_wndproc = set_wndproc

    def start(self, hwnd):
        if self._hwnd is not None:
            raise RuntimeError("Raw mouse capture is already active.")

        self._hwnd = wintypes.HWND(hwnd)

        wndproc_type = ctypes.WINFUNCTYPE(
            ctypes.c_ssize_t,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )

        @wndproc_type
        def wndproc(window, message, wparam, lparam):
            if message == WM_INPUT:
                self._handle_raw_input(lparam)

            return self._user32.CallWindowProcW(
                self._old_wndproc,
                window,
                message,
                wparam,
                lparam,
            )

        self._callback = wndproc
        self._old_wndproc = self._set_wndproc(
            self._hwnd,
            GWLP_WNDPROC,
            ctypes.cast(self._callback, ctypes.c_void_p),
        )

        if not self._old_wndproc:
            error = ctypes.get_last_error()
            self._hwnd = None
            self._callback = None
            raise OSError(error, "SetWindowLongPtrW failed")

        device = RAWINPUTDEVICE(
            HID_USAGE_PAGE_GENERIC,
            HID_USAGE_GENERIC_MOUSE,
            0,
            self._hwnd,
        )

        if not self._user32.RegisterRawInputDevices(
            ctypes.byref(device),
            1,
            ctypes.sizeof(RAWINPUTDEVICE),
        ):
            error = ctypes.get_last_error()
            self.stop()
            raise OSError(error, "RegisterRawInputDevices failed")

    def stop(self):
        if self._hwnd is None:
            return

        remove_device = RAWINPUTDEVICE(
            HID_USAGE_PAGE_GENERIC,
            HID_USAGE_GENERIC_MOUSE,
            RIDEV_REMOVE,
            None,
        )
        self._user32.RegisterRawInputDevices(
            ctypes.byref(remove_device),
            1,
            ctypes.sizeof(RAWINPUTDEVICE),
        )

        if self._old_wndproc:
            self._set_wndproc(
                self._hwnd,
                GWLP_WNDPROC,
                self._old_wndproc,
            )

        self._hwnd = None
        self._old_wndproc = None
        self._callback = None

    def reset(self):
        with self._lock:
            self._dx = 0
            self._dy = 0
            self._event_count = 0

    def snapshot(self, reset=False):
        with self._lock:
            result = {
                "dx": self._dx,
                "dy": self._dy,
                "event_count": self._event_count,
                "device_path": self._device_name(self._last_device),
            }

            if reset:
                self._dx = 0
                self._dy = 0
                self._event_count = 0

        vid, pid = parse_vid_pid(result["device_path"])
        result["vid"] = vid
        result["pid"] = pid
        return result

    def _handle_raw_input(self, lparam):
        size = wintypes.UINT(0)
        header_size = ctypes.sizeof(RAWINPUTHEADER)

        result = self._user32.GetRawInputData(
            wintypes.HANDLE(lparam),
            RID_INPUT,
            None,
            ctypes.byref(size),
            header_size,
        )

        if result == 0xFFFFFFFF or size.value == 0:
            return

        buffer = ctypes.create_string_buffer(size.value)
        result = self._user32.GetRawInputData(
            wintypes.HANDLE(lparam),
            RID_INPUT,
            buffer,
            ctypes.byref(size),
            header_size,
        )

        if result == 0xFFFFFFFF:
            return

        raw = ctypes.cast(buffer, ctypes.POINTER(RAWINPUT)).contents
        if raw.header.dwType != RIM_TYPEMOUSE:
            return

        mouse = raw.mouse
        if mouse.usFlags & MOUSE_MOVE_ABSOLUTE:
            return

        with self._lock:
            self._dx += int(mouse.lLastX)
            self._dy += int(mouse.lLastY)
            self._event_count += 1
            self._last_device = raw.header.hDevice

    def _device_name(self, handle):
        if not handle:
            return None

        try:
            key = int(ctypes.cast(handle, ctypes.c_void_p).value or 0)
        except (TypeError, ValueError):
            key = int(handle or 0)
        if key in self._device_names:
            return self._device_names[key]

        size = wintypes.UINT(0)
        self._user32.GetRawInputDeviceInfoW(
            handle,
            RIDI_DEVICENAME,
            None,
            ctypes.byref(size),
        )

        if size.value == 0:
            self._device_names[key] = None
            return None

        buffer = ctypes.create_unicode_buffer(size.value)
        result = self._user32.GetRawInputDeviceInfoW(
            handle,
            RIDI_DEVICENAME,
            buffer,
            ctypes.byref(size),
        )

        if result == 0xFFFFFFFF:
            self._device_names[key] = None
            return None

        self._device_names[key] = buffer.value
        return buffer.value
