#pragma once

// Salix GREEN 0.3 TinyUSB configuration.
//
// Native RP2350 USB controller:
//   roothub 0 -> USB device -> CDC/stdout diagnostics.
//
// Pico-PIO-USB:
//   PIO root port 0 -> TinyUSB rhport 1 -> PRIMARY-1 GP16/GP17.
//   PIO root port 1 -> TinyUSB rhport 2 -> PRIMARY-2 GP18/GP19.
//
// PRIMARY-1 was physically proven under GREEN 0.2. GREEN 0.3 enables the
// second Pico-PIO-USB root port so two directly attached devices can coexist.
// External USB hub support remains disabled.

#ifndef CFG_TUSB_RHPORT0_MODE
#define CFG_TUSB_RHPORT0_MODE (OPT_MODE_DEVICE)
#endif

#ifndef CFG_TUSB_RHPORT1_MODE
#define CFG_TUSB_RHPORT1_MODE (OPT_MODE_HOST)
#endif

#ifndef CFG_TUD_ENABLED
#define CFG_TUD_ENABLED 1
#endif

#ifndef CFG_TUH_ENABLED
#define CFG_TUH_ENABLED 1
#endif

#ifndef CFG_TUH_RPI_PIO_USB
#define CFG_TUH_RPI_PIO_USB 1
#endif

#ifndef CFG_TUSB_DEBUG
#define CFG_TUSB_DEBUG 0
#endif

// ---------------------------------------------------------------------------
// Native USB device / CDC diagnostics
// ---------------------------------------------------------------------------

#ifndef CFG_TUD_ENDPOINT0_SIZE
#define CFG_TUD_ENDPOINT0_SIZE 64
#endif

#ifndef CFG_TUD_CDC
#define CFG_TUD_CDC 1
#endif

#ifndef CFG_TUD_CDC_RX_BUFSIZE
#define CFG_TUD_CDC_RX_BUFSIZE 64
#endif

#ifndef CFG_TUD_CDC_TX_BUFSIZE
#define CFG_TUD_CDC_TX_BUFSIZE 64
#endif

#ifndef CFG_TUD_CDC_EP_BUFSIZE
#define CFG_TUD_CDC_EP_BUFSIZE 64
#endif

// ---------------------------------------------------------------------------
// PRIMARY-1 + PRIMARY-2 host / HID
// ---------------------------------------------------------------------------

// Two directly attached devices, one on each PRIMARY root port.
#ifndef CFG_TUH_HUB
#define CFG_TUH_HUB 0
#endif

#ifndef CFG_TUH_DEVICE_MAX
#define CFG_TUH_DEVICE_MAX 2
#endif

// A single USB controller can expose more than one HID interface.
#ifndef CFG_TUH_HID
#define CFG_TUH_HID 4
#endif

#ifndef CFG_TUH_ENUMERATION_BUFSIZE
#define CFG_TUH_ENUMERATION_BUFSIZE 512
#endif

#ifndef CFG_TUH_HID_EPIN_BUFSIZE
#define CFG_TUH_HID_EPIN_BUFSIZE 64
#endif

#ifndef CFG_TUH_HID_EPOUT_BUFSIZE
#define CFG_TUH_HID_EPOUT_BUFSIZE 64
#endif
