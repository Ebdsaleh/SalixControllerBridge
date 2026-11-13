#!/usr/bin/env python3
"""
Render the SalixControllerBridge KiCad schematic hierarchy to PNG files.

Default output:
    %USERPROFILE%\\Downloads\\kicad_fixes

Each PNG is named after its source .kicad_sch file:
    01_Power.kicad_sch -> 01_Power.png
    07_Front_USB_Daughterboard.kicad_sch -> 07_Front_USB_Daughterboard.png

Rendering strategy:
- Newer KiCad builds with "sch export png" use KiCad's native PNG exporter.
- KiCad 10.x builds without schematic PNG export use KiCad's PDF exporter,
  then rasterize the one-page PDF to PNG with PyMuPDF.

PyMuPDF is installed automatically into the active Python environment only if
the PDF fallback is needed and PyMuPDF is not already available.

The script also runs KiCad ERC and writes:
    %USERPROFILE%\\Downloads\\kicad_fixes\\ERC.rpt

ERC violations are captured in the report but do not abort the render/ZIP
workflow.

Typical use from the repository root:
    py tools\\render_kicad_schematics.py

Optional:
    py tools\\render_kicad_schematics.py --dpi 300
    py tools\\render_kicad_schematics.py --theme "KiCad Classic"
    py tools\\render_kicad_schematics.py --no-zip
"""

from __future__ import annotations

import argparse
import importlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


DEFAULT_RELATIVE_SCHEMATIC = Path(
    "hardware/motherboard/rev_a/SalixControllerBridge_RevA.kicad_sch"
)
DEFAULT_DPI = 300


@dataclass(frozen=True)
class SheetPage:
    page: str
    source: Path


@dataclass(frozen=True)
class RendererInfo:
    version: str
    native_png: bool


def _version_key(path: Path) -> tuple[int, ...]:
    """Return a numeric-ish key for KiCad install folders such as 10.0."""
    parts: list[int] = []
    for token in path.parts:
        if re.fullmatch(r"\d+(?:\.\d+)*", token):
            parts.extend(int(x) for x in token.split("."))
    return tuple(parts) or (0,)


def find_kicad_cli(explicit: str | None) -> Path:
    candidates: list[Path] = []

    if explicit:
        candidates.append(Path(explicit).expanduser())

    env_cli = os.environ.get("KICAD_CLI")
    if env_cli:
        candidates.append(Path(env_cli).expanduser())

    found = shutil.which("kicad-cli")
    if found:
        candidates.append(Path(found))

    if os.name == "nt":
        program_files = [
            os.environ.get("ProgramFiles"),
            os.environ.get("ProgramW6432"),
            os.environ.get("ProgramFiles(x86)"),
        ]
        for root in filter(None, program_files):
            kicad_root = Path(root) / "KiCad"
            if not kicad_root.exists():
                continue
            installs = sorted(
                (p for p in kicad_root.iterdir() if p.is_dir()),
                key=_version_key,
                reverse=True,
            )
            for install in installs:
                candidates.append(install / "bin" / "kicad-cli.exe")

    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate

        key = os.path.normcase(str(resolved))
        if key in seen:
            continue
        seen.add(key)

        if resolved.is_file():
            return resolved

    raise FileNotFoundError(
        "Could not find kicad-cli. KiCad must be installed.\n"
        "Either add kicad-cli to PATH, set KICAD_CLI, or pass "
        "--kicad-cli \"C:\\Program Files\\KiCad\\10.0\\bin\\kicad-cli.exe\"."
    )


def extract_balanced_blocks(text: str, marker: str) -> Iterable[str]:
    """Yield balanced S-expression blocks beginning at marker."""
    index = 0

    while True:
        start = text.find(marker, index)
        if start < 0:
            return

        depth = 0
        quoted = False
        escaped = False
        end = None

        for pos in range(start, len(text)):
            char = text[pos]

            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
                continue

            if char == '"':
                quoted = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    end = pos + 1
                    break

        if end is None:
            raise ValueError(f"Unbalanced KiCad S-expression near offset {start}")

        yield text[start:end]
        index = end


