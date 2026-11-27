# Remaining rendering failures with a warm pipeline library

The RTX 3090 log identified eight different compute shaders that the pinned translator could not produce. Three failed on a first-lane read under partial execution, four on a lane-read vector register without a 32-bit value, and one on a descriptor read as data. Each row lists the shader hash, instruction offset and error. [Eight translation failures](translator.csv)

Two unimplemented device pipeline-creation methods also reported calls. The highest logged counters were 16,384 for slot `0x1c8` and 2,048 for slot `0x218`. These counters include loading and play, and the methods only log at selected call counts.

In the recorded two-minute walk, all 22 periodic samples showed zero pipelines being built at the instant sampled. The same reports counted 322 to 680 omitted draws or dispatches per frame in their reporting windows. The renderer increments that aggregate for several reasons, including a missing host pipeline, unsuccessful binding and certain skipped stages. These records do not assign individual omissions or visible artifacts to one of the eight shaders. [Measured route and counters](https://github.com/danekbiglike/leonida-rtx3090-bringup/tree/df4e2a96c08f93601de1fbd2e0ed0833c65dd155/reports/2026-11-27-rtx3090/ssd-4k-background-textures)

The next rendering fix needs a translation or binding change and a scene comparison. A longer warmup alone cannot translate an operation rejected by the compiler. [Upstream translator](https://github.com/edsuuu/VI-BR-PORT/blob/2954325320735fa8b56a15e7f3e9654965e3462e/crates/victory-shader/src/emit/lower.rs#L9091) · [Draw and dispatch accounting](https://github.com/edsuuu/VI-BR-PORT/blob/2954325320735fa8b56a15e7f3e9654965e3462e/crates/victory-gpu/src/draw.rs)

Observation ID `danekbiglike/rtx3090-20261127-warm-pipeline-failures`. Local measurements by the danekbiglike bring-up project with ChatGPT. No shader bytecode or machine-specific runtime addresses are included.
