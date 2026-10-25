"""Show raw Pygame joystick indices for one-button-at-a-time calibration."""

import time

import pygame


def main():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        raise SystemExit("No joystick/game controller detected by Pygame.")

    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    print(f"Name    : {joystick.get_name()}")
    try:
        print(f"GUID    : {joystick.get_guid()}")
    except AttributeError:
        pass
    print(f"Buttons : {joystick.get_numbuttons()}")
    print(f"Hats    : {joystick.get_numhats()}")
    print(f"Axes    : {joystick.get_numaxes()}")
    print()
    print("Press ONE physical control at a time. Ctrl+C exits.")

    last_buttons = None
    last_hats = None
    last_axes = None

    try:
        while True:
            pygame.event.pump()

            buttons = tuple(joystick.get_button(i) for i in range(joystick.get_numbuttons()))
            hats = tuple(joystick.get_hat(i) for i in range(joystick.get_numhats()))
            axes = tuple(round(joystick.get_axis(i), 3) for i in range(joystick.get_numaxes()))

            if buttons != last_buttons:
                pressed = [i for i, value in enumerate(buttons) if value]
                print(f"BUTTONS pressed indices: {pressed}")
                last_buttons = buttons

            if hats != last_hats:
                print(f"HATS: {hats}")
                last_hats = hats

            if axes != last_axes:
                significant = [(i, value) for i, value in enumerate(axes) if abs(value) >= 0.5]
                if significant:
                    print(f"AXES significant: {significant}")
                last_axes = axes

            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
