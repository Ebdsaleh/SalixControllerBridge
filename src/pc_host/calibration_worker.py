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

from axis_calibration import apply_deadzone, normalize_axis
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

# Keep the console math at the native logical resolution, but render it large
# enough to read comfortably. Instructions and live telemetry live beside the
# console surface rather than covering it.
SNES_RENDER_SCALE = 3
INSTRUCTION_PANEL_WIDTH = 420
CALIBRATION_WINDOW_WIDTH = (
    SNES_WIDTH * SNES_RENDER_SCALE
    + INSTRUCTION_PANEL_WIDTH
)
CALIBRATION_WINDOW_HEIGHT = SNES_HEIGHT * SNES_RENDER_SCALE

THROW_MIN_PRIMARY_COUNTS = 24
THROW_MAX_OFF_AXIS_RATIO = 0.45


def _write_result(path, payload):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _draw_text(surface, font, text, x, y, color=(235, 235, 235)):
    rendered = font.render(text, True, color)
    surface.blit(rendered, (x, y))


def _wrap_text(font, text, max_width):
    words = str(text).split()
    if not words:
        return [""]

    lines = []
    current = words[0]

    for word in words[1:]:
        candidate = current + " " + word
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


def _present_calibration_frame(
    window,
    console_surface,
    title_font,
    body_font,
    small_font,
    heading,
    lines,
):
    window.fill((13, 15, 19))

    scaled = pygame.transform.scale(
        console_surface,
        (
            SNES_WIDTH * SNES_RENDER_SCALE,
            SNES_HEIGHT * SNES_RENDER_SCALE,
        ),
    )
    window.blit(scaled, (0, 0))

    panel_x = SNES_WIDTH * SNES_RENDER_SCALE
    pygame.draw.line(
        window,
        (72, 78, 92),
        (panel_x, 0),
        (panel_x, CALIBRATION_WINDOW_HEIGHT),
        2,
    )

    x = panel_x + 24
    y = 24
    max_width = INSTRUCTION_PANEL_WIDTH - 48

    _draw_text(
        window,
        title_font,
        heading,
        x,
        y,
        color=(90, 255, 160),
    )
    y += 44

    for entry in lines:
        if isinstance(entry, tuple):
            text, kind = entry
        else:
            text, kind = entry, "body"

        font = small_font if kind == "small" else body_font
        color = (170, 178, 194) if kind == "small" else (235, 235, 235)

        for wrapped in _wrap_text(font, text, max_width):
            _draw_text(window, font, wrapped, x, y, color=color)
            y += font.get_linesize() + 3
        y += 7

    pygame.display.flip()


def _create_calibration_display(title):
    window = pygame.display.set_mode(
        (CALIBRATION_WINDOW_WIDTH, CALIBRATION_WINDOW_HEIGHT)
    )
    pygame.display.set_caption(title)

    console_surface = pygame.Surface((SNES_WIDTH, SNES_HEIGHT))
    title_font = pygame.font.Font(None, 34)
    body_font = pygame.font.Font(None, 26)
    small_font = pygame.font.Font(None, 21)

    return window, console_surface, title_font, body_font, small_font


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


