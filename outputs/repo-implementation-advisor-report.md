# Implementation Advisor Report

**Target repository:** `C:\Users\molze\GitHub\finance-use-ubuntu-for-changes` (Finance Tracker)
**Date:** 2026-07-25
**Scope:** Identify the highest-impact work candidates across three apps (Python/Tkinter desktop, Electron/React modern desktop, Android/Kotlin) based on the codebase state and the Obsidian AI vault.

**Assumptions:**
- The shared `finance_data.json` schema (`/shared/finance_data_schema.md`) is the stability boundary — no breaking changes to it.
- Both desktop apps and the Android app must remain independently runnable.
- "No AI" is a deliberate principle per vault notes; AI Insights was deferred in the modern desktop and should stay deferred.
- The user is the sole developer; effort estimates are for one person.

---

## 1. Repository Map

```
finance-use-ubuntu-for-changes/
├── run.py                          # Python entry point
├── requirements.txt                # Python deps
├── finance_tracker/                # Python/Tkinter desktop (original, complete)
│   ├── app.py, state.py
│   ├── services/                   # budget, projection, goals, reconciliation, AI insights, asset tracking, currency
│   └── ui/                         # charts, tabs for all features, help window
├── modern-desktop/                 # Electron/React/TypeScript (complete except AI)
│   ├── src/
│   │   ├── main/                   # Electron main process (data store, file utils)
│   │   ├── preload/                # Bridge API
│   │   ├── renderer/components/    # 17 screens + ui.tsx
│   │   └── shared/                 # finance.ts (400+ lines), types.ts, journey.ts, reconciliation.ts
│   ├── tests/e2e/                  # Playwright E2E
│   └── vitest unit tests           # 7 test files
├── android/                        # Kotlin/Jetpack Compose (MVP — gaps)
│   └── app/src/main/java/.../
│       ├── data/                   # JSON codec, file store, repository, DataStore
│       ├── domain/                 # Models, BudgetMath, FinanceAggregator, etc.
│       └── ui/screens/             # 7 screens: Dashboard, Add, Transactions, Budget, NetWorth, Projection, Goals, Settings
└── shared/
    └── finance_data_schema.md
```

### Feature presence by app

| Feature | Python Tkinter | Modern Desktop | Android |
|---|---|---|---|
| Dashboard + daily pace | Yes | Yes | Yes |
| Transactions CRUD + filter | Yes | Yes | Yes |
| BNPL (behavior_date) | Yes | Yes | Yes |
| Budget / fixed costs / income | Yes | Yes | Yes |
| Category limits | Yes | Yes | No |
| Savings goals | Yes | Yes | Yes |
| Reports (charts, history) | Yes | Yes | No |
| Net worth / snapshots | Yes | Yes | Yes |
| Projection | Yes | Yes | Yes |
| Exploration (simulator, journey, balancer) | No | Yes | No |
| CSV bank reconciliation | Yes | Yes | No |
| Text export | Yes | Yes | No |
| AI Insights | Yes | Deferred | No |
| Lending (loans) view | Yes | Yes | No |
| Day-of-week heatmap | No | Yes | No |

---

## 2. Obsidian AI Vault Evidence

The vault at `C:\Users\molze\GitHub\Obsidian\AI/` contains these relevant signals:

### Project intent (`Other/Ideas phone.md:18-23`)
```
Finance
1. Plan open source
2. Two separate repos? One for me and one open?
3. Local database
4. Emphasize no AI and totally local
5. In the lending view, change for both app and modern-desktop, instead of at the bottom a few boxes, remove it and add a text in every item called "modify", when clicked opens a pop-up window in desktop and a new window in the mobile app, which gives more space for notes and ability to modify everything else, when clicking on done, it shows the difference if the amount was changed and requires confirmation
```

### Active practice signals (`wiki/topics/local-ai-agent-workflows.md`)
- Privacy-oriented development: local-first, no cloud AI for personal finance data
- Prefers small, explicit changes over speculative architecture

### Career context (`wiki/projects/career-and-work-transition.md:67,73`)
- Android finance app development noted as recent project engagement (Jun 2026)
- Previous work at a finance startup (Numa) cited as best work environment

