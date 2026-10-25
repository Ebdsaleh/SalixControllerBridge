# src/pc_host/probe_hid.py


import hid

print("Scanning USB HID devices...\n")
devices = hid.enuerate()

for d in devices:
    # Filter for generic game controllers / joysticks (Usage Page 1, Usage 4/5)
    # or print any device that has a product string
    if d['product_string']:
        print(f"Device: {d['product_string']}")
        print(f"  Vendor ID : 0x{d['vendor_id']:04x}")
        print(f"  Product ID: 0x{d['product_id']:04x}")
        print(f"  Usage Page: 0x{d['usage_page']:04x}")
        print(f"  Usage     : 0x{d['usage']:04x}")
        print(f"  Path      : {d['path']}\n")
