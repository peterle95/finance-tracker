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

| Change area or user intent | Relevant wiki page | Exact source entry points | Important symbols or types | Focused tests | Minimal validation command |
|---|---|---|---|---|---|
| Change shared JSON shape or ownership | [Data contract](data-contract/index.md) | `shared/finance_data_schema.md`, `modern-desktop/src/main/data-store.ts`, Android data layer | `AppState`, `DataStore`, Android stores | `tests/test_persistence.py`, `data-store.test.ts`, Android codec/store tests | Run the affected test command from the owning client |
| Change Python calculations | [Python services](python-desktop/services.md) | `finance_tracker/services/*`, feature tabs | Service calculation functions and tab controllers | Repository Python tests; affected service tests | `pytest` |
| Change Electron persistence | [DataStore](modern-desktop/data-store.md) | `modern-desktop/src/main/data-store.ts` | `DataStore.load`, `saveDocument`, `saveCategoryChanges` | `modern-desktop/src/main/data-store.test.ts` | `npm test -- src/main/data-store.test.ts` (from `modern-desktop`) |
| Change Electron formulas/reports | [Domain](modern-desktop/domain.md) | `modern-desktop/src/shared/finance.ts`, settings modules | Shared finance/domain functions | Relevant Vitest suites | `npm test` (from `modern-desktop`) |
| Change Android file access | [Android data layer](android/data-layer.md) | `android/app/src/main/java/`, repository and codec implementations | `FinanceRepository`, `FinanceDirectoryStore`, `FinanceJsonCodec` | Android repository, codec, and store tests | `./gradlew test` (from `android/`) |
| Change watch transaction delivery | [Transaction lifecycle](workflows/transaction-lifecycle.md) and [Wear protocol](android/wear-protocol.md) | Android Wear outbox/sender and phone intake implementations | `WatchOutbox`, `WatchSubmissionSender`, `PhoneTransactionIntake` | Wear delivery, intake, and codec tests | Run the affected Android test class |
| Change category sync to watch | [Wear protocol](android/wear-protocol.md) | Android category publisher and watch cache implementations | `CategorySnapshotPublisher`, `WatchCategoryCache` | `CategorySnapshotPublisherTest`, `WatchCategoriesTest` | Run those focused Android tests |
| Change packaging/CI wiki updates | [Operations](operations/release.md) | `.github/workflows/openwiki-update.yml` (`update` job), `modern-desktop/package.json` scripts | OpenWiki update job, Electron package scripts | Workflow manual dispatch; Electron build checks | `npm run build` (from `modern-desktop`); manually dispatch workflow when CI changes |

## Validation commands

Python: `python run.py` after installing `requirements.txt`; run the repository Python tests with `pytest`. Electron: from `modern-desktop`, run `npm run typecheck`, `npm test`, `npm run build`, and `npm run test:e2e`; `npm run package:win` emits `release/`. Android: from `android/`, run `./gradlew test assembleDebug` (Windows uses `gradlew.bat`).

## Safety boundaries

Select and synchronize the complete directory, not a single file. Wait for Syncthing before switching clients. Per-file writes are atomic in key implementations, but category operations span multiple files and are not globally atomic; retain Syncthing versioning and inspect conflict/orphan warnings. Never place credentials in shared JSON or documentation.

## Verification status

The source-grounded verification pass covered shared ownership/migration, Electron persistence safety, Python services, Android data/domain flow, protocol constraints, Wear delivery, category snapshots, and wiki automation. All eight questions passed after targeted repairs.

## Backlog

No source-grounded substantial component is intentionally deferred. Modern desktop AI Insights remains a product scope boundary documented in the UI/domain pages, not an undocumented repository area.