### Software engineering MOC (`wiki/mocs/software-engineering-moc.md`)
- Active use of Matt Pocock Skills workflow (wayfinder → to-spec → to-tickets → implement)
- Interest in database performance, operational engineering, and testing
- No mention of the finance tracker as an active project page in the projects index — it's not tracked as a formal "project" in the vault, which suggests it's treated as a living utility rather than a bounded deliverable

---

## 3. Evidence Matrix

| Finding | Source | Type |
|---|---|---|
| Android lacks Reports, Reconciliation, Exploration, Category Limits, Loans UI | `android/app/src/main/.../ui/screens/` has 7 screens vs modern desktop's 17 components | Repository evidence |
| Modern Desktop explicitly deferred AI Insights | `modern-desktop/README.md:23` | Repository evidence |
| AI Insights JSON preserved untouched by modern desktop | `modern-desktop/src/shared/types.ts:78` (ai_settings field) | Repository evidence |
| User wants lending view pop-up editing | `Other/Ideas phone.md:23` | Vault guidance |
| User wants local DB migration | `Other/Ideas phone.md:20` | Vault guidance |
| User wants open-source preparation | `Other/Ideas phone.md:18-19` | Vault guidance |
| User values "no AI, totally local" | `Other/Ideas phone.md:21` | Vault guidance |
| Exploration screen is the newest modern-desktop feature (July 2026 commits) | `git log --oneline -30` shows 15+ exploration commits | Repository evidence |
| JSON file is single source of truth across 3 apps | `shared/finance_data_schema.md`, all three apps read/write it | Repository evidence |
| Python app and modern desktop have near-feature parity (modern desktop has more) | Comparison of Python `finance_tracker/ui/tabs/` vs modern desktop `components/` | Repository evidence |

---

## 4. Candidate Comparison

### Candidate A: Android feature parity — Reports + Reconciliation + Category Limits + Loans

**What:** Build the 4 missing screens for Android to match modern desktop.

| Aspect | Detail |
|---|---|
| **Effort** | Medium-high (4 screens: data layer + domain logic + UI) |
| **Files touched** | 8-12 new files in android/domain/ and android/ui/screens/ |
| **Reusability** | Domain models exist; `BudgetMath.kt` and `FinanceAggregator.kt` already have report math. Reconciliation needs a new CSV parser. |
| **Risk** | Low — the data schema is stable, the existing screens are a template. |
| **Reversibility** | Full — isolated to new files, no schema changes. |
| **Vault alignment** | Weak — user mentions lending UI improvements but not general feature parity. |

### Candidate B: Lending view pop-up editing (desktop + Android)

**What:** Replace inline lending boxes with a modal/pop-up editor for loan items per `Ideas phone.md:23`.

| Aspect | Detail |
|---|---|
| **Effort** | Low |
| **Files touched** | Modern desktop: `BudgetScreen.tsx` (loans section). Android: `BudgetScreen.kt`. |
| **Reusability** | N/A — per-platform UI change |
| **Risk** | Low |
| **Reversibility** | Full |
| **Vault alignment** | Strong — directly requested in vault |

### Candidate C: Local database migration (SQLite)

**What:** Replace `finance_data.json` with SQLite as the primary store, keeping JSON export/import for Syncthing compatibility.

| Aspect | Detail |
|---|---|
| **Effort** | High — affects all 3 apps, adds a sync layer, must coexist with Syncthing |
| **Files touched** | All data layers in all 3 apps + new sync service |
| **Reusability** | Would standardize query logic |
| **Risk** | High — Syncthing is file-based; SQLite + Syncthing = corruption risk without careful export/import flow |
| **Reversibility** | Hard — once migrated, rollback requires re-exporting to JSON |
| **Vault alignment** | Stated desire, but conflicts with the "simple" principle in AGENTS.md and current Syncthing workflow |

### Candidate D: Open-source preparation

**What:** Split into two repos (public + private), sanitize config/keys, add LICENSE, CI, contribution docs.

