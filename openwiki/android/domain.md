---
type: domain library
title: Android finance domain
description: Kotlin models and pure calculations for aggregation, budgets, projections, net worth, goals, charts, amounts, and transaction UI rules.
tags: [android, kotlin, domain]
---

# Android finance domain

`Models.kt` defines the document model. `FinanceAggregator`, `BudgetMath`, `ProjectionService`, `NetWorthMath`, `SavingsGoals`, and `DashboardCharts` derive feature values without owning persistence. `TransactionUiLogic` centralizes date/BNPL and editor rules; `AmountText` handles user-facing money parsing/formatting; `InsightsJson` decodes insight payloads.

Focused unit tests cover each calculation family, including negative/edge cases. Keep results compatible with the TypeScript [domain library](../modern-desktop/domain.md) and shared JSON semantics.