def discover_pages(root_schematic: Path) -> list[SheetPage]:
    """
    Discover the root and direct child sheets, preserving KiCad page numbers.

    Rev-A currently has a flat hierarchy. If a page number cannot be recovered
    from sheet_instances, appearance order is used as a safe fallback.
    """
    text = root_schematic.read_text(encoding="utf-8")

    children: list[tuple[str, Path]] = []

    # KiCad does not require a specific indentation style. Earlier versions of
    # this helper looked only for "\\n\\t(sheet\\n", which silently skipped a
    # valid child sheet if it happened to be indented with spaces. Find every
    # top-level-looking sheet expression by scanning all "(sheet" starts and
    # parsing each balanced S-expression instead.
    sheet_starts = [m.start() for m in re.finditer(r'(?m)^[ \\t]*\\(sheet\\s*
    pages = [SheetPage("1", root_schematic)]
    for fallback_index, (uuid, child) in enumerate(children, start=2):
        pages.append(SheetPage(page_map.get(uuid, str(fallback_index)), child))

    def sort_key(item: SheetPage) -> tuple[Any, ...]:
        pieces = re.split(r"([0-9]+)", item.page)
        return tuple(int(p) if p.isdigit() else p for p in pieces)

    return sorted(pages, key=sort_key)


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def run_checked(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = run_command(command)

    if result.returncode != 0:
        quoted = subprocess.list2cmdline(command)
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}:\n"
            f"{quoted}\n\n{result.stdout}"
        )

    return result


def detect_renderer(kicad_cli: Path) -> RendererInfo:
    version = run_checked([str(kicad_cli), "--version"]).stdout.strip()

    png_help = run_command([str(kicad_cli), "sch", "export", "png", "--help"])
    native_png = png_help.returncode == 0 and "--dpi" in png_help.stdout

    if not native_png:
        pdf_help = run_command([str(kicad_cli), "sch", "export", "pdf", "--help"])
        if pdf_help.returncode != 0 or "--pages" not in pdf_help.stdout:
            raise RuntimeError(
                "This KiCad CLI supports neither schematic PNG export nor the "
                "PDF fallback required by this script."
            )

    return RendererInfo(version=version, native_png=native_png)


def ensure_pymupdf() -> Any:
    """Import PyMuPDF, installing it into the active environment if necessary."""
    try:
        return importlib.import_module("pymupdf")
    except ImportError:
        print("PyMuPDF  : not installed; installing into the active Python environment...")
        install = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "pymupdf",
            ],
            check=False,
        )
        if install.returncode != 0:
            raise RuntimeError(
                "PyMuPDF is required for KiCad 10 PDF-to-PNG conversion, "
                "and automatic installation failed.\n"
                "Run this once, then retry:\n"
                f"  {sys.executable} -m pip install pymupdf"
            )

        importlib.invalidate_caches()
        try:
            return importlib.import_module("pymupdf")
        except ImportError as exc:
            raise RuntimeError(
                "PyMuPDF installation completed but Python still cannot import it."
            ) from exc


