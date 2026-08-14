---
type: persistence component
title: Python persistence
description: AppState loading, split-file ownership, legacy migration, category lifecycle, and transaction persistence.
tags: [python, persistence]
---

# Python persistence

`finance_tracker/state.py:AppState` resolves `FINANCE_DATA_DIR`, legacy `FINANCE_DATA_FILE`, or the repository `shared/` default. `load` chooses split load, migration, or default initialization. `_load_split` validates category records and file keys, loads static owners and category transaction arrays, assigns missing IDs, and preserves extension fields. `save` computes desired owner files and removes deleted transaction files after validating lifecycle constraints.

Category creation allocates a stable slug; rename retains it and updates transaction/category-budget references; deletion rejects populated files; moves retain IDs and unknown fields. Per-file writes are atomic, but multi-file edits are not. `tests/test_persistence.py` covers split round trips, migration, unknown-field preservation, category operations, and safety failures. See the [shared contract](../data-contract/index.md).
