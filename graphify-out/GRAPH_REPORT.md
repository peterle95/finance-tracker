# Graph Report - .  (2026-07-09)

## Corpus Check
- 99 files · ~203,498 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1146 nodes · 2208 edges · 73 communities (56 shown, 17 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 57 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_UI Data Model|UI Data Model]]
- [[_COMMUNITY_Data Models|Data Models]]
- [[_COMMUNITY_Budget Categories|Budget Categories]]
- [[_COMMUNITY_Settings Tab|Settings Tab]]
- [[_COMMUNITY_Transaction Types|Transaction Types]]
- [[_COMMUNITY_Kotlin Models|Kotlin Models]]
- [[_COMMUNITY_Budget Transactions|Budget Transactions]]
- [[_COMMUNITY_Goals Tab|Goals Tab]]
- [[_COMMUNITY_Financial Logic|Financial Logic]]
- [[_COMMUNITY_UI Composables|UI Composables]]
- [[_COMMUNITY_Keyboard Shortcuts|Keyboard Shortcuts]]
- [[_COMMUNITY_Reports Tab|Reports Tab]]
- [[_COMMUNITY_AI Insights Service|AI Insights Service]]
- [[_COMMUNITY_Net Worth Tab|Net Worth Tab]]
- [[_COMMUNITY_Kotlin Savings Goals|Kotlin Savings Goals]]
- [[_COMMUNITY_Kotlin UI Paint|Kotlin UI Paint]]
- [[_COMMUNITY_Goals Service|Goals Service]]
- [[_COMMUNITY_Budgets Tab|Budgets Tab]]
- [[_COMMUNITY_Reconciliation Service|Reconciliation Service]]
- [[_COMMUNITY_View Transactions Tab|View Transactions Tab]]
- [[_COMMUNITY_Net Worth Math|Net Worth Math]]
- [[_COMMUNITY_Reconciliation Tab|Reconciliation Tab]]
- [[_COMMUNITY_Project Architecture|Project Architecture]]
- [[_COMMUNITY_Chart Generation|Chart Generation]]
- [[_COMMUNITY_Dashboard Summary|Dashboard Summary]]
- [[_COMMUNITY_Projection Service|Projection Service]]
- [[_COMMUNITY_JSON Codec Tests|JSON Codec Tests]]
- [[_COMMUNITY_Asset Tracking|Asset Tracking]]
- [[_COMMUNITY_Transaction UI Logic|Transaction UI Logic]]
- [[_COMMUNITY_Architecture Overview|Architecture Overview]]
- [[_COMMUNITY_Main View|Main View]]
- [[_COMMUNITY_Window Management|Window Management]]
- [[_COMMUNITY_AI Insights Tab|AI Insights Tab]]
- [[_COMMUNITY_Transaction UI Tests|Transaction UI Tests]]
- [[_COMMUNITY_Budget Math Tests|Budget Math Tests]]
- [[_COMMUNITY_Bug Reproduction|Bug Reproduction]]
- [[_COMMUNITY_Add Transaction Tab|Add Transaction Tab]]
- [[_COMMUNITY_Amount Text|Amount Text]]
- [[_COMMUNITY_App State|App State]]
- [[_COMMUNITY_Dashboard Charts Tests|Dashboard Charts Tests]]
- [[_COMMUNITY_Report Builder|Report Builder]]
- [[_COMMUNITY_Projection Tab|Projection Tab]]
- [[_COMMUNITY_Help and Window UI|Help and Window UI]]
- [[_COMMUNITY_Insights JSON|Insights JSON]]
- [[_COMMUNITY_Launcher Icon|Launcher Icon]]
- [[_COMMUNITY_Launcher Foreground|Launcher Foreground]]
- [[_COMMUNITY_Launcher Round|Launcher Round]]
- [[_COMMUNITY_Projection Service Tests|Projection Service Tests]]
- [[_COMMUNITY_Currency Service|Currency Service]]
- [[_COMMUNITY_Projection Text|Projection Text]]
- [[_COMMUNITY_Shortcut Setup|Shortcut Setup]]
- [[_COMMUNITY_Theme Styles|Theme Styles]]
- [[_COMMUNITY_Settings Data Store|Settings Data Store]]
- [[_COMMUNITY_Main Activity|Main Activity]]
- [[_COMMUNITY_Amount Text Tests|Amount Text Tests]]
- [[_COMMUNITY_Net Worth Math Tests|Net Worth Math Tests]]
- [[_COMMUNITY_App Entry Point|App Entry Point]]
- [[_COMMUNITY_Finance Agg Tests|Finance Agg Tests]]
- [[_COMMUNITY_Finance App|Finance App]]
- [[_COMMUNITY_Synced File Status|Synced File Status]]
- [[_COMMUNITY_Projection Screen|Projection Screen]]
- [[_COMMUNITY_Settings Screen|Settings Screen]]
- [[_COMMUNITY_App Cover Images|App Cover Images]]
- [[_COMMUNITY_Category Defaults|Category Defaults]]
- [[_COMMUNITY_Entry Point|Entry Point]]

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
10. `String` - 21 edges

