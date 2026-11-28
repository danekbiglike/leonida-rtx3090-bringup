# RTX 3090, Series X 4K, constants-heap experiment

The 120-second window beside Yolanda's table produced **1,588 real frames (13.23 FPS)**. Five-second averages ranged from 13.0 to 13.4 FPS. The 95th-percentile frame took 114.4 ms and the longest took 184.0 ms. At least 5.44 GiB of physical RAM remained available.

The renderer was 70635d0095783ddd8307b435627f9af829dda78abbd14694015a3ecce96fb211, with the same Series X 3840×2160 profile, SSD save snapshot and 16 GiB resident ceiling as the [completed escort](../4k-guard-escort-and-interview). This trial enabled VICTORY_PORT_CONSTANTS=1. The log confirms that the renderer tried to use the in-place path and refused one 4 MiB request. This run's log filter did not record how much of the constants heap ultimately used that path.

Both boundary images show the cell. Lucia moved and interacted with the inmates afterwards, but the cell door remained closed when the trial was ended. The result measures the cell conversation only. It supplies neither an escort comparison nor a diagnosis of why the door was closed. The playable launcher continues to use the profile that completed the escort.
