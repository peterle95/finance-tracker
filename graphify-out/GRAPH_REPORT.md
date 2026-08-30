# Graph Report - finance-use-ubuntu-for-changes  (2026-08-30)

## Corpus Check
- 196 files · ~260,570 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2128 nodes · 4822 edges · 124 communities (107 shown, 17 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 114 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `61d90ba4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- FinanceJsonCodec
- money
- FinanceViewModel
- FinanceDirectoryStore
- FinanceRepository
- WatchDelivery.kt
- GoalsTab
- Models.kt
- DashboardScreen.kt
- SettingsScreen.tsx
- finance.ts
- BudgetMath
- BudgetScreen.kt
- data-store.ts
- SettingsTab
- get_active_fixed_costs
- net_worth_tab.py
- App.tsx
- types.ts
- ReportsScreen.tsx
- PhoneTransactionIntake.kt
- ShortcutManager
- FinanceJsonCodecTest
- NetWorthMath
- ReconciliationTab
- App
- compilerOptions
- ReportsTab
- cloneDocument
- Implementation Advisor Report
- FinanceViewModel.kt
- ProjectionService
- devDependencies
- WatchCaptureTest
- BudgetScreen.tsx
- CategorySnapshot
- Modern Desktop App Details
- ai_insights_service.py
- Shared Finance Data Directory Contract
- Desktop App (Python/Tkinter)
- main_view.py
- BudgetsTab
- InMemoryFinanceDirectory
- TransactionSubmission
- .__init__
- reproduce_issue.py
- scripts
- ViewTransactionsTab
- AcknowledgementStatus
- AppState
- todayIsoDate
- build
- BudgetSettings
- FinanceApp
- WatchCaptureFormLogic
- TransactionProtocolCodec
- ProjectionTab
- package.json
- dependencies
- TransactionsScreen.kt
- Wear OS Data Layer Research for Issue #72
- CategorySnapshotPublisher.kt
- SavingsGoalsScreen.kt
- Finance Tracker
- Constraints From Official Documentation
- modern-desktop/domain.md
- nsis
- Android Launcher Icon
- python-desktop/index.md
- Ticket #98 Research: Dialog and Editable-Control Interaction
- AddTransactionTab
- quickstart.md
- Features
- Shared Data Model
- app_cover.png (drawable-nodpi)
- Android Launcher Icon Round
- ic_launcher_foreground.png (hdpi)
- data-contract/index.md
- Daily Usage
- Finance Tracker code wiki
- main() entry point (Tkinter)
- currency_service.py
- .setup_shortcuts
- openwiki/index.md
- workflows/index.md
- InsightsJson
- Issue tracker: GitHub
- Galaxy Watch 8 validation
- Architecture
- overview.md
- FinanceRepository.kt
- NetWorthChart
- Technology Stack
- Installation and Running
- Development Commands
- Test Coverage
- release.md
- mapNotNullIndexed
- Finance Tracker Context
- Migration and Recovery
- install-electron.mjs
- gradlew
- agents/domain.md
- triage-labels.md
- electron-vite
- @testing-library/user-event
- @types/node
- vitest

## God Nodes (most connected - your core abstractions)
1. `FinanceViewModel` - 70 edges
2. `FinanceDirectoryStore` - 54 edges
3. `FinanceRepository` - 51 edges
4. `SettingsTab` - 40 edges
5. `FinanceJsonCodec` - 39 edges
6. `AppState` - 33 edges
7. `FinanceDocument` - 33 edges
8. `FinanceDocument` - 31 edges
9. `money()` - 30 edges
10. `DataStore` - 30 edges

## Surprising Connections (you probably didn't know these)
- `Android MVP Plan` --semantically_similar_to--> `Finance Tracker Package`  [INFERRED] [semantically similar]
  docs/android_mvp_plan.md → code.txt
- `Android MVP Plan` --semantically_similar_to--> `Python Dependencies: matplotlib, numpy, python-dateutil`  [INFERRED] [semantically similar]
  docs/android_mvp_plan.md → requirements.txt
- `app-cover.png (repo root)` --semantically_similar_to--> `app_cover.png (drawable-nodpi)`  [INFERRED] [semantically similar]
  app-cover.png → android/app/src/main/res/drawable-nodpi/app_cover.png
- `Empty Test File` --conceptually_related_to--> `Finance Tracker Package`  [AMBIGUOUS]
  test_file.txt → code.txt
- `PersistenceTests` --uses--> `AppState`  [INFERRED]
  tests/test_persistence.py → finance_tracker/state.py

## Import Cycles
- None detected.

## Communities (124 total, 17 thin omitted)

### Community 0 - "FinanceJsonCodec"
Cohesion: 0.06
Nodes (21): FinanceDocument, FinanceJsonCodec, FinanceRecord, BudgetSettings, FinanceTransaction, FixedCost, IncomeSource, JsonArray (+13 more)

### Community 1 - "money"
Cohesion: 0.23
Nodes (19): AssetAllocation, money(), AllocationChart(), AssetBalanceCards(), AssetBreakdownChart(), drawAxisText(), AssetSnapshot, BudgetSettings (+11 more)

### Community 2 - "FinanceViewModel"
Cohesion: 0.09
Nodes (8): FinanceViewModel, BudgetSettings, FinanceTransaction, FixedCost, IncomeSource, Loan, SavingsGoal, TransactionType

### Community 3 - "FinanceDirectoryStore"
Cohesion: 0.08
Nodes (24): CategoryRecord, DirectoryLoadResult, FileOwner, Budget, Loans, NetWorth, SavingsGoals, FinanceDirectory (+16 more)

### Community 4 - "FinanceRepository"
Cohesion: 0.06
Nodes (17): FinanceRepository, BudgetSettings, FinanceTransaction, FixedCost, IncomeSource, Loan, SavingsGoal, TransactionType (+9 more)

### Community 5 - "WatchDelivery.kt"
Cohesion: 0.06
Nodes (28): DeliveryAttempt, Failed, NotNeeded, Succeeded, DeliveryResult, Retry, Success, ByteArray (+20 more)

### Community 6 - "GoalsTab"
Cohesion: 0.06
Nodes (39): auto_distribute_savings(), calculate_all_goals_summary(), calculate_goal_progress(), calculate_monthly_savings(), estimate_completion_date(), generate_goals_report(), get_total_allocated(), get_total_savings_available() (+31 more)

### Community 7 - "Models.kt"
Cohesion: 0.21
Nodes (22): booleanValue(), boundedInt(), BudgetReportDay, CategoryBudgets, IncomeSource, jsonPrimitiveOrNull(), JsonObject, nullableStringValue() (+14 more)

### Community 8 - "DashboardScreen.kt"
Cohesion: 0.06
Nodes (64): BarBreakdownMode, Categories, Flexible, OverUnder, Total, ChartDisplayMode, Percentage, Value (+56 more)

### Community 9 - "SettingsScreen.tsx"
Cohesion: 0.07
Nodes (29): DefaultBehaviorsDialog(), save(), DefaultBehaviorsDialogProps, DefaultRangesDialog(), save(), DefaultRangesDialogProps, KeyboardNavigationPrototype(), KeyboardNavigationPrototypeProps (+21 more)

### Community 10 - "finance.ts"
Cohesion: 0.13
Nodes (50): BudgetDepletionChart(), COLORS, formatSignedCurrency(), NetWorthScreen(), recordSnapshot(), asDate(), asNumber(), assetAllocation() (+42 more)

### Community 11 - "BudgetMath"
Cohesion: 0.06
Nodes (19): BudgetMath, BudgetSettings, FinanceTransaction, FixedCost, IncomeSource, YearMonth, FinanceTransaction, TransactionType (+11 more)

### Community 12 - "BudgetScreen.kt"
Cohesion: 0.17
Nodes (27): BudgetReport, BalanceEditor(), BudgetButton(), BudgetDepletionChart(), BudgetOutlinedButton(), BudgetOverview(), BudgetScreen(), BudgetSectionButton() (+19 more)

### Community 13 - "data-store.ts"
Cohesion: 0.10
Nodes (22): BUDGET_KEYS, CategoriesFile, CategoryRecord, categoryRecords(), DataStore, decodeCsv(), equal(), exists() (+14 more)

### Community 14 - "SettingsTab"
Cohesion: 0.08
Nodes (15): Update the readonly income display with CURRENT month's active income., Update the readonly costs display with CURRENT month's active fixed costs., Render the budget depletion graph in the main UI., Update the money lent entry with current balance., Open the lending manager window to manage individual loans., Refresh the loans treeview with current data., Populate the form fields when a loan is selected in the tree., Add a new loan and update the balance. (+7 more)

### Community 15 - "get_active_fixed_costs"
Cohesion: 0.09
Nodes (40): auto_assign_percentages(), compute_net_available_for_spending(), days_in_month_str(), generate_daily_budget_report(), get_active_fixed_costs(), get_active_monthly_income(), get_active_monthly_income_sources(), get_month_end_flexible_balance() (+32 more)

### Community 16 - "net_worth_tab.py"
Cohesion: 0.07
Nodes (33): delete_snapshot(), generate_net_worth_report(), get_asset_allocation_data(), get_asset_snapshots(), get_current_net_worth(), get_net_worth_change(), finance_tracker/services/asset_tracking_service.py Service for tracking asset…, Record current asset balances as a snapshot (+25 more)

### Community 17 - "App.tsx"
Cohesion: 0.13
Nodes (22): EditorState, navigation, Page, Theme, DashboardScreen(), TransactionEditor(), submit(), TransactionEditorProps (+14 more)

### Community 18 - "types.ts"
Cohesion: 0.07
Nodes (25): financeApi, ReconciliationScreen(), addRows(), chooseCsv(), DEFAULT_EXPENSE_CATEGORIES, DEFAULT_INCOME_CATEGORIES, datesApart(), findColumn() (+17 more)

### Community 19 - "ReportsScreen.tsx"
Cohesion: 0.10
Nodes (28): BudgetTooltip(), tooltipStyle, tooltipTextStyle, draftFromLoan(), LoanDraft, LoanEditor(), confirmSave(), submit() (+20 more)

### Community 20 - "PhoneTransactionIntake.kt"
Cohesion: 0.12
Nodes (16): android, RoomDatabase, legacyLedgerRows(), RoomSubmissionLedger, SubmissionLedger, SubmissionLedgerDao, SubmissionLedgerDatabase, SubmissionLedgerEntry (+8 more)

### Community 21 - "ShortcutManager"
Cohesion: 0.06
Nodes (16): Handle Ctrl+A shortcut to open Add Transaction tab, Handle Ctrl+N shortcut to clear Add Transaction form, Handle Alt+Left shortcut to go to previous tab, Handle Alt+Right shortcut to go to next tab, Handle Ctrl+S shortcut to save in current tab, Handle Ctrl+D or Delete shortcut to delete selected item, Handle Ctrl+E shortcut to edit selected item, Handle F5 shortcut to refresh current view (+8 more)

### Community 22 - "FinanceJsonCodecTest"
Cohesion: 0.09
Nodes (6): FinanceJsonFileStore, FinanceDocument, StateFlow, CategoryDefaults, SavingsGoal, FinanceJsonCodecTest

### Community 23 - "NetWorthMath"
Cohesion: 0.28
Nodes (5): NetWorthChange, NetWorthSummary, AssetSnapshot, BudgetSettings, NetWorthMath

### Community 24 - "ReconciliationTab"
Cohesion: 0.09
Nodes (26): BankTransaction, _amounts_match(), BankTransaction, _dates_close(), _detect_encoding_and_sep(), get_summary(), match_transactions(), parse_bank_csv() (+18 more)

### Community 25 - "App"
Cohesion: 0.14
Nodes (22): App(), applyLoadResult(), chooseDataFile(), content(), createDataFile(), deleteTransaction(), exportText(), loadData() (+14 more)

### Community 26 - "compilerOptions"
Cohesion: 0.07
Nodes (29): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+21 more)

### Community 27 - "ReportsTab"
Cohesion: 0.15
Nodes (6): Open a modal dialog to select categories for the line chart., Update the category button text to show selection count., Render the bar chart based on current breakdown and display modes, Get flexible income vs flexible costs data for each month, Handle click events on the bar chart, ReportsTab

### Community 28 - "cloneDocument"
Cohesion: 0.19
Nodes (19): CategoryLimitsScreen(), addCategory(), autoAssign(), removeCategory(), updateLimits(), goalsReport(), GoalsScreen(), addGoal() (+11 more)

### Community 29 - "Implementation Advisor Report"
Cohesion: 0.09
Nodes (21): 1. Repository Map, 2. Obsidian AI Vault Evidence, 3. Evidence Matrix, 4. Candidate Comparison, 5. Recommendation, 6. Phased Plan — Candidate E (Lending View Pop-up Editing), 7. Risks and Open Questions, Active practice signals (`wiki/topics/local-ai-agent-workflows.md`) (+13 more)

### Community 30 - "FinanceViewModel.kt"
Cohesion: 0.18
Nodes (11): FinanceAggregator, FinanceTransaction, JsonObject, YearMonth, DashboardSummary, FinanceTotals, TransactionCounts, JsonObject (+3 more)

### Community 31 - "ProjectionService"
Cohesion: 0.27
Nodes (6): BudgetSettings, NetWorthInterval, ProjectionMode, NetWorthTrend, TargetSavings, ProjectionService

### Community 32 - "devDependencies"
Cohesion: 0.08
Nodes (25): electron, electron-builder, jsdom, devDependencies, electron, electron-builder, jsdom, @playwright/test (+17 more)

### Community 33 - "WatchCaptureTest"
Cohesion: 0.13
Nodes (7): WatchCaptureInput, WatchCaptureSubmission, WatchCaptureTest, ActiveSubmission, Bundle, ComponentActivity, WearMainActivity

### Community 34 - "BudgetScreen.tsx"
Cohesion: 0.21
Nodes (17): BudgetScreen(), addIncome(), markLoanReturned(), saveBalances(), saveCost(), saveLoan(), saveLoanChanges(), updateSettings() (+9 more)

### Community 35 - "CategorySnapshot"
Cohesion: 0.20
Nodes (12): CategorySnapshot, CategorySnapshotAcceptance, Accepted, Rejected, Stale, ByteArray, Context, StateFlow (+4 more)

### Community 36 - "Modern Desktop App Details"
Cohesion: 0.16
Nodes (15): AI Insights Deferred, German-Bank CSV Reconciliation, Modern Desktop Data Safety (Atomic Writes), Modern Desktop Features, Modern Desktop App Details, Modern Desktop HTML Entry Point, Android MVP (Kotlin + Jetpack Compose), BNPL (Buy Now Pay Later) Booking (+7 more)

### Community 37 - "ai_insights_service.py"
Cohesion: 0.19
Nodes (10): _aggregate_transactions(), AIConfig, build_chat_messages(), build_insights_prompt(), _month_list(), Any, finance_tracker/services/ai_insights_service.py Service for generating AI…, request_ai_insights() (+2 more)

### Community 38 - "Shared Finance Data Directory Contract"
Cohesion: 0.07
Nodes (29): AddTransactionTab UI Class, AppState Class (State Management), Asset Tracking Service, Budget Calculator Service, Chart Generator (create_budget_depletion_figure, create_net_worth_figure, etc.), Finance Tracker Package, NetWorthTab UI Class, SettingsTab UI Class (Budget Report + Lending Manager) (+21 more)

### Community 39 - "Desktop App (Python/Tkinter)"
Cohesion: 0.22
Nodes (11): Android App (Kotlin/Jetpack Compose), android/, BNPL Convention, Desktop App (Python/Tkinter), finance_data.json, finance_tracker/, FinanceTracker class, Personal Finance Tracker (+3 more)

### Community 40 - "main_view.py"
Cohesion: 0.16
Nodes (18): finance_tracker/ui/help_window.py Displays the help and instructions window for…, show_help(), finance_tracker/ui/main_view.py Main application window and tab management., finance_tracker/ui/shortcuts.py This module handles the registration and…, Show the net worth report in a dialog, finance_tracker/ui/tabs/settings_tab.py Tab for configuring budget settings,…, finance_tracker/ui/tabs/view_transactions_tab.py Tab for viewing, filtering,…, close_window() (+10 more)

### Community 42 - "InMemoryFinanceDirectory"
Cohesion: 0.32
Nodes (4): InMemorySubmissionLedger, PhoneTransactionIntake, InMemoryFinanceDirectory, PhoneTransactionIntakeTest

### Community 43 - "TransactionSubmission"
Cohesion: 0.16
Nodes (3): TransactionAcknowledgement, TransactionSubmission, TransactionProtocolCodecTest

### Community 44 - ".__init__"
Cohesion: 0.17
Nodes (12): MainView, Update the toggle button label for the active theme., Toggle between dark and light themes., Ensure report/text widgets are updated after a theme switch., Show keyboard shortcuts reference window, apply_styles(), _apply_tk_widget_colors(), get_current_theme() (+4 more)

### Community 45 - "reproduce_issue.py"
Cohesion: 0.22
Nodes (3): date, MockDate, MockState

### Community 46 - "scripts"
Cohesion: 0.18
Nodes (11): scripts, build, dev, install:electron, package:win, postinstall, preview, test (+3 more)

### Community 47 - "ViewTransactionsTab"
Cohesion: 0.18
Nodes (5): Sort transactions by the specified column, Rebuild the tree view with current sorted transactions, Update the available options in filter dropdowns based on current transactions, Clear all filter fields and refresh, ViewTransactionsTab

### Community 48 - "AcknowledgementStatus"
Cohesion: 0.17
Nodes (9): AcknowledgementStatus, Accepted, Duplicate, Rejected, CategorySnapshotDefaults, SubmissionType, Expense, Income (+1 more)

### Community 49 - "AppState"
Cohesion: 0.09
Nodes (5): main(), finance_tracker/app.py Main application entry point and initialization., AppState, finance_tracker/state.py Manages the application state, including data loading,…, PersistenceTests

### Community 50 - "todayIsoDate"
Cohesion: 0.25
Nodes (7): formatAmountField(), hasThousandsGrouping(), parseAmountText(), todayIsoDate(), AddTransactionScreen(), LoanEditorScreen(), AmountTextTest

### Community 51 - "build"
Cohesion: 0.18
Nodes (10): build, appId, directories, files, productName, win, output, target (+2 more)

### Community 52 - "BudgetSettings"
Cohesion: 0.34
Nodes (5): AssetBalances, AssetSnapshot, BudgetSettings, NetWorthMathTest, ProjectionServiceTest

### Community 53 - "FinanceApp"
Cohesion: 0.21
Nodes (8): Bundle, ComponentActivity, MainActivity, Destination, FinanceApp(), ProjectionScreen(), SettingsScreen(), FinanceTrackerTheme()

### Community 56 - "ProjectionTab"
Cohesion: 0.23
Nodes (7): _build_monthly_net_worth_change_projection(), _build_target_savings_projection(), _format_signed_euro(), projection_text(), finance_tracker/services/projection_service.py Service for generating financial…, ProjectionTab, finance_tracker/ui/tabs/projection_tab.py Tab for projecting future financial…

### Community 57 - "package.json"
Cohesion: 0.33
Nodes (5): description, main, name, private, version

### Community 58 - "dependencies"
Cohesion: 0.18
Nodes (11): lucide-react, dependencies, lucide-react, @radix-ui/react-dialog, react, react-dom, recharts, @radix-ui/react-dialog (+3 more)

### Community 59 - "TransactionsScreen.kt"
Cohesion: 0.32
Nodes (10): CategoryDropdown(), Color, Modifier, MetricCard(), EditTransactionDialog(), Color, FinanceTransaction, SummaryValue() (+2 more)

### Community 60 - "Wear OS Data Layer Research for Issue #72"
Cohesion: 0.17
Nodes (11): Alternative: messages only, APIs and dependency, Category synchronization choices, Decision for the next implementation ticket, Galaxy Watch 8 implications, Message paths and payloads, Node discovery and routing, Not recommended for this ticket: full shared-file synchronization (+3 more)

### Community 61 - "CategorySnapshotPublisher.kt"
Cohesion: 0.27
Nodes (5): CategorySnapshotPublisher, newestCategoryPublicationRequest(), nextCategorySnapshot(), PendingCategorySnapshot, CategorySnapshotPublisherTest

### Community 62 - "SavingsGoalsScreen.kt"
Cohesion: 0.45
Nodes (10): SavingsGoalsSummary, ActionRow(), AllocationEditor(), GoalActions(), GoalEditor(), SavingsGoal, SavingsGoalCard(), SavingsGoalsScreen() (+2 more)

### Community 63 - "Finance Tracker"
Cohesion: 0.18
Nodes (10): Client Feature Matrix, Finance Tracker, First-Use Workflow, Important Technical Caveats, Key Source Files, Persistence and Concurrency Limits, Project Goals, Repository Layout (+2 more)

### Community 64 - "Constraints From Official Documentation"
Cohesion: 0.18
Nodes (10): Constraints From Official Documentation, Deduplication, Issue #75: Reliable Watch Delivery Constraints, Lifecycle and background execution, Local persistence, Minimal Protocol Shape, Reconnect and transport choice, Resolution (+2 more)

### Community 65 - "modern-desktop/domain.md"
Cohesion: 0.24
Nodes (6): Change navigation and validation, Electron DataStore, Extension and change navigation, Modern desktop finance domain, Files, Modern desktop React UI

### Community 66 - "nsis"
Cohesion: 0.40
Nodes (5): nsis, allowToChangeInstallationDirectory, createDesktopShortcut, createStartMenuShortcut, oneClick

### Community 67 - "Android Launcher Icon"
Cohesion: 0.50
Nodes (4): ic_launcher.png (hdpi), ic_launcher.png (mdpi), ic_launcher.png (xhdpi), Android Launcher Icon

### Community 68 - "python-desktop/index.md"
Cohesion: 0.22
Nodes (5): Bank reconciliation, Files, Python persistence, Python domain services, Python Tkinter UI

### Community 69 - "Ticket #98 Research: Dialog and Editable-Control Interaction"
Cohesion: 0.20
Nodes (9): Authoritative evidence, Dialog accessibility, Existing implementation, Keyboard event and browser defaults, Question, Radix Dialog, Recommendation, Ticket #98 Research: Dialog and Editable-Control Interaction (+1 more)

### Community 71 - "quickstart.md"
Cohesion: 0.31
Nodes (4): Android data layer, Android finance domain, Files, Wear transaction protocol

### Community 72 - "Features"
Cohesion: 0.25
Nodes (8): Bank CSV reconciliation, Budget planning, Features, Net worth and assets, Optional AI insights, Projections, Reports and charts, Transaction management

### Community 73 - "Shared Data Model"
Cohesion: 0.25
Nodes (8): BNPL date convention, Budget owner file, Live directory contents, Loans and savings goals, Net-worth owner file, Preferences, Shared Data Model, Transactions

### Community 74 - "app_cover.png (drawable-nodpi)"
Cohesion: 1.00
Nodes (3): app_cover.png (drawable-nodpi), Android Cover Image, app-cover.png (repo root)

### Community 75 - "Android Launcher Icon Round"
Cohesion: 0.67
Nodes (3): ic_launcher_round.png (hdpi), ic_launcher_round.png (mdpi), Android Launcher Icon Round

### Community 77 - "data-contract/index.md"
Cohesion: 0.32
Nodes (4): Files, Migration and integrity, Legacy migration, Shared-directory synchronization

### Community 78 - "Daily Usage"
Cohesion: 0.29
Nodes (7): Daily Usage, Manage categories, Reconcile a bank statement, Record a BNPL expense, Record a normal expense, Record income, Review budget status

### Community 81 - "Finance Tracker code wiki"
Cohesion: 0.29
Nodes (7): Backlog, Finance Tracker code wiki, Map, Safety boundaries, Task routing, Validation commands, Verification status

### Community 83 - "currency_service.py"
Cohesion: 0.33
Nodes (5): format_amount(), parse_amount(), finance_tracker/services/currency_service.py Central utility for parsing and…, Formats a float with dot as thousands separator and comma as decimal separator.…, Parses a currency string in comma notation. Example: '3.000,20' -> 3000.20,…

### Community 88 - ".setup_shortcuts"
Cohesion: 0.33
Nodes (3): Enable Enter key to activate focused buttons, Switch to a specific tab by index, Setup global keyboard shortcuts for the application

### Community 89 - "openwiki/index.md"
Cohesion: 0.33
Nodes (3): Directories, Files, OpenWiki navigation

### Community 90 - "workflows/index.md"
Cohesion: 0.33
Nodes (3): Bank reconciliation workflow, Files, Transaction lifecycle

### Community 92 - "Issue tracker: GitHub"
Cohesion: 0.40
Nodes (4): Conventions, Issue tracker: GitHub, Pull requests as a triage surface, Wayfinding operations

### Community 93 - "Galaxy Watch 8 validation"
Cohesion: 0.40
Nodes (4): Build, install, and identity checks, Galaxy Watch 8 validation, Manual matrix, Prerequisites

### Community 94 - "Architecture"
Cohesion: 0.40
Nodes (5): Android architecture, Architecture, Modern desktop architecture, Overall flow, Python architecture

### Community 95 - "overview.md"
Cohesion: 0.40
Nodes (3): Files, Electron process boundary, System architecture

### Community 96 - "FinanceRepository.kt"
Cohesion: 0.50
Nodes (3): Flow, JsonObject, FixedCost

### Community 97 - "NetWorthChart"
Cohesion: 0.50
Nodes (4): NetWorthChart, Allocation, Breakdown, NetWorth

### Community 98 - "Technology Stack"
Cohesion: 0.50
Nodes (4): Android, Modern desktop, Python desktop, Technology Stack

### Community 99 - "Installation and Running"
Cohesion: 0.50
Nodes (4): Android, Installation and Running, Modern desktop, Python desktop

### Community 100 - "Development Commands"
Cohesion: 0.50
Nodes (4): Android, Development Commands, Modern desktop, Python

### Community 101 - "Test Coverage"
Cohesion: 0.50
Nodes (4): Android tests, Modern desktop tests, Python tests, Test Coverage

### Community 103 - "mapNotNullIndexed"
Cohesion: 0.67
Nodes (3): R, T, mapNotNullIndexed()

### Community 105 - "Migration and Recovery"
Cohesion: 0.67
Nodes (3): Legacy migration, Migration and Recovery, Warnings and invalid files

## Ambiguous Edges - Review These
- `Finance Tracker Package` → `Empty Test File`  [AMBIGUOUS]
  test_file.txt · relation: conceptually_related_to

## Knowledge Gaps
- **316 isolated node(s):** `Budget`, `NetWorth`, `Loans`, `SavingsGoals`, `Pending` (+311 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Finance Tracker Package` and `Empty Test File`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `FinanceViewModel` connect `FinanceViewModel` to `money`, `FinanceRepository`, `DashboardScreen.kt`, `BudgetScreen.kt`, `todayIsoDate`, `FinanceApp`, `SavingsGoalsScreen.kt`, `TransactionsScreen.kt`, `FinanceViewModel.kt`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `TransactionType` connect `BudgetMath` to `FinanceJsonCodec`, `FinanceRepository.kt`, `FinanceDirectoryStore`, `Models.kt`, `DashboardScreen.kt`, `todayIsoDate`, `PhoneTransactionIntake.kt`, `FinanceApp`, `FinanceJsonCodecTest`, `TransactionsScreen.kt`, `FinanceViewModel.kt`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Why does `FinanceRepository` connect `FinanceRepository` to `FinanceRepository.kt`, `FinanceViewModel`, `FinanceDirectoryStore`, `DashboardScreen.kt`, `InMemoryFinanceDirectory`, `PhoneTransactionIntake.kt`, `CategorySnapshotPublisher.kt`, `FinanceViewModel.kt`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `FinanceDirectoryStore` (e.g. with `.categoriesCreateDeleteRenameAndBlockUnsafeDeletion()` and `.migratedDirectory()`) actually correct?**
  _`FinanceDirectoryStore` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `FinanceRepository` (e.g. with `CategorySnapshotPublisher` and `RoomSubmissionLedger`) actually correct?**
  _`FinanceRepository` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Budget`, `NetWorth`, `Loans` to the rest of the system?**
  _316 weakly-connected nodes found - possible documentation gaps or missing edges._