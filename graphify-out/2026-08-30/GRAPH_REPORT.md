# Graph Report - .  (2026-07-12)

## Corpus Check
- 9 files · ~218,738 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1393 nodes · 2835 edges · 91 communities (73 shown, 18 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 48 edges (avg confidence: 0.83)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Desktop Data Models|Desktop Data Models]]
- [[_COMMUNITY_Android Compose UI Layer|Android Compose UI Layer]]
- [[_COMMUNITY_Dashboard & Budget State|Dashboard & Budget State]]
- [[_COMMUNITY_Desktop Settings & Display|Desktop Settings & Display]]
- [[_COMMUNITY_Transaction & Category Models|Transaction & Category Models]]
- [[_COMMUNITY_Android Theme & UI Constants|Android Theme & UI Constants]]
- [[_COMMUNITY_AI Insights Service|AI Insights Service]]
- [[_COMMUNITY_Android JSON Serialization|Android JSON Serialization]]
- [[_COMMUNITY_Android Budget Settings|Android Budget Settings]]
- [[_COMMUNITY_Savings Goals|Savings Goals]]
- [[_COMMUNITY_Budget Types (Python)|Budget Types (Python)]]
- [[_COMMUNITY_Modern Desktop Screens|Modern Desktop Screens]]
- [[_COMMUNITY_Android ViewModel & Settings|Android ViewModel & Settings]]
- [[_COMMUNITY_Keyboard Shortcuts|Keyboard Shortcuts]]
- [[_COMMUNITY_Reports & Charts Tab|Reports & Charts Tab]]
- [[_COMMUNITY_Modern Desktop Goals & Budget|Modern Desktop Goals & Budget]]
- [[_COMMUNITY_Modern Desktop Data Store|Modern Desktop Data Store]]
- [[_COMMUNITY_Net Worth Tracking|Net Worth Tracking]]
- [[_COMMUNITY_Shared Budget Types|Shared Budget Types]]
- [[_COMMUNITY_Modern Desktop Net Worth|Modern Desktop Net Worth]]
- [[_COMMUNITY_Python Goals Service|Python Goals Service]]
- [[_COMMUNITY_Desktop Budgets Tab|Desktop Budgets Tab]]
- [[_COMMUNITY_Budget Settings Types (Android)|Budget Settings Types (Android)]]
- [[_COMMUNITY_Transaction Filtering UI|Transaction Filtering UI]]
- [[_COMMUNITY_Bank Reconciliation Tab|Bank Reconciliation Tab]]
- [[_COMMUNITY_Modern Desktop Category Limits|Modern Desktop Category Limits]]
- [[_COMMUNITY_TypeScript Configuration|TypeScript Configuration]]
- [[_COMMUNITY_Python Chart Renderer|Python Chart Renderer]]
- [[_COMMUNITY_Desktop Main Window|Desktop Main Window]]
- [[_COMMUNITY_Dashboard Metrics|Dashboard Metrics]]
- [[_COMMUNITY_Budget Types (Legacy)|Budget Types (Legacy)]]
- [[_COMMUNITY_Electron Build Config|Electron Build Config]]
- [[_COMMUNITY_Android Codec Tests|Android Codec Tests]]
- [[_COMMUNITY_Asset Tracking Service|Asset Tracking Service]]
- [[_COMMUNITY_Modern Desktop Budget Screen|Modern Desktop Budget Screen]]
- [[_COMMUNITY_Modern Desktop Docs & Rationale|Modern Desktop Docs & Rationale]]
- [[_COMMUNITY_Android Transaction Types|Android Transaction Types]]
- [[_COMMUNITY_Desktop Conceptual Architecture|Desktop Conceptual Architecture]]
- [[_COMMUNITY_Shared Reconciliation Logic|Shared Reconciliation Logic]]
- [[_COMMUNITY_Cross-Platform Architecture|Cross-Platform Architecture]]
- [[_COMMUNITY_Desktop Windowing|Desktop Windowing]]
- [[_COMMUNITY_AI Insights Tab UI|AI Insights Tab UI]]
- [[_COMMUNITY_Android BNPL Logic Tests|Android BNPL Logic Tests]]
- [[_COMMUNITY_Android Budget Math Tests|Android Budget Math Tests]]
- [[_COMMUNITY_Test Mocks & Reproduction|Test Mocks & Reproduction]]
- [[_COMMUNITY_Dev Scripts (npm)|Dev Scripts (npm)]]
- [[_COMMUNITY_Add Transaction Tab|Add Transaction Tab]]
- [[_COMMUNITY_Android Amount Formatting|Android Amount Formatting]]
- [[_COMMUNITY_Desktop App State|Desktop App State]]
- [[_COMMUNITY_Android Dashboard Charts Tests|Android Dashboard Charts Tests]]
- [[_COMMUNITY_Electron Builder Config|Electron Builder Config]]
- [[_COMMUNITY_Python Report Builder|Python Report Builder]]
- [[_COMMUNITY_Projection Tab|Projection Tab]]
- [[_COMMUNITY_Desktop Help Window|Desktop Help Window]]
- [[_COMMUNITY_Android Insights JSON|Android Insights JSON]]
- [[_COMMUNITY_Android Projection Tests|Android Projection Tests]]
- [[_COMMUNITY_Package Metadata|Package Metadata]]
- [[_COMMUNITY_React Dependencies|React Dependencies]]
- [[_COMMUNITY_Currency Formatting|Currency Formatting]]
- [[_COMMUNITY_Python Projection Service|Python Projection Service]]
- [[_COMMUNITY_Shortcut Setup|Shortcut Setup]]
- [[_COMMUNITY_Android Settings DataStore|Android Settings DataStore]]
- [[_COMMUNITY_Android Main Activity|Android Main Activity]]
- [[_COMMUNITY_Android Amount Text Tests|Android Amount Text Tests]]
- [[_COMMUNITY_Android Net Worth Math Tests|Android Net Worth Math Tests]]
- [[_COMMUNITY_NSIS Installer Config|NSIS Installer Config]]
- [[_COMMUNITY_Android Launcher Icons|Android Launcher Icons]]
- [[_COMMUNITY_App Entry Point (Python)|App Entry Point (Python)]]
- [[_COMMUNITY_Android Aggregator Tests|Android Aggregator Tests]]
- [[_COMMUNITY_Android Navigation|Android Navigation]]
- [[_COMMUNITY_Android Synced File Status|Android Synced File Status]]
- [[_COMMUNITY_Android Projection Screen|Android Projection Screen]]
- [[_COMMUNITY_Android Settings Screen|Android Settings Screen]]
- [[_COMMUNITY_App Cover Images|App Cover Images]]
- [[_COMMUNITY_Android Round Icons|Android Round Icons]]
- [[_COMMUNITY_Android Icon Foregrounds|Android Icon Foregrounds]]
- [[_COMMUNITY_Android Category Defaults|Android Category Defaults]]
- [[_COMMUNITY_Android Theme|Android Theme]]
- [[_COMMUNITY_E2E Tests|E2E Tests]]

