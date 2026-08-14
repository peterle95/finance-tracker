---
type: persistence policy
title: Migration and integrity
description: Initialization, legacy conversion, atomic per-file writes, warnings, and recovery boundaries for the split finance directory.
tags: [migration, persistence, recovery]
---

# Migration and integrity

When `categories.json` is absent, clients either migrate an existing `finance_data.json` or initialize an empty directory; a non-empty directory without the registry is rejected. Python implements this in `AppState.load`/`_migrate_legacy`; Electron implements it in `DataStore.load`/`migrate`. Both assign UUIDs to missing transaction IDs, add categories inferred from transaction rows, write category-owned files, reconstruct the document, verify semantic equality, and leave the legacy input unchanged on failure.

Python maps unknown legacy `budget_settings` keys to `preferences.json._extra.legacy_budget_settings`, unknown legacy root keys to `_extra.legacy_root`, and tracks owner provenance in `_extra_owners`; category and transaction unknown fields remain inline. Electron reads canonical `legacy_budget_settings`/`legacy_root` plus temporary `_extra.budget_settings`/`_extra.document`, then writes canonical names. Both add UUIDs to missing rows, infer categories from row category values, emit one file per category, reread, and compare normalized semantics before completion. Python's `tests/test_persistence.py` covers legacy-to-split round trips, generated IDs, inferred categories, unknown root/settings/category/transaction fields, verification failure, and untouched legacy input; Electron `src/main/data-store.test.ts` covers migration creation, reconstruction, and failure handling.

Each JSON file is written through a same-directory temporary file and rename, but category rename/move/delete operations span multiple files and are not transactionally atomic. Electron serializes saves with `saveQueue`; Python protects file writes with atomic replacement but not cross-client coordination. Conflict and orphan files produce warnings. Syncthing versioning and manual inspection are the recovery mechanism; see [shared sync](../workflows/shared-sync.md).

Focused evidence: `tests/test_persistence.py`, `modern-desktop/src/main/data-store.test.ts`, and the migration sections of `shared/finance_data_schema.md`.
