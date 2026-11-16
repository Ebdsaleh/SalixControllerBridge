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
import math
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from render_kicad_schematics import find_kicad_cli


DEFAULT_RELATIVE_BOARD = Path(
    "hardware/motherboard/rev_a/SalixControllerBridge_RevA.kicad_pcb"
)
FRONT_BOARD_SHEETS = (
    "07_Front_USB_Daughterboard.kicad_sch",
    "07a_Front_USB_Presence.kicad_sch",
)

# KiCad .kicad_pcb files store placed-pad angles as absolute board angles,
# not footprint-local angles.  These references have been deliberately rotated
# during placement and are guarded because changing only the footprint-level
# angle leaves rectangular pad copper at the old orientation.
ROTATED_PLACEMENT_PAD_ANGLES = {
    "J16": 270.0,
    "J17": 180.0,
    "F1": 180.0,
    "D29": 90.0,
    "Q9": 270.0,
    "Q10": 90.0,
    "U6": 90.0,
    "C13": 180.0,
    "C12": 270.0,
    "C15": 180.0,
    "R26": 270.0,
    "R27": 270.0,
    "Q2": 180.0,
    "Q4": 180.0,
    "Q5": 180.0,
    "Q7": 180.0,
    "C9": 90.0,
    "C11": 90.0,
    "R75": 180.0,
    "R74": 180.0,
    "C76": 180.0,
    "C75": 180.0,
    "R76": 180.0,
    "C77": 180.0,
    "C78": 180.0,
    "C79": 180.0,
    "J14": 90.0,
}


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
    parser.add_argument(
        "--expect-populated",
        action="store_true",
        help=(
            "Fail if the PCB still contains only the four H1-H4 scaffold "
            "mounting holes after Update PCB from Schematic."
        ),
    )
    return parser.parse_args()


def board_references(board: Path) -> list[str]:
    text = board.read_text(encoding="utf-8")
    return re.findall(r'\(property\s+"Reference"\s+"([^"]+)"', text)


def extract_footprint_by_reference(text: str, reference: str) -> str:
    ref_match = re.search(
        rf'\(property\s+"Reference"\s+"{re.escape(reference)}"',
        text,
    )
    if not ref_match:
        raise RuntimeError(f"PCB footprint {reference} not found")

    start = text.rfind("(footprint ", 0, ref_match.start())
    if start < 0:
        raise RuntimeError(f"PCB footprint block for {reference} not found")

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]

    raise RuntimeError(f"Unbalanced PCB footprint block for {reference}")


def validate_j16_center_positive(board: Path) -> None:
    text = board.read_text(encoding="utf-8")
    footprint = extract_footprint_by_reference(text, "J16")

    expected = {
        "1": "/12V BARREL {slash} AUTOMOTIVE FRONT END/BARREL_JACK_RAW",
        "2": "GND",
    }
    actual: dict[str, str] = {}

    for pad_number in expected:
        pad_match = re.search(
            rf'\(pad\s+"{pad_number}"[\s\S]*?\(net\s+"([^"]+)"\)',
            footprint,
        )
        if not pad_match:
            raise RuntimeError(f"J16 pad {pad_number} net assignment not found")
        actual[pad_number] = pad_match.group(1)

    if actual != expected:
        raise RuntimeError(
            "J16 center-positive mapping regression: "
            f"pad1={actual.get('1')!r}, pad2={actual.get('2')!r}; "
            "expected pad1=BARREL_JACK_RAW and pad2=GND"
        )


def validate_rotated_placement_pad_angles(board: Path) -> None:
    text = board.read_text(encoding="utf-8")

    def norm(angle: float) -> float:
        value = angle % 360.0
        return 0.0 if abs(value - 360.0) < 1e-9 else value

    for reference, expected in ROTATED_PLACEMENT_PAD_ANGLES.items():
        footprint = extract_footprint_by_reference(text, reference)

        footprint_at = re.search(
            r'\n\s*\(at\s+[-+0-9.]+\s+[-+0-9.]+(?:\s+([-+0-9.]+))?\)',
            footprint,
        )
        if not footprint_at:
            raise RuntimeError(f"{reference} footprint position/rotation not found")
        footprint_angle = norm(float(footprint_at.group(1) or 0.0))
        if abs(footprint_angle - norm(expected)) > 1e-6:
            raise RuntimeError(
                f"{reference} footprint rotation regression: "
                f"{footprint_angle:g} deg; expected {expected:g} deg"
            )

        pad_angles = re.findall(
            r'\(pad\s+"[^"]*"\s+\S+\s+\S+\s+'
            r'\(at\s+[-+0-9.]+\s+[-+0-9.]+(?:\s+([-+0-9.]+))?\)',
            footprint,
        )
        if not pad_angles:
            raise RuntimeError(f"{reference} has no pads to validate")

        missing = sum(1 for angle in pad_angles if angle == "")
        wrong = [
            angle
            for angle in pad_angles
            if angle != "" and abs(norm(float(angle)) - norm(expected)) > 1e-6
        ]
        if missing or wrong:
            raise RuntimeError(
                f"{reference} absolute-pad-angle regression: "
                f"{missing} pad(s) missing angle, "
                f"{len(wrong)} pad(s) at wrong angle; "
                f"expected every placed pad at {expected:g} deg"
            )