## God Nodes (most connected - your core abstractions)
1. `FinanceViewModel` - 43 edges
2. `FinanceRepository` - 42 edges
3. `FinanceJsonCodec` - 38 edges
4. `SettingsTab` - 38 edges
5. `FinanceDocument` - 32 edges
6. `String` - 30 edges
7. `String` - 24 edges
8. `money()` - 24 edges
9. `ShortcutManager` - 23 edges
10. `FinanceDocument` - 23 edges

## Surprising Connections (you probably didn't know these)
- `Android MVP Plan` --semantically_similar_to--> `Finance Tracker Package`  [INFERRED] [semantically similar]
  docs/android_mvp_plan.md → code.txt
- `Android MVP Plan` --semantically_similar_to--> `Python Dependencies: matplotlib, numpy, python-dateutil`  [INFERRED] [semantically similar]
  docs/android_mvp_plan.md → requirements.txt
- `app-cover.png (repo root)` --semantically_similar_to--> `app_cover.png (drawable-nodpi)`  [INFERRED] [semantically similar]
  app-cover.png → android/app/src/main/res/drawable-nodpi/app_cover.png
- `Empty Test File` --conceptually_related_to--> `Finance Tracker Package`  [AMBIGUOUS]
  test_file.txt → code.txt
- `CodeRabbit Configuration` --references--> `Finance Tracker Package`  [INFERRED]
  .coderabbit.yaml → code.txt

