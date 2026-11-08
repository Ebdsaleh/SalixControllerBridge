#include <cinttypes>
#include <cstdio>
#include <cstring>

#include "hardware/clocks.h"
#include "pico/multicore.h"
#include "pico/stdlib.h"
#include "pico/util/queue.h"

#include "pio_usb.h"
#include "tusb.h"

namespace salix {

constexpr uint32_t kSystemClockKHz = 120000;
constexpr uint32_t kHeartbeatIntervalMs = 2000;

constexpr uint8_t kNativeUsbRhport = 0;
constexpr uint8_t kPrimary1Rhport = 1;
constexpr uint8_t kPrimary1DpPin = 16;
constexpr uint8_t kPrimary1DmPin = 17;

constexpr uint16_t kMaxCapturedReportBytes = 64;
constexpr uint kHostEventQueueDepth = 32;

enum class HostEventType : uint8_t {
    HostReady,
    HostConfigureFailed,
    HostInitFailed,
    HidMounted,
    HidUnmounted,
    HidReport,
    HidReceiveFailed,
};

enum class HostRuntimeState : uint32_t {
    Starting,
    ConfigureFailed,
    InitFailed,
    Ready,
};

struct HostEvent {
    HostEventType type;
    uint8_t dev_addr;
    uint8_t instance;
    uint8_t interface_number;
    uint8_t protocol;
    uint16_t vid;
    uint16_t pid;
    uint16_t descriptor_len;
    uint16_t report_len;
    uint16_t captured_len;
    uint8_t report[kMaxCapturedReportBytes];
};

queue_t g_host_event_queue;
volatile uint32_t g_host_runtime_state =
    static_cast<uint32_t>(HostRuntimeState::Starting);

void SetHostRuntimeState(HostRuntimeState state)
{
    __atomic_store_n(
        &g_host_runtime_state,
        static_cast<uint32_t>(state),
        __ATOMIC_RELEASE
    );
}

HostRuntimeState GetHostRuntimeState()
{
    return static_cast<HostRuntimeState>(
        __atomic_load_n(&g_host_runtime_state, __ATOMIC_ACQUIRE)
    );
}

bool PushHostEvent(const HostEvent& event)
{
    return queue_try_add(&g_host_event_queue, &event);
}

const char* ProtocolName(uint8_t protocol)
{
    switch (protocol) {
        case HID_ITF_PROTOCOL_KEYBOARD:
            return "Keyboard";
        case HID_ITF_PROTOCOL_MOUSE:
            return "Mouse";
        case HID_ITF_PROTOCOL_NONE:
        default:
            return "None";
    }
}

void PrintBootBanner()
{
    std::printf("\r\n");
    std::printf("SalixControllerBridge - Main I/O Processor\r\n");
    std::printf("Firmware milestone: green-main 0.2\r\n");
    std::printf("Board role: GREEN Pico 2 W / real-time master\r\n");
    std::printf("Runtime: Pico SDK C++ (MicroPython-free)\r\n");
    std::printf("System clock: %" PRIu32 " kHz\r\n", kSystemClockKHz);
    std::printf("Native USB: CDC/stdout diagnostics\r\n");
    std::printf(
        "PRIMARY-1 USB host: PIO USB D+=GP%u D-=GP%u\r\n",
        kPrimary1DpPin,
        kPrimary1DmPin
    );
    std::printf("PRIMARY-2 USB host: reserved / disabled\r\n");
    std::printf("SNES backend: not enabled in this milestone\r\n");
    std::printf("\r\n");
}

void PrintCurrentHostState()
{
    switch (GetHostRuntimeState()) {
        case HostRuntimeState::Starting:
            std::printf("[PRIMARY-1] host state=starting\r\n");
            break;
        case HostRuntimeState::ConfigureFailed:
            std::printf("[PRIMARY-1] host state=configure-failed\r\n");
            break;
        case HostRuntimeState::InitFailed:
            std::printf("[PRIMARY-1] host state=init-failed\r\n");
            break;
        case HostRuntimeState::Ready:
            std::printf(
                "[PRIMARY-1] host ready rhport=%u D+=GP%u D-=GP%u\r\n",
                kPrimary1Rhport,
                kPrimary1DpPin,
                kPrimary1DmPin
            );
            break;
    }
}

void PrintHostEvent(const HostEvent& event)
{
    switch (event.type) {
        case HostEventType::HostReady:
            std::printf(
                "[PRIMARY-1] host ready rhport=%u D+=GP%u D-=GP%u\r\n",
                kPrimary1Rhport,
                kPrimary1DpPin,
                kPrimary1DmPin
            );
            break;

        case HostEventType::HostConfigureFailed:
            std::printf("[PRIMARY-1] ERROR: tuh_configure failed\r\n");
            break;

        case HostEventType::HostInitFailed:
            std::printf("[PRIMARY-1] ERROR: tuh_init failed\r\n");
            break;

        case HostEventType::HidMounted:
            std::printf(
                "[PRIMARY-1] HID mount vid=%04x pid=%04x addr=%u "
                "instance=%u interface=%u protocol=%s report_desc_len=%u\r\n",
                event.vid,
                event.pid,
                event.dev_addr,
                event.instance,
                event.interface_number,
                ProtocolName(event.protocol),
                event.descriptor_len
            );
            break;

        case HostEventType::HidUnmounted:
            std::printf(
                "[PRIMARY-1] HID unmount addr=%u instance=%u interface=%u\r\n",
                event.dev_addr,
                event.instance,
                event.interface_number
            );
            break;

        case HostEventType::HidReceiveFailed:
            std::printf(
                "[PRIMARY-1] ERROR: cannot request HID report "
                "addr=%u instance=%u interface=%u\r\n",
                event.dev_addr,
                event.instance,
                event.interface_number
            );
            break;

        case HostEventType::HidReport:
            std::printf(
                "[PRIMARY-1] HID report addr=%u instance=%u interface=%u "
                "len=%u captured=%u data=",
                event.dev_addr,
                event.instance,
                event.interface_number,
                event.report_len,
                event.captured_len
            );

            for (uint16_t i = 0; i < event.captured_len; ++i) {
                std::printf("%02X", event.report[i]);
                if (i + 1 < event.captured_len) {
                    std::printf(" ");
                }
            }

            std::printf("\r\n");
            break;
    }
}

void Primary1HostCore()
{
    // Pico-PIO-USB requires a system clock that is a multiple of 12 MHz.
    // main() establishes 120 MHz before this core is launched.
    pio_usb_configuration_t pio_config = PIO_USB_DEFAULT_CONFIG;
    pio_config.pin_dp = kPrimary1DpPin;
    pio_config.pinout = PIO_USB_PINOUT_DPDM;

    HostEvent event{};

    if (!tuh_configure(
            kPrimary1Rhport,
            TUH_CFGID_RPI_PIO_USB_CONFIGURATION,
            &pio_config
        )) {
        SetHostRuntimeState(HostRuntimeState::ConfigureFailed);
        event.type = HostEventType::HostConfigureFailed;
        PushHostEvent(event);
        return;
    }

    if (!tuh_init(kPrimary1Rhport)) {
        SetHostRuntimeState(HostRuntimeState::InitFailed);
        event.type = HostEventType::HostInitFailed;
        PushHostEvent(event);
        return;
    }

    SetHostRuntimeState(HostRuntimeState::Ready);
    event.type = HostEventType::HostReady;
    PushHostEvent(event);

    while (true) {
        tuh_task();
    }
}

}  // namespace salix

