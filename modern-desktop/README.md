# Finance Tracker Modern Desktop

The original Python/Tkinter desktop app remains unchanged. This separate Electron app reads and writes the same finance_data.json contract used by the Python and Android clients.

## Run locally

~~~powershell
cd modern-desktop
npm install
npm run dev
~~~

On first launch, choose the existing synced finance_data.json. In development, the app also detects the repository data file or the FINANCE_DATA_FILE environment variable. The selected path is remembered in the app user-data directory.

## What it includes

- Modern dashboard, transaction entry/editing, BNPL booking, filtering, and sorting.
- Budget balances, recurring income and costs, daily pace, category limits, loans, savings goals, and snapshots.
- Category, history, line, weekday, and pace reports; projection and text export.
- German-bank CSV reconciliation with exact/fuzzy matches and category suggestions.
- Dark emerald-and-gold and light themes, plus a file connection/reload screen.

AI Insights is intentionally deferred in this version. Its existing budget_settings.ai_settings JSON is preserved without being used or changed.

## Data safety

Each mutation reloads the selected file, preserves unknown JSON fields, then writes an atomic replacement. Keep Syncthing versioning enabled and avoid editing the same file from multiple clients at the exact same time.

## Verify and package

~~~powershell
npm run typecheck
npm test
npm run build
npm run test:e2e
npm run package:win
~~~

The Windows NSIS installer is written to modern-desktop/release/.
