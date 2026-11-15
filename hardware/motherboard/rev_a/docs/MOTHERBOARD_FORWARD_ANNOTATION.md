# Rev-A Motherboard — First Forward Annotation

The empty motherboard PCB foundation is native-green. The next operation is KiCad's normal **Update PCB from Schematic** workflow.

## Board boundary

The system root schematic contains the universal front-USB daughterboard for system-level documentation, but those two physical-board sheets are intentionally excluded from this motherboard PCB:

- page 07 — `FRONT USB DUAL-BANK DAUGHTERBOARD`
- page 07A — `FRONT USB PRESENCE / MANAGEMENT`

Both sheet instances are serialized as `on_board no` in the motherboard project root. Do not override this during forward annotation.

## First update

1. Pull current `main`.
2. Open `hardware/motherboard/rev_a/SalixControllerBridge_RevA.kicad_pro` in KiCad 10.
3. Open PCB Editor.
4. Press **F8** / **Tools -> Update PCB from Schematic**.
5. Leave **Re-link footprints to schematic symbols based on their reference designators** unchecked.
6. Keep **Replace footprints with those specified by symbols** checked.
7. Keep **Delete footprints with no symbols** unchecked so H1-H4 remain.
8. Keep **Update footprint fields from symbols** checked.
9. Confirm the changes pane reports **0 errors**.
10. Click **Update PCB**, then **Close**.
11. Place the imported footprint group temporarily in the middle of the working board area; do not individually arrange/rout yet.
12. Save the board.

The next automated gate is:

```bat
py tools\render_kicad_pcb.py
```

At this stage many unrouted/unconnected-pad DRC findings are expected because the real circuit population has just been introduced. The important gate is that KiCad successfully imports the correct motherboard population and does **not** import the front-USB daughterboard population.

## Why this is interactive

KiCad 10 documents **Update PCB from Schematic** as the preferred forward-annotation workflow and performs it through the editor's F8 tool. `kicad-cli` can export schematic netlists, run ERC/DRC, and render boards, but does not expose the F8 update operation as a CLI subcommand.
