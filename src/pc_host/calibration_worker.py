# src/pc_host/calibration_worker.py

"""SDL/Pygame calibration surfaces launched by the DearPyGui utility."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from pathlib import Path

import pygame

from hardware_profiles import CONSOLE_ENVIRONMENTS
from windows_mouse_settings import (
    get_windows_mouse_settings,
    temporarily_disable_windows_mouse_acceleration,
)
from windows_raw_mouse import WindowsRawMouseCapture


SNES_ENV = CONSOLE_ENVIRONMENTS["snes"]
SNES_WIDTH = int(SNES_ENV["logical_width"])
SNES_HEIGHT = int(SNES_ENV["logical_height"])
SNES_MARGIN = 16


def _write_result(path, payload):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _draw_text(surface, font, text, x, y):
    rendered = font.render(text, True, (235, 235, 235))
    surface.blit(rendered, (x, y))


def _draw_console_environment(surface, target=None, cursor=None):
    surface.fill((18, 20, 24))
    pygame.draw.rect(surface, (90, 96, 110), surface.get_rect(), 1)

    center = (SNES_WIDTH // 2, SNES_HEIGHT // 2)
    pygame.draw.line(
        surface,
        (55, 60, 70),
        (center[0], 0),
        (center[0], SNES_HEIGHT - 1),
        1,
    )
    pygame.draw.line(
        surface,
        (55, 60, 70),
        (0, center[1]),
        (SNES_WIDTH - 1, center[1]),
        1,
    )

    if target is not None:
        pygame.draw.circle(surface, (255, 210, 80), target, 7, 2)
        pygame.draw.circle(surface, (255, 210, 80), target, 2)

    if cursor is not None:
        x = max(0, min(SNES_WIDTH - 1, int(round(cursor[0]))))
        y = max(0, min(SNES_HEIGHT - 1, int(round(cursor[1]))))
        pygame.draw.line(surface, (80, 255, 150), (x - 4, y), (x + 4, y), 1)
        pygame.draw.line(surface, (80, 255, 150), (x, y - 4), (x, y + 4), 1)


def _mouse_targets():
    center = (SNES_WIDTH // 2, SNES_HEIGHT // 2)
    return (
        ("RIGHT", (SNES_WIDTH - SNES_MARGIN - 1, center[1]), "x", +1),
        ("LEFT", (SNES_MARGIN, center[1]), "x", -1),
        ("DOWN", (center[0], SNES_HEIGHT - SNES_MARGIN - 1), "y", +1),
        ("UP", (center[0], SNES_MARGIN), "y", -1),
    )


def _measurement_gain(measurements):
    center_x = SNES_WIDTH // 2
    center_y = SNES_HEIGHT // 2

    horizontal_target = max(
        1.0,
        ((SNES_WIDTH - SNES_MARGIN - 1) - center_x + center_x - SNES_MARGIN) / 2.0,
    )
    vertical_target = max(
        1.0,
        ((SNES_HEIGHT - SNES_MARGIN - 1) - center_y + center_y - SNES_MARGIN) / 2.0,
    )

    horizontal_counts = [
        abs(int(item["raw_dx"]))
        for item in measurements
        if item["axis"] == "x" and abs(int(item["raw_dx"])) > 0
    ]
    vertical_counts = [
        abs(int(item["raw_dy"]))
        for item in measurements
        if item["axis"] == "y" and abs(int(item["raw_dy"])) > 0
    ]

    if not horizontal_counts or not vertical_counts:
        raise RuntimeError(
            "Calibration did not capture enough raw X/Y movement. "
            "Repeat the point-to-point throws."
        )

    raw_horizontal = statistics.median(horizontal_counts)
    raw_vertical = statistics.median(vertical_counts)

    gain_x = horizontal_target / raw_horizontal
    gain_y = vertical_target / raw_vertical

    # A mouse should retain one scalar sensitivity so diagonal direction is not
    # distorted. Use the geometric mean of the independent axis measurements.
    recommended_gain = math.sqrt(gain_x * gain_y)

    return {
        "horizontal_target_pixels": horizontal_target,
        "vertical_target_pixels": vertical_target,
        "horizontal_raw_counts": raw_horizontal,
        "vertical_raw_counts": raw_vertical,
        "gain_x_measurement": gain_x,
        "gain_y_measurement": gain_y,
        "recommended_gain": recommended_gain,
    }


def run_snes_mouse_calibration(output_path, *, disable_acceleration, declared_dpi):
    pygame.init()
    pygame.display.init()
    pygame.font.init()

    surface = pygame.display.set_mode((SNES_WIDTH, SNES_HEIGHT))
    pygame.display.set_caption("Salix Hardware Profiler // SNES Mouse 256x224")
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

    font = pygame.font.Font(None, 15)
    small_font = pygame.font.Font(None, 13)
    clock = pygame.time.Clock()

    raw = WindowsRawMouseCapture()
    cancelled = False
    accepted_gain = None
    measurements = []

    original_settings = get_windows_mouse_settings()

    try:
        with temporarily_disable_windows_mouse_acceleration(
            enabled=disable_acceleration
        ) as settings_guard:
            calibration_settings = (
                settings_guard["calibration"]
                if settings_guard is not None
                else original_settings
            )

            pygame.event.pump()
            pygame.mouse.get_rel()

            hwnd = pygame.display.get_wm_info().get("window")
            if not hwnd:
                raise RuntimeError(
                    "Could not obtain the SDL calibration window handle."
                )

            raw.start(hwnd)

            # Intro.
            intro = True
            while intro:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        cancelled = True
                        intro = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            cancelled = True
                            intro = False
                        elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                            intro = False

                _draw_console_environment(surface)
                _draw_text(surface, font, "SNES MOUSE CALIBRATION", 10, 10)
                _draw_text(surface, small_font, "256 x 224 logical environment", 10, 30)
                _draw_text(surface, small_font, "Use your normal daily-driver DPI.", 10, 52)
                _draw_text(surface, small_font, "SPACE: begin comfortable throw test", 10, 72)
                _draw_text(surface, small_font, "ESC: cancel", 10, 90)
                pygame.display.flip()
                clock.tick(60)

            if cancelled:
                raise KeyboardInterrupt

            center = (SNES_WIDTH // 2, SNES_HEIGHT // 2)

            for direction, target, axis, sign in _mouse_targets():
                armed = False
                finished = False
                raw.reset()
                pygame.mouse.get_rel()

                while not finished:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            cancelled = True
                            finished = True
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                cancelled = True
                                finished = True
                            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                                if not armed:
                                    raw.reset()
                                    pygame.mouse.get_rel()
                                    armed = True
                                else:
                                    finished = True

                    if cancelled:
                        break

                    snapshot = raw.snapshot(reset=False)
                    _draw_console_environment(surface, target=target)
                    _draw_text(surface, font, f"FULL THROW: {direction}", 10, 8)

                    if not armed:
                        _draw_text(
                            surface,
                            small_font,
                            "Place mouse at a comfortable start.",
                            10,
                            30,
                        )
                        _draw_text(
                            surface,
                            small_font,
                            "SPACE to arm, then make ONE natural throw.",
                            10,
                            46,
                        )
                    else:
                        _draw_text(
                            surface,
                            small_font,
                            "Move naturally toward the target.",
                            10,
                            30,
                        )
                        _draw_text(
                            surface,
                            small_font,
                            "SPACE when your hand reaches a comfortable end.",
                            10,
                            46,
                        )
                        _draw_text(
                            surface,
                            small_font,
                            f"raw dx/dy: {snapshot['dx']:+d} / {snapshot['dy']:+d}",
                            10,
                            64,
                        )

                    pygame.display.flip()
                    clock.tick(120)

                if cancelled:
                    break

                snapshot = raw.snapshot(reset=False)
                measured_axis = snapshot["dx"] if axis == "x" else snapshot["dy"]

                # Reject a throw in the wrong direction rather than silently
                # creating a nonsensical profile.
                if measured_axis == 0 or (measured_axis > 0) != (sign > 0):
                    raise RuntimeError(
                        f"{direction} throw was not captured in the expected "
                        "direction. Repeat calibration."
                    )

                measurements.append(
                    {
                        "direction": direction,
                        "axis": axis,
                        "raw_dx": int(snapshot["dx"]),
                        "raw_dy": int(snapshot["dy"]),
                        "event_count": int(snapshot["event_count"]),
                    }
                )

            if cancelled:
                raise KeyboardInterrupt

            derived = _measurement_gain(measurements)
            accepted_gain = float(derived["recommended_gain"])

            # Live console-environment test. Raw counts drive the virtual
            # console cursor through the derived scalar gain. +/- adjusts by 5%.
            cursor_x = float(center[0])
            cursor_y = float(center[1])
            raw.reset()
            testing = True

            while testing:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        cancelled = True
                        testing = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            cancelled = True
                            testing = False
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            testing = False
                        elif (
                            event.unicode in ("+", "=")
                            or event.key in (pygame.K_EQUALS, pygame.K_KP_PLUS)
                        ):
                            accepted_gain *= 1.05
                        elif (
                            event.unicode == "-"
                            or event.key in (pygame.K_MINUS, pygame.K_KP_MINUS)
                        ):
                            accepted_gain /= 1.05
                        elif event.key == pygame.K_r:
                            accepted_gain = float(derived["recommended_gain"])
                            cursor_x = float(center[0])
                            cursor_y = float(center[1])
                            raw.reset()

                snapshot = raw.snapshot(reset=True)
                cursor_x += snapshot["dx"] * accepted_gain
                cursor_y += snapshot["dy"] * accepted_gain
                cursor_x = max(0.0, min(SNES_WIDTH - 1.0, cursor_x))
                cursor_y = max(0.0, min(SNES_HEIGHT - 1.0, cursor_y))

                _draw_console_environment(
                    surface,
                    cursor=(cursor_x, cursor_y),
                )
                _draw_text(surface, font, "SNES ENVIRONMENT TEST", 10, 8)
                _draw_text(
                    surface,
                    small_font,
                    f"gain: {accepted_gain:.4f}x",
                    10,
                    28,
                )
                _draw_text(
                    surface,
                    small_font,
                    "+/- adjust 5% | R reset | ENTER accept",
                    10,
                    44,
                )
                _draw_text(
                    surface,
                    small_font,
                    "Move naturally across the full 256x224 area.",
                    10,
                    60,
                )

                pygame.display.flip()
                clock.tick(120)

            if cancelled:
                raise KeyboardInterrupt

            identity = raw.snapshot(reset=False)
            device_path = identity.get("device_path")
            vid = identity.get("vid")
            pid = identity.get("pid")

            payload = {
                "status": "ok",
                "kind": "mouse",
                "console": "snes",
                "environment": {
                    "logical_width": SNES_WIDTH,
                    "logical_height": SNES_HEIGHT,
                    "target_margin": SNES_MARGIN,
                    "report_hz": float(SNES_ENV["mouse"]["report_hz"]),
                    "max_throw": int(SNES_ENV["mouse"]["max_throw"]),
                },
                "identity": {
                    "device_path": device_path,
                    "vid": vid,
                    "pid": pid,
                    "declared_dpi": declared_dpi,
                },
                "host_environment": {
                    "windows_mouse_settings_before": original_settings,
                    "windows_mouse_settings_during": calibration_settings,
                    "acceleration_temporarily_disabled": bool(
                        disable_acceleration
                    ),
                    "raw_input_used": True,
                },
                "measurements": measurements,
                "derived": {
                    **derived,
                    "accepted_gain": accepted_gain,
                },
            }
            _write_result(output_path, payload)
            return 0

    except KeyboardInterrupt:
        _write_result(
            output_path,
            {
                "status": "cancelled",
                "kind": "mouse",
                "console": "snes",
            },
        )
        return 2

    except Exception as exc:
        _write_result(
            output_path,
            {
                "status": "error",
                "kind": "mouse",
                "console": "snes",
                "error": f"{type(exc).__name__}: {exc}",
            },
        )
        return 1

    finally:
        try:
            raw.stop()
        except Exception:
            pass
        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)
        pygame.quit()


def _axis_statistics(samples, minimums, maximums):
    axes = []
    if not samples:
        return axes

    axis_count = len(samples[0])
    for index in range(axis_count):
        values = [sample[index] for sample in samples]
        center = statistics.median(values)
        noise = max(abs(value - center) for value in values)

        minimum = minimums[index]
        maximum = maximums[index]
        negative_span = max(0.001, center - minimum)
        positive_span = max(0.001, maximum - center)

        deadzone = min(0.35, max(0.05, noise * 1.75 + 0.02))

        axes.append(
            {
                "index": index,
                "center": center,
                "center_noise": noise,
                "minimum": minimum,
                "maximum": maximum,
                "negative_span": negative_span,
                "positive_span": positive_span,
                "recommended_deadzone": deadzone,
            }
        )

    return axes


def run_controller_calibration(output_path, *, device_index):
    pygame.init()
    pygame.display.init()
    pygame.joystick.init()
    pygame.font.init()

    if pygame.joystick.get_count() <= device_index:
        _write_result(
            output_path,
            {
                "status": "error",
                "kind": "controller",
                "error": f"Controller index {device_index} is not available.",
            },
        )
        pygame.quit()
        return 1

    joystick = pygame.joystick.Joystick(device_index)
    joystick.init()

    surface = pygame.display.set_mode((SNES_WIDTH, SNES_HEIGHT))
    pygame.display.set_caption("Salix Hardware Profiler // Controller Axes")
    font = pygame.font.Font(None, 15)
    small_font = pygame.font.Font(None, 13)
    clock = pygame.time.Clock()

    axis_count = joystick.get_numaxes()
    center_samples = []
    minimums = [1.0] * axis_count
    maximums = [-1.0] * axis_count

    try:
        # Center/noise capture.
        center_start = time.monotonic()
        while time.monotonic() - center_start < 2.5:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    raise KeyboardInterrupt

            pygame.event.pump()
            sample = tuple(
                float(joystick.get_axis(index))
                for index in range(axis_count)
            )
            center_samples.append(sample)

            _draw_console_environment(surface)
            _draw_text(surface, font, "CONTROLLER AXIS CALIBRATION", 10, 10)
            _draw_text(surface, small_font, "Release every stick to neutral.", 10, 32)
            _draw_text(surface, small_font, "Measuring center/noise for 2.5 sec...", 10, 48)
            pygame.display.flip()
            clock.tick(120)

        # Full-range capture.
        capturing = True
        while capturing:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        raise KeyboardInterrupt
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        capturing = False

            pygame.event.pump()
            for index in range(axis_count):
                value = float(joystick.get_axis(index))
                minimums[index] = min(minimums[index], value)
                maximums[index] = max(maximums[index], value)

            _draw_console_environment(surface)
            _draw_text(surface, font, "FULL ANALOG RANGE", 10, 10)
            _draw_text(surface, small_font, "Move every analog stick through full circles.", 10, 32)
            _draw_text(surface, small_font, "Also press analog triggers if present.", 10, 48)
            _draw_text(surface, small_font, "ENTER/SPACE when finished | ESC cancel", 10, 64)

            y = 88
            for index in range(min(axis_count, 6)):
                value = float(joystick.get_axis(index))
                _draw_text(
                    surface,
                    small_font,
                    f"axis {index}: {value:+.3f}  [{minimums[index]:+.3f}, {maximums[index]:+.3f}]",
                    10,
                    y,
                )
                y += 14

            pygame.display.flip()
            clock.tick(120)

        axes = _axis_statistics(center_samples, minimums, maximums)
        primary_pair = [0, 1] if axis_count >= 2 else []

        payload = {
            "status": "ok",
            "kind": "controller",
            "console": "snes",
            "identity": {
                "name": joystick.get_name(),
                "guid": joystick.get_guid(),
                "buttons": joystick.get_numbuttons(),
                "hats": joystick.get_numhats(),
                "axes": axis_count,
            },
            "source_calibration": {
                "axes": axes,
                "primary_directional_axis_pair": primary_pair,
                "center_sample_count": len(center_samples),
            },
            "console_module": {
                "environment": {
                    "logical_width": SNES_WIDTH,
                    "logical_height": SNES_HEIGHT,
                },
                "mouse_emulation": {
                    "axis_pair": primary_pair,
                    "recommended_deadzone": (
                        max(
                            axes[0]["recommended_deadzone"],
                            axes[1]["recommended_deadzone"],
                        )
                        if len(axes) >= 2
                        else 0.18
                    ),
                },
            },
        }
        _write_result(output_path, payload)
        return 0

    except KeyboardInterrupt:
        _write_result(
            output_path,
            {
                "status": "cancelled",
                "kind": "controller",
                "console": "snes",
            },
        )
        return 2

    except Exception as exc:
        _write_result(
            output_path,
            {
                "status": "error",
                "kind": "controller",
                "console": "snes",
                "error": f"{type(exc).__name__}: {exc}",
            },
        )
        return 1

    finally:
        try:
            joystick.quit()
        except pygame.error:
            pass
        pygame.quit()


def parse_args():
    parser = argparse.ArgumentParser(
        description="SalixControllerBridge calibration worker."
    )
    parser.add_argument(
        "kind",
        choices=("mouse-snes", "controller-snes"),
    )
    parser.add_argument(
        "--output",
        required=True,
        help="JSON result path.",
    )
    parser.add_argument(
        "--declared-dpi",
        type=int,
        default=None,
        help="Optional hardware DPI supplied by the user/profile.",
    )
    parser.add_argument(
        "--keep-windows-acceleration",
        action="store_true",
        help="Do not temporarily disable Windows pointer acceleration.",
    )
    parser.add_argument(
        "--device-index",
        type=int,
        default=0,
        help="Pygame controller index for controller calibration.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.kind == "mouse-snes":
        raise SystemExit(
            run_snes_mouse_calibration(
                args.output,
                disable_acceleration=not args.keep_windows_acceleration,
                declared_dpi=args.declared_dpi,
            )
        )

    raise SystemExit(
        run_controller_calibration(
            args.output,
            device_index=max(0, args.device_index),
        )
    )


if __name__ == "__main__":
    main()