def extract_sexpr_blocks(text: str, prefix: str) -> list[str]:
    blocks: list[str] = []
    search_from = 0

    while True:
        start = text.find(prefix, search_from)
        if start < 0:
            return blocks

        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    blocks.append(text[start:index + 1])
                    search_from = index + 1
                    break
        else:
            raise RuntimeError(f"Unbalanced PCB block beginning with {prefix!r}")


def validate_numbered_pad_centers_inside_board_outline(board: Path) -> None:
    text = board.read_text(encoding="utf-8")
    edge_rects = [
        block
        for block in extract_sexpr_blocks(text, "(gr_rect")
        if '(layer "Edge.Cuts")' in block
    ]
    if len(edge_rects) != 1:
        raise RuntimeError(
            "Rev-A mechanical validation expects exactly one rectangular "
            f"Edge.Cuts outline; found {len(edge_rects)}"
        )

    outline = edge_rects[0]
    start_match = re.search(
        r'\(start\s+([-+0-9.]+)\s+([-+0-9.]+)\)', outline
    )
    end_match = re.search(
        r'\(end\s+([-+0-9.]+)\s+([-+0-9.]+)\)', outline
    )
    if not start_match or not end_match:
        raise RuntimeError("Could not parse Rev-A rectangular Edge.Cuts outline")

    x1, y1 = map(float, start_match.groups())
    x2, y2 = map(float, end_match.groups())
    min_x, max_x = sorted((x1, x2))
    min_y, max_y = sorted((y1, y2))
    tolerance = 1e-6
    outside: list[str] = []

    for footprint in extract_sexpr_blocks(text, "(footprint "):
        reference_match = re.search(
            r'\(property\s+"Reference"\s+"([^"]+)"', footprint
        )
        footprint_at = re.search(
            r'\n\s*\(at\s+([-+0-9.]+)\s+([-+0-9.]+)'
            r'(?:\s+([-+0-9.]+))?\)',
            footprint,
        )
        if not reference_match or not footprint_at:
            continue

        reference = reference_match.group(1)
        fp_x = float(footprint_at.group(1))
        fp_y = float(footprint_at.group(2))
        fp_angle = math.radians(float(footprint_at.group(3) or 0.0))
        cos_a = math.cos(fp_angle)
        sin_a = math.sin(fp_angle)

        for pad in extract_sexpr_blocks(footprint, "(pad "):
            pad_id_match = re.match(r'\(pad\s+"([^"]*)"', pad)
            pad_at = re.search(
                r'\(at\s+([-+0-9.]+)\s+([-+0-9.]+)'
                r'(?:\s+[-+0-9.]+)?\)',
                pad,
            )
            if not pad_at:
                continue

            pad_id = pad_id_match.group(1) if pad_id_match else ""
            if not pad_id:
                # Edge-mounted connectors may intentionally use unnumbered
                # mechanical holes/tabs that straddle Edge.Cuts.
                continue

            local_x = float(pad_at.group(1))
            local_y = float(pad_at.group(2))
            # KiCad board coordinates grow downward in Y.  Positive footprint
            # rotation therefore maps local +X toward board -Y.
            board_x = fp_x + local_x * cos_a + local_y * sin_a
            board_y = fp_y - local_x * sin_a + local_y * cos_a

            if (
                board_x < min_x - tolerance
                or board_x > max_x + tolerance
                or board_y < min_y - tolerance
                or board_y > max_y + tolerance
            ):
                outside.append(
                    f"{reference} pad {pad_id} "
                    f"center=({board_x:.3f}, {board_y:.3f}) mm"
                )

    if outside:
        raise RuntimeError(
            "Numbered pad center(s) outside Rev-A Edge.Cuts outline:\n  "
            + "\n  ".join(outside)
        )


