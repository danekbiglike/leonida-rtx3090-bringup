# RTX 3090 at Yolanda's table with background GPU work disabled

In a 120-second Series X 4K cell conversation the game presented **12.63 real FPS**, with 7.8 FPS in the slowest five seconds. Average board power was **116.53 W** from the driver's two-second samples. The 95th-percentile frame took 114.63 ms, and the longest took 496.39 ms.

This release uses [the split descriptor-shape lock and lookup changes](https://github.com/trustno1-coder/VIctory-NVIDIA/pull/666) on the indexed refresh planner. The launcher disables the background compute job that keeps the GPU clocks elevated. The game data, shader quality, 3840×2160 output and 16 GiB resident ceiling match the previous Series X runs. Binary SHA-256 4746eaa472cd1d0771988d18729d9a63dd228d7ade449280b789334784536a6e. Six relevant test groups passed, totaling 113 tests.

The two boundaries show different angles of the same interaction. The run with the constants option at the same table rendered a median 4,547 draws per frame, while this sample rendered 5,850. The camera and renderer settings both changed, so these measurements cannot isolate either the power effect or the FPS effect of the GPU-clock setting. [Constants experiment](../4k-constants-heap-cell).
