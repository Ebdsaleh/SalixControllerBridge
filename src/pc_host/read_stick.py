# src/pc_host/read_stick.py


import sys
import time
import serial
import hid

COM_PORT = 'COM3'
BAUD_RATE = 115200

# 1. Establish Serial Pipeline to Pico
try:
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=0.1)
    print(f"Connected to Pico on {COM_PORT}")
except Exception as e:
    print(f"Error opening {COM_PORT}: {e}")
    sys.exit(1)

# 2. Bind to JJ USB HID Encoder
target_vid = 0x20bc
target_pid = 0x5501

dev_info = None
for d in hid.enumerate():
    if d['vendor_id'] == target_vid and d['product_id'] == target_pid:
        dev_info = d
        break

if not dev_info:
    print(f"Device 0x{target_vid:04x}:0x{target_pid:04x} not found.")
    ser.close()
    sys.exit(1)

dev = hid.device()
dev.open_path(dev_info['path'])
dev.set_nonblocking(True)
print(f"Bridging {dev_info['product_string']} -> SNES Bitmask -> Pico.")
print("Active. Press Ctrl+C to stop.\n")

# SNES Bitmasks (Active-LOW: cleared bit (0) = pressed)
# Bit: 0=B, 1=Y, 2=Select, 3=Start, 4=Up, 5=Down, 6=Left, 7=Right, 8=A, 9=X, 10=L, 11=R
MASK_UP    = 1 << 4
MASK_DOWN  = 1 << 5
MASK_LEFT  = 1 << 6
MASK_RIGHT = 1 << 7

# Precomputed hat lookup table (Index 0-7 = Directions, 15 = Neutral)
# Maps Byte 2 values directly to active direction bits
HAT_MAP = {
    0:  MASK_UP,
    1:  MASK_UP | MASK_RIGHT,
    2:  MASK_RIGHT,
    3:  MASK_DOWN | MASK_RIGHT,
    4:  MASK_DOWN,
    5:  MASK_DOWN | MASK_LEFT,
    6:  MASK_LEFT,
    7:  MASK_UP | MASK_LEFT,
    15: 0
}

last_sent_mask = -1

try:
    while True:
        data = dev.read(64)
        if data:
            b0 = data[0]
            b1 = data[1]
            hat = data[2]

            # Construct active-high pressed flags
            pressed = 0

            # Direction lookup
            pressed |= HAT_MAP.get(hat, 0)

            # Byte 0 mappings:
            # 0x01: Square   -> SNES Y  (bit 1)
            # 0x02: Cross    -> SNES B  (bit 0)
            # 0x08: Triangle -> SNES X  (bit 9)
            # 0x10: Circle   -> SNES A  (bit 8)
            # 0x04: R1       -> SNES L  (bit 10)
            # 0x20: R2       -> SNES R  (bit 11)
            if b0 & 0x01: pressed |= (1 << 1)   # Y
            if b0 & 0x02: pressed |= (1 << 0)   # B
            if b0 & 0x08: pressed |= (1 << 9)   # X
            if b0 & 0x10: pressed |= (1 << 8)   # A
            if b0 & 0x04: pressed |= (1 << 10)  # L
            if b0 & 0x20: pressed |= (1 << 11)  # R

            # Byte 1 mappings:
            # 0x04: Select -> SNES Select (bit 2)
            # 0x08: Start  -> SNES Start  (bit 3)
            if b1 & 0x04: pressed |= (1 << 2)   # Select
            if b1 & 0x08: pressed |= (1 << 3)   # Start

            # Convert to SNES active-LOW format (invert pressed bits)
            snes_mask = (~pressed) & 0xFFFF

            # Transmit only when the bitmask changes
            if snes_mask != last_sent_mask:
                ser.write(snes_mask.to_bytes(2, byteorder='little'))
                last_sent_mask = snes_mask

        # Minimal yield to keep CPU consumption low without introducing input lag
        time.sleep(0.001)

except KeyboardInterrupt:
    print("\nShutting down bridge...")
finally:
    # Send released state (0xFFFF) before exit
    ser.write((0xFFFF).to_bytes(2, byteorder='little'))
    dev.close()
    ser.close()
