---
type: domain library
title: Modern desktop finance domain
description: TypeScript document types, normalization, budgeting, goals, net worth, projections, reports, and shared date semantics.
tags: [typescript, domain, finance]
---

# Modern desktop finance domain

`src/shared/types.ts` defines `FinanceDocument`, transactions, income, fixed costs, loans, goals, snapshots, settings, and the `FinanceApi` bridge contract. `finance.ts` normalizes unknown input, supplies defaults, preserves IDs, and implements monthly income/cost activity, transaction date-basis selection, carryover, daily budgets, category limits, goals, net worth, snapshots, projections, historical reports, spending pace, and heatmaps. `behavior-settings.ts` and `range-settings.ts` normalize user preferences within bounded values.

The test files beside these modules are the narrowest checks for formulas and normalization. Keep BNPL `date` versus `behavior_date` semantics aligned with [the data contract](../data-contract/index.md).
