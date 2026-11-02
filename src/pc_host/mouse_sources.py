# src/pc_host/mouse_sources.py

import sys

import pygame

from mouse_state import MouseState


class PhysicalMouseSource:
    """Capture a PC mouse and expose console-independent relative MouseState."""

    WINDOW_SIZE = (480, 120)

    def __init__(self):
        self._screen = None
        self._started = False
        self._raw_capture = None
        self._source_mode = "SDL relative mouse"

    @property
    def source_mode(self):
        return self._source_mode

    def start(self):
        pygame.init()
        pygame.display.init()

        self._screen = pygame.display.set_mode(self.WINDOW_SIZE)
        pygame.display.set_caption(
            "SalixControllerBridge - Mouse Capture (ESC to release)"
        )

        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)

        # Prefer the same unaccelerated Win32 Raw Input stream used by the
        # calibration utility. This makes a calibrated profile meaningful at
        # runtime and more closely matches the final standalone USB-HID host.
        if sys.platform == "win32":
            try:
                from windows_raw_mouse import WindowsRawMouseCapture

                hwnd = pygame.display.get_wm_info().get("window")
                if not hwnd:
                    raise RuntimeError(
                        "SDL did not expose a Windows capture HWND."
                    )

                self._raw_capture = WindowsRawMouseCapture()
                self._raw_capture.start(hwnd)
                self._source_mode = "Windows Raw Input"
            except Exception as exc:
                self._raw_capture = None
                self._source_mode = (
                    "SDL relative mouse fallback "
                    f"(Raw Input unavailable: {exc})"
                )

        # Clear motion accumulated before capture began. This remains useful
        # for the SDL fallback and for Pygame's button state.
        pygame.event.pump()
        pygame.mouse.get_rel()
        if self._raw_capture is not None:
            self._raw_capture.reset()

        self._started = True

    def poll(self):
        """Return (MouseState, stop_requested, button_down_events)."""
        if not self._started:
            raise RuntimeError("PhysicalMouseSource.start() was not called.")

        stop_requested = False
        button_down_events = []

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_requested = True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                stop_requested = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                button_down_events.append(int(event.button))

        if self._raw_capture is not None:
            snapshot = self._raw_capture.snapshot(reset=True)
            dx = int(snapshot["dx"])
            dy = int(snapshot["dy"])

            # Drain Pygame's relative accumulator too so a future fallback
            # never replays movement captured while Raw Input was active.
            pygame.mouse.get_rel()
        else:
            dx, dy = pygame.mouse.get_rel()

        buttons = pygame.mouse.get_pressed(3)

        return (
            MouseState(
                dx=int(dx),
                dy=int(dy),
                left=bool(buttons[0]),
                right=bool(buttons[2]),
            ),
            stop_requested,
            tuple(button_down_events),
        )

    def stop(self):
        if not self._started:
            return

        if self._raw_capture is not None:
            try:
                self._raw_capture.stop()
            finally:
                self._raw_capture = None

        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)
        pygame.display.quit()
        self._started = False
