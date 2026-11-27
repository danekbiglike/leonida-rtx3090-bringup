# 4K cell scene with a per-application NVIDIA power preference

This is a cell-scene measurement. Lucia remained at a closed door for the 120-second replay. Its frame rate cannot be compared to a walk behind the officer.

The RTX 3090 used 780 MHz median graphics clock with 91.5% median utilization. There were 1,293 presents (10.775 FPS), a 110.2 ms p95 interval, and one five-second window with no presents. The 5.719 s longest gap started just before the marker. The renderer continued presenting across 15 minutes from process start. It peaked at 33.86 GiB job commitment with no limit events, a 42 GiB process limit, and 15.26 GiB minimum system commit headroom. The relay regression suite built during preparation and ended before the 120-second measurement. All three tests passed.

The executable was byte-identical to the flagged-range renderer, SHA-256 1616719bc89e37496014172e30bad84b1a97e7cbea6b7cb879689a510b294e48. A unique executable name and marker file selected a dedicated NVIDIA application profile with PREFERRED_PSTATE_PREFER_MAX. An independent driver query confirmed it applied to the test executable only. The renderer was visible and windowed. Attempts to activate it did not establish foreground focus. The application preference did not lift the median clock above that in the prior corridor test. No hardware clocks, power limit or global driver profile were set. The temporary application profile was removed and its absence was verified after timing.

The local utility was built against NVIDIA's public NVAPI SDK commit 51e5aae4bc40c3ccd3fb7d4dfd94256e7bfc496e. It checks the test and control executable matches before saving and restricts restoration to the profile it created. Recorded by danekbiglike with ChatGPT on 28 November 2026.
