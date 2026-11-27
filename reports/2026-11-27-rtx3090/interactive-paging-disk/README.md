# Disk activity during interactive 4K play

The game was on a SATA SSD. Windows had one 38 GiB pagefile, on a different physical drive, a mechanical HDD. We took 100 one-second system and disk samples while controlling Lucia in the prison cell on the ordinary-upload player launch. This interval includes preparation for the escort. [Samples](samples.csv)

The HDD was reading in **all 100 samples**, at a median of **2.63 MiB/s** and a median reported read latency of **20.58 ms**. The highest sampled average read latency was 146.77 ms. Available physical memory fell to 616 MiB, and the median system-wide page input rate was 1,879 pages per second.

In 24 sampled wall-clock seconds the renderer logged a frame of at least 200 ms. HDD reads were active in all 24 and also in all the other samples. Median HDD read throughput in those 24 seconds was 2.73 MiB/s. The largest logged slow frame during the sample was 525 ms. The renderer log has one-second timestamps. Disk counters reflect all activity on that drive, and system page input includes memory-mapped files. The samples therefore neither identify individual reads as pagefile reads nor establish that paging caused these stalls.

Windows paging settings were unchanged throughout collection. No FPS change from a pagefile move was measured. The interactive player used the integrated renderer, native Series X graphics and 3840×2160 output with manual controls. [Four timed replays on the same machine](https://github.com/danekbiglike/leonida-rtx3090-bringup/tree/65eacdfcab0189cbf702d531cb3f56688d5207af/reports/2026-11-27-rtx3090/ssd-4k-escort-comparison)

Measurement ID `danekbiglike/rtx3090-20261127-paging-disk`. Local measurements by the danekbiglike bring-up project with ChatGPT.
