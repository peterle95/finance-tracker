---
type: user interface
title: Python Tkinter UI
description: MainView and feature tabs that bind user actions to AppState and Python domain services.
tags: [python, ui]
---

# Python Tkinter UI

`MainView` creates the notebook and shared shortcuts, passing one `AppState` to each tab. `AddTransactionTab` and `ViewTransactionsTab` handle transaction edits; budgets, reports, projection, net worth, goals, reconciliation, settings, and AI tabs delegate calculations to the corresponding modules in [Python services](services.md). UI callbacks save through state and refresh dependent views.

The UI owns presentation and validation affordances, while persistence and business invariants remain in `AppState` and services. Focused behavior is best checked through `tests/test_persistence.py` plus a manual Tkinter smoke run.
