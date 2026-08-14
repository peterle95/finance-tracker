---
type: workflow
title: Legacy migration
description: Conversion of monolithic finance_data.json into the split directory with semantic verification and recovery behavior.
tags: [workflow, migration]
---

# Legacy migration

Migration runs only when `categories.json` is absent and `finance_data.json` exists. Python `AppState._migrate_legacy` and Electron `DataStore.migrate` normalize legacy expenses, incomes, categories, settings, unknown fields, and IDs; create category-owned files plus static owner files; reconstruct the document; and compare semantics before treating migration as complete. The legacy input remains unchanged.

A malformed legacy object or failed verification aborts without writing the completion marker. A non-empty directory missing `categories.json` is rejected rather than guessed. See [migration integrity](../data-contract/migration-and-integrity.md) and [shared schema](../data-contract/index.md).
