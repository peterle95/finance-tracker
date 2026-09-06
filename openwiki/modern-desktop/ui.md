---
type: user interface
title: Modern desktop React UI
description: React feature screens, document state flow, configurable keyboard navigation, and renderer tests for the Electron finance client.
tags: [react, ui, electron]
---

# Modern desktop React UI

`App.tsx` owns connection/document loading and dispatches changes through the preload `FinanceApi`. Screens cover dashboard, transactions/editor, budgets/category limits, goals/loans, net worth, projection, reports, reconciliation, and settings. Components render derived values from `src/shared/finance.ts`; persistence stays in the main-process [DataStore](data-store.md) behind the [Electron process boundary](../architecture/overview.md#electron-process-boundary).

## Keyboard navigation

`src/renderer/keyboard-navigation.ts` provides an opt-in hint mode for the whole renderer. Press the configured activation key (the default is Space) to label visible actionable elements with generated hints from the configured alphabet, then type a hint to focus and click that element. The hook limits discovery to the topmost visible dialog when one is open, ignores editable fields and modified/repeated/composing key events, refreshes hints after DOM mutations, and exits with Escape when no dialog is open. This is a renderer interaction layer: it activates existing button/link/input behavior rather than adding a second command or persistence path.

`App.tsx` stores normalized settings in browser `localStorage` under `finance-tracker-keyboard-navigation` and passes them to `SettingsScreen.tsx`. Settings validates a one-character activation key and an alphabet with at least two unique non-space characters; invalid persisted values fall back to `DEFAULT_KEYBOARD_NAVIGATION`. The `?` key opens contextual help while keyboard mode is active, and the settings reset action restores defaults. Because this state is local to the Electron renderer, it is not part of the shared finance JSON contract documented in [the data contract](../data-contract/index.md).

**Change navigation:** modify the hook and normalization rules in `modern-desktop/src/renderer/keyboard-navigation.ts`, update renderer/settings wiring in `App.tsx` and `components/SettingsScreen.tsx`, then update the keyboard, app, and settings suites. The focused command is `npm test -- src/renderer/keyboard-navigation.test.tsx src/renderer/App.test.tsx src/renderer/components/SettingsScreen.test.tsx` from `modern-desktop`; use `npm run typecheck` when changing the renderer API or types, and reserve `npm run test:e2e` for changes that cross the built Electron boundary.

Component tests also cover transactions, budget behavior, category limits, reports, net worth, and editor flows. `tests/e2e/desktop.spec.ts` is the broad smoke path; use `npm run typecheck` and the relevant Vitest suite for ordinary focused validation.