def clean_previous_outputs(output_dir: Path, zip_path: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for png in output_dir.glob("*.png"):
        if png.is_file():
            png.unlink()

    erc_path = output_dir / "ERC.rpt"
    if erc_path.exists():
        erc_path.unlink()

    if zip_path.exists():
        zip_path.unlink()


def generate_erc_report(
    kicad_cli: Path,
    root_schematic: Path,
    report_path: Path,
) -> None:
    """
    Run KiCad ERC and write a complete human-readable report.

    We intentionally do not pass --exit-code-violations. ERC findings are
    expected during development and should be captured without preventing the
    image/ZIP workflow from completing.
    """
    command = [
        str(kicad_cli),
        "sch",
        "erc",
        "--output",
        str(report_path),
        "--format",
        "report",
        "--units",
        "mm",
        "--severity-all",
        str(root_schematic),
    ]
    run_checked(command)

    if not report_path.is_file():
        raise RuntimeError(
            f"KiCad ERC reported success but did not create: {report_path}"
        )


def render_page_native_png(
    kicad_cli: Path,
    root_schematic: Path,
    sheet: SheetPage,
    destination: Path,
    dpi: int,
    theme: str | None,
    scratch: Path,
) -> None:
    page_dir = scratch / f"page_{sheet.page.replace('/', '_')}"
    page_dir.mkdir(parents=True, exist_ok=True)

    command = [
        str(kicad_cli),
        "sch",
        "export",
        "png",
        "--output",
        str(page_dir),
        "--dpi",
        str(dpi),
        "--pages",
        sheet.page,
    ]

    if theme:
        command.extend(["--theme", theme])

    command.append(str(root_schematic))
    run_checked(command)

    produced = sorted(page_dir.glob("*.png"))
    if len(produced) != 1:
        names = ", ".join(p.name for p in produced) or "<none>"
        raise RuntimeError(
            f"Expected exactly one PNG for page {sheet.page}, but found "
            f"{len(produced)}: {names}"
        )

    shutil.copy2(produced[0], destination)


def render_page_via_pdf(
    kicad_cli: Path,
    root_schematic: Path,
    sheet: SheetPage,
    destination: Path,
    dpi: int,
    theme: str | None,
    scratch: Path,
    pymupdf: Any,
) -> None:
    page_dir = scratch / f"page_{sheet.page.replace('/', '_')}"
    page_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = page_dir / "sheet.pdf"

    command = [
        str(kicad_cli),
        "sch",
        "export",
        "pdf",
        "--output",
        str(pdf_path),
        "--pages",
        sheet.page,
    ]

    if theme:
        command.extend(["--theme", theme])

    command.append(str(root_schematic))
    run_checked(command)

    if not pdf_path.is_file():
        raise RuntimeError(
            f"KiCad reported success but did not create the expected PDF: {pdf_path}"
        )

    document = pymupdf.open(str(pdf_path))
    try:
        if len(document) != 1:
            raise RuntimeError(
                f"Expected a one-page PDF for schematic page {sheet.page}, "
                f"but KiCad produced {len(document)} pages."
            )

        page = document[0]
        pixmap = page.get_pixmap(dpi=dpi, alpha=False)
        pixmap.save(str(destination))
    finally:
        document.close()


def create_zip(output_dir: Path, zip_path: Path) -> None:
    payload = sorted(output_dir.glob("*.png"))

    erc_path = output_dir / "ERC.rpt"
    if erc_path.is_file():
        payload.append(erc_path)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in payload:
            archive.write(item, arcname=item.name)


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    default_schematic = repo_root / DEFAULT_RELATIVE_SCHEMATIC

    user_profile = Path(os.environ.get("USERPROFILE", Path.home()))
    default_output = user_profile / "Downloads" / "kicad_fixes"

    parser = argparse.ArgumentParser(
        description="Render the KiCad schematic hierarchy to PNG images."
    )

    parser.add_argument(
        "schematic",
        nargs="?",
        type=Path,
        default=default_schematic,
        help=f"Root .kicad_sch file (default: {default_schematic})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help=r"Output directory (default: %USERPROFILE%\Downloads\kicad_fixes)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=DEFAULT_DPI,
        help=f"PNG render DPI (default: {DEFAULT_DPI})",
    )
    parser.add_argument(
        "--theme",
        default=None,
        help="Optional KiCad color theme. Omit to use KiCad's selected theme.",
    )
    parser.add_argument(
        "--kicad-cli",
        default=None,
        help="Explicit path to kicad-cli.exe if auto-detection fails.",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not remove existing PNGs from the output directory first.",
    )
    parser.add_argument(
        "--no-erc",
        action="store_true",
        help="Do not run KiCad ERC or create ERC.rpt.",
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Do not create Downloads\\kicad_fixes.zip after rendering.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    root_schematic = args.schematic.expanduser().resolve()
    output_dir = args.output.expanduser().resolve()
    zip_path = output_dir.parent / f"{output_dir.name}.zip"

    if not root_schematic.is_file():
        print(f"ERROR: schematic not found: {root_schematic}", file=sys.stderr)
        return 2

    if args.dpi < 72 or args.dpi > 1200:
        print("ERROR: --dpi must be between 72 and 1200.", file=sys.stderr)
        return 2

    try:
        kicad_cli = find_kicad_cli(args.kicad_cli)
        renderer = detect_renderer(kicad_cli)
        pages = discover_pages(root_schematic)

        if not pages:
            raise RuntimeError("No schematic pages were discovered.")

        missing = [p.source for p in pages if not p.source.is_file()]
        if missing:
            listing = "\n".join(f"  - {p}" for p in missing)
            raise FileNotFoundError(f"Referenced schematic sheet(s) missing:\n{listing}")

        pymupdf = None
        if not renderer.native_png:
            pymupdf = ensure_pymupdf()

        if not args.no_clean:
            clean_previous_outputs(output_dir, zip_path)
        else:
            output_dir.mkdir(parents=True, exist_ok=True)

        print(f"KiCad CLI : {kicad_cli}")
        print(f"KiCad     : {renderer.version}")
        print(
            "Renderer  : "
            + (
                "native schematic PNG"
                if renderer.native_png
                else "KiCad PDF -> PyMuPDF PNG fallback"
            )
        )
        print(f"Root      : {root_schematic}")
        print(f"Output    : {output_dir}")
        print(f"DPI       : {args.dpi}")
        print(f"Sheets    : {len(pages)}")
        print()

        with tempfile.TemporaryDirectory(prefix="salix_kicad_png_") as temp:
            scratch = Path(temp)

            for index, sheet in enumerate(pages, start=1):
                output_name = sheet.source.with_suffix(".png").name
                destination = output_dir / output_name

                print(
                    f"[{index}/{len(pages)}] page {sheet.page}: "
                    f"{sheet.source.name} -> {output_name}"
                )

                if renderer.native_png:
                    render_page_native_png(
                        kicad_cli=kicad_cli,
                        root_schematic=root_schematic,
                        sheet=sheet,
                        destination=destination,
                        dpi=args.dpi,
                        theme=args.theme,
                        scratch=scratch,
                    )
                else:
                    render_page_via_pdf(
                        kicad_cli=kicad_cli,
                        root_schematic=root_schematic,
                        sheet=sheet,
                        destination=destination,
                        dpi=args.dpi,
                        theme=args.theme,
                        scratch=scratch,
                        pymupdf=pymupdf,
                    )

        erc_path = output_dir / "ERC.rpt"
        if not args.no_erc:
            print()
            print("Running KiCad ERC...")
            generate_erc_report(
                kicad_cli=kicad_cli,
                root_schematic=root_schematic,
                report_path=erc_path,
            )
            print(f"ERC       : {erc_path}")

        if not args.no_zip:
            create_zip(output_dir, zip_path)
            print(f"ZIP       : {zip_path}")

        print()
        if args.no_erc:
            print("Done. The PNG filenames match their .kicad_sch source filenames.")
        else:
            print(
                "Done. PNGs and ERC.rpt are ready; PNG names match the schematic sources."
            )
        return 0

    except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
, text)]
    for start in sheet_starts:
        depth = 0
        quoted = False
        escaped = False
        end = None

        for pos in range(start, len(text)):
            char = text[pos]

            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\\\":
                    escaped = True
                elif char == '"':
                    quoted = False
                continue

            if char == '"':
                quoted = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    end = pos + 1
                    break

        if end is None:
            raise ValueError(f"Unbalanced sheet S-expression near offset {start}")

        block = text[start:end]
        uuid_match = re.search(r'\\(uuid\\s+"([^"]+)"\\)', block)
        file_match = re.search(r'\\(property\\s+"Sheetfile"\\s+"([^"]+)"', block)

        if not uuid_match or not file_match:
            continue

        children.append(
            (uuid_match.group(1), root_schematic.parent / file_match.group(1))
        )

    page_map: dict[str, str] = {}
    for uuid, _ in children:
        # sheet_instances paths are absolute within the root hierarchy, e.g.
        # /<root-uuid>/<sheet-uuid>. Match the child UUID at the end of path.
        match = re.search(
            rf'\\(path\\s+"[^"]*/{re.escape(uuid)}"\\s*\\(page\\s+"([^"]+)"\\)',
            text,
            flags=re.DOTALL,
        )
        if match:
            page_map[uuid] = match.group(1)

    pages = [SheetPage("1", root_schematic)]
    for fallback_index, (uuid, child) in enumerate(children, start=2):
        pages.append(SheetPage(page_map.get(uuid, str(fallback_index)), child))

    def sort_key(item: SheetPage) -> tuple[Any, ...]:
        pieces = re.split(r"([0-9]+)", item.page)
        return tuple(int(p) if p.isdigit() else p for p in pieces)

    return sorted(pages, key=sort_key)


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def run_checked(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = run_command(command)

    if result.returncode != 0:
        quoted = subprocess.list2cmdline(command)
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}:\n"
            f"{quoted}\n\n{result.stdout}"
        )

    return result


