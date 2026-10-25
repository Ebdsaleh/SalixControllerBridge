# Controller Compatibility Investigation

## Confirmed host-side diagonal states

The Mayflash F300 in PS3/DINPUT mode reports a Pygame hat. The host bridge
correctly constructs simultaneous SNES direction bits:

- Up+Right = 0xFF6F
- Down+Right = 0xFF5F
- Down+Left = 0xFF9F
- Up+Left = 0xFFAF

Therefore difficulty performing diagonal moves in some games is not caused by
the F300-to-Pygame mapping.

## Current physical-game observations

- Mortal Kombat II: controller works, but diagonal jumps can be difficult.
- WeaponLord: controller works, but diagonals are not consistently convincing.
- SFC Aladdin through Datel passthrough: controller works.
- PAL Donkey Kong Country 2: game boots but does not accept controller input.
- SFC Super Street Fighter II: game boots but does not accept controller input.

The stricter-game problem remains under investigation. Do not treat cartridge
region as the root cause: PAL DKC2 reproduces the symptom.

## Diagnostic direction

Keep the USB mapping and SNES button bit layout unchanged. Focus on exact
standard-controller electrical/timing behavior, including latch/clock timing and
behavior around/after the 16-bit report.

The experimental post-16th-bit firmware change did not improve PAL DKC2 and was
reverted to the previously validated firmware baseline.