## Import Cycles
- None detected.

## Communities (91 total, 18 thin omitted)

### Community 0 - "Desktop Data Models"
Cohesion: 0.10
Nodes (22): BudgetSettings, CategoryState, Double, FinanceTransaction, FixedCost, IncomeSource, Int, JsonObject (+14 more)

### Community 1 - "Android Compose UI Layer"
Cohesion: 0.07
Nodes (53): Double, List, Modifier, String, FinanceViewModel, BudgetSettings, Color, Double (+45 more)

### Community 2 - "Dashboard & Budget State"
Cohesion: 0.08
Nodes (18): Boolean, BudgetSettings, CategoryState, DashboardSummary, Double, FinanceTransaction, FixedCost, JsonObject (+10 more)

### Community 3 - "Desktop Settings & Display"
Cohesion: 0.08
Nodes (16): finance_tracker/ui/tabs/settings_tab.py  Tab for configuring budget settings, fi, Update the readonly income display with CURRENT month's active income., Update the readonly costs display with CURRENT month's active fixed costs., Render the budget depletion graph in the main UI., Update the money lent entry with current balance., Open the lending manager window to manage individual loans., Refresh the loans treeview with current data., Populate the form fields when a loan is selected in the tree. (+8 more)

### Community 4 - "Transaction & Category Models"
Cohesion: 0.09
Nodes (16): BudgetSettings, CategoryState, Double, FinanceTransaction, FixedCost, Flow, IncomeSource, JsonObject (+8 more)

### Community 5 - "Android Theme & UI Constants"
Cohesion: 0.11
Nodes (48): Boolean, Color, Double, FinanceViewModel, Float, List, Modifier, Paint (+40 more)

### Community 6 - "AI Insights Service"
Cohesion: 0.07
Nodes (45): Any, _aggregate_transactions(), AIConfig, build_chat_messages(), build_insights_prompt(), _month_list(), finance_tracker/services/ai_insights_service.py  Service for generating AI insig, request_ai_insights() (+37 more)

### Community 7 - "Android JSON Serialization"
Cohesion: 0.12
Nodes (43): Double, Int, JsonObject, List, String, AssetAllocation, AssetBalances, AssetSnapshot (+35 more)

### Community 8 - "Android Budget Settings"
Cohesion: 0.17
Nodes (24): Boolean, BudgetSettings, CategoryState, Double, FinanceTransaction, FixedCost, Int, JsonObject (+16 more)

### Community 9 - "Savings Goals"
Cohesion: 0.08
Nodes (18): GoalsTab, finance_tracker/ui/tabs/goals_tab.py  Tab for creating and managing savings goal, Handle mouse wheel scrolling, Update scrollregion when goals container changes, Update the width of the canvas window to match the canvas, Recursively bind mouse wheel event to all children, Refresh the goals display, Update the savings overview display (+10 more)

### Community 10 - "Budget Types (Python)"
Cohesion: 0.14
Nodes (24): CategoryLimitsScreen(), ReconciliationScreen(), SettingsScreen(), SettingsScreenProps, TransactionEditor(), TransactionEditorProps, TransactionsScreen(), TransactionsScreenProps (+16 more)

### Community 11 - "Modern Desktop Screens"
Cohesion: 0.21
Nodes (13): Boolean, BudgetSettings, Double, FinanceTransaction, FixedCost, IncomeSource, Int, List (+5 more)

### Community 12 - "Android ViewModel & Settings"
Cohesion: 0.17
Nodes (32): Boolean, BudgetSettings, Color, Double, FinanceViewModel, Float, List, Modifier (+24 more)

### Community 13 - "Keyboard Shortcuts"
Cohesion: 0.07
Nodes (15): Handle Ctrl+A shortcut to open Add Transaction tab, Handle Alt+Left shortcut to go to previous tab, Handle Alt+Right shortcut to go to next tab, Handle Ctrl+S shortcut to save in current tab, Handle Ctrl+D or Delete shortcut to delete selected item, Handle Ctrl+E shortcut to edit selected item, Handle F5 shortcut to refresh current view, Handle Ctrl+Shift+R to generate report in current tab (+7 more)

