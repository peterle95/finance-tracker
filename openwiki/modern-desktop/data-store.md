---
type: persistence component
title: Electron DataStore
description: Directory selection, split-file parsing, migration, serialized saves, category lifecycle, and CSV/export file operations in the Electron main process.
tags: [electron, persistence]
---

# Electron DataStore

`DataStore.load` resolves the remembered directory, initializes or migrates it, reads owner files and category transaction files, and returns a document plus connection warnings. `saveDocument` chains operations on `saveQueue`; `saveDocumentNow` compares the requested document with the previous one, rejects arbitrary simultaneous category and transaction changes, calls `saveCategoryChanges`, merges transaction edits against the latest on-disk category files, then writes changed `budget.json`, `net_worth.json`, `preferences.json`, `loans.json`, and `savings_goals.json` before rereading. `writeJsonAtomically` protects each file, not multi-file operations.

Category renames retain their existing `file_key`; additions allocate a slug and an empty array; populated-category deletion is rejected. Missing `categories.json` migrates legacy input or rejects a non-empty incomplete directory. Invalid JSON, non-object categories, invalid names/keys, duplicate names/keys, and non-object transaction rows return disconnected load errors. `findWarnings` reports conflict-named files and unregistered transaction files as warnings. `chooseBankCsv` opens a CSV, decodes UTF-8/Latin-1/CP1252, and delegates parsing; `exportText` writes a selected report file.

`src/main/data-store.test.ts` covers new-directory loading, malformed/incomplete directories, migration and verification, category add/rename/delete, queued saves and latest-file merging, orphan/conflict warnings, and owner-file persistence. `file-utils.test.ts` covers atomic replacement; reconciliation tests cover the CSV parser itself.
