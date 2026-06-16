# Android MVP Plan

## Summary

The Android app lives in `/android` as a standalone Kotlin project. It does not import or rewrite the Python/Tkinter desktop app, but it shares the `finance_data.json` contract documented in `/shared/finance_data_schema.md`.

The MVP uses Jetpack Compose, Material 3, Room, DataStore, and kotlinx.serialization.

## Architecture

- `data/`: Room database, DAO classes, DataStore category settings, JSON import/export, and repository orchestration.
- `domain/`: transaction models, category defaults, dashboard/insights aggregation, and JSON summary rendering.
- `ui/`: Compose navigation shell, theme, components, screens, and the Android view model.

Room stores transaction rows and preserved desktop metadata. DataStore stores editable category lists and small app settings.

## Screens

- Dashboard: current-month income, expenses, net, top expense categories, and balance estimate from preserved desktop balances.
- Add Transaction: Expense/Income toggle, amount, category, description, ISO date input, and Room persistence.
- Transactions: list with type/category/search filters and delete action.
- Insights: placeholder view that renders the generated JSON summary used by the future AI insight flow.
- Settings: category editing plus Storage Access Framework import/export for `finance_data.json`.

## Compatibility Rules

- Import replaces the local Android dataset only after parsing succeeds.
- Export writes top-level `expenses`, `incomes`, `budget_settings`, and `categories` keys.
- Android preserves unknown root fields and unknown transaction fields.
- Android preserves imported desktop rows without `id`; Android-created rows include an export id.
- Advanced desktop settings are not edited by Android in MVP.

## Test Strategy

JVM unit tests cover:

- JSON import from desktop-style files.
- JSON export back to desktop-compatible shape.
- Monthly totals including fixed costs and base monthly income.
- Category totals and flexible transaction counts.

Manual acceptance:

1. Open `/android` in Android Studio.
2. Sync and build the project.
3. Run unit tests.
4. Add transactions on an emulator or phone.
5. Import the repo’s `finance_data.json`, export a new `finance_data.json`, and load it from the desktop app with `python run.py`.
