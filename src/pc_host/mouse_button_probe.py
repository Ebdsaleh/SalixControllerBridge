# src/pc_host/mouse_button_probe.py

"""Probe Pygame mouse-button events without opening the Pico serial port."""

import pygame


WINDOW_SIZE = (760, 360)


def format_pressed_state():
    try:
        pressed = pygame.mouse.get_pressed(5)
    except (TypeError, ValueError):
        pressed = pygame.mouse.get_pressed(3)

    return " ".join(
        f"{index + 1}={int(value)}"
        for index, value in enumerate(pressed)
    )


def main():
    pygame.init()
    pygame.display.init()
    pygame.font.init()

    window = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption(
        "SalixControllerBridge // Mouse Button Probe"
    )

    font = pygame.font.Font(None, 28)
    small = pygame.font.Font(None, 22)
    clock = pygame.time.Clock()

    lines = [
        "Click this window once to give it focus.",
        "Then press ONE mouse control at a time.",
        "",
        "Suggested order:",
        "Left, Right, Middle, Side Front, Side Rear,",
        "DPI Down, DPI Up, Wheel Up, Wheel Down.",
        "",
        "Watch the console for MOUSEBUTTON / MOUSEWHEEL events.",
        "ESC closes the probe. COM3 / Pico / SNES are not used.",
    ]

    print("Salix mouse-button probe active.")
    print("The Pico serial port will NOT be opened.")
    print(
        "Press one control at a time: "
        "Left, Right, Middle, Side Front, Side Rear, "
        "DPI Down, DPI Up, Wheel Up, Wheel Down."
    )
    print("ESC in the probe window exits.")

    running = True
    last_pressed = None

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                print(
                    f"MOUSEBUTTONDOWN button={event.button} "
                    f"pos={event.pos}"
                )

            elif event.type == pygame.MOUSEBUTTONUP:
                print(
                    f"MOUSEBUTTONUP   button={event.button} "
                    f"pos={event.pos}"
                )

            elif event.type == pygame.MOUSEWHEEL:
                print(
                    f"MOUSEWHEEL x={event.x:+d} y={event.y:+d} "
                    f"flipped={getattr(event, 'flipped', False)}"
                )

        pressed = format_pressed_state()
        if pressed != last_pressed:
            print(f"PRESSED_STATE {pressed}")
            last_pressed = pressed

        window.fill((20, 22, 26))
        y = 24

        for index, line in enumerate(lines):
            renderer = font if index in (0, 1) else small
            color = (100, 255, 170) if index == 0 else (235, 235, 235)
            rendered = renderer.render(line, True, color)
            window.blit(rendered, (24, y))
            y += renderer.get_linesize() + 4

        status = small.render(
            f"Current pressed state: {pressed}",
            True,
            (180, 190, 210),
        )
        window.blit(status, (24, WINDOW_SIZE[1] - 42))

        pygame.display.flip()
        clock.tick(120)

    pygame.quit()
    print("Mouse-button probe stopped.")


if __name__ == "__main__":
    main()
