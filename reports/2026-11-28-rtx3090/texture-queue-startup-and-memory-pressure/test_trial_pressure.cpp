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
    TrialPressure falling;
    assert(!falling.inspect(true, 5*g, 12*g, true));
    assert(!falling.inspect(true, 19*g/4, 12*g, true));
    assert(!falling.inspect(true, 17*g/4, 12*g, true));
    assert(std::strcmp(falling.inspect(true, 25*g/8, 12*g, true),
                       "available physical memory falling rapidly below 3.25 GiB") == 0);
    TrialPressure level;
    for (int i = 0; i < 16; ++i) assert(!level.inspect(true, 7*g/2, 12*g, true));
    TrialPressure gap;
    assert(!gap.inspect(true, 5*g, 12*g, true));
    assert(!gap.inspect(true, 19*g/4, 12*g, true));
    assert(!gap.inspect(false, 0, 0, true));
    assert(!gap.inspect(true, 17*g/4, 12*g, true));
    assert(!gap.inspect(true, 25*g/8, 12*g, true));

}
