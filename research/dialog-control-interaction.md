# Ticket #98 Research: Dialog and Editable-Control Interaction

Context pointer: [Resolve dialog and editable-control interaction](https://github.com/peterle95/finance-tracker/issues/98), part of [Keyboard Navigation System for Modern Desktop](https://github.com/peterle95/finance-tracker/issues/93).

## Question

How navigation mode should interact with Radix dialogs, focus trapping/restoration, text inputs, selects, checkboxes, contenteditable controls, and Space/Enter browser behavior in the existing Electron React app.

## Existing implementation

- `modern-desktop/package.json` uses `@radix-ui/react-dialog` `^1.1.19` and Electron `^43.1.0`.
- `App.tsx` has ordinary React page state and button-based navigation, but no global keyboard/navigation-mode handler.
- `TransactionEditor.tsx`, `LoanEditor.tsx`, `DefaultRangesDialog.tsx`, and `DefaultBehaviorsDialog.tsx` use controlled `Dialog.Root`, `Dialog.Portal`, `Dialog.Overlay`, `Dialog.Content`, `Dialog.Title`, `Dialog.Description`, and `Dialog.Close`.
- Dialog forms use native `input` (date, number, text), `select`, checkbox, and submit/cancel buttons. No `contentEditable` usage exists in `modern-desktop/src/renderer`.
- Dialog contents are portaled to `document.body`; the app's transaction editor is conditionally mounted from `App.tsx` and closed by `onOpenChange(false)`.
- Forms call `preventDefault()` on submit, validate/update React state, persist through app callbacks, and close explicitly. Cancel and close buttons use `Dialog.Close`.

## Authoritative evidence

### Radix Dialog

Radix Dialog documentation says the default `modal` mode renders content underneath inert, automatically traps focus, and closes on Escape. Its keyboard interaction contract is Tab/Shift+Tab within the dialog and Escape closes and moves focus to `Dialog.Trigger`. `Dialog.Content` exposes `onOpenAutoFocus`, `onCloseAutoFocus`, and `onEscapeKeyDown` for deliberate overrides. The controlled `open`/`onOpenChange` API supports the app's current pattern.

Source: [Radix Dialog documentation](https://www.radix-ui.com/primitives/docs/components/dialog), Features, Root, Content, and Keyboard Interactions sections.

The current app does not render `Dialog.Trigger`; it opens dialogs from React state and conditionally mounts the editor. Therefore focus restoration should be verified in the actual UI and, if needed, supplied through an explicit focus ref or `onCloseAutoFocus` rather than assuming an absent trigger can receive focus.

### Dialog accessibility

MDN's dialog guidance requires moving focus into the dialog, returning focus to the prior location on dismissal, wrapping Tab order, and preventing interaction with modal content outside the dialog. It also recommends labeling the dialog with its title and optionally description. The existing dialogs provide `Dialog.Title` and `aria-describedby` descriptions, matching this requirement.

Source: [MDN ARIA dialog role](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/dialog_role), Required JavaScript features and Labeling sections.

### Keyboard event and browser defaults

MDN documents `keydown` as preceding `beforeinput`/`input` for printable keys in inputs, textareas, and `contentEditable`; `KeyboardEvent.key` is layout/modifier-aware. Its example checks `event.defaultPrevented` before handling and calls `preventDefault()` only after deciding to handle a key. Space is represented by `" "`, Enter by `"Enter"`, and Escape by `"Escape"`.

Source: [MDN KeyboardEvent.key](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/key), KeyboardEvent sequence and example sections.

Native buttons are keyboard-activated controls. MDN states that a button inside a form defaults to `type="submit"` unless its type is explicitly set, while `type="button"` has no default behavior. The app correctly marks cancel/reset-style controls as `type="button"`; submit buttons intentionally retain form submission behavior.

Source: [MDN button element](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/button), `type` and Notes sections.

## Recommendation

1. Install one document-level navigation listener only while navigation mode is active. First return when `event.defaultPrevented` is true, the event has a modifier, or the target is an editable control (`input`, `textarea`, `select`, or an element whose `isContentEditable` is true). This preserves typing, native select operation, checkbox toggling, text editing, IME/input events, and browser behavior.
2. Detect an open modal from the dialog layer, or scope the listener to the active navigation root. While a Radix modal is open, suspend page/sidebar/header hint discovery and navigation. Do not use a second focus trap or manually move focus around the dialog; Radix owns that contract.
3. Dialog actions may be exposed as navigation targets, but activating a chosen hint should focus/select the target first by default. Immediate activation is an explicit setting. When activating a button or submit control, use its native `.click()`/normal activation path rather than synthesizing Space/Enter key events; this avoids duplicate form submission and preserves native semantics.
4. Never call `preventDefault()` for Space or Enter merely because navigation mode is active. Only prevent the event after a navigation command is positively recognized and only when the app is intentionally replacing the browser action. In editable controls, do not intercept these keys at all. A focused submit button should submit; a focused checkbox should toggle; a focused select should retain native platform behavior.
5. Treat Escape as a priority boundary: Radix handles Escape inside an open modal, including close/focus restoration. Navigation mode should not also exit or consume that Escape event. Outside a modal, Escape can exit navigation mode.
6. Preserve the pre-dialog focused element and verify restoration for state-mounted dialogs because the current dialogs have no `Dialog.Trigger`. If Radix cannot restore correctly in this structure, pass an explicit focus-restoration callback/ref via `onCloseAutoFocus`; do not globally focus the page or indicator.
7. There is no current `contentEditable` control, so support it generically with `target instanceof HTMLElement && target.isContentEditable`; no special component or dependency is justified.

## Validation boundary for destination work

Test the mode with a real browser/Electron interaction matrix: page buttons, dialog open/close, Tab and Shift+Tab wrapping, Escape close then restored focus, text/date/number inputs, native select open and option selection, checkboxes, submit buttons, and a temporary contenteditable fixture. Assert that normal typing and Space/Enter activation remain unchanged when mode is off or an editable control is focused, and that hint activation does not double-submit.
