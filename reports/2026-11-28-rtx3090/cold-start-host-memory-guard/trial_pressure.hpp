#pragma once
#include <cstdint>

struct TrialPressure {
    static constexpr std::uint64_t GiB = 1ULL << 30;
    unsigned low_seconds = 0;
    unsigned missing_seconds = 0;

    const char* inspect(bool available, std::uint64_t physical, std::uint64_t commit) {
        missing_seconds = available ? 0 : missing_seconds + 1;
        if (!available) return missing_seconds >= 3 ? "system counters unavailable" : nullptr;
        if (physical < 3 * GiB / 2) return "physical memory below 1.5 GiB";
        if (commit < 5 * GiB) return "system commit headroom below 5 GiB";
        low_seconds = physical < 3 * GiB ? low_seconds + 1 : 0;
        return low_seconds >= 8 ? "physical memory below 3 GiB for eight samples" : nullptr;
    }
};