extern "C" void tuh_hid_mount_cb(
    uint8_t dev_addr,
    uint8_t instance,
    uint8_t const* desc_report,
    uint16_t desc_len
)
{
    (void)desc_report;

    salix::HostEvent event{};
    event.type = salix::HostEventType::HidMounted;
    event.dev_addr = dev_addr;
    event.instance = instance;
    event.descriptor_len = desc_len;

    tuh_itf_info_t interface_info{};
    if (tuh_hid_itf_get_info(dev_addr, instance, &interface_info)) {
        event.interface_number = interface_info.desc.bInterfaceNumber;
    } else {
        event.interface_number = 0xFF;
    }

    event.protocol = tuh_hid_interface_protocol(dev_addr, instance);
    tuh_vid_pid_get(dev_addr, &event.vid, &event.pid);
    salix::PushHostEvent(event);

    // Request interrupt-IN reports for every HID protocol, including protocol
    // NONE used by gamepads and arcade sticks.
    if (!tuh_hid_receive_report(dev_addr, instance)) {
        event = {};
        event.type = salix::HostEventType::HidReceiveFailed;
        event.dev_addr = dev_addr;
        event.instance = instance;
        event.interface_number =
            interface_info.desc.bInterfaceNumber;
        salix::PushHostEvent(event);
    }
}

