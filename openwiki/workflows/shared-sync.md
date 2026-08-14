---
type: workflow
title: Shared-directory synchronization
description: How clients select, read, write, and recover the synchronized split finance directory.
tags: [workflow, synchronization]
---

# Shared-directory synchronization

Select the complete directory in Python (`FINANCE_DATA_DIR`), Electron's directory picker, or Android's SAF tree picker. Each client reads `categories.json` first, derives the expected transaction files, then reads static owners and category arrays. Writes preserve unknown fields and use per-file atomic replacement where implemented.

Syncthing must finish before another client edits. Category renames, moves, and deletes touch multiple files and are not cross-file atomic; conflict/orphan warnings require manual review and Syncthing version history. The [data contract](../data-contract/index.md) defines ownership; [migration](../data-contract/migration-and-integrity.md) covers incomplete directories.