## Surprising Connections (you probably didn't know these)
- `Android MVP Plan` --semantically_similar_to--> `Finance Tracker Package`  [INFERRED] [semantically similar]
  docs/android_mvp_plan.md → code.txt
- `Android MVP Plan` --semantically_similar_to--> `Python Dependencies: matplotlib, numpy, python-dateutil`  [INFERRED] [semantically similar]
  docs/android_mvp_plan.md → requirements.txt
- `app-cover.png (repo root)` --semantically_similar_to--> `app_cover.png (drawable-nodpi)`  [INFERRED] [semantically similar]
  app-cover.png → android/app/src/main/res/drawable-nodpi/app_cover.png
- `Empty Test File` --conceptually_related_to--> `Finance Tracker Package`  [AMBIGUOUS]
  test_file.txt → code.txt
- `Desktop App (README)` --references--> `Desktop App (Python/Tkinter)`  [EXTRACTED]
  README.md → AGENTS.md

## Import Cycles
- None detected.

## Communities (73 total, 17 thin omitted)

### Community 0 - "UI Data Model"
Cohesion: 0.06
Nodes (77): Double, List, Modifier, String, FinanceViewModel, Boolean, Color, Double (+69 more)

### Community 1 - "Data Models"
Cohesion: 0.10
Nodes (22): BudgetSettings, CategoryState, Double, FinanceTransaction, FixedCost, IncomeSource, Int, JsonObject (+14 more)

### Community 2 - "Budget Categories"
Cohesion: 0.08
Nodes (18): Boolean, BudgetSettings, CategoryState, DashboardSummary, Double, FinanceTransaction, FixedCost, JsonObject (+10 more)

### Community 3 - "Settings Tab"
Cohesion: 0.08
Nodes (16): finance_tracker/ui/tabs/settings_tab.py  Tab for configuring budget settings, fi, Update the readonly income display with CURRENT month's active income., Update the readonly costs display with CURRENT month's active fixed costs., Render the budget depletion graph in the main UI., Update the money lent entry with current balance., Open the lending manager window to manage individual loans., Refresh the loans treeview with current data., Populate the form fields when a loan is selected in the tree. (+8 more)

### Community 4 - "Transaction Types"
Cohesion: 0.09
Nodes (16): BudgetSettings, CategoryState, Double, FinanceTransaction, FixedCost, Flow, IncomeSource, JsonObject (+8 more)

### Community 5 - "Kotlin Models"
Cohesion: 0.12
Nodes (43): Double, Int, JsonObject, List, String, AssetAllocation, AssetBalances, AssetSnapshot (+35 more)

### Community 6 - "Budget Transactions"
Cohesion: 0.17
Nodes (24): Boolean, BudgetSettings, CategoryState, Double, FinanceTransaction, FixedCost, Int, JsonObject (+16 more)

