# src/pc_host/calibration_app.py

"""Salix-style DearPyGui hardware calibration/profile utility."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import dearpygui.dearpygui as dpg
import pygame

from hardware_profiles import (
    ensure_console_module,
    list_profiles,
    load_profile,
    new_profile,
    profile_path,
    save_profile,
    set_console_module,
    set_host_environment,
    set_source_calibration,
)


APP_TITLE = "Salix Controller Bridge // Hardware Profiler"
VIEWPORT_WIDTH = 1040
VIEWPORT_HEIGHT = 700


def _worker_path():
    return Path(__file__).with_name("calibration_worker.py")


def _format_json(data):
    return json.dumps(data, indent=2, sort_keys=True)


class CalibrationApp:
    def __init__(self):
        self.current_profile = None
        self.current_profile_path = None

        dpg.create_context()
        dpg.create_viewport(
            title=APP_TITLE,
            width=VIEWPORT_WIDTH,
            height=VIEWPORT_HEIGHT,
        )
        try:
            dpg.set_viewport_min_width(900)
            dpg.set_viewport_min_height(620)
        except Exception:
            pass

        self._build_theme()
        self._build_ui()
        dpg.setup_dearpygui()

    def _build_theme(self):
        with dpg.theme(tag="salix_theme"):
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 12, 10)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 5)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 7)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 3)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 4)

        dpg.bind_theme("salix_theme")

    def _build_ui(self):
        with dpg.window(
            tag="primary_window",
            no_title_bar=True,
            no_resize=True,
        ):
            with dpg.group(horizontal=True):
                dpg.add_text(
                    "SALIX // CONTROLLER BRIDGE",
                    color=(0, 255, 128),
                )
                dpg.add_spacer(width=18)
                dpg.add_text("Hardware Profiler & Calibration Utility")

            dpg.add_separator()
            dpg.add_spacer(height=4)

            with dpg.tab_bar():
                with dpg.tab(label="Profile"):
                    self._build_profile_tab()

                with dpg.tab(label="Mouse Calibration"):
                    self._build_mouse_tab()

                with dpg.tab(label="Controller Calibration"):
                    self._build_controller_tab()

                with dpg.tab(label="Profile Data"):
                    self._build_profile_data_tab()

        dpg.set_primary_window("primary_window", True)

    def _build_profile_tab(self):
        dpg.add_text(
            "One hardware profile owns the device baseline and every compatible "
            "console module calibrated for that device.",
            wrap=900,
        )
        dpg.add_spacer(height=8)

        with dpg.group(horizontal=True):
            dpg.add_text("Profile name", bullet=True)
            dpg.add_input_text(
                tag="profile_name",
                default_value="New Hardware Profile",
                width=360,
            )

        with dpg.group(horizontal=True):
            dpg.add_text("Device label", bullet=True)
            dpg.add_input_text(
                tag="device_label",
                default_value="",
                hint="e.g. Razer Naga Pro / Switch Pro / Mayflash F300",
                width=360,
            )

        with dpg.group(horizontal=True):
            dpg.add_text("Device type", bullet=True)
            dpg.add_combo(
                ("mouse", "controller"),
                default_value="mouse",
                tag="device_type",
                width=180,
            )

        dpg.add_spacer(height=8)
        dpg.add_text("Profile destination")
        dpg.add_input_text(
            tag="profile_path",
            readonly=True,
            width=-1,
        )

        with dpg.group(horizontal=True):
            dpg.add_button(label="New Profile", callback=self._new_profile)
            dpg.add_button(label="Save Profile", callback=self._save_current_profile)

        dpg.add_spacer(height=8)
        dpg.add_text("Status")
        dpg.add_text("", tag="status_text", wrap=900)

        self._new_profile()

    def _build_mouse_tab(self):
        dpg.add_text(
            "Keep the mouse in its normal daily-driver hardware setting. "
            "Salix measures that baseline rather than asking you to ruin your "
            "desktop DPI just for a console.",
            wrap=900,
        )
        dpg.add_spacer(height=8)

        with dpg.group(horizontal=True):
            dpg.add_text("Current hardware DPI (optional)")
            dpg.add_input_int(
                tag="mouse_dpi",
                default_value=0,
                min_value=0,
                min_clamped=True,
                width=150,
            )

        dpg.add_checkbox(
            label=(
                "Temporarily disable Windows pointer acceleration during "
                "the calibration test (restored automatically)"
            ),
            tag="disable_windows_acceleration",
            default_value=True,
        )

        dpg.add_spacer(height=8)
        dpg.add_text("Target console environment")
        dpg.add_combo(
            ("SNES // 256 x 224 // Mouse",),
            default_value="SNES // 256 x 224 // Mouse",
            tag="mouse_console",
            width=320,
        )

        dpg.add_spacer(height=8)
        dpg.add_button(
            label="Launch SNES Mouse Calibration",
            callback=self._run_mouse_calibration,
        )

        dpg.add_spacer(height=10)
        dpg.add_text(
            "Calibration flow:\n"
            "1. Leave the mouse at your comfortable daily-driver setting.\n"
            "2. A 256x224 SDL window opens.\n"
            "3. Teach Salix four natural full throws: right, left, down, up.\n"
            "4. Salix derives one scalar raw-count gain.\n"
            "5. Test that gain in the same SNES-sized environment.\n"
            "6. +/- adjusts by 5%; Enter accepts; Esc cancels.",
            wrap=900,
        )

        dpg.add_spacer(height=10)
        dpg.add_text("Last mouse calibration")
        dpg.add_input_text(
            tag="mouse_result",
            multiline=True,
            readonly=True,
            width=-1,
            height=210,
        )

    def _build_controller_tab(self):
        dpg.add_text(
            "Controller calibration measures the source device first: neutral "
            "center, center noise, full axis range and recommended deadzones. "
            "Console modules then consume that normalized baseline.",
            wrap=900,
        )
        dpg.add_spacer(height=8)

        dpg.add_button(
            label="Refresh Controllers",
            callback=self._refresh_controllers,
        )
        dpg.add_combo(
            (),
            tag="controller_selector",
            width=500,
        )
        self._refresh_controllers()

        dpg.add_spacer(height=8)
        dpg.add_button(
            label="Launch Controller Axis Calibration",
            callback=self._run_controller_calibration,
        )

        dpg.add_spacer(height=10)
        dpg.add_text(
            "The SDL window first measures neutral noise for 2.5 seconds, then "
            "asks you to move every analog axis through its full range. "
            "The first axis pair is provisionally treated as the primary "
            "directional pair and saved into the SNES mouse-emulation module.",
            wrap=900,
        )

        dpg.add_spacer(height=10)
        dpg.add_text("Last controller calibration")
        dpg.add_input_text(
            tag="controller_result",
            multiline=True,
            readonly=True,
            width=-1,
            height=220,
        )

    def _build_profile_data_tab(self):
        dpg.add_text(
            "This is the actual versioned hardware profile that future SNES, "
            "Saturn, Dreamcast and other console modules can share.",
            wrap=900,
        )
        dpg.add_spacer(height=8)
        dpg.add_button(
            label="Refresh JSON",
            callback=lambda: self._refresh_profile_json(),
        )
        dpg.add_input_text(
            tag="profile_json",
            multiline=True,
            readonly=True,
            width=-1,
            height=-1,
        )

    def _status(self, message):
        dpg.set_value("status_text", message)

    def _profile_name(self):
        name = str(dpg.get_value("profile_name") or "").strip()
        return name or "New Hardware Profile"

    def _device_label(self):
        return str(dpg.get_value("device_label") or "").strip()

    def _new_profile(self, sender=None, app_data=None, user_data=None):
        del sender, app_data, user_data

        name = self._profile_name()
        device_type = str(dpg.get_value("device_type") or "mouse")

        self.current_profile = new_profile(
            name,
            device_type,
            {
                "label": self._device_label(),
            },
        )
        self._seed_compatible_modules(self.current_profile, device_type)
        self.current_profile_path = profile_path(self.current_profile)

        if dpg.does_item_exist("profile_path"):
            dpg.set_value("profile_path", str(self.current_profile_path))
        self._status("New profile ready. Run a calibration or save manually.")
        self._refresh_profile_json()

    @staticmethod
    def _seed_compatible_modules(profile, device_type):
        if device_type == "mouse":
            for console, module in (
                ("snes", "mouse"),
                ("saturn", "mouse"),
                ("dreamcast", "mouse"),
            ):
                ensure_console_module(profile, console, module)
        else:
            for console, module in (
                ("snes", "pad"),
                ("snes", "mouse_emu"),
                ("saturn", "pad"),
                ("saturn", "mouse_emu"),
                ("dreamcast", "controller"),
                ("dreamcast", "mouse_emu"),
            ):
                ensure_console_module(profile, console, module)

    def _ensure_profile(self, expected_device_type):
        name = self._profile_name()
        device_type = str(dpg.get_value("device_type") or expected_device_type)

        if device_type != expected_device_type:
            dpg.set_value("device_type", expected_device_type)
            device_type = expected_device_type

        expected_path = profile_path(
            {
                "profile_name": name,
            }
        )

        if (
            self.current_profile is None
            or self.current_profile.get("profile_name") != name
            or self.current_profile.get("device_type") != device_type
        ):
            if expected_path.exists():
                self.current_profile = load_profile(expected_path)
            else:
                self.current_profile = new_profile(
                    name,
                    device_type,
                    {
                        "label": self._device_label(),
                    },
                )
                self._seed_compatible_modules(
                    self.current_profile,
                    device_type,
                )

        self.current_profile["profile_name"] = name
        self.current_profile["device_type"] = device_type
        self.current_profile.setdefault("identity", {})["label"] = (
            self._device_label()
        )
        self.current_profile_path = profile_path(self.current_profile)
        dpg.set_value("profile_path", str(self.current_profile_path))
        return self.current_profile

    def _save_current_profile(self, sender=None, app_data=None, user_data=None):
        del sender, app_data, user_data

        if self.current_profile is None:
            self._new_profile()

        self.current_profile["profile_name"] = self._profile_name()
        self.current_profile["device_type"] = str(
            dpg.get_value("device_type") or "mouse"
        )
        self.current_profile.setdefault("identity", {})["label"] = (
            self._device_label()
        )

        saved = save_profile(self.current_profile)
        self.current_profile_path = saved
        dpg.set_value("profile_path", str(saved))
        self._status(f"Profile saved: {saved}")
        self._refresh_profile_json()

    def _refresh_profile_json(self):
        if not dpg.does_item_exist("profile_json"):
            return
        dpg.set_value(
            "profile_json",
            _format_json(self.current_profile or {}),
        )

    def _run_worker(self, arguments):
        with tempfile.TemporaryDirectory(
            prefix="salix-controller-calibration-"
        ) as temp_dir:
            result_path = Path(temp_dir) / "result.json"
            command = [
                sys.executable,
                str(_worker_path()),
                *arguments,
                "--output",
                str(result_path),
            ]

            self._status(
                "Calibration window active. Complete the SDL test, then return "
                "to this utility."
            )
            completed = subprocess.run(
                command,
                cwd=str(Path(__file__).resolve().parents[2]),
                check=False,
            )

            if not result_path.exists():
                raise RuntimeError(
                    f"Calibration worker exited {completed.returncode} "
                    "without producing a result."
                )

            return json.loads(result_path.read_text(encoding="utf-8"))

    def _run_mouse_calibration(self):
        profile = self._ensure_profile("mouse")

        dpi = int(dpg.get_value("mouse_dpi") or 0)
        args = ["mouse-snes"]
        if dpi > 0:
            args.extend(("--declared-dpi", str(dpi)))
        if not bool(dpg.get_value("disable_windows_acceleration")):
            args.append("--keep-windows-acceleration")

        try:
            result = self._run_worker(args)
        except Exception as exc:
            self._status(f"Mouse calibration failed: {exc}")
            return

        dpg.set_value("mouse_result", _format_json(result))

        if result.get("status") == "cancelled":
            self._status("Mouse calibration cancelled. Profile was not changed.")
            return

        if result.get("status") != "ok":
            self._status(
                "Mouse calibration failed: "
                + str(result.get("error") or "unknown worker error")
            )
            return

        identity = result.get("identity", {})
        profile_identity = profile.setdefault("identity", {})
        profile_identity.update(
            {
                key: value
                for key, value in identity.items()
                if value is not None
            }
        )
        if self._device_label():
            profile_identity["label"] = self._device_label()

        set_host_environment(
            profile,
            "windows",
            result.get("host_environment", {}),
        )

        set_source_calibration(
            profile,
            "mouse",
            {
                "raw_input": True,
                "declared_dpi": identity.get("declared_dpi"),
                "device_path": identity.get("device_path"),
                "vid": identity.get("vid"),
                "pid": identity.get("pid"),
                "measurements": result.get("measurements", []),
                "derived": result.get("derived", {}),
            },
        )

        derived = result.get("derived", {})
        environment = result.get("environment", {})
        set_console_module(
            profile,
            "snes",
            "mouse",
            {
                "environment": environment,
                "source": "mouse",
                "gain": float(
                    derived.get("accepted_gain")
                    or derived.get("recommended_gain")
                    or 1.0
                ),
                "max_throw": int(environment.get("max_throw", 28)),
                "report_hz": float(environment.get("report_hz", 60.0)),
                "measurements": result.get("measurements", []),
                "derived": derived,
            },
        )

        saved = save_profile(profile)
        self.current_profile_path = saved
        dpg.set_value("profile_path", str(saved))
        self._status(
            "SNES mouse calibration saved. Other compatible console modules "
            "remain in this same hardware profile for future calibration."
        )
        self._refresh_profile_json()

    def _refresh_controllers(self, sender=None, app_data=None, user_data=None):
        del sender, app_data, user_data

        pygame.init()
        pygame.joystick.init()
        choices = []
        for index in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(index)
            joystick.init()
            choices.append(
                f"{index}: {joystick.get_name()} [{joystick.get_guid()}]"
            )
            joystick.quit()
        pygame.joystick.quit()
        pygame.quit()

        if not choices:
            choices = ["No controllers detected"]

        if dpg.does_item_exist("controller_selector"):
            dpg.configure_item("controller_selector", items=choices)
            dpg.set_value("controller_selector", choices[0])

    def _selected_controller_index(self):
        value = str(dpg.get_value("controller_selector") or "")
        if not value or value.startswith("No controllers"):
            raise RuntimeError("No controller is available for calibration.")

        return int(value.split(":", 1)[0])

    def _run_controller_calibration(self):
        profile = self._ensure_profile("controller")

        try:
            device_index = self._selected_controller_index()
            result = self._run_worker(
                (
                    "controller-snes",
                    "--device-index",
                    str(device_index),
                )
            )
        except Exception as exc:
            self._status(f"Controller calibration failed: {exc}")
            return

        dpg.set_value("controller_result", _format_json(result))

        if result.get("status") == "cancelled":
            self._status(
                "Controller calibration cancelled. Profile was not changed."
            )
            return

        if result.get("status") != "ok":
            self._status(
                "Controller calibration failed: "
                + str(result.get("error") or "unknown worker error")
            )
            return

        identity = result.get("identity", {})
        profile_identity = profile.setdefault("identity", {})
        profile_identity.update(identity)
        if self._device_label():
            profile_identity["label"] = self._device_label()

        source_calibration = result.get("source_calibration", {})
        set_source_calibration(
            profile,
            "controller",
            source_calibration,
        )

        console_module = result.get("console_module", {})
        mouse_emu = console_module.get("mouse_emulation", {})
        set_console_module(
            profile,
            "snes",
            "mouse_emu",
            {
                "environment": console_module.get("environment", {}),
                "source": "controller",
                "axis_pair": mouse_emu.get("axis_pair", [0, 1]),
                "deadzone": float(
                    mouse_emu.get("recommended_deadzone", 0.18)
                ),
                "axis_calibration": source_calibration.get("axes", []),
            },
        )

        saved = save_profile(profile)
        self.current_profile_path = saved
        dpg.set_value("profile_path", str(saved))
        self._status(
            "Controller source calibration saved with the SNES mouse-emulation "
            "module. Other compatible modules remain available in the same "
            "hardware profile."
        )
        self._refresh_profile_json()

    def run(self):
        dpg.show_viewport()
        try:
            while dpg.is_dearpygui_running():
                dpg.render_dearpygui_frame()
        finally:
            dpg.destroy_context()


def main():
    app = CalibrationApp()
    app.run()


if __name__ == "__main__":
    main()
