#include <cinttypes>
#include <cstdio>

#include "pico/stdlib.h"

namespace salix {

constexpr uint32_t kHeartbeatIntervalMs = 2000;

void PrintBootBanner()
{
    std::printf("\r\n");
    std::printf("SalixControllerBridge - Main I/O Processor\r\n");
    std::printf("Firmware milestone: green-main 0.1\r\n");
    std::printf("Board role: GREEN Pico 2 W / real-time master\r\n");
    std::printf("Runtime: Pico SDK C++ (MicroPython-free)\r\n");
    std::printf("Native USB: CDC/stdout diagnostics\r\n");
    std::printf("PRIMARY USB host: not enabled in this milestone\r\n");
    std::printf("SNES backend: not enabled in this milestone\r\n");
    std::printf("\r\n");
}

}  // namespace salix

int main()
{
    stdio_init_all();

    // Do not wait indefinitely for a PC. Standalone firmware must boot even
    // when nothing is attached to the native USB connector.
    sleep_ms(100);

    salix::PrintBootBanner();

    uint32_t heartbeat = 0;

    while (true) {
        const uint64_t uptime_ms = to_ms_since_boot(get_absolute_time());

        std::printf(
            "[green-main] heartbeat=%" PRIu32 " uptime_ms=%" PRIu64 "\r\n",
            heartbeat,
            uptime_ms
        );

        ++heartbeat;
        sleep_ms(salix::kHeartbeatIntervalMs);
    }

    return 0;
}
