# Shared Finance Data Directory Contract

This document is the authoritative cross-client data contract. Finance Tracker data is a set of JSON files stored directly in one synchronized directory. Clients must synchronize and select the complete directory, not an individual file.

## File set

```text
categories.json
budget.json
net_worth.json
loans.json
savings_goals.json
preferences.json
transactions_expense_<file_key>.json
transactions_income_<file_key>.json
```

`categories.json` is the registry and migration-completion marker. It determines the complete expected transaction-file set. The six static files are singleton feature owners. There is no schema-version file.

`finance_data.json` is a legacy migration input only. It is not part of the live split dataset after migration.

All files are UTF-8 JSON. Dates use `YYYY-MM-DD`, money values are JSON numbers, and unknown fields must be preserved as described below.

## Categories and transaction-file identity

`categories.json` is an object with required `Expense` and `Income` arrays:

```json
{
  "Expense": [
    { "name": "Food", "file_key": "food" },
    { "name": "Café Bar", "file_key": "cafe-bar" }
  ],
  "Income": [
    { "name": "Salary", "file_key": "salary" }
  ]
}
```

Each entry is a record, not a string:

- `name`: non-empty display name, unique case-insensitively within its type.
- `file_key`: stable storage identity, unique within its type and matching `[a-z0-9]+(?:-[a-z0-9]+)*`.
- Other entry fields are extensions and remain on that entry.

The type prefix prevents expense/income collisions:

```text
Expense + food   -> transactions_expense_food.json
Income  + salary -> transactions_income_salary.json
```

The `file_key` is generated once from a lowercase ASCII kebab slug. Collisions use `-2`, `-3`, and so on. It never changes when `name` changes. Unknown root fields in `categories.json` are preserved in place.

### Category lifecycle

- Create: validate the name, allocate an unused `file_key`, add the registry record, and create its empty transaction array.
- Rename: retain `file_key`; update the category record, each owned transaction's `category`, and matching category-budget keys.
- Delete: allowed only when the owned transaction file is empty. A populated category blocks deletion. Successful deletion removes its registry record and transaction file.
- Move transaction: remove it from its source category file and add it to the destination category file. Keep its `id` and unknown fields.

Category edits and moves touch multiple files and are not transactionally atomic. An interrupted operation must be recovered from Syncthing versioning or inspected manually.

## Transactions

Each `transactions_<type>_<file_key>.json` contains an array of transactions owned by that category record:

```json
[
  {
    "id": "075b20b7-2a31-4ea9-b8ec-31fe6466de62",
    "date": "2026-07-01",
    "amount": 25.5,
    "category": "Food",
    "description": "Lunch",
    "behavior_date": "2026-06-16"
  }
]
```

- `id`: stable string identity. New rows use a UUID. Readers assign IDs to legacy rows that lack one; Python and Android persist the assigned ID during load, while modern desktop currently persists it with a later edit.
- `date`: required booking date.
- `amount`: required number.
- `category`: current category display name. The owning registry record/file is authoritative if it disagrees.
- `description`: free-text string.
- `behavior_date`: optional real spending date.
- Unknown fields stay inline on the transaction and survive edits, moves, and migration.

BNPL/pay-next-month expenses store the first day of the next month in `date` and the real spend date in `behavior_date`. For a spend on `2026-06-16`, use `date: "2026-07-01"` and `behavior_date: "2026-06-16"`. Normal month filters use `date`; behavior-based reports may use `behavior_date` with `date` as fallback.

## Static owner files

Clients should update only the file that owns a changed feature and preserve the latest unrelated fields.

### `budget.json`

```json
{
  "monthly_income": [
    {
      "amount": 2500,
      "description": "Salary",
      "start_date": "2026-01-01",
      "end_date": null
    }
  ],
  "fixed_costs": [
    {
      "amount": 900,
      "desc": "Rent",
      "start_date": "2026-01-01",
      "end_date": null
    }
  ],
  "daily_savings_goal": 10,
  "category_budgets": {
    "Expense": { "Food": 25 },
    "Income": {}
  },
  "_extra": {}
}
```

- `monthly_income`: income-source array. A legacy number is accepted as always-active base income and may be normalized to an array on write.
- `fixed_costs`: recurring-cost array. Readers accept `description` or `desc`; writers may canonicalize to `desc`.
- `daily_savings_goal`: per-day savings target.
- `category_budgets`: percentage maps keyed by category display name.

Income sources and fixed costs are active in every month overlapped by `start_date`/`end_date`. `end_date: null` means no end. Archiving sets `end_date`; deleting removes the record. Unknown fields on nested records remain inline.

### `net_worth.json`

```json
{
  "bank_account_balance": 1000,
  "wallet_balance": 50,
  "savings_balance": 5000,
  "investment_balance": 2500,
  "money_lent_balance": 0,
  "cash_balance": 25,
  "asset_snapshots": [
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
  ],
  "_extra": {}
}
```

All balances are numbers. Snapshots are identified by `date`, sorted by date by current clients, and preserve unknown inline fields. Recording an existing date replaces that snapshot.

### `loans.json`

```json
[
  {
    "id": "loan-1",
    "borrower": "Alex",
    "amount": 40,
    "description": "Tickets",
    "notes": "",
    "date": "2026-06-10"
  }
]
```

This array owns loans. `id` is the stable identity. Loan changes may also update `net_worth.json.money_lent_balance`. Unknown loan fields remain inline.

### `savings_goals.json`

```json
[
  {
    "name": "Emergency fund",
    "description": "",
    "target_amount": 5000,
    "allocated_amount": 1200,
    "priority": "High",
    "target_date": null,
    "created_date": "2026-01-01",
    "completion_date": null
  }
]
```

