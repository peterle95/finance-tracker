---
type: guide
title: Finance Tracker code wiki
description: Entry point for understanding the Python, Electron, Android, and Wear clients, their shared JSON contract, workflows, tests, and safe change routes.
tags: [quickstart, architecture, finance]
---

# Finance Tracker code wiki

This repository is a multi-client personal finance tracker. Python/Tkinter, Electron/React, and Android/Jetpack Compose share one split JSON directory; Wear capture sends transactions to the phone using a versioned reliable-delivery protocol. Start with [architecture](architecture/overview.md), then the [shared data contract](data-contract/index.md).

## Map

- [Python desktop](python-desktop/index.md): [persistence](python-desktop/persistence.md), [services](python-desktop/services.md), and [Tkinter UI](python-desktop/ui.md).
- [Modern Electron desktop](modern-desktop/index.md): [DataStore](modern-desktop/data-store.md), [domain](modern-desktop/domain.md), [reconciliation](modern-desktop/reconciliation.md), and [React UI](modern-desktop/ui.md).
- [Android and Wear](android/index.md): [data layer](android/data-layer.md), [domain](android/domain.md), and [Wear protocol](android/wear-protocol.md).
- [Workflows](workflows/shared-sync.md): [transactions](workflows/transaction-lifecycle.md), [legacy migration](workflows/legacy-migration.md), and [bank reconciliation](workflows/bank-reconciliation.md).
- [Operations and release](operations/release.md): scheduled wiki updates and Electron artifacts.

## Task routing

| Intent | Canonical page | Entry points/symbols | Focused validation |
|---|---|---|---|
| Change shared JSON shape or ownership | [Data contract](data-contract/index.md) | `shared/finance_data_schema.md`, `AppState`, `DataStore`, Android stores | `tests/test_persistence.py`, `data-store.test.ts`, Android codec/store tests |
| Change Python calculations | [Python services](python-desktop/services.md) | `finance_tracker/services/*`, feature tabs | Manual tab smoke; persistence regression |
| Change Electron persistence | [DataStore](modern-desktop/data-store.md) | `DataStore.load`, `saveDocument`, `saveCategoryChanges` | `npm test -- src/main/data-store.test.ts` |
| Change Electron formulas/reports | [Domain](modern-desktop/domain.md) | `src/shared/finance.ts`, settings modules | `npm test` |
| Change Android file access | [Android data layer](android/data-layer.md) | `FinanceRepository`, `FinanceDirectoryStore`, `FinanceJsonCodec` | `./gradlew test` |
| Change watch transaction delivery | [Transaction lifecycle](workflows/transaction-lifecycle.md) and [Wear protocol](android/wear-protocol.md) | `WatchOutbox`, `WatchSubmissionSender`, `PhoneTransactionIntake` | Wear delivery, intake, codec tests |
| Change category sync to watch | [Wear protocol](android/wear-protocol.md) | `CategorySnapshotPublisher`, `WatchCategoryCache` | `CategorySnapshotPublisherTest`, `WatchCategoriesTest` |
| Change packaging/CI wiki updates | [Operations](operations/release.md) | workflow YAML, `package.json` scripts | `npm run build`, workflow manual dispatch |

## Validation commands

Python: `python run.py` after installing `requirements.txt`; run the repository Python tests with `pytest`. Electron: from `modern-desktop`, run `npm run typecheck`, `npm test`, `npm run build`, and `npm run test:e2e`; `npm run package:win` emits `release/`. Android: from `android/`, run `./gradlew test assembleDebug` (Windows uses `gradlew.bat`).

## Safety boundaries

Select and synchronize the complete directory, not a single file. Wait for Syncthing before switching clients. Per-file writes are atomic in key implementations, but category operations span multiple files and are not globally atomic; retain Syncthing versioning and inspect conflict/orphan warnings. Never place credentials in shared JSON or documentation.

## Verification status

The source-grounded verification pass covered shared ownership/migration, Electron persistence safety, Python services, Android data/domain flow, protocol constraints, Wear delivery, category snapshots, and wiki automation. All eight questions passed after targeted repairs.

## Backlog

No source-grounded substantial component is intentionally deferred. Modern desktop AI Insights remains a product scope boundary documented in the UI/domain pages, not an undocumented repository area.
