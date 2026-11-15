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
11. After clicking **Update PCB**, the PCB canvas must visibly show the imported footprint group attached to the cursor / placed on the board. If the board still shows only H1-H4, the update did not apply.
12. Place the imported footprint group temporarily in the middle of the working board area; do not individually arrange/rout yet.
13. Press **Ctrl+S** in PCB Editor and confirm the board is saved.

The next automated gate is:

```bat
py tools\render_kicad_pcb.py --expect-populated
```

The validator now prints the footprint count, fails if the board is still scaffold-only, and rejects any reference that belongs to the excluded page-07/page-07A front USB PCB.

At this stage many unrouted/unconnected-pad DRC findings are expected because the real circuit population has just been introduced. The important gate is that KiCad successfully imports the correct motherboard population and does **not** import the front-USB daughterboard population.

## Why this is interactive

KiCad 10 documents **Update PCB from Schematic** as the preferred forward-annotation workflow and performs it through the editor's F8 tool. `kicad-cli` can export schematic netlists, run ERC/DRC, and render boards, but does not expose the F8 update operation as a CLI subcommand.


## First populated-board correction cycle

The first successful F8 population proved the motherboard boundary but reported 92 pin-map errors / 72 warnings. The complete copied F8 report was used to close every error class in source.

After pulling the correction commits, **do not restore or delete the locally saved populated .kicad_pcb**. Reopen it and run F8 again with the same options so KiCad replaces the affected footprints and remaps corrected symbols.

Expected update result:
- **0 errors**;
- **4 known warnings only**, for unnetted MP mechanical mounting pads on J12/J14;
- no page-07/page-07A front-board population.

After the corrected update:
1. click Update PCB;
2. close the dialog;
3. leave the imported group as-is (do not manually arrange yet);
4. Ctrl+S;
5. run `py tools\render_kicad_pcb.py --expect-populated`.

The piled first-import placement is temporary and its overlap/clearance DRC noise is not a routing/layout failure.
