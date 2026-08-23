---
type: domain library
title: Modern desktop finance domain
description: TypeScript document types, normalization, budgeting, goals, net worth, projections, reports, and shared date semantics.
tags: [typescript, domain, finance]
---

# Modern desktop finance domain

`src/shared/types.ts` defines `FinanceDocument`, transactions, income, fixed costs, loans, goals, snapshots, settings, and the `FinanceApi` bridge contract. `finance.ts` normalizes unknown input, supplies defaults, preserves IDs, and implements monthly income/cost activity, transaction date-basis selection, carryover, daily budgets, category limits, goals, net worth, snapshots, projections, historical reports, spending pace, and heatmaps. `behavior-settings.ts` and `range-settings.ts` normalize user preferences within bounded values.

These functions are consumed by the React screens through the preload API described in [the Electron process boundary](../architecture/overview.md#electron-process-boundary) and persisted by [DataStore](data-store.md). Keep BNPL `date` versus `behavior_date` semantics aligned with [the data contract](../data-contract/index.md): changing formulas without checking persistence normalization can make clients disagree about month filters.

## Extension and change navigation

For a new calculation or domain field, start with the type in `src/shared/types.ts`, normalization/default handling in `src/shared/finance.ts`, and the screen or report consumer. Preserve unknown fields during normalization and preserve transaction IDs so persistence can match edits. Preference changes belong in `behavior-settings.ts` or `range-settings.ts` and must retain their bounded/default behavior.

The focused checks are the adjacent `src/shared/*/*.test.ts` suites: `finance.test.ts` for formulas and normalization, `behavior-settings.test.ts` and `range-settings.test.ts` for preference constraints, and `reconciliation.test.ts` for CSV-domain parsing. Run `npm test -- src/shared/finance.test.ts` (plus the changed focused suite) from `modern-desktop`; use `npm run typecheck` whenever `FinanceApi`, `FinanceDocument`, or another shipped type changes. Run renderer tests when a screen consumer changes, and `npm run build` only when the public preload or bundled surface is affected.
