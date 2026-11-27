# Batch constant-view updates on the card-step path

The 4K streaming run logged roughly 5,000–6,000 constant-buffer fills per frame near the prison corridor. Previously every worker walked the entire operation list and each matching slot took its own registry read lock. The patch partitions slots once, preserves the original assignment and update order per slot, and resolves consecutive slots of the same heap under one registry lock. Each group is capped at 64. The CPU already knows the resource-relative byte offset and now reuses that offset for the raw view. The ordinary draw path keeps its original interface.

The local release executable SHA-256 is 01207dc87710f553de2d92cab1a92ea87630dc77136717a8ef6d296986a02e28. Apply descriptor-batches.patch to the integrated renderer. file-pool-page-state.patch applies on top of the separate SSD-pool patch. It marks file-backed pages as already committed so the optional low-address rearranger cannot mistake written pages for unused ones. The measured profile disables that rearranger.

The release GPU tests passed on the RTX 3090. Eight card-step cases passed together, the in-flight dependency case passed in its own process with VICTORY_RELAY=2 and VICTORY_CARD_STEPS=2, and the constant-buffer-view test passed with ordinary and explicitly offset views. The attached output lists the tests. Both patches passed git apply --check. These tests establish correctness of the exercised paths. They do not measure gameplay performance.

Implemented and tested by danekbiglike with ChatGPT on 27 November 2026, on top of the VI-BR-PORT / VIctory work.
