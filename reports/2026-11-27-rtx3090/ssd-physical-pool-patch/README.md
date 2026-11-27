# Optional file-backed storage for the large physical page pool

Implemented and exercised on Windows by danekbiglike. An interactive 4K session had previously exhausted its process commit limit at 13m44s. This experiment gives one large physical allocation a dedicated SSD file. Windows still manages the existing system page file.

Apply ssd-page-pool.patch on top of the integrated build with the previously published fallback allocation fix. Set VICTORY_PAGE_POOL_DIR in the renderer environment to an existing writable directory on the SSD. The first eligible 1–8 GiB physical pool can use this backing. The file is unique to the process and deleted when its handles and views close. Other requests and file creation failures take the ordinary path. Windows desktop apps and restricted launchers must both have access to the selected directory under their own identity.

The release build SHA-256 is 5ddc4f14297533d16d5fc6a753e582dfcd90ae1804eb5f316df475d0a4ca41ac. The patch applied to a clean copy of the two affected paths. The module suite passed 18 tests on the Ryzen 7 3700X with one benchmark excluded. The new regression test exercises zero-initialization, slot reuse after failure, sharing across three views including a replaced placeholder, and deletion after the final release.

On first in-game use the runtime reported 6,538,919,936 bytes backed by the file. This establishes that the live title actually uses the new branch. Frame rate and long-session memory behavior require separate measurements.
