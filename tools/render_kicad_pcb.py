#!/usr/bin/env python3
"""Native KiCad validation helper for the Rev-A motherboard PCB.

Runs KiCad 10 PCB DRC and top/bottom 3D renders, then creates:
    %USERPROFILE%\\Downloads\\kicad_pcb_validation
    %USERPROFILE%\\Downloads\\kicad_pcb_validation.zip

This first PCB-foundation gate intentionally does NOT request schematic parity.
The board begins as an outline/mounting/stack-up scaffold; schematic footprints
will be forward-annotated in the next layout batch.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from render_kicad_schematics import find_kicad_cli


DEFAULT_RELATIVE_BOARD = Path(
    "hardware/motherboard/rev_a/SalixControllerBridge_RevA.kicad_pcb"
)


def run_checked(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}:\n"
            f"{subprocess.list2cmdline(command)}\n\n{result.stdout}"
        )
    return result


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    default_board = repo_root / DEFAULT_RELATIVE_BOARD
    user_profile = Path(os.environ.get("USERPROFILE", Path.home()))
    default_output = user_profile / "Downloads" / "kicad_pcb_validation"

    parser = argparse.ArgumentParser(
        description="Run native KiCad DRC and renders for the Rev-A motherboard PCB."
    )
    parser.add_argument("board", nargs="?", type=Path, default=default_board)
    parser.add_argument("--output", type=Path, default=default_output)
    parser.add_argument("--kicad-cli", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    board = args.board.expanduser().resolve()
    output = args.output.expanduser().resolve()
    zip_path = output.parent / f"{output.name}.zip"

    if not board.is_file():
        print(f"ERROR: board not found: {board}", file=sys.stderr)
        return 2

    try:
        kicad_cli = find_kicad_cli(args.kicad_cli)
        version = run_checked([str(kicad_cli), "--version"]).stdout.strip()

        if output.exists():
            shutil.rmtree(output)
        output.mkdir(parents=True, exist_ok=True)
        if zip_path.exists():
            zip_path.unlink()

        drc = output / "PCB_DRC.rpt"
        top = output / "motherboard_top.png"
        bottom = output / "motherboard_bottom.png"

        print(f"KiCad CLI : {kicad_cli}")
        print(f"KiCad     : {version}")
        print(f"Board     : {board}")
        print(f"Output    : {output}")
        print()

        print("Running PCB DRC...")
        run_checked([
            str(kicad_cli), "pcb", "drc",
            "--output", str(drc),
            "--format", "report",
            "--units", "mm",
            "--severity-all",
            str(board),
        ])
        print(f"DRC       : {drc}")

        print("Rendering top...")
        run_checked([
            str(kicad_cli), "pcb", "render",
            "--output", str(top),
            "--width", "1600",
            "--height", "1000",
            "--side", "top",
            str(board),
        ])
        print(f"TOP       : {top}")

        print("Rendering bottom...")
        run_checked([
            str(kicad_cli), "pcb", "render",
            "--output", str(bottom),
            "--width", "1600",
            "--height", "1000",
            "--side", "bottom",
            str(board),
        ])
        print(f"BOTTOM    : {bottom}")

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for item in (drc, top, bottom):
                zf.write(item, arcname=item.name)
        print(f"ZIP       : {zip_path}")
        print()
        print("Done. Native PCB foundation validation bundle is ready.")
        return 0

    except (FileNotFoundError, RuntimeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