### Community 14 - "Reports & Charts Tab"
Cohesion: 0.11
Nodes (9): finance_tracker/ui/tabs/reports_tab.py  Tab for generating and viewing various, Open a modal dialog to select categories for the line chart., Update the category button text to show selection count., Render the bar chart based on current breakdown and display modes, Get category-wise data for each month, Get flexible income vs flexible costs data for each month, Get total income vs total expenses for each month, Handle click events on the bar chart (+1 more)

### Community 15 - "Modern Desktop Goals & Budget"
Cohesion: 0.14
Nodes (21): DashboardScreen(), formatSignedCurrency(), ProjectionMode, ProjectionScreen(), ChartKind, COLORS, DAYS, HistoryDisplay (+13 more)

### Community 16 - "Modern Desktop Data Store"
Cohesion: 0.11
Nodes (13): NetWorthTab, finance_tracker/ui/tabs/net_worth_tab.py  Tab for tracking and visualizing net w, Refresh all data and displays, Update the current net worth display, Refresh the snapshots tree view, Record a new asset snapshot, Delete the selected snapshot, Generate the selected chart type (+5 more)

### Community 17 - "Net Worth Tracking"
Cohesion: 0.20
Nodes (10): BudgetSettings, Double, Int, List, LocalDate, SavingsGoal, String, SavingsGoalProgress (+2 more)

### Community 18 - "Shared Budget Types"
Cohesion: 0.11
Nodes (17): decodeCsv(), exists(), LocalConfig, categoryList(), DEFAULT_EXPENSE_CATEGORIES, DEFAULT_INCOME_CATEGORIES, mergeDocuments(), moneyLentFromLoans() (+9 more)

### Community 19 - "Modern Desktop Net Worth"
Cohesion: 0.18
Nodes (20): BudgetScreen(), AssetAllocationItem, AutoAssignResult, computeNetAvailableForSpending(), DailyBudgetOverview, defaultDocument(), getActiveFixedCosts(), getActiveMonthlyIncome() (+12 more)

### Community 20 - "Python Goals Service"
Cohesion: 0.15
Nodes (21): auto_distribute_savings(), calculate_all_goals_summary(), calculate_goal_progress(), calculate_monthly_savings(), estimate_completion_date(), generate_goals_report(), get_total_allocated(), get_total_savings_available() (+13 more)

### Community 21 - "Desktop Budgets Tab"
Cohesion: 0.18
Nodes (3): BudgetsTab, finance_tracker/ui/tabs/budgets_tab.py  Tab for managing category budget limit, Handle category type change (Expense/Income)

### Community 22 - "Budget Settings Types (Android)"
Cohesion: 0.16
Nodes (6): finance_tracker/ui/tabs/view_transactions_tab.py  Tab for viewing, filtering,, Sort transactions by the specified column, Rebuild the tree view with current sorted transactions, Update the available options in filter dropdowns based on current transactions, Clear all filter fields and refresh, ViewTransactionsTab

### Community 23 - "Transaction Filtering UI"
Cohesion: 0.24
Nodes (9): BudgetSettings, Double, Int, List, LocalDate, String, NetWorthMath, NetWorthChange (+1 more)

### Community 24 - "Bank Reconciliation Tab"
Cohesion: 0.16
Nodes (6): BankTransaction, Notebook, _find_candidates(), finance_tracker/ui/tabs/reconciliation_tab.py  Reconciliation tab: finds the ", For each unmatched expense, score how likely it contributes to the     reconcil, ReconciliationTab

### Community 25 - "Modern Desktop Category Limits"
Cohesion: 0.14
Nodes (15): BudgetScreenProps, emptyCost(), emptyIncome(), emptyLoan(), financeApi, isoToday(), AssetSnapshot, BudgetSettings (+7 more)

### Community 26 - "TypeScript Configuration"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+10 more)

### Community 27 - "Python Chart Renderer"
Cohesion: 0.11
Nodes (17): create_allocation_figure(), create_bar_figure(), create_breakdown_figure(), create_budget_depletion_figure(), create_dow_heatmap_figure(), create_line_figure(), create_net_worth_figure(), create_spending_pace_figure() (+9 more)

