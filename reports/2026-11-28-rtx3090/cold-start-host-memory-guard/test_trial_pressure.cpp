#include "trial_pressure.hpp"
#include <cassert>
#include <cstring>

int main() {
    const auto g = TrialPressure::GiB;
    TrialPressure guard;
    assert(!guard.inspect(true, 4*g, 10*g));
    assert(std::strcmp(guard.inspect(true, g, 10*g), "physical memory below 1.5 GiB") == 0);
    assert(std::strcmp(guard.inspect(true, 4*g, 4*g), "system commit headroom below 5 GiB") == 0);
    for (int i = 0; i < 7; ++i) assert(!guard.inspect(true, 2*g, 10*g));
    assert(!guard.inspect(true, 3*g, 10*g));
    for (int i = 0; i < 7; ++i) assert(!guard.inspect(true, 2*g, 10*g));
    assert(std::strcmp(guard.inspect(true, 2*g, 10*g), "physical memory below 3 GiB for eight samples") == 0);
    assert(!guard.inspect(false, 0, 0));
    assert(!guard.inspect(false, 0, 0));
    assert(!guard.inspect(true, 3*g, 5*g));
    assert(!guard.inspect(false, 0, 0));
    assert(!guard.inspect(false, 0, 0));
    assert(std::strcmp(guard.inspect(false, 0, 0), "system counters unavailable") == 0);
}
