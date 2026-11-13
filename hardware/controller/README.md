# Salix controller concepts

This directory intentionally parks two future Salix USB-controller concepts while the main SalixControllerBridge motherboard remains the active hardware priority.

## Projects

- `screen_pro/` — modern ergonomic dual-stick controller with a central TF034 2.4-inch touchscreen and VMU-oriented storage/UI.
- `saturn_hybrid/` — Saturn-inspired wide controller with D-pad emphasis, the shared four-button Salix Greek action cluster, modern analog sticks/haptics and the same central touchscreen/VMU architecture.
- `common/` — shared concept-stage KiCad symbol library and display notes.

Both controller concepts use the same Salix primary face-action symbols:

- **Π** = left
- **Ω** = top
- **Φ** = right
- **Α** = bottom / primary confirm position

These are **not fabrication-ready PCBs**. They are deliberately small feasibility projects intended to preserve architecture and layout intent for later.

The two controller projects share the same electronics concept wherever practical so a future firmware stack, VMU protocol and hardware validation effort can be reused across both shells.
