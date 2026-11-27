# Back off failed spare-page refills in the ray structure builder

Yorivel identified a low-address allocation failure that made the NVIDIA fork retry a 64 MiB arena on every build dispatch. The upstream test was on an RTX 4090. Our RTX 3090 integration already releases failed reservations and rejects a full descriptor registry before allocating. It still retried speculative refills on later dispatches in the same frame. [Original investigation and fix](https://github.com/trustno1-coder/VIctory-NVIDIA/pull/88)

The local patch records the frame of the last failed speculative refill and allows another refill on the next frame. A request for a page that is already needed retains its independent allocation attempt, even in the frame of a failed refill. Successful refills still populate as many spares as before. The first failed speculative refill is logged once per process. The change reserves no additional memory at startup.

The regression checks four requests: a failed refill, a suppressed refill, a demand request in the same frame, and a refill on the next frame. The allocator sees three attempts. The test also checks that the failures leave no arena or free pages behind. The seven release memory-module tests passed on the local Windows x64 system. [Patch and regression](spare-refill.patch) · [Test results](tests.txt)

This evidence covers the allocation failure path. An FPS gain or prevention of long-session memory growth requires a separate gameplay measurement. Apply the patch to the integrated source after the allocation rollback fix. Run `cargo test --release --locked -p victory-gpu --lib memory::tests -- --test-threads=1`.

Local adaptation and regression by danekbiglike with ChatGPT, 28 November 2026. Provenance marker `danekbiglike/rtx3090-20261128-spare-refill`. Original retry investigation credit belongs to Yorivel.
