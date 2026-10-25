# SNES Standard Controller Wire Semantics

This project distinguishes between the physical DATA-wire level and the
CPU-visible controller bit.

## Physical wire

- DATA LOW = asserted / pressed for button stages.
- DATA HIGH = released for button stages.
- Standard-pad unused stages 12-15 are physically HIGH.
- After the 16-bit report, an official standard pad drives DATA LOW until the
  next latch cycle.

## CPU-visible report

The SNES controller input circuitry presents the logical controller report as:

`B Y Select Start Up Down Left Right A X L R 0 0 0 0`

The final four zeroes are the standard-pad signature. They correspond to HIGH
levels on the physical DATA wire.

A manual 17th read reports 1 for an attached standard controller. This requires
the physical DATA wire to be LOW after the 16th report bit.

This distinction matters for games that perform controller-presence or
peripheral-type checks. A bridge can appear to work in games that only consume
the twelve button bits while being rejected as "no controller" by stricter
software if the signature or post-report state is wrong.
