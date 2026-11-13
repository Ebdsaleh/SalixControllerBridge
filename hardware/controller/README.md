# Salix controller concepts

This directory intentionally parks two future Salix USB-controller concepts while the main SalixControllerBridge motherboard remains the active hardware priority.

## Projects

- `screen_pro/` — modern ergonomic dual-stick controller with a central TF034 2.4-inch touchscreen and VMU-oriented storage/UI.
- `saturn_hybrid/` — Saturn-inspired wide controller with D-pad emphasis, the shared four-button Salix Salix action cluster, modern analog sticks/haptics and the same central touchscreen/VMU architecture.
- `common/` — shared concept-stage KiCad symbol library and display notes.

Both controller concepts use the same Salix primary face-action symbols:

- **Salix action legends:** ا / ب / φ / π

Screen Pro default face-button diamond is now:
- **ا (Alif)** = up
- **ب (Ba)** = down
- **φ (phi)** = left
- **π (pi)** = right

Saturn-Hybrid retains the same four core symbols and adds two Saturn-only secondary symbols in the six-button cluster:
- **Σ (uppercase Sigma)** = purple upper-right secondary
- **و (Waw)** = blue lower-right tertiary, positioned after **π**
- **ا (Alif)** = yellow upper-middle, directly above **π**

Fine mechanical spacing/orientation remains subject to later ergonomic tuning.

For production shells, these face legends should be converted to **vector artwork/outlines rather than relying on a runtime font**, so the exact Arabic/Greek glyph shapes are preserved across CAD, silkscreen, engraving and mould tooling.

These are **not fabrication-ready PCBs**. They are deliberately small feasibility projects intended to preserve architecture and layout intent for later.

The two controller projects share the same electronics concept wherever practical so a future firmware stack, VMU protocol and hardware validation effort can be reused across both shells.