`priority` is normally `High`, `Medium`, or `Low`. Readers accept legacy `current_amount` as `allocated_amount`. Unknown goal fields remain inline.

### `preferences.json`

```json
{
  "ai_settings": { "api_key": "" },
  "default_behaviors": {
    "includeNegativeCarryover": true,
    "projectionMode": "target",
    "netWorthChangeMode": "month-by-month",
    "reportView": "pie",
    "reportType": "Expense",
    "reportDateBasis": "transaction",
    "reportHistoryMode": "total",
    "reportHistoryDisplay": "value",
    "reportIncludeRecurring": false,
    "reportShowHistoryLabels": false
  },
  "default_ranges": {
    "projectionMonths": 12,
    "projectionHistoryMonths": 6,
    "carryoverMonths": 3,
    "reportHistoryMonths": 6,
    "reportLineMonths": 6,
    "journeyHorizon": "12-months"
  },
  "_extra": {}
}
```

Preferences are shared hints. Clients apply supported values and preserve unsupported keys.

## Extensions and ownership

Known top-level ownership is fixed:

| Owner | Keys |
|---|---|
| `budget.json` | `monthly_income`, `fixed_costs`, `daily_savings_goal`, `category_budgets` |
| `net_worth.json` | six balance fields and `asset_snapshots` |
| `loans.json` | loan array |
| `savings_goals.json` | goal array |
| `preferences.json` | `ai_settings`, `default_behaviors`, `default_ranges` |

Unknown fields already associated with `budget.json` or `net_worth.json` are canonicalized under that file's `_extra` object. Readers also accept unknown owner fields temporarily left at top level and preserve them. Unknown fields on categories, transactions, array records, and preference subobjects remain inline.

Legacy data has no split owner. Migration stores it under these canonical preference extension keys:

```json
{
  "_extra": {
    "legacy_budget_settings": { "custom_setting": true },
    "legacy_root": { "custom_root": { "version": 2 } }
  }
}
```

- `legacy_budget_settings`: unknown keys from legacy `budget_settings`.
- `legacy_root`: unknown keys from the legacy root object.

Writers must not use these names for unrelated extensions. Modern desktop also reads the temporary aliases `_extra.budget_settings` and `_extra.document`, but canonical writes use the names above.

## Initialization and legacy migration

Migration runs only when `categories.json` is absent and a legacy `finance_data.json` is available:

1. Read the legacy object and preserve unknown root, settings, category, and transaction data.
2. Assign IDs to transactions that lack them.
3. Add categories referenced only by transactions.
4. Generate category records and all split owner/transaction files.
5. Reconstruct and compare the migrated data semantically.
6. Write `categories.json` last as the completion marker.

The legacy file is never modified or deleted and is the migration recovery copy; no additional backup is created. After successful migration, clients ignore it for normal reads and writes. On verification failure, `categories.json` is withheld or removed, but partial split files may remain; inspect them and restore/version before retrying.

`FINANCE_DATA_FILE` exists only for migration compatibility. It identifies the legacy file or lets clients infer its parent directory. New configuration must use a directory.

## Missing, orphan, and conflict files

- Missing registered transaction file: clients recreate it as `[]`.
- Missing static owner file: modern desktop and Android stop loading. Python currently supplies defaults and rewrites the missing file. Restore the missing version before opening a client when data may have existed.
- Orphan transaction file: a transaction filename not referenced by `categories.json` is ignored, retained, and reported. Reattach or recover it manually; clients do not merge or delete it automatically.
- Conflict copy: filenames containing Syncthing conflict markers are ignored and reported, not merged. Resolve them manually before further edits.
- Invalid JSON or wrong root type blocks that file from loading; clients do not silently repair malformed content.

Do not rename files manually. Change categories through a client so registry, transaction rows, budgets, and files stay aligned.

## Directory selection and synchronization

Store every expected file directly in one Syncthing folder such as `FinanceTrackerData`; do not place the files in a nested app subdirectory and do not sync only `finance_data.json`.

- Python desktop: uses `FINANCE_DATA_DIR` when set. Without configuration it uses the repository `shared/` directory. It has no directory picker.
- Modern desktop: choose/create the directory in the app. The selection is remembered. `FINANCE_DATA_DIR` is supported for development/automation.
- Android: Settings uses Storage Access Framework `OpenDocumentTree`. Choose the directory, not a JSON file. The app persists read/write tree permission and reloads on startup, resume, or manual reload.

When both desktop variables are set, `FINANCE_DATA_DIR` owns the split files and `FINANCE_DATA_FILE` is only the legacy migration source. Existing modern-desktop settings that stored a file path are interpreted as its parent directory.

Enable Syncthing file versioning. Ignore rules may include only the normal static and transaction filenames; conflict and temporary copies must not be propagated as live data.

## Write and concurrency limits

There is no database transaction, cross-file lock, compare-and-swap protocol, or automatic conflict merge across clients.

- Python writes a same-directory temporary file, flushes/fsyncs it, and replaces one target file.
- Modern desktop writes a same-directory temporary file and renames it over one target file; its queue serializes only that process.
- Android SAF writes and then verifies the target document, but the provider write is not an atomic rename and may truncate on failure.

Per-file replacement does not make category changes, migration, loan/balance updates, or transaction moves atomic across their several files. A move interrupted between destination and source writes may duplicate a row. Avoid simultaneous edits from different clients, let Syncthing settle before switching devices, inspect warnings, and use Syncthing versioning for recovery.
