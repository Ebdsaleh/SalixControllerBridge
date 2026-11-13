# TF034 / 2.4-inch display baseline

Source basis for this parked design is the user's physical module and supplied photos/listing screenshots.

Observed/printed information:

- Front marking: **2.4inch RPi Display**.
- Rear marking: **2.4inch RPi Display** and **320X240 Pixels**.
- Sticker serial/model text: **TF034**.
- Board uses a **2x13 / 26-position Raspberry-Pi-style header**.
- Seller imagery shows an approximately **65 mm x 56 mm** board outline.
- Seller imagery identifies the product as a 2.4-inch Raspberry Pi display with touch-controller circuitry.

What is **not frozen**:

- Exact 26-pin signal map on the user's unit.
- Exact LCD controller IC.
- Exact touch controller IC/revision.
- Logic-voltage tolerance and backlight-current requirements.
- Mechanical hole coordinates/tolerances.

Therefore both controller schematics use a functional `TF034_TOUCH_LCD` abstraction instead of pretending the connector pinout is known. Before a controller PCB is laid out, the actual module should be powered and bench-mapped/verified.
