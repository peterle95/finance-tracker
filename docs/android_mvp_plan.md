# Android MVP Plan

## Summary

The standalone `android/` app uses Kotlin, Jetpack Compose, Material 3, Preferences DataStore, Android Storage Access Framework (SAF), and kotlinx.serialization. It shares the split JSON directory contract in [`../shared/finance_data_schema.md`](../shared/finance_data_schema.md) with both desktop clients.

## Architecture

- `data/`: persisted tree URI, SAF directory access, split-file store, JSON compatibility, and repository orchestration.
- `domain/`: transactions, categories, budgets, goals, net worth, reports, and calculations.
- `ui/`: Compose navigation, screens, components, theme, and view model.

The selected synchronized directory is the financial source of truth. DataStore stores only app settings, including the persisted SAF tree URI.

## Screens

- Dashboard: current-month totals, daily budget, balance estimate, charts, loans, goals, and net worth.
- Add Transaction: type, amount, category, description, date, and optional BNPL booking.
- Transactions: filters plus transaction update/delete.
- Settings: connect/reload directory, status/warnings, categories, budgets, and balances.

## Compatibility rules

- Settings launches `OpenDocumentTree`; users select the synchronized directory, not a JSON file.
- Android takes persistent read/write permission and reloads on app start, resume, and manual request.
- Mutations read their current owner files, preserve unknown fields, write only required owners, verify each write, and refresh state.
- Android-created transactions use UUID `id`; legacy missing IDs are assigned and persisted on load.
- BNPL stores the first of next month in `date` and real spend date in `behavior_date`.
- Category `file_key` values are stable lowercase ASCII kebab identifiers. Rename retains the key; populated-category deletion is blocked; transaction moves keep IDs and unknown fields.
- Unknown legacy settings/root data lives in `preferences.json._extra.legacy_budget_settings` and `.legacy_root`.
- Conflict and orphan files are reported and left untouched. Missing registered transaction files are recreated; missing static files block loading.

SAF writes directly to a document and verifies the result; it cannot guarantee atomic replacement. Multi-file category edits, moves, migration, and loan/balance changes are also not atomic.

## Syncthing setup

1. Create a folder such as `FinanceTrackerData` and enable versioning.
2. Synchronize the complete split file set directly in that folder, not only legacy `finance_data.json`.
3. In Android Settings, connect the folder through the directory picker.
4. Point both desktop clients at the same directory.
5. Wait for synchronization before switching clients and resolve warnings manually.

If only a legacy `finance_data.json` exists, Android migrates it once, verifies the split result, and writes `categories.json` last. The legacy source remains unchanged; no second backup is created.

## Verification

```powershell
cd android
.\gradlew.bat test assembleDebug
```

Manual acceptance:

1. Connect a Syncthing-managed directory in Settings.
2. Add, edit, move, and delete transactions; confirm only category-owner files change.
3. Create, rename, and delete an empty category; confirm `file_key` stays stable on rename.
4. Confirm populated-category deletion is blocked.
5. Edit budgets, loans, goals, and balances; confirm desktop clients read the changes.
6. Confirm conflict/orphan warnings and app-start/resume reload behavior.