### Community 28 - "Desktop Main Window"
Cohesion: 0.17
Nodes (12): MainView, Update the toggle button label for the active theme., Toggle between dark and light themes., Ensure report/text widgets are updated after a theme switch., Show keyboard shortcuts reference window, apply_styles(), _apply_tk_widget_colors(), get_current_theme() (+4 more)

### Community 29 - "Dashboard Metrics"
Cohesion: 0.28
Nodes (17): COLORS, NetWorthScreen(), asDate(), asNumber(), assetAllocation(), asString(), createSnapshot(), isRecord() (+9 more)

### Community 30 - "Budget Types (Legacy)"
Cohesion: 0.18
Nodes (13): DashboardSummary, Double, FinanceTransaction, InsightsSummary, Int, JsonObject, List, String (+5 more)

### Community 31 - "Electron Build Config"
Cohesion: 0.33
Nodes (8): BudgetSettings, Double, Int, LocalDate, String, NetWorthInterval, ProjectionMode, ProjectionService

### Community 32 - "Android Codec Tests"
Cohesion: 0.12
Nodes (17): devDependencies, electron, electron-builder, electron-vite, jsdom, @playwright/test, @swc/core, @tailwindcss/vite (+9 more)

### Community 34 - "Modern Desktop Budget Screen"
Cohesion: 0.27
Nodes (3): DataStore, writeJsonAtomically(), DataLoadResult

### Community 35 - "Modern Desktop Docs & Rationale"
Cohesion: 0.15
Nodes (15): delete_snapshot(), generate_net_worth_report(), get_asset_allocation_data(), get_asset_snapshots(), get_current_net_worth(), get_net_worth_change(), finance_tracker/services/asset_tracking_service.py  Service for tracking asset s, Record current asset balances as a snapshot (+7 more)

### Community 36 - "Android Transaction Types"
Cohesion: 0.16
Nodes (15): AI Insights Deferred, German-Bank CSV Reconciliation, Modern Desktop Data Safety (Atomic Writes), Modern Desktop Features, Modern Desktop App Details, Android MVP (Kotlin + Jetpack Compose), BNPL (Buy Now Pay Later) Booking, finance_data.json Shared Data File (+7 more)

### Community 37 - "Desktop Conceptual Architecture"
Cohesion: 0.24
Nodes (8): Boolean, FinanceTransaction, List, String, TransactionType, YearMonth, TransactionBookingDates, TransactionUiLogic

### Community 38 - "Shared Reconciliation Logic"
Cohesion: 0.15
Nodes (14): AddTransactionTab UI Class, AppState Class (State Management), Asset Tracking Service, Budget Calculator Service, Chart Generator (create_budget_depletion_figure, create_net_worth_figure, etc.), Finance Tracker Package, NetWorthTab UI Class, SettingsTab UI Class (Budget Report + Lending Manager) (+6 more)

### Community 39 - "Cross-Platform Architecture"
Cohesion: 0.19
Nodes (11): Android App (Kotlin/Jetpack Compose), android/, BNPL Convention, Desktop App (Python/Tkinter), finance_data.json, finance_tracker/, FinanceTracker class, Personal Finance Tracker (+3 more)

### Community 40 - "Desktop Windowing"
Cohesion: 0.24
Nodes (11): Misc, Tk, Toplevel, close_window(), create_child_window(), _managed_windows(), finance_tracker/ui/windowing.py  Helpers for stable Tk window show/close behavio, Show the root window using a conservative, WSLg-friendly sequence. (+3 more)

### Community 42 - "Android BNPL Logic Tests"
Cohesion: 0.38
Nodes (8): goalsReport(), GoalsScreen(), GoalsScreenProps, autoDistributeGoals(), cloneDocument(), cloneRecord(), getGoals(), goalSummary()

### Community 44 - "Test Mocks & Reproduction"
Cohesion: 0.33
Nodes (3): BudgetSettings, BudgetMathTest, String

### Community 45 - "Dev Scripts (npm)"
Cohesion: 0.22
Nodes (3): date, MockDate, MockState

### Community 46 - "Add Transaction Tab"
Cohesion: 0.22
Nodes (9): scripts, build, dev, package:win, preview, test, test:e2e, test:watch (+1 more)

### Community 48 - "Desktop App State"
Cohesion: 0.36
Nodes (7): Boolean, Double, String, Char, formatAmountField(), hasThousandsGrouping(), parseAmountText()