| Aspect | Detail |
|---|---|
| **Effort** | Low-medium |
| **Files touched** | Repo config, new repo, CI files, docs |
| **Reusability** | N/A |
| **Risk** | Low-Medium — must avoid leaking personal data or synced file paths |
| **Reversibility** | Full — repos can be merged back |
| **Vault alignment** | Stated desire, but no evidence of active blockers or urgency |

### Candidate E: Lending improvements — full rewrite for loans feature

**What:** Implement the user's vault vision for a dedicated loan editing experience with confirmation dialogs, diff display on amount change, and note space.

| Aspect | Detail |
|---|---|
| **Effort** | Medium |
| **Files touched** | Modern desktop: `BudgetScreen.tsx` (add `LoanEditor` component). Android: `BudgetScreen.kt` (add loan dialog). Shared: none — loans already in schema. |
| **Reusability** | Per-platform UI only |
| **Risk** | Low — loans are already in the data model; this is a UX change only |
| **Reversibility** | Full |
| **Vault alignment** | Very strong — exact spec in `Ideas phone.md:23` |

---

## 5. Recommendation

**Implement Candidate E first** — lending view pop-up editing with diff confirmation.

**Why it wins:**
1. Directly matches the user's own spec in the vault (`Ideas phone.md:23`) — no discovery needed.
2. Smallest coherent change that preserves all boundaries — loans exist in the schema and both UIs, this is pure UX improvement.
3. Quick win on both platforms in a single session.
4. Teaches the cross-platform edit flow pattern that applies to Candidate A later.

**Then Candidate A** — Android feature parity (Reports, Reconciliation) — because it closes the feature gap that makes Android a first-class client. This is the work that has the most user-facing value: the user tracks finances on their phone.

**Defer:**
- Candidate C (local DB) — high risk, conflicts with Syncthing file-based sync. Revisit when JSON file grows past ~10MB or query latency becomes noticeable.
- Candidate D (open source) — no active blockers or urgency. Worth ~2 hours of sanitization work when the user is ready to publish.
- Candidate B (lending popup) — subsumed by Candidate E, which is the full implementation of the vault spec.

---

## 6. Phased Plan — Candidate E (Lending View Pop-up Editing)

### Phase 1: Modern Desktop

**Files:**
- `modern-desktop/src/renderer/components/BudgetScreen.tsx` — extract loans section, add `LoanEditor` dialog
- New file: `modern-desktop/src/renderer/components/LoanEditor.tsx` — modal with full fields: borrower, amount, description, date, notes; amount-change diff + confirmation on save

**Validation:**
```powershell
cd modern-desktop
npm run typecheck
npm test
$env:TEST_MODE="1"; npm run dev  # manual check
```

### Phase 2: Android

**Files:**
- `android/app/src/main/java/.../ui/screens/BudgetScreen.kt` — add loan editing dialog
- `android/app/src/main/java/.../ui/components/LoanEditorDialog.kt` — Compose dialog mirroring desktop UX

**Validation:**
- Android Studio build + JVM unit tests + emulator run

### Test strategy
- Modern desktop: vitest unit test for `LoanEditor` (render, submit, cancel, diff display). E2E: Playwright test for loan edit flow.
- Android: JVM unit test for loan mutation + confirmation logic.

---

## 7. Risks and Open Questions

| Risk | Mitigation |
|---|---|
| Loans data model may have edge cases (zero amounts, missing IDs, migrated data without IDs) | Use existing `normalizeLoan` in `finance.ts:125`; add same guard for Android in `Models.kt` |
| Android loan editing needs `behavior_date`-style fields? | Schema already has loans with `id, borrower, amount, description, date` — no change needed |
| Confirmation dialog on amount change could be annoying for small corrections | Show diff only when `abs(old - new) > 0.01` |
| Does the user want the diff confirmation on desktop only, or also on Android? | Open question — vault mentions both. Implement on both; the code is minimal. |

---

**Caveat:** Obsidian vault notes are personal and may not reflect current priorities — the daily raws from Jul 20-24 show the user is in a high-stress period (health, career), which may deprioritize feature work. The lending view improvement is the smallest committed step that aligns with stated intent without assuming additional bandwidth.
