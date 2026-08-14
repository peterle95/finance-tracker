---
type: data layer
title: Android data layer
description: SAF directory access, JSON codec/store/repository composition, preferences, category snapshots, and phone transaction intake boundaries.
tags: [android, persistence, saf]
---

# Android data layer

`SafFinanceDirectory` owns persisted tree access; `FinanceJsonFileStore` and `FinanceJsonCodec` read/write the split contract; `FinanceDirectoryStore` maps files into domain data and performs transaction/category changes; `FinanceRepository` exposes flows to `FinanceViewModel`. `SettingsDataStore` remembers the selected tree URI. `CategorySnapshotPublisher` keeps Wear categories current. Missing registered transaction files are initialized as empty arrays; malformed JSON, wrong top-level shapes, or invalid records are surfaced as load/store errors rather than silently rewritten, while missing transaction IDs are generated and persisted on the next write.

`PhoneTransactionIntake` is the phone boundary for watch submissions: it validates, serializes intake with a mutex, uses a Room submission ledger for idempotency, assigns transaction IDs, applies BNPL booking dates, and commits through the directory store. Tests cover codecs, directory operations, intake, snapshots, and persistence.
