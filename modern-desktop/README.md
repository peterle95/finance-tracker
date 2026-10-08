# Finance Tracker Modern Desktop

Electron 43, React 19, TypeScript, Vite, and Tailwind desktop client for the shared split JSON directory contract.

## Run locally

```powershell
cd modern-desktop
npm install
npm run dev
```

On first launch choose/create the directory containing `categories.json`, the static owner files, and all registered transaction files. The path is remembered in the Electron user-data directory. Development and automation can set `FINANCE_DATA_DIR`; `FINANCE_DATA_FILE` is legacy parent-directory compatibility only.

## Features

- Dashboard, transaction entry/editing, BNPL booking, filtering, and sorting.
- Budgets, recurring income/costs, category limits, loans, goals, and snapshots.
- Category/history/line/weekday/pace reports, projection, and text export.
- German-bank CSV reconciliation.
- Clickable Syncthing conflict notices with side-by-side review, explicit record/setting choices, and confirmed cleanup.
- Shared preferences and unknown JSON fields are preserved; AI Insights remains deferred.

## Data safety

Writes target only changed owner/category files where possible. Modern desktop uses same-directory temporary files and rename for each JSON file, but multi-file operations are not atomic and the save queue protects only this process. Keep Syncthing versioning enabled and wait for synchronization before switching clients.

Click a conflict notice to inspect both file paths and their differing records or settings. Keep the current file, use the conflict copy, or choose a version for each difference. Loans and transactions are matched by unique IDs; savings goals by unique names; object files by top-level keys. Files without reliable record identities offer whole-file choices. Confirmation saves the chosen content to the normal filename and deletes only the selected conflict copy after validation and reload. If either version changes during review, refresh the preview. Orphan transaction files still require manual inspection.

See [`../shared/finance_data_schema.md`](../shared/finance_data_schema.md) for the complete contract and migration behavior.

## Verify and package

```powershell
npm run typecheck
npm test
npm run build
npm run test:e2e
npm run package:win
```

The NSIS installer is written to `modern-desktop/release/`.

On Windows, run `npm run package:win`, launch the generated installer, and keep
the desktop shortcut option enabled. The installer creates a desktop shortcut
that launches Finance Tracker Modern with the default Electron icon.