def detect_renderer(kicad_cli: Path) -> RendererInfo:
    version = run_checked([str(kicad_cli), "--version"]).stdout.strip()

    png_help = run_command([str(kicad_cli), "sch", "export", "png", "--help"])
    native_png = png_help.returncode == 0 and "--dpi" in png_help.stdout

    if not native_png:
        pdf_help = run_command([str(kicad_cli), "sch", "export", "pdf", "--help"])
        if pdf_help.returncode != 0 or "--pages" not in pdf_help.stdout:
            raise RuntimeError(
                "This KiCad CLI supports neither schematic PNG export nor the "
                "PDF fallback required by this script."
            )

    return RendererInfo(version=version, native_png=native_png)


def ensure_pymupdf() -> Any:
    """Import PyMuPDF, installing it into the active environment if necessary."""
    try:
        return importlib.import_module("pymupdf")
    except ImportError:
        print("PyMuPDF  : not installed; installing into the active Python environment...")
        install = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "pymupdf",
            ],
            check=False,
        )
        if install.returncode != 0:
            raise RuntimeError(
                "PyMuPDF is required for KiCad 10 PDF-to-PNG conversion, "
                "and automatic installation failed.\n"
                "Run this once, then retry:\n"
                f"  {sys.executable} -m pip install pymupdf"
            )

        importlib.invalidate_caches()
        try:
            return importlib.import_module("pymupdf")
        except ImportError as exc:
            raise RuntimeError(
                "PyMuPDF installation completed but Python still cannot import it."
            ) from exc


