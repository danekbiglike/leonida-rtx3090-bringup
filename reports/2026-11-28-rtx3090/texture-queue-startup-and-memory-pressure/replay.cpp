#include "trial_pressure.hpp"
#include <cstdint>
#include <iostream>

int main() {
    TrialPressure guard;
    std::uint64_t time, physical, headroom;
    while (std::cin >> time >> physical >> headroom) {
        if (const auto* reason = guard.inspect(true, physical, headroom, true)) {
            std::cout << time << ',' << physical << ',' << reason << '\n';
            return 0;
        }
    }
    std::cout << "no pressure stop\n";
}
