# Paired-wave renderer in the prison cell on RTX 3090

The 4K output from the 26 November lighting branch reached Lucia's cell on the SSD. The 120 seconds starting with the first capture of the cellmate tutorial contained 197 accepted presents, averaging **1.64 FPS**. The player walked between the window, table and door and selected the interaction with Yolanda. The guard corridor is a separate route. Three five-second windows contained zero presents. [All presents](frames.csv) · [Window counts](metrics.json) · [Cell captures](cell.jpg)

The 95th percentile frame interval was 932 ms. The longest interval lasted 18.67 s. The renderer attributed 18.20 s of that frame to preparing buffer copies. All 17 pipeline reports in the interval recorded zero draws omitted for lack of a host pipeline. During the earlier transition into the prison, one 4.16 s frame included 1.97 s waiting for guest memory to finish remapping during texture refresh. These are two distinct sources of stalls. [Frame costs](frame-costs.csv)

Available physical memory stayed at or above 5.30 GiB during the two minutes. The peak resident set was 15.94 GiB. The executable used an SSD-backed guest page pool and a hard process working-set ceiling. The captures used for the four panels were taken at the offsets marked on the images. Capture and manual input occurred during this window. [System memory samples](memory.csv)

This experiment used a private copy of the older player state, the paired-wave shader compiler, and the Series X preset. The GPU and the RAM limit differ in their effect on each scene. These cell data do not establish equivalent visual quality everywhere or an improvement on the earlier 10.02 FPS corridor measurement. [Earlier 120-second corridor measurement](https://github.com/danekbiglike/leonida-rtx3090-bringup/tree/23ab4b45edecb7a96cac32f2aa8e3b611751e851/reports/2026-11-27-rtx3090/stable-player-corridor-boundary-captures)

Executable SHA-256 2696794b4b404a2b0870097e379e7c6088b64d97b60e1573de0e99c0de6268eb. Ryzen 7 3700X, RTX 3090 and 32 GiB system RAM. Measured by danekbiglike with ChatGPT on 28 November 2026.
