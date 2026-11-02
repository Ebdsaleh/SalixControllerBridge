# src/pc_host/mouse_sources.py

import pygame

from mouse_state import MouseState


class PhysicalMouseSource:
    """Capture the PC/USB mouse and expose console-independent MouseState."""

    WINDOW_SIZE = (480, 120)

    def __init__(self):
        self._screen = None
        self._started = False

    def start(self):
        pygame.init()
        pygame.display.init()

        self._screen = pygame.display.set_mode(self.WINDOW_SIZE)
        pygame.display.set_caption(
            "SalixControllerBridge - Mouse Capture (ESC to release)"
        )

        # SDL/Pygame relative motion remains usable at desktop edges when the
        # cursor is hidden and input is grabbed by the capture window.
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)

        # Clear motion accumulated before capture began.
        pygame.event.pump()
        pygame.mouse.get_rel()
        self._started = True

    def poll(self):
        """Return (MouseState, stop_requested) for the current capture sample."""
        if not self._started:
            raise RuntimeError("PhysicalMouseSource.start() was not called.")

        stop_requested = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_requested = True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                stop_requested = True

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
        )

    def stop(self):
        if not self._started:
            return

        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)
        pygame.display.quit()
        self._started = False