ALLOWED_ROUTING_DRC_CATEGORIES = {
    "lib_footprint_mismatch",
    "unconnected_items",
}


def validate_routing_drc_baseline(report: Path) -> None:
    text = report.read_text(encoding="utf-8", errors="replace")
    categories = re.findall(r"^\[([^\]]+)\]:", text, re.MULTILINE)
    counts: dict[str, int] = {}
    for category in categories:
        counts[category] = counts.get(category, 0) + 1

    unexpected = sorted(set(counts) - ALLOWED_ROUTING_DRC_CATEGORIES)
    if unexpected:
        details = ", ".join(
            f"{category}={counts[category]}" for category in unexpected
        )
        raise RuntimeError(
            "Unexpected PCB DRC category regression: "
            + details
            + ". Only library-instance mismatch warnings and unrouted "
              "connections are allowed during routing."
        )

    if "** Found 0 Footprint errors **" not in text:
        raise RuntimeError("PCB DRC reports one or more footprint errors")

    summary = ", ".join(
        f"{category}={counts.get(category, 0)}"
        for category in sorted(ALLOWED_ROUTING_DRC_CATEGORIES)
    )
    print(f"DRC gate  : {summary}; no unexpected categories")


def validate_inner_ground_plane(board: Path) -> None:
    text = board.read_text(encoding="utf-8")
    matches = [
        zone
        for zone in extract_sexpr_blocks(text, "(zone")
        if '(net "GND")' in zone and '(layer "In1.Cu")' in zone
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "Rev-A requires exactly one GND zone on In1.Cu; "
            f"found {len(matches)}"
        )

    zone = matches[0]
    required_corners = (
        "(xy 20.8 20.8)",
        "(xy 179.2 20.8)",
        "(xy 179.2 119.2)",
        "(xy 20.8 119.2)",
    )
    missing = [corner for corner in required_corners if corner not in zone]
    if missing:
        raise RuntimeError(
            "In1.Cu GND plane no longer matches the 0.8 mm inset outline: "
            + ", ".join(missing)
        )

def schematic_instance_references(sheet: Path) -> set[str]:
    text = sheet.read_text(encoding="utf-8")
    return set(re.findall(r'\(reference\s+"([^"]+)"\)', text))


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

        references = board_references(board)
        non_scaffold = [
            ref for ref in references if ref not in {"H1", "H2", "H3", "H4"}
        ]

        front_refs: set[str] = set()
        for name in FRONT_BOARD_SHEETS:
            sheet = board.parent / name
            if sheet.is_file():
                front_refs.update(schematic_instance_references(sheet))
        leaked_front_refs = sorted(set(references) & front_refs)

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
        print(f"Footprints: {len(references)}")
        print(f"Population: {len(non_scaffold)} non-scaffold footprint(s)")
        if leaked_front_refs:
            print(
                "ERROR: front-board references leaked onto motherboard PCB: "
                + ", ".join(leaked_front_refs),
                file=sys.stderr,
            )
            return 3
        print("Front PCB : no excluded page-07/07A references detected")

        validate_j16_center_positive(board)
        print("J16       : center-positive pad mapping verified (1=RAW, 2=GND)")

        validate_rotated_placement_pad_angles(board)
        print("Rotation  : placed-pad absolute angles verified for rotated anchors/block")
        validate_numbered_pad_centers_inside_board_outline(board)
        print("Mechanics : all numbered pad centers lie inside Edge.Cuts")
        validate_inner_ground_plane(board)
        print("Plane     : In1.Cu GND zone present with 0.8 mm board-edge inset")

        if args.expect_populated and not non_scaffold:
            print(
                "ERROR: motherboard is still scaffold-only (H1-H4). "
                "Run KiCad F8 Update PCB from Schematic, click Update PCB, "
                "close the dialog, then Ctrl+S the board before validating.",
                file=sys.stderr,
            )
            return 4

        print()

        print("Running PCB DRC...")
        run_checked([
            str(kicad_cli), "pcb", "drc",
            "--refill-zones",
            "--output", str(drc),
            "--format", "report",
            "--units", "mm",
            "--severity-all",
            str(board),
        ])
        print(f"DRC       : {drc}")
        validate_routing_drc_baseline(drc)

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
