---
type: user interface
title: Modern desktop React UI
description: React feature screens, document state flow, and renderer tests for the Electron finance client.
tags: [react, ui, electron]
---

# Modern desktop React UI

`App.tsx` owns connection/document loading and dispatches changes through the preload `FinanceApi`. Screens cover dashboard, transactions/editor, budgets/category limits, goals/loans, net worth, projection, reports, reconciliation, and settings. Components render derived values from `src/shared/finance.ts`; persistence stays in the main-process [DataStore](data-store.md).

Component tests cover transactions, budget behavior, category limits, reports, net worth, and editor flows. `tests/e2e/desktop.spec.ts` is the broad smoke path; use `npm run typecheck` and `npm test` for focused validation.
