# Android MVP Plan

## Summary

The Android app lives in `/android` as a standalone Kotlin project. It does not import or rewrite the Python/Tkinter desktop app, but it shares the `finance_data.json` contract documented in `/shared/finance_data_schema.md`.

The MVP uses Jetpack Compose, Material 3, DataStore, Android's Storage Access Framework, and kotlinx.serialization.

## Architecture

- `data/`: DataStore app settings, synced-file state, JSON read/write, and repository orchestration.
- `domain/`: transaction models, category defaults, dashboard aggregation, and shared finance calculations.
- `ui/`: Compose navigation shell, theme, components, screens, and the Android view model.

`finance_data.json` is the source of truth. DataStore stores only app settings such as the persisted Storage Access Framework URI.

## Screens

- Dashboard: current-month income, expenses, net, top expense categories, and balance estimate from preserved desktop balances.
- Add Transaction: Expense/Income toggle, amount, category, description, ISO date input, optional BNPL / pay-next-month expense toggle, and synced JSON write.
- Transactions: list with month/category/type/search filters and delete action.
- Settings: connect synced file, reload synced file, connection status, and category editing.

## Compatibility Rules

- Android connects to an existing synced `finance_data.json` through Settings.
- The selected URI is persisted with read/write permission.
- On app start and resume, Android reloads the selected file.
- Before every add, delete, or category edit, Android reads the latest file, applies the change, writes the whole JSON document back, and refreshes UI state.
- Android preserves unknown root fields and unknown transaction fields.
- Android-created rows include a UUID `id`.
- Android BNPL expenses mirror desktop semantics by writing the booked `date` as the 1st of the next month and the original spending date as `behavior_date`.
- Transaction month filtering uses the booked `date`, not `behavior_date`.
- Deletes use exported JSON `id`, not a local database id.
- Advanced desktop settings are not edited by Android in MVP.

## Syncthing Setup

Recommended folder name: `FinanceTrackerData`.

Only sync `finance_data.json` in that folder. Enable Syncthing file versioning for safety. Avoid editing from desktop and Android at the exact same second because Syncthing syncs at file granularity.

Desktop can use the synced file with:

```bash
export FINANCE_DATA_FILE="$HOME/Syncthing/FinanceTrackerData/finance_data.json"
python run.py
```

## Test Strategy

JVM unit tests cover:

- JSON import from desktop-style files.
- JSON document mutation back to desktop-compatible shape.
- BNPL booking-date calculation and `behavior_date` export.
- Transaction month filtering by booked date, including BNPL rows.
- Monthly totals including fixed costs and base monthly income.
- Category totals and flexible transaction counts.
- Reloading Android app state from changed file text.

Manual acceptance:

1. Open `/android` in Android Studio.
2. Sync and build the project.
3. Run unit tests.
4. Connect a Syncthing-managed `finance_data.json` in Android Settings.
5. Add/delete/edit categories on Android and confirm the same file updates.
6. Load the same file from desktop with `FINANCE_DATA_FILE`.
