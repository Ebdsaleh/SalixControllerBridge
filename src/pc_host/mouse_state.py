# src/pc_host/mouse_state.py

from dataclasses import dataclass


@dataclass(frozen=True)
class MouseState:
    """Console-independent relative mouse state shared by every source/output."""

    dx: int = 0
    dy: int = 0
    left: bool = False
    right: bool = False