### Community 7 - "Goals Tab"
Cohesion: 0.08
Nodes (18): GoalsTab, finance_tracker/ui/tabs/goals_tab.py  Tab for creating and managing savings goal, Handle mouse wheel scrolling, Update scrollregion when goals container changes, Update the width of the canvas window to match the canvas, Recursively bind mouse wheel event to all children, Refresh the goals display, Update the savings overview display (+10 more)

### Community 8 - "Financial Logic"
Cohesion: 0.21
Nodes (13): Boolean, BudgetSettings, Double, FinanceTransaction, FixedCost, IncomeSource, Int, List (+5 more)

### Community 9 - "UI Composables"
Cohesion: 0.17
Nodes (32): Boolean, BudgetSettings, Color, Double, FinanceViewModel, Float, List, Modifier (+24 more)

### Community 10 - "Keyboard Shortcuts"
Cohesion: 0.06
Nodes (16): Handle Ctrl+A shortcut to open Add Transaction tab, Handle Ctrl+N shortcut to clear Add Transaction form, Handle Alt+Left shortcut to go to previous tab, Handle Alt+Right shortcut to go to next tab, Handle Ctrl+S shortcut to save in current tab, Handle Ctrl+D or Delete shortcut to delete selected item, Handle Ctrl+E shortcut to edit selected item, Handle F5 shortcut to refresh current view (+8 more)

### Community 11 - "Reports Tab"
Cohesion: 0.11
Nodes (9): finance_tracker/ui/tabs/reports_tab.py  Tab for generating and viewing various, Open a modal dialog to select categories for the line chart., Update the category button text to show selection count., Render the bar chart based on current breakdown and display modes, Get category-wise data for each month, Get flexible income vs flexible costs data for each month, Get total income vs total expenses for each month, Handle click events on the bar chart (+1 more)

### Community 12 - "AI Insights Service"
Cohesion: 0.13
Nodes (25): _aggregate_transactions(), AIConfig, build_chat_messages(), build_insights_prompt(), _month_list(), finance_tracker/services/ai_insights_service.py  Service for generating AI insig, request_ai_insights(), auto_assign_percentages() (+17 more)

### Community 13 - "Net Worth Tab"
Cohesion: 0.11
Nodes (13): NetWorthTab, finance_tracker/ui/tabs/net_worth_tab.py  Tab for tracking and visualizing net w, Refresh all data and displays, Update the current net worth display, Refresh the snapshots tree view, Record a new asset snapshot, Delete the selected snapshot, Generate the selected chart type (+5 more)

### Community 14 - "Kotlin Savings Goals"
Cohesion: 0.20
Nodes (10): BudgetSettings, Double, Int, List, LocalDate, SavingsGoal, String, SavingsGoalProgress (+2 more)

### Community 15 - "Kotlin UI Paint"
Cohesion: 0.17
Nodes (24): BudgetSettings, Color, Double, FinanceViewModel, Float, List, Paint, String (+16 more)

### Community 16 - "Goals Service"
Cohesion: 0.15
Nodes (21): auto_distribute_savings(), calculate_all_goals_summary(), calculate_goal_progress(), calculate_monthly_savings(), estimate_completion_date(), generate_goals_report(), get_total_allocated(), get_total_savings_available() (+13 more)

### Community 17 - "Budgets Tab"
Cohesion: 0.18
Nodes (3): BudgetsTab, finance_tracker/ui/tabs/budgets_tab.py  Tab for managing category budget limit, Handle category type change (Expense/Income)

### Community 18 - "Reconciliation Service"
Cohesion: 0.14
Nodes (20): Any, _amounts_match(), BankTransaction, _dates_close(), _detect_encoding_and_sep(), get_summary(), match_transactions(), parse_bank_csv() (+12 more)

### Community 19 - "View Transactions Tab"
Cohesion: 0.16
Nodes (6): finance_tracker/ui/tabs/view_transactions_tab.py  Tab for viewing, filtering,, Sort transactions by the specified column, Rebuild the tree view with current sorted transactions, Update the available options in filter dropdowns based on current transactions, Clear all filter fields and refresh, ViewTransactionsTab