extern "C" void tuh_hid_umount_cb(uint8_t dev_addr, uint8_t instance)
{
    salix::HostEvent event{};
    event.type = salix::HostEventType::HidUnmounted;
    event.dev_addr = dev_addr;
    event.instance = instance;

    tuh_itf_info_t interface_info{};
    if (tuh_hid_itf_get_info(dev_addr, instance, &interface_info)) {
        event.interface_number = interface_info.desc.bInterfaceNumber;
    } else {
        event.interface_number = 0xFF;
    }

    salix::PushHostEvent(event);
}

extern "C" void tuh_hid_report_received_cb(
    uint8_t dev_addr,
    uint8_t instance,
    uint8_t const* report,
    uint16_t len
)
{
    salix::HostEvent event{};
    event.type = salix::HostEventType::HidReport;
    event.dev_addr = dev_addr;
    event.instance = instance;
    event.report_len = len;

    tuh_itf_info_t interface_info{};
    if (tuh_hid_itf_get_info(dev_addr, instance, &interface_info)) {
        event.interface_number = interface_info.desc.bInterfaceNumber;
    } else {
        event.interface_number = 0xFF;
    }

    event.captured_len =
        len < salix::kMaxCapturedReportBytes
            ? len
            : salix::kMaxCapturedReportBytes;

    if (event.captured_len > 0 && report != nullptr) {
        std::memcpy(event.report, report, event.captured_len);
    }

    salix::PushHostEvent(event);

    if (!tuh_hid_receive_report(dev_addr, instance)) {
        event = {};
        event.type = salix::HostEventType::HidReceiveFailed;
        event.dev_addr = dev_addr;
        event.instance = instance;
        event.interface_number =
            interface_info.desc.bInterfaceNumber;
        salix::PushHostEvent(event);
    }
}

int main()
{
    // Upstream Pico-PIO-USB requires a multiple-of-12-MHz system clock.
    // 120 MHz is the conservative bring-up clock used by the upstream
    // host-to-device CDC example.
    set_sys_clock_khz(salix::kSystemClockKHz, true);

    // Initialize the native USB controller strictly as the CDC device before
    // stdio_init_all(). PICO_STDIO_USB_ENABLE_TINYUSB_INIT=0 prevents the
    // stdio layer from trying to initialize both TinyUSB roles itself.
    tud_init(salix::kNativeUsbRhport);
    stdio_init_all();

    queue_init(
        &salix::g_host_event_queue,
        sizeof(salix::HostEvent),
        salix::kHostEventQueueDepth
    );

    // Do not wait indefinitely for a PC. Standalone firmware must boot even
    // when nothing is attached to the native USB connector.
    sleep_ms(100);

    multicore_reset_core1();
    multicore_launch_core1(salix::Primary1HostCore);

    uint32_t heartbeat = 0;
    bool cdc_was_connected = false;
    absolute_time_t next_heartbeat =
        make_timeout_time_ms(salix::kHeartbeatIntervalMs);

    while (true) {
        // Because GREEN 0.2 links TinyUSB directly, Pico SDK deliberately
        // disables pico_stdio_usb's background tud_task() worker. Service the
        // native CDC device stack explicitly on core 0 so Windows can
        // enumerate and stdio USB remains alive.
        tud_task();

        const bool cdc_connected = tud_cdc_connected();
        if (cdc_connected && !cdc_was_connected) {
            salix::PrintBootBanner();
            salix::PrintCurrentHostState();
        }
        cdc_was_connected = cdc_connected;

        salix::HostEvent event{};
        while (queue_try_remove(&salix::g_host_event_queue, &event)) {
            salix::PrintHostEvent(event);
        }

        if (time_reached(next_heartbeat)) {
            const uint64_t uptime_ms =
                to_ms_since_boot(get_absolute_time());

            std::printf(
                "[green-main] heartbeat=%" PRIu32 " uptime_ms=%" PRIu64 "\r\n",
                heartbeat,
                uptime_ms
            );

            ++heartbeat;
            next_heartbeat =
                delayed_by_ms(next_heartbeat, salix::kHeartbeatIntervalMs);
        }

        sleep_ms(1);
    }

    return 0;
}
