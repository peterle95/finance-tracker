# finance_data.json Schema

The desktop app persists state through `finance_tracker.state.AppState.save()`. The Android MVP reads and writes the same top-level JSON shape directly through a synced file URI.

## Root Object

```json
{
  "expenses": [],
  "incomes": [],
  "budget_settings": {},
  "categories": {
    "Expense": [],
    "Income": []
  }
}
```

- `expenses`: flexible expense transactions.
- `incomes`: flexible income transactions.
- `budget_settings`: desktop-owned settings such as balances, fixed costs, monthly income, goals, loans, snapshots, and AI settings. Android preserves this object during import/export.
- `categories`: editable category labels for each transaction type.

Unknown root fields are preserved by Android read/write operations.

## Transaction Object

Known transaction fields:

```json
{
  "id": "1781073241.664611",
  "date": "2026-06-10",
  "amount": 25.5,
  "category": "Food",
  "description": "Lunch",
  "behavior_date": "2026-06-09"
}
```

- `id` is optional. Older desktop rows may not have it. Android-created rows export with an `id`; imported rows without an `id` continue exporting without one.
- `date` uses `YYYY-MM-DD`.
- `amount` is a number.
- `category` is a string from the matching `categories` list when possible.
- `description` is free text.
- `behavior_date` is optional. For desktop and Android BNPL/Klarna-style rows, `date` is the booking date and `behavior_date` is the original spending date.

BNPL / pay-next-month expenses are booked on the 1st day of the next month. For example, an expense spent on `2026-06-16` is stored with `date: "2026-07-01"` and `behavior_date: "2026-06-16"`. Transaction month filters use the booked `date`, not `behavior_date`.

Unknown transaction fields are preserved by Android read/write operations.

## Category Defaults

If categories are missing or empty, both apps use compatible defaults.

Expense:

```text
Food, Transportation, Entertainment, Utilities, Shopping, Healthcare, Money Lent, Other
```

Income:

```text
Salary, Side Gig, Bonus, Gift, Investment, Other
```

## Budget Settings Used By Android

Android reads and writes the budget and net-worth subset of `budget_settings` while preserving unknown fields:

- `monthly_income`: either the legacy number format or the newer list of `{ amount, description, start_date, end_date }`.
- `fixed_costs`: list of `{ amount, description|desc, start_date, end_date }`. Android writes the desktop-friendly `desc` key.
- `bank_account_balance`, `wallet_balance`, `savings_balance`, `investment_balance`, `money_lent_balance`: summed for the dashboard balance estimate.
- `daily_savings_goal`: per-day savings target used by the daily budget report.
- `category_budgets.Expense`: percent limits by expense category.
- `asset_snapshots`: net-worth snapshots.

Unknown budget settings fields remain desktop-owned and are preserved by Android mutations.

### Income Source

```json
{
  "amount": 2500,
  "description": "Salary",
  "start_date": "2026-01-01",
  "end_date": null
}
```

An income source is active for a month when its date range overlaps that month. Legacy numeric `monthly_income` is still read as an always-active base income; Android may rewrite it to the list format when budget settings are edited.

### Fixed Cost

```json
{
  "amount": 900,
  "desc": "Rent",
  "start_date": "2026-01-01",
  "end_date": null
}
```

A fixed cost is active for a month when its date range overlaps that month. Archiving sets `end_date`; deleting removes the row.

### Asset Snapshot

```json
{
  "date": "2026-06-18",
  "bank_balance": 1000,
  "wallet_balance": 50,
  "savings_balance": 5000,
  "investment_balance": 2500,
  "money_lent_balance": 0,
  "note": "Month end",
  "net_worth": 8550
}
```

Snapshots are keyed by `date` in Android. Recording a snapshot for an existing date updates that entry and keeps the list sorted by date.

## Syncthing Compatibility

Use a Syncthing folder named `FinanceTrackerData` and sync only `finance_data.json`.

Android must connect to the file through Settings using Android's file picker. The app persists read/write URI permission and reloads the file on app start and resume. Each Android mutation reads the latest file first, writes the entire updated document, and refreshes from the written text.

The desktop app uses `finance_data.json` in the working directory by default. To use the Syncthing copy instead, set `FINANCE_DATA_FILE` to the synced file path before running `python run.py`.

Avoid editing the file from desktop and Android at the exact same second. Enable Syncthing file versioning so accidental overwrites or sync conflicts can be recovered.
