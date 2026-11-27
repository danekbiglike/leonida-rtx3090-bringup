# Read-only card-step planner experiment

Thirty synthetic submissions each contain 200 constant-buffer fills. Each fill reads title memory. When a submission has no copy or placed-copy operation, the requested fills can keep their original order at dependency level zero. The patch keeps the original rejection checks and uses the general planner for mixed submissions.

On the Ryzen 7 3700X the median cost across twelve interleaved rounds was 1.493 ms for the original planner and 0.088 ms for the candidate per 6,000 synthetic fills. Each round repeats the workload forty times. Another application was running on the machine. These numbers are specific to this CPU-side benchmark. The frequency of qualifying submissions in gameplay and any change in FPS are unmeasured. This patch is separate from the renderer used for the measured escort.

The harness checks 10,000 deterministic input lists with two stages and two ordering settings, including operations that must fail, and checks three batches near the step-count limit. Both planners returned the same selected operations, rejection reasons and blocked dependencies.

To reproduce, apply read-only-plan.patch to a copy of the VI-BR-PORT integrated sources. Run `python assemble.py ORIGINAL_SOURCE PATCHED_SOURCE bench.rs`, then `rustc --edition=2024 -C opt-level=3 bench.rs -o bench.exe` and run the resulting program. The assembly script reads the original functions directly from the two source trees. Prepared and measured by danekbiglike with ChatGPT on 27 November 2026.