def clean_previous_outputs(output_dir: Path, zip_path: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for png in output_dir.glob("*.png"):
        if png.is_file():
            png.unlink()

    erc_path = output_dir / "ERC.rpt"
    if erc_path.exists():
        erc_path.unlink()

    if zip_path.exists():
        zip_path.unlink()


def generate_erc_report(
    kicad_cli: Path,
    root_schematic: Path,
    report_path: Path,
) -> None:
    """
    Run KiCad ERC and write a complete human-readable report.

    We intentionally do not pass --exit-code-violations. ERC findings are
    expected during development and should be captured without preventing the
    image/ZIP workflow from completing.
    """
    command = [
        str(kicad_cli),
        "sch",
        "erc",
        "--output",
        str(report_path),
        "--format",
        "report",
        "--units",
        "mm",
        "--severity-all",
        str(root_schematic),
    ]
    run_checked(command)

    if not report_path.is_file():
        raise RuntimeError(
            f"KiCad ERC reported success but did not create: {report_path}"
        )


def render_page_native_png(
    kicad_cli: Path,
    root_schematic: Path,
    sheet: SheetPage,
    destination: Path,
    dpi: int,
    theme: str | None,
    scratch: Path,
) -> None:
    page_dir = scratch / f"page_{sheet.page.replace('/', '_')}"
    page_dir.mkdir(parents=True, exist_ok=True)

    command = [
        str(kicad_cli),
        "sch",
        "export",
        "png",
        "--output",
        str(page_dir),
        "--dpi",
        str(dpi),
        "--pages",
        sheet.page,
    ]

    if theme:
        command.extend(["--theme", theme])

    command.append(str(root_schematic))
    run_checked(command)

    produced = sorted(page_dir.glob("*.png"))
    if len(produced) != 1:
        names = ", ".join(p.name for p in produced) or "<none>"
        raise RuntimeError(
            f"Expected exactly one PNG for page {sheet.page}, but found "
            f"{len(produced)}: {names}"
        )

    shutil.copy2(produced[0], destination)


def render_page_via_pdf(
    kicad_cli: Path,
    root_schematic: Path,
    sheet: SheetPage,
    destination: Path,
    dpi: int,
    theme: str | None,
    scratch: Path,
    pymupdf: Any,
) -> None:
    page_dir = scratch / f"page_{sheet.page.replace('/', '_')}"
    page_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = page_dir / "sheet.pdf"

    command = [
        str(kicad_cli),
        "sch",
        "export",
        "pdf",
        "--output",
        str(pdf_path),
        "--pages",
        sheet.page,
    ]

    if theme:
        command.extend(["--theme", theme])

    command.append(str(root_schematic))
    run_checked(command)

    if not pdf_path.is_file():
        raise RuntimeError(
            f"KiCad reported success but did not create the expected PDF: {pdf_path}"
        )

    document = pymupdf.open(str(pdf_path))
    try:
        if len(document) != 1:
            raise RuntimeError(
                f"Expected a one-page PDF for schematic page {sheet.page}, "
                f"but KiCad produced {len(document)} pages."
            )

        page = document[0]
        pixmap = page.get_pixmap(dpi=dpi, alpha=False)
        pixmap.save(str(destination))
    finally:
        document.close()


def create_zip(output_dir: Path, zip_path: Path) -> None:
    payload = sorted(output_dir.glob("*.png"))

    erc_path = output_dir / "ERC.rpt"
    if erc_path.is_file():
        payload.append(erc_path)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in payload:
            archive.write(item, arcname=item.name)


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    default_schematic = repo_root / DEFAULT_RELATIVE_SCHEMATIC

    user_profile = Path(os.environ.get("USERPROFILE", Path.home()))
    default_output = user_profile / "Downloads" / "kicad_fixes"

    parser = argparse.ArgumentParser(
        description="Render the KiCad schematic hierarchy to PNG images."
    )

    parser.add_argument(
        "schematic",
        nargs="?",
        type=Path,
        default=default_schematic,
        help=f"Root .kicad_sch file (default: {default_schematic})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help=r"Output directory (default: %USERPROFILE%\Downloads\kicad_fixes)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=DEFAULT_DPI,
        help=f"PNG render DPI (default: {DEFAULT_DPI})",
    )
    parser.add_argument(
        "--theme",
        default=None,
        help="Optional KiCad color theme. Omit to use KiCad's selected theme.",
    )
    parser.add_argument(
        "--kicad-cli",
        default=None,
        help="Explicit path to kicad-cli.exe if auto-detection fails.",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not remove existing PNGs from the output directory first.",
    )
    parser.add_argument(
        "--no-erc",
        action="store_true",
        help="Do not run KiCad ERC or create ERC.rpt.",
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Do not create Downloads\\kicad_fixes.zip after rendering.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    root_schematic = args.schematic.expanduser().resolve()
    output_dir = args.output.expanduser().resolve()
    zip_path = output_dir.parent / f"{output_dir.name}.zip"

    if not root_schematic.is_file():
        print(f"ERROR: schematic not found: {root_schematic}", file=sys.stderr)
        return 2

    if args.dpi < 72 or args.dpi > 1200:
        print("ERROR: --dpi must be between 72 and 1200.", file=sys.stderr)
        return 2

    try:
        kicad_cli = find_kicad_cli(args.kicad_cli)
        renderer = detect_renderer(kicad_cli)
        pages = discover_pages(root_schematic)

        if not pages:
            raise RuntimeError("No schematic pages were discovered.")

        missing = [p.source for p in pages if not p.source.is_file()]
        if missing:
            listing = "\n".join(f"  - {p}" for p in missing)
            raise FileNotFoundError(f"Referenced schematic sheet(s) missing:\n{listing}")

        pymupdf = None
        if not renderer.native_png:
            pymupdf = ensure_pymupdf()

        if not args.no_clean:
            clean_previous_outputs(output_dir, zip_path)
        else:
            output_dir.mkdir(parents=True, exist_ok=True)

        print(f"KiCad CLI : {kicad_cli}")
        print(f"KiCad     : {renderer.version}")
        print(
            "Renderer  : "
            + (
                "native schematic PNG"
                if renderer.native_png
                else "KiCad PDF -> PyMuPDF PNG fallback"
            )
        )
        print(f"Root      : {root_schematic}")
        print(f"Output    : {output_dir}")
        print(f"DPI       : {args.dpi}")
        print(f"Sheets    : {len(pages)}")
        print()

        with tempfile.TemporaryDirectory(prefix="salix_kicad_png_") as temp:
            scratch = Path(temp)

            for index, sheet in enumerate(pages, start=1):
                output_name = sheet.source.with_suffix(".png").name
                destination = output_dir / output_name

                print(
                    f"[{index}/{len(pages)}] page {sheet.page}: "
                    f"{sheet.source.name} -> {output_name}"
                )

                if renderer.native_png:
                    render_page_native_png(
                        kicad_cli=kicad_cli,
                        root_schematic=root_schematic,
                        sheet=sheet,
                        destination=destination,
                        dpi=args.dpi,
                        theme=args.theme,
                        scratch=scratch,
                    )
                else:
                    render_page_via_pdf(
                        kicad_cli=kicad_cli,
                        root_schematic=root_schematic,
                        sheet=sheet,
                        destination=destination,
                        dpi=args.dpi,
                        theme=args.theme,
                        scratch=scratch,
                        pymupdf=pymupdf,
                    )

        erc_path = output_dir / "ERC.rpt"
        if not args.no_erc:
            print()
            print("Running KiCad ERC...")
            generate_erc_report(
                kicad_cli=kicad_cli,
                root_schematic=root_schematic,
                report_path=erc_path,
            )
            print(f"ERC       : {erc_path}")

        if not args.no_zip:
            create_zip(output_dir, zip_path)
            print(f"ZIP       : {zip_path}")

        print()
        if args.no_erc:
            print("Done. The PNG filenames match their .kicad_sch source filenames.")
        else:
            print(
                "Done. PNGs and ERC.rpt are ready; PNG names match the schematic sources."
            )
        return 0

    except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
