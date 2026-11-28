#pragma once
#include <cstdint>
#include <array>

struct TrialPressure {
    static constexpr std::uint64_t GiB = 1ULL << 30;
    unsigned low_seconds = 0;
    unsigned missing_seconds = 0;
    std::array<std::uint64_t, 3> previous{};
    unsigned previous_count = 0;

    const char* inspect(bool available, std::uint64_t physical, std::uint64_t commit, bool anticipate = false) {
        missing_seconds = available ? 0 : missing_seconds + 1;
        if (!available) {
            previous_count = low_seconds = 0;
            return missing_seconds >= 3 ? "system counters unavailable" : nullptr;
        }
        if (physical < 3 * GiB / 2) return "physical memory below 1.5 GiB";
        if (commit < 5 * GiB) return "system commit headroom below 5 GiB";
        if (anticipate) {
            // The renderer can take several seconds to release its pages after shutdown begins.
            const bool falling = previous_count == previous.size() && previous[0] > previous[1]
                && previous[1] > previous[2] && previous[2] > physical;
            if (falling && physical < 13 * GiB / 4 && previous[0] - physical >= GiB / 2)
                return "available physical memory falling rapidly below 3.25 GiB";
            previous = {previous[1], previous[2], physical};
            if (previous_count < previous.size()) ++previous_count;
        }
        low_seconds = physical < 3 * GiB ? low_seconds + 1 : 0;
        return low_seconds >= 8 ? "physical memory below 3 GiB for eight samples" : nullptr;
    }
};
