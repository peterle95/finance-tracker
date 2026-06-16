# finance_data.json Schema

The desktop app persists state through `finance_tracker.state.AppState.save()`. The Android MVP reads and writes the same top-level JSON shape so files can be moved manually between desktop and phone.

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

Unknown root fields are preserved by Android import/export.

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
- `behavior_date` is optional and is preserved for desktop BNPL/Klarna-style rows.

Unknown transaction fields are preserved by Android import/export.

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

Android reads a small subset of `budget_settings` for dashboard and insights calculations:

- `monthly_income`: either the legacy number format or the newer list of `{ amount, description, start_date, end_date }`.
- `fixed_costs`: list of `{ amount, description|desc, start_date, end_date }`.
- `bank_account_balance`, `wallet_balance`, `savings_balance`, `investment_balance`, `money_lent_balance`: summed for the dashboard balance estimate.

All other budget settings remain desktop-owned and are preserved.
