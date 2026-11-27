# Fifteen-minute prison session with the SSD physical pool

The RTX 3090 renderer continued presenting frames through 15 minutes of process uptime. The session included loading, the prison-cell escort, the common area and movement near the gate. There were no Windows process memory-limit notifications. The peak job commit was 36,382,035,968 bytes against a 45,097,156,608-byte limit. Minimum system commit headroom was 15,739,428,864 bytes. An earlier interactive session on a different build and profile reached its process limit after 13m44s.

The lowest system headroom and Windows memory events are from sampled host counters and the job's completion port. Private commit at the end of minutes 10 and 15 was 35,854,217,216 and 36,338,769,920 bytes respectively. The run cleared the previous failure time but does not prove a leak was eliminated. The launch sequences, limits, scenes, and background load differed. The one-minute FPS includes menus or changing camera positions and is not an escort benchmark. The operator ended the test after the window to start the next renderer comparison.

Recorded by danekbiglike on 27 November 2026 with the 4K Series X profile.
