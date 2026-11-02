# src/pc_host/snes_mouse_bridge.py

"""Compatibility launcher for the generic mouse-emulation bridge.

Existing commands such as:

    py src\\pc_host\\snes_mouse_bridge.py COM3

remain valid, but the implementation now lives in mouse_bridge.py. SNES Mouse
is an output personality of that generic bridge rather than a separate input
pipeline.
"""

from mouse_bridge import main


if __name__ == "__main__":
    main()