def _validate_mouse_throw(axis, sign, snapshot):
    primary = int(snapshot["dx"] if axis == "x" else snapshot["dy"])
    secondary = int(snapshot["dy"] if axis == "x" else snapshot["dx"])

    primary_abs = abs(primary)
    secondary_abs = abs(secondary)
    ratio = (
        secondary_abs / float(primary_abs)
        if primary_abs > 0
        else float("inf")
    )

    quality = {
        "primary_counts": primary,
        "secondary_counts": secondary,
        "primary_abs": primary_abs,
        "secondary_abs": secondary_abs,
        "off_axis_ratio": ratio,
        "event_count": int(snapshot["event_count"]),
    }

    if primary == 0 or (primary > 0) != (sign > 0):
        return False, "Movement went in the wrong primary direction.", quality

    if primary_abs < THROW_MIN_PRIMARY_COUNTS:
        return (
            False,
            f"Primary throw was too small ({primary_abs} raw counts).",
            quality,
        )

    if ratio > THROW_MAX_OFF_AXIS_RATIO:
        return (
            False,
            "Too much off-axis movement "
            f"({secondary_abs} vs {primary_abs} raw counts).",
            quality,
        )

    return True, None, quality


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

    (
        window,
        console_surface,
        title_font,
        body_font,
        small_font,
    ) = _create_calibration_display(
        "Salix Hardware Profiler // SNES Mouse 256x224"
    )
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

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

                _draw_console_environment(console_surface)
                _present_calibration_frame(
                    window,
                    console_surface,
                    title_font,
                    body_font,
                    small_font,
                    "SNES MOUSE CALIBRATION",
                    (
                        "Native logical area: 256 x 224.",
                        "The test area is rendered at 3x for readability; "
                        "the calibration math still uses native SNES coordinates.",
                        "Keep the mouse at your normal daily-driver hardware setting.",
                        "SPACE / ENTER: begin the throw test.",
                        ("ESC: cancel without applying anything.", "small"),
                    ),
                )
                clock.tick(60)

            if cancelled:
                raise KeyboardInterrupt

            center = (SNES_WIDTH // 2, SNES_HEIGHT // 2)

            for direction, target, axis, sign in _mouse_targets():
                accepted = False
                attempt = 1
                rejection_reason = None

                while not accepted:
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
                                elif event.key in (
                                    pygame.K_SPACE,
                                    pygame.K_RETURN,
                                ):
                                    if not armed:
                                        raw.reset()
                                        pygame.mouse.get_rel()
                                        armed = True
                                        rejection_reason = None
                                    else:
                                        finished = True

                        if cancelled:
                            break

                        snapshot = raw.snapshot(reset=False)
                        _draw_console_environment(
                            console_surface,
                            target=target,
                        )

                        lines = [
                            f"Attempt {attempt}",
                            (
                                "Place the mouse comfortably, then press SPACE "
                                "to arm this throw."
                                if not armed
                                else
                                "Make ONE natural throw toward the highlighted "
                                "target. Press SPACE when your hand reaches a "
                                "comfortable end."
                            ),
                        ]

                        if armed:
                            lines.extend(
                                (
                                    f"Raw delta: "
                                    f"{snapshot['dx']:+d} / {snapshot['dy']:+d}",
                                    f"Raw events: {snapshot['event_count']}",
                                )
                            )

                        if rejection_reason:
                            lines.append(
                                (
                                    "Previous attempt rejected: "
                                    + rejection_reason,
                                    "small",
                                )
                            )

                        lines.append(("ESC: cancel calibration.", "small"))

                        _present_calibration_frame(
                            window,
                            console_surface,
                            title_font,
                            body_font,
                            small_font,
                            f"FULL THROW // {direction}",
                            lines,
                        )
                        clock.tick(120)

                    if cancelled:
                        break

                    snapshot = raw.snapshot(reset=False)
                    valid, reason, quality = _validate_mouse_throw(
                        axis,
                        sign,
                        snapshot,
                    )

                    if not valid:
                        rejection_reason = reason
                        attempt += 1
                        continue

                    measurements.append(
                        {
                            "direction": direction,
                            "axis": axis,
                            "raw_dx": int(snapshot["dx"]),
                            "raw_dy": int(snapshot["dy"]),
                            "event_count": int(snapshot["event_count"]),
                            "quality": quality,
                            "attempt": attempt,
                        }
                    )
                    accepted = True

                if cancelled:
                    break

            if cancelled:
                raise KeyboardInterrupt

            derived = _measurement_gain(measurements)
            accepted_gain = max(
                0.01,
                min(4.0, float(derived["recommended_gain"])),
            )

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
                            accepted_gain = min(4.0, accepted_gain * 1.05)
                        elif (
                            event.unicode == "-"
                            or event.key in (pygame.K_MINUS, pygame.K_KP_MINUS)
                        ):
                            accepted_gain = max(0.01, accepted_gain / 1.05)
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
                    console_surface,
                    cursor=(cursor_x, cursor_y),
                )
                _present_calibration_frame(
                    window,
                    console_surface,
                    title_font,
                    body_font,
                    small_font,
                    "SNES ENVIRONMENT TEST",
                    (
                        f"Current gain: {accepted_gain:.4f}x",
                        "Move naturally across the whole 256 x 224 logical area.",
                        "+ / - : adjust gain by 5%",
                        "R: reset to measured recommendation",
                        "ENTER / SPACE: accept this test result",
                        ("ESC: cancel without applying.", "small"),
                    ),
                )
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

        normalized_noise = max(
            noise / negative_span,
            noise / positive_span,
        )
        deadzone = min(
            0.35,
            max(0.05, normalized_noise * 1.75 + 0.02),
        )

        axes.append(
            {
                "index": index,
                "center": center,
                "center_noise": noise,
                "normalized_center_noise": normalized_noise,
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

        accepted_base_speed = 8.0
        recommended_deadzone = (
            max(
                axes[0]["recommended_deadzone"],
                axes[1]["recommended_deadzone"],
            )
            if len(axes) >= 2
            else 0.18
        )

        # Console-environment sensitivity test for the primary stick pair.
        # The accepted value is the MEDIUM/base speed that the existing
        # five-tier curve scales around at runtime.
        if len(primary_pair) == 2:
            cursor_x = float(SNES_WIDTH // 2)
            cursor_y = float(SNES_HEIGHT // 2)
            testing = True

            while testing:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        raise KeyboardInterrupt
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            raise KeyboardInterrupt
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            testing = False
                        elif (
                            event.unicode in ("+", "=")
                            or event.key in (pygame.K_EQUALS, pygame.K_KP_PLUS)
                        ):
                            accepted_base_speed = min(
                                32.0,
                                accepted_base_speed + 0.5,
                            )
                        elif (
                            event.unicode == "-"
                            or event.key in (pygame.K_MINUS, pygame.K_KP_MINUS)
                        ):
                            accepted_base_speed = max(
                                1.0,
                                accepted_base_speed - 0.5,
                            )
                        elif event.key == pygame.K_r:
                            accepted_base_speed = 8.0
                            cursor_x = float(SNES_WIDTH // 2)
                            cursor_y = float(SNES_HEIGHT // 2)

                pygame.event.pump()

                x_index, y_index = primary_pair
                raw_x = float(joystick.get_axis(x_index))
                raw_y = float(joystick.get_axis(y_index))

                norm_x = apply_deadzone(
                    normalize_axis(raw_x, axes[x_index]),
                    recommended_deadzone,
                )
                norm_y = apply_deadzone(
                    normalize_axis(raw_y, axes[y_index]),
                    recommended_deadzone,
                )

                cursor_x += norm_x * accepted_base_speed
                cursor_y += norm_y * accepted_base_speed
                cursor_x = max(0.0, min(SNES_WIDTH - 1.0, cursor_x))
                cursor_y = max(0.0, min(SNES_HEIGHT - 1.0, cursor_y))

                _draw_console_environment(
                    surface,
                    cursor=(cursor_x, cursor_y),
                )
                _draw_text(surface, font, "SNES ANALOG MOUSE TEST", 10, 8)
                _draw_text(
                    surface,
                    small_font,
                    f"MEDIUM/base speed: {accepted_base_speed:.1f}",
                    10,
                    28,
                )
                _draw_text(
                    surface,
                    small_font,
                    f"deadzone: {recommended_deadzone:.3f}",
                    10,
                    44,
                )
                _draw_text(
                    surface,
                    small_font,
                    "+/- speed | R reset | ENTER accept",
                    10,
                    60,
                )
                _draw_text(
                    surface,
                    small_font,
                    f"normalized: {norm_x:+.3f} / {norm_y:+.3f}",
                    10,
                    76,
                )

                pygame.display.flip()
                clock.tick(60)

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
                    "recommended_deadzone": recommended_deadzone,
                    "accepted_base_analog_speed": accepted_base_speed,
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