### Community 20 - "Net Worth Math"
Cohesion: 0.24
Nodes (9): BudgetSettings, Double, Int, List, LocalDate, String, NetWorthMath, NetWorthChange (+1 more)

### Community 21 - "Reconciliation Tab"
Cohesion: 0.16
Nodes (6): BankTransaction, Notebook, _find_candidates(), finance_tracker/ui/tabs/reconciliation_tab.py  Reconciliation tab: finds the ", For each unmatched expense, score how likely it contributes to the     reconcil, ReconciliationTab

### Community 22 - "Project Architecture"
Cohesion: 0.16
Nodes (17): Android App (Kotlin/Jetpack Compose), android/, BNPL Convention, Desktop App (Python/Tkinter), finance_data.json, finance_tracker/, FinanceTracker class, Personal Finance Tracker (+9 more)

### Community 23 - "Chart Generation"
Cohesion: 0.11
Nodes (17): create_allocation_figure(), create_bar_figure(), create_breakdown_figure(), create_budget_depletion_figure(), create_dow_heatmap_figure(), create_line_figure(), create_net_worth_figure(), create_spending_pace_figure() (+9 more)

### Community 24 - "Dashboard Summary"
Cohesion: 0.18
Nodes (13): DashboardSummary, Double, FinanceTransaction, InsightsSummary, Int, JsonObject, List, String (+5 more)

### Community 25 - "Projection Service"
Cohesion: 0.33
Nodes (8): BudgetSettings, Double, Int, LocalDate, String, NetWorthInterval, ProjectionMode, ProjectionService

### Community 27 - "Asset Tracking"
Cohesion: 0.15
Nodes (15): delete_snapshot(), generate_net_worth_report(), get_asset_allocation_data(), get_asset_snapshots(), get_current_net_worth(), get_net_worth_change(), finance_tracker/services/asset_tracking_service.py  Service for tracking asset s, Record current asset balances as a snapshot (+7 more)

### Community 28 - "Transaction UI Logic"
Cohesion: 0.24
Nodes (8): Boolean, FinanceTransaction, List, String, TransactionType, YearMonth, TransactionBookingDates, TransactionUiLogic

### Community 29 - "Architecture Overview"
Cohesion: 0.15
Nodes (14): AddTransactionTab UI Class, AppState Class (State Management), Asset Tracking Service, Budget Calculator Service, Chart Generator (create_budget_depletion_figure, create_net_worth_figure, etc.), Finance Tracker Package, NetWorthTab UI Class, SettingsTab UI Class (Budget Report + Lending Manager) (+6 more)

### Community 30 - "Main View"
Cohesion: 0.23
Nodes (7): MainView, Update the toggle button label for the active theme., Toggle between dark and light themes., Ensure report/text widgets are updated after a theme switch., Show keyboard shortcuts reference window, get_current_theme(), get_theme_colors()

### Community 31 - "Window Management"
Cohesion: 0.24
Nodes (11): Misc, Tk, Toplevel, close_window(), create_child_window(), _managed_windows(), finance_tracker/ui/windowing.py  Helpers for stable Tk window show/close behavio, Show the root window using a conservative, WSLg-friendly sequence. (+3 more)

### Community 34 - "Budget Math Tests"
Cohesion: 0.33
Nodes (3): BudgetSettings, BudgetMathTest, String

### Community 35 - "Bug Reproduction"
Cohesion: 0.22
Nodes (3): date, MockDate, MockState

### Community 37 - "Amount Text"
Cohesion: 0.36
Nodes (7): Boolean, Double, String, Char, formatAmountField(), hasThousandsGrouping(), parseAmountText()

### Community 40 - "Report Builder"
Cohesion: 0.38
Nodes (4): line_expense_category_range(), _month_range(), pie_data_range(), finance_tracker/services/report_builder.py  Service for preparing data for var

### Community 42 - "Help and Window UI"
Cohesion: 0.43
Nodes (4): finance_tracker/ui/help_window.py  Displays the help and instructions window for, show_help(), finance_tracker/ui/main_view.py  Main application window and tab management., finance_tracker/ui/shortcuts.py  This module handles the registration and proc