### Community 51 - "Python Report Builder"
Cohesion: 0.25
Nodes (8): build, appId, directories, files, productName, win, output, target

### Community 52 - "Projection Tab"
Cohesion: 0.38
Nodes (4): line_expense_category_range(), _month_range(), pie_data_range(), finance_tracker/services/report_builder.py  Service for preparing data for var

### Community 54 - "Android Insights JSON"
Cohesion: 0.43
Nodes (4): finance_tracker/ui/help_window.py  Displays the help and instructions window for, show_help(), finance_tracker/ui/main_view.py  Main application window and tab management., finance_tracker/ui/shortcuts.py  This module handles the registration and proc

### Community 55 - "Android Projection Tests"
Cohesion: 0.40
Nodes (3): InsightsSummary, String, InsightsJson

### Community 57 - "React Dependencies"
Cohesion: 0.33
Nodes (5): description, main, name, private, version

### Community 58 - "Currency Formatting"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, @radix-ui/react-dialog, react, react-dom, recharts

### Community 59 - "Python Projection Service"
Cohesion: 0.33
Nodes (5): format_amount(), parse_amount(), finance_tracker/services/currency_service.py  Central utility for parsing and, Formats a float with dot as thousands separator and comma as decimal separator., Parses a currency string in comma notation.     Example: '3.000,20' -> 3000.20,

### Community 60 - "Shortcut Setup"
Cohesion: 0.53
Nodes (5): _build_monthly_net_worth_change_projection(), _build_target_savings_projection(), _format_signed_euro(), projection_text(), finance_tracker/services/projection_service.py  Service for generating financial

### Community 61 - "Android Settings DataStore"
Cohesion: 0.33
Nodes (3): Enable Enter key to activate focused buttons, Switch to a specific tab by index, Setup global keyboard shortcuts for the application

### Community 62 - "Android Main Activity"
Cohesion: 0.50
Nodes (3): Flow, String, SettingsDataStore

### Community 63 - "Android Amount Text Tests"
Cohesion: 0.40
Nodes (3): Bundle, ComponentActivity, MainActivity

### Community 66 - "Android Launcher Icons"
Cohesion: 0.40
Nodes (5): nsis, allowToChangeInstallationDirectory, createDesktopShortcut, createStartMenuShortcut, oneClick

### Community 67 - "App Entry Point (Python)"
Cohesion: 0.50
Nodes (4): Android Launcher Icon, ic_launcher.png (hdpi), ic_launcher.png (mdpi), ic_launcher.png (xhdpi)

### Community 70 - "Android Synced File Status"
Cohesion: 0.50
Nodes (3): FinanceViewModel, Destination, FinanceApp()

### Community 74 - "Android Round Icons"
Cohesion: 1.00
Nodes (3): Android Cover Image, app-cover.png (repo root), app_cover.png (drawable-nodpi)

### Community 75 - "Android Icon Foregrounds"
Cohesion: 0.67
Nodes (3): Android Launcher Icon Round, ic_launcher_round.png (hdpi), ic_launcher_round.png (mdpi)

## Ambiguous Edges - Review These
- `Finance Tracker Package` → `Empty Test File`  [AMBIGUOUS]
  test_file.txt · relation: conceptually_related_to

## Knowledge Gaps
- **192 isolated node(s):** `Bundle`, `AssetBalances`, `CategoryState`, `Flow`, `FinanceTransaction` (+187 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Finance Tracker Package` and `Empty Test File`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `money()` connect `Android Compose UI Layer` to `Android ViewModel & Settings`, `Android Theme & UI Constants`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `DashboardScreen()` connect `Android Theme & UI Constants` to `Android Compose UI Layer`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Why does `T` connect `Android Theme & UI Constants` to `Desktop Data Models`, `Android JSON Serialization`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **What connects `Bundle`, `AssetBalances`, `CategoryState` to the rest of the system?**
  _340 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Desktop Data Models` be split into smaller, more focused modules?**
  _Cohesion score 0.09943502824858758 - nodes in this community are weakly interconnected._
- **Should `Android Compose UI Layer` be split into smaller, more focused modules?**
  _Cohesion score 0.07017543859649122 - nodes in this community are weakly interconnected._