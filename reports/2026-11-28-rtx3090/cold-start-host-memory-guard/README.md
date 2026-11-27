# Cold-cache startup and host memory on RTX 3090

A 3840 × 2160 Series X trial on a Ryzen 7 3700X, 32 GiB of system memory and an RTX 3090 (24 GiB) exited during loading. The source was [fxceless/victory-fork at 2eade68](https://github.com/fxceless/victory-fork/commit/2eade68cade9b2f8cd2511cc97328e83f58508c3), built locally with split data mounting, SSD guest pool backing and accepted-present logging. This run used the project play settings with six translation workers, an 80% texture budget, and a 30 Hz frame cap. Game data and the 6,538,919,936-byte file-backed pool were on SSD. The shader cache started empty. The game never reached the escort.

The process exited with 0xc0000005 at guest offset 0x23cf683. The previous [spare-refill build](../../2026-11-27-rtx3090/spare-refill-intro-watchdog/) recorded the same offset. Counters sampled every second showed minimum available physical memory of 2,187,968,512 bytes and minimum unused system commit of 25,189,031,936 bytes. Peak job commit was 25,003,335,680 bytes against a 40,425,037,824-byte process limit. Windows reported zero job memory-limit notifications. The cause of the underlying stall is still open. The 3,596 recorded presents include the account selector and loading. They provide no gameplay FPS estimate.

The launcher now also checks available physical memory and system commit once per second. It ends only the renderer job immediately below 1.5 GiB available physical memory or below 5 GiB available commit, after eight low physical samples below 3 GiB, or after three unavailable counter samples. Launch requires 8 GiB available physical memory and 32 GiB of available commit. The process limit leaves at least 8 GiB of initial commit headroom, up to a 42 GiB ceiling for the process. A job CPU cap leaves scheduling capacity for the desktop. Automated tests expire after 15 minutes. The guard cannot guarantee that Windows will always remain responsive between samples.

The header and its deterministic C++ test are included. With the MSVC x64 tools, compile and run the test using the following commands. It supplies synthetic counter values and uses no memory stress workload.

```bat
cl /EHsc /std:c++17 test_trial_pressure.cpp
test_trial_pressure.exe
```

Measured by danekbiglike with ChatGPT on 28 November 2026.
