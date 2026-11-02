# src/pc_host/hardware_profiles.py

"""Versioned hardware-profile storage for SalixControllerBridge."""

from __future__ import annotations

import json
import os
import re
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


PROFILE_SCHEMA_VERSION = 1

CONSOLE_ENVIRONMENTS = {
    "snes": {
        "display_name": "Super Nintendo / Super Famicom",
        "logical_width": 256,
        "logical_height": 224,
        "notes": (
            "Default low-resolution SNES active picture. Individual games can "
            "use overscan/high-resolution modes; calibration modules may "
            "override this environment later."
        ),
        "mouse": {
            "report_hz": 60.0,
            "max_throw": 28,
        },
    },
}


STATE_DIR_ENV = "SALIX_CONTROLLER_BRIDGE_STATE_DIR"


def repository_root():
    return Path(__file__).resolve().parents[2]


def state_directory():
    """Writable per-user application state, separate from the source tree."""
    override = os.environ.get(STATE_DIR_ENV)
    if override:
        return Path(override).expanduser().resolve()

    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "SalixControllerBridge"
        return Path.home() / "AppData" / "Local" / "SalixControllerBridge"

    if sys.platform == "darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "SalixControllerBridge"
        )

    xdg_state_home = os.environ.get("XDG_STATE_HOME")
    if xdg_state_home:
        return Path(xdg_state_home) / "SalixControllerBridge"
    return Path.home() / ".local" / "state" / "SalixControllerBridge"


def default_profile_directory():
    return state_directory() / "profiles" / "hardware"


def slugify(value):
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    value = value.strip("-_.")
    return value.lower() or "hardware-profile"


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def new_profile(profile_name, device_type, identity=None):
    now = utc_now_iso()
    return {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "profile_name": profile_name,
        "device_type": device_type,
        "identity": deepcopy(identity or {}),
        "host_environment": {},
        "source_calibration": {},
        "consoles": {},
        "created_utc": now,
        "updated_utc": now,
    }


def ensure_console_module(profile, console_name, module_name):
    console_name = console_name.strip().lower()
    module_name = module_name.strip().lower()

    consoles = profile.setdefault("consoles", {})
    console = consoles.setdefault(console_name, {})
    modules = console.setdefault("modules", {})
    return modules.setdefault(
        module_name,
        {
            "compatible": True,
            "calibrated": False,
        },
    )


def set_console_module(profile, console_name, module_name, values):
    module = ensure_console_module(profile, console_name, module_name)
    module.update(deepcopy(values))
    module["compatible"] = True
    module["calibrated"] = True
    profile["updated_utc"] = utc_now_iso()
    return module


def set_source_calibration(profile, source_name, values):
    profile.setdefault("source_calibration", {})[source_name] = deepcopy(values)
    profile["updated_utc"] = utc_now_iso()


def set_host_environment(profile, host_name, values):
    profile.setdefault("host_environment", {})[host_name] = deepcopy(values)
    profile["updated_utc"] = utc_now_iso()


def profile_path(profile, directory=None):
    directory = Path(directory) if directory else default_profile_directory()
    return directory / f"{slugify(profile['profile_name'])}.json"


def save_profile(profile, path=None, directory=None):
    profile = deepcopy(profile)
    profile["schema_version"] = PROFILE_SCHEMA_VERSION
    profile["updated_utc"] = utc_now_iso()

    output_path = Path(path) if path else profile_path(profile, directory)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(profile, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def load_profile(path):
    path = Path(path)
    profile = json.loads(path.read_text(encoding="utf-8"))

    schema = profile.get("schema_version")
    if schema != PROFILE_SCHEMA_VERSION:
        raise RuntimeError(
            f"Unsupported hardware profile schema {schema!r}; "
            f"expected {PROFILE_SCHEMA_VERSION}."
        )

    return profile


def merge_profile(existing, update):
    """Merge a calibration update while retaining existing console modules."""
    merged = deepcopy(existing)

    for key in (
        "profile_name",
        "device_type",
        "identity",
        "host_environment",
        "source_calibration",
    ):
        if key in update:
            if isinstance(update[key], dict) and isinstance(merged.get(key), dict):
                merged[key].update(deepcopy(update[key]))
            else:
                merged[key] = deepcopy(update[key])

    for console_name, console_data in update.get("consoles", {}).items():
        destination = merged.setdefault("consoles", {}).setdefault(
            console_name,
            {},
        )
        destination_modules = destination.setdefault("modules", {})
        for module_name, module_data in console_data.get("modules", {}).items():
            destination_modules[module_name] = deepcopy(module_data)

    merged["updated_utc"] = utc_now_iso()
    return merged


def resolve_profile_reference(reference):
    """Resolve an explicit JSON path or a profile name in the state directory."""
    if reference is None:
        return None

    raw = str(reference).strip()
    if not raw:
        return None

    candidate = Path(raw).expanduser()
    if candidate.is_file():
        return candidate.resolve()

    by_name = default_profile_directory() / f"{slugify(raw)}.json"
    if by_name.is_file():
        return by_name

    raise RuntimeError(
        f"Hardware profile not found: {reference}. "
        f"Looked for an explicit file and {by_name}."
    )


def load_profile_reference(reference):
    path = resolve_profile_reference(reference)
    if path is None:
        return None, None
    return load_profile(path), path


def get_console_module(profile, console_name, module_name):
    if not profile:
        return None

    return (
        profile.get("consoles", {})
        .get(str(console_name).strip().lower(), {})
        .get("modules", {})
        .get(str(module_name).strip().lower())
    )
