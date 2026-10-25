# src/pc_host/inspect_packet.py


import sys
import time
import hid

target_vid = 0x20bc
target_pid = 0x5501

dev_info = None
for d in hid.enumerate():
    if d['vendor_id'] == target_vid and d['product_id'] == target_pid:
        dev_info = d
        break

if not dev_info:
    print("Device not found.")
    sys.exit(1)

dev = hid.device()
dev.open_path(dev_info['path'])
dev.set_nonblocking(True)

print("Packet Inspector Active. Press Ctrl+C to stop.")
print("Format: [Byte 0, Byte 1, Byte 2, Byte 3, Byte 4, Byte 5, Byte 6, Byte 7, Byte 8]\n")

last_packet = None

try:
    while True:
        data = dev.read(64)
        if data:
            current = list(data)
            if current != last_packet:
                last_packet = current
                # Print index aligned with values
                print(f"Packet: {current}")
        time.sleep(0.005)
except KeyboardInterrupt:
    dev.close()
    print("\nDone.")