### Community 43 - "Insights JSON"
Cohesion: 0.40
Nodes (3): InsightsSummary, String, InsightsJson

### Community 44 - "Launcher Icon"
Cohesion: 0.33
Nodes (6): Android Launcher Icon, ic_launcher.png (hdpi), ic_launcher.png (mdpi), ic_launcher.png (xhdpi), ic_launcher.png (xxhdpi), ic_launcher.png (xxxhdpi)

### Community 45 - "Launcher Foreground"
Cohesion: 0.33
Nodes (6): Android Launcher Icon Foreground, ic_launcher_foreground.png (hdpi), ic_launcher_foreground.png (mdpi), ic_launcher_foreground.png (xhdpi), ic_launcher_foreground.png (xxhdpi), ic_launcher_foreground.png (xxxhdpi)

### Community 46 - "Launcher Round"
Cohesion: 0.33
Nodes (6): Android Launcher Icon Round, ic_launcher_round.png (hdpi), ic_launcher_round.png (mdpi), ic_launcher_round.png (xhdpi), ic_launcher_round.png (xxhdpi), ic_launcher_round.png (xxxhdpi)

### Community 48 - "Currency Service"
Cohesion: 0.33
Nodes (5): format_amount(), parse_amount(), finance_tracker/services/currency_service.py  Central utility for parsing and, Formats a float with dot as thousands separator and comma as decimal separator., Parses a currency string in comma notation.     Example: '3.000,20' -> 3000.20,

### Community 49 - "Projection Text"
Cohesion: 0.53
Nodes (5): _build_monthly_net_worth_change_projection(), _build_target_savings_projection(), _format_signed_euro(), projection_text(), finance_tracker/services/projection_service.py  Service for generating financial

### Community 50 - "Shortcut Setup"
Cohesion: 0.33
Nodes (3): Enable Enter key to activate focused buttons, Switch to a specific tab by index, Setup global keyboard shortcuts for the application

### Community 51 - "Theme Styles"
Cohesion: 0.47
Nodes (5): apply_styles(), _apply_tk_widget_colors(), finance_tracker/ui/style.py  Defines and applies custom Tkinter styles for the a, Best-effort native title bar theming (Windows only)., _set_native_titlebar_theme()

### Community 52 - "Settings Data Store"
Cohesion: 0.50
Nodes (3): Flow, String, SettingsDataStore

### Community 53 - "Main Activity"
Cohesion: 0.40
Nodes (3): Bundle, ComponentActivity, MainActivity

### Community 58 - "Finance App"
Cohesion: 0.50
Nodes (3): FinanceViewModel, Destination, FinanceApp()

### Community 62 - "App Cover Images"
Cohesion: 1.00
Nodes (3): Android Cover Image, app-cover.png (repo root), app_cover.png (drawable-nodpi)

## Ambiguous Edges - Review These
- `Finance Tracker Package` → `Empty Test File`  [AMBIGUOUS]
  test_file.txt · relation: conceptually_related_to

## Knowledge Gaps
- **113 isolated node(s):** `Bundle`, `AssetBalances`, `CategoryState`, `Flow`, `FinanceTransaction` (+108 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Finance Tracker Package` and `Empty Test File`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `money()` connect `UI Data Model` to `UI Composables`, `Kotlin UI Paint`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Why does `T` connect `UI Data Model` to `Data Models`, `Kotlin Models`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **What connects `Bundle`, `AssetBalances`, `CategoryState` to the rest of the system?**
  _263 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `UI Data Model` be split into smaller, more focused modules?**
  _Cohesion score 0.057813911472448055 - nodes in this community are weakly interconnected._
- **Should `Data Models` be split into smaller, more focused modules?**
  _Cohesion score 0.09943502824858758 - nodes in this community are weakly interconnected._
- **Should `Budget Categories` be split into smaller, more focused modules?**
  _Cohesion score 0.07878787878787878 - nodes in this community are weakly interconnected._