# Graph Report - finance-use-ubuntu-for-changes  (2026-09-06)

## Corpus Check
- 197 files · ~251,902 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1835 nodes · 4113 edges · 144 communities (99 shown, 45 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 50 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80
- Community 81
- Community 82
- Community 83
- Community 84
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92
- Community 93
- Community 94
- Community 95
- Community 96
- Community 97
- Community 98
- Community 99
- Community 100
- Community 101
- Community 102
- Community 106
- Community 107
- Community 108
- Community 109
- Community 110
- Community 111
- Community 120
- Community 121
- Community 122
- Community 123
- Community 124
- Community 125
- Community 126
- Community 127
- Community 128
- Community 129
- Community 130
- Community 131
- Community 132
- Community 133
- Community 134
- Community 135
- Community 136
- Community 137
- Community 138
- Community 139
- Community 140
- Community 141
- Community 142
- Community 143

## God Nodes (most connected - your core abstractions)
1. `FinanceViewModel` - 70 edges
2. `FinanceDirectoryStore` - 46 edges
3. `FinanceRepository` - 44 edges
4. `SettingsTab` - 40 edges
5. `FinanceJsonCodec` - 39 edges
6. `AppState` - 33 edges
7. `FinanceDocument` - 33 edges
8. `FinanceDocument` - 31 edges
9. `money()` - 30 edges
10. `DataStore` - 30 edges

## Surprising Connections (you probably didn't know these)
- `Split JSON Data Contract` --semantically_similar_to--> `Synchronized Split JSON Directory`  [INFERRED] [semantically similar]
  docs/finance-tracker-project.md → AGENTS.md
- `Atomic per-file writes` --semantically_similar_to--> `Write and concurrency limits`  [INFERRED] [semantically similar]
  openwiki/data-contract/migration-and-integrity.md → shared/finance_data_schema.md
- `Legacy migration` --semantically_similar_to--> `Initialization and legacy migration`  [INFERRED] [semantically similar]
  openwiki/data-contract/migration-and-integrity.md → shared/finance_data_schema.md
- `Legacy data migration` --semantically_similar_to--> `Legacy migration`  [INFERRED] [semantically similar]
  shared/finance_data_schema.md → openwiki/python-desktop/persistence.md
- `PersistenceTests` --uses--> `AppState`  [INFERRED]
  tests/test_persistence.py → finance_tracker/state.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Finance Tracking Visual** — android_app_src_main_res_mipmap_hdpi_ic_launcher_wallet, android_app_src_main_res_mipmap_hdpi_ic_launcher_financial_bar_chart, android_app_src_main_res_mipmap_hdpi_ic_launcher_upward_growth [EXTRACTED 1.00]
- **Personal Finance Visual Language** — android_app_src_main_res_mipmap_xxxhdpi_ic_launcher_round_wallet, android_app_src_main_res_mipmap_xxxhdpi_ic_launcher_round_payment_cards, android_app_src_main_res_mipmap_xxxhdpi_ic_launcher_round_growth_chart, android_app_src_main_res_mipmap_xxxhdpi_ic_launcher_round_coin [EXTRACTED 1.00]
- **Android data layer composition** — openwiki_android_data_layer_saf_finance_directory, openwiki_android_data_layer_financejsonfilestore, openwiki_android_data_layer_financejsoncodec, openwiki_android_data_layer_finance_directory_store, openwiki_android_data_layer_financerepository [EXTRACTED 1.00]
- **Finance tracker icon visual language** — android_app_src_main_res_mipmap_mdpi_ic_launcher_foreground_icon, android_app_src_main_res_mipmap_mdpi_ic_launcher_foreground_wallet, android_app_src_main_res_mipmap_mdpi_ic_launcher_foreground_financial_growth_chart, android_app_src_main_res_mipmap_mdpi_ic_launcher_foreground_gold_coin [EXTRACTED 1.00]
- **Personal Finance Visual** — app_cover_wallet, app_cover_payment_card, app_cover_financial_growth_chart [EXTRACTED 1.00]
- **BNPL uses booking and behavior dates** — context_booking_date, context_behavior_date, readme_bnpl_date_convention, docs_finance_tracker_project_bnpl_date_convention, docs_android_mvp_plan_bnpl_storage [EXTRACTED 1.00]
- **Finance data contract integrity** — openwiki_shared_finance_data_schema_categories_registry, openwiki_shared_finance_data_schema_transactions, openwiki_shared_finance_data_schema_unknown_field_preservation, openwiki_shared_finance_data_schema_write_concurrency_limits [EXTRACTED 1.00]
- **Wear transaction delivery flow** — openwiki_workflows_transaction_lifecycle_watch_outbox, openwiki_workflows_transaction_lifecycle_phone_transaction_intake, openwiki_workflows_transaction_lifecycle_finance_directory_store [EXTRACTED 1.00]
- **Python service orchestration** — openwiki_python_desktop_services_budget_calculator, openwiki_python_desktop_services_report_builder, openwiki_python_desktop_services_reconciliation_service, openwiki_python_desktop_services_goals_service, openwiki_python_desktop_services_projection_service, openwiki_python_desktop_services_asset_tracking_service [EXTRACTED 1.00]
- **Python UI tabs use central application state** — code_mainview, code_appstate, code_networthtab, code_addtransactiontab, code_settingstab, code_reportstab [EXTRACTED 1.00]
- **Clients integrated through shared directory** — openwiki_architecture_overview_shared_split_json_directory, openwiki_android_data_layer_finance_directory_store, openwiki_modern_desktop_data_store_electron_data_store [EXTRACTED 1.00]
- **Clients participate in shared split JSON contract** — agents_python_tkinter_client, agents_electron_react_client, agents_android_client, docs_finance_tracker_project_shared_contract [EXTRACTED 1.00]
- **Shared data integrity boundaries** — shared_finance_data_schema_categories_registry, shared_finance_data_schema_legacy_migration, shared_finance_data_schema_missing_orphan_conflict_files, shared_finance_data_schema_concurrency_limits [EXTRACTED 1.00]
- **Clients over shared split JSON directory** — openwiki_architecture_overview_python_appstate, openwiki_architecture_overview_electron_datastore_react_ui, openwiki_architecture_overview_android_financerepository_compose_ui, openwiki_architecture_overview_shared_split_json_directory [EXTRACTED 1.00]
- **Wear to phone transaction flow** — openwiki_android_wear_protocol_transaction_submission, openwiki_android_wear_protocol_watch_delivery_outbox, openwiki_android_data_layer_phone_transaction_intake [EXTRACTED 1.00]

## Communities (144 total, 45 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (62): BarBreakdownMode, Categories, Flexible, OverUnder, Total, ChartDisplayMode, Percentage, Value (+54 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (39): BUDGET_KEYS, CategoriesFile, CategoryRecord, categoryRecords(), DataStore, decodeCsv(), equal(), exists() (+31 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (21): CategoryRecord, DirectoryLoadResult, FileOwner, Budget, Loans, NetWorth, SavingsGoals, FinanceDirectory (+13 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (16): FinanceRepository, BudgetSettings, FinanceTransaction, FixedCost, Flow, IncomeSource, JsonObject, Loan (+8 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (39): auto_distribute_savings(), calculate_all_goals_summary(), calculate_goal_progress(), calculate_monthly_savings(), estimate_completion_date(), generate_goals_report(), get_total_allocated(), get_total_savings_available() (+31 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (17): FinanceDocument, FinanceJsonCodec, FinanceRecord, BudgetSettings, FinanceTransaction, FixedCost, IncomeSource, JsonArray (+9 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (15): Update the readonly income display with CURRENT month's active income., Update the readonly costs display with CURRENT month's active fixed costs., Render the budget depletion graph in the main UI., Update the money lent entry with current balance., Open the lending manager window to manage individual loans., Refresh the loans treeview with current data., Populate the form fields when a loan is selected in the tree., Add a new loan and update the balance. (+7 more)

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (3): AppState, finance_tracker/state.py Manages the application state, including data loading,…, PersistenceTests

### Community 8 - "Community 8"
Cohesion: 0.15
Nodes (45): NetWorthScreen(), recordSnapshot(), removeSnapshot(), asDate(), asNumber(), assetAllocation(), AssetAllocationItem, asString() (+37 more)

### Community 9 - "Community 9"
Cohesion: 0.07
Nodes (33): delete_snapshot(), generate_net_worth_report(), get_asset_allocation_data(), get_asset_snapshots(), get_current_net_worth(), get_net_worth_change(), finance_tracker/services/asset_tracking_service.py Service for tracking asset…, Record current asset balances as a snapshot (+25 more)

### Community 10 - "Community 10"
Cohesion: 0.08
Nodes (12): FinanceViewModel, BudgetSettings, FinanceTransaction, FixedCost, IncomeSource, JsonObject, Loan, SavingsGoal (+4 more)

### Community 11 - "Community 11"
Cohesion: 0.09
Nodes (26): BankTransaction, _amounts_match(), BankTransaction, _dates_close(), _detect_encoding_and_sep(), get_summary(), match_transactions(), parse_bank_csv() (+18 more)

### Community 12 - "Community 12"
Cohesion: 0.06
Nodes (19): Enable Enter key to activate focused buttons, Switch to a specific tab by index, Handle Ctrl+A shortcut to open Add Transaction tab, Handle Ctrl+N shortcut to clear Add Transaction form, Handle Alt+Left shortcut to go to previous tab, Handle Alt+Right shortcut to go to next tab, Handle Ctrl+S shortcut to save in current tab, Handle Ctrl+D or Delete shortcut to delete selected item (+11 more)

### Community 13 - "Community 13"
Cohesion: 0.16
Nodes (19): EditorState, navigation, Page, Theme, DashboardScreen(), TransactionEditor(), submit(), TransactionEditorProps (+11 more)

### Community 14 - "Community 14"
Cohesion: 0.17
Nodes (28): BudgetReport, todayIsoDate(), BalanceEditor(), BudgetButton(), BudgetDepletionChart(), BudgetOutlinedButton(), BudgetOverview(), BudgetScreen() (+20 more)

### Community 15 - "Community 15"
Cohesion: 0.07
Nodes (29): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+21 more)

### Community 16 - "Community 16"
Cohesion: 0.20
Nodes (23): booleanValue(), boundedInt(), CategoryBudgets, jsonPrimitiveOrNull(), JsonObject, R, T, mapNotNullIndexed() (+15 more)

### Community 17 - "Community 17"
Cohesion: 0.12
Nodes (24): App(), applyLoadResult(), chooseDataFile(), content(), createDataFile(), deleteTransaction(), exportText(), loadData() (+16 more)

### Community 18 - "Community 18"
Cohesion: 0.15
Nodes (22): BudgetScreen(), addIncome(), markLoanReturned(), saveBalances(), saveCost(), saveLoan(), saveLoanChanges(), updateSettings() (+14 more)

### Community 19 - "Community 19"
Cohesion: 0.14
Nodes (24): get_active_fixed_costs(), get_active_monthly_income(), Returns the total base monthly income active for the specified month. An income…, Returns only the fixed costs that were active during the specified month. A…, history_data(), line_expense_category_range(), _month_range(), pie_data() (+16 more)

### Community 20 - "Community 20"
Cohesion: 0.20
Nodes (7): BudgetMath, BudgetSettings, FinanceTransaction, FixedCost, IncomeSource, YearMonth, BudgetReportDay

### Community 21 - "Community 21"
Cohesion: 0.14
Nodes (19): finance_tracker/ui/help_window.py Displays the help and instructions window for…, show_help(), finance_tracker/ui/main_view.py Main application window and tab management., Show keyboard shortcuts reference window, finance_tracker/ui/shortcuts.py This module handles the registration and…, get_theme_colors(), Show the net worth report in a dialog, finance_tracker/ui/tabs/view_transactions_tab.py Tab for viewing, filtering,… (+11 more)

### Community 22 - "Community 22"
Cohesion: 0.08
Nodes (26): Android data layer, CategorySnapshotPublisher, FinanceDirectoryStore, FinanceRepository, PhoneTransactionIntake, SafFinanceDirectory, Android files index, CategorySnapshot (+18 more)

### Community 23 - "Community 23"
Cohesion: 0.08
Nodes (25): electron, electron-builder, electron-vite, jsdom, devDependencies, electron, electron-builder, electron-vite (+17 more)

### Community 24 - "Community 24"
Cohesion: 0.14
Nodes (7): Open a modal dialog to select categories for the line chart., Update the category button text to show selection count., Render the bar chart based on current breakdown and display modes, Get category-wise data for each month, Get flexible income vs flexible costs data for each month, Handle click events on the bar chart, ReportsTab

### Community 25 - "Community 25"
Cohesion: 0.19
Nodes (22): AssetAllocation, Color, Modifier, MetricCard(), money(), AllocationChart(), AssetBalanceCards(), AssetBreakdownChart() (+14 more)

### Community 26 - "Community 26"
Cohesion: 0.14
Nodes (16): MainActivity, CategoryDropdown(), Destination, FinanceApp(), AddTransactionScreen(), ProjectionScreen(), SettingsScreen(), EditTransactionDialog() (+8 more)

### Community 27 - "Community 27"
Cohesion: 0.08
Nodes (24): Legacy migration, Python persistence, Python Tkinter UI, AppState, Atomic per-file writes, Legacy migration, Split-file ownership, MainView (+16 more)

### Community 28 - "Community 28"
Cohesion: 0.14
Nodes (5): FinanceTransaction, BudgetMathTest, BudgetSettings, DashboardChartsTest, FinanceAggregatorTest

### Community 29 - "Community 29"
Cohesion: 0.16
Nodes (12): main(), finance_tracker/app.py Main application entry point and initialization., MainView, Update the toggle button label for the active theme., Toggle between dark and light themes., Ensure report/text widgets are updated after a theme switch., apply_styles(), _apply_tk_widget_colors() (+4 more)

### Community 30 - "Community 30"
Cohesion: 0.19
Nodes (10): _aggregate_transactions(), AIConfig, build_chat_messages(), build_insights_prompt(), _month_list(), Any, finance_tracker/services/ai_insights_service.py Service for generating AI…, request_ai_insights() (+2 more)

### Community 32 - "Community 32"
Cohesion: 0.17
Nodes (15): ChartKind, COLORS, DAYS, HistoryDisplay, HistoryMode, lineRows(), ReportsScreen(), setChartValue() (+7 more)

### Community 33 - "Community 33"
Cohesion: 0.23
Nodes (4): BudgetSettings, SavingsGoal, SavingsGoalProgress, SavingsGoals

### Community 34 - "Community 34"
Cohesion: 0.16
Nodes (16): auto_assign_percentages(), compute_net_available_for_spending(), days_in_month_str(), generate_daily_budget_report(), get_active_monthly_income_sources(), get_month_end_flexible_balance(), get_negative_carryover_from_previous_month(), get_previous_month_str() (+8 more)

### Community 35 - "Community 35"
Cohesion: 0.18
Nodes (5): Sort transactions by the specified column, Rebuild the tree view with current sorted transactions, Update the available options in filter dropdowns based on current transactions, Clear all filter fields and refresh, ViewTransactionsTab

### Community 36 - "Community 36"
Cohesion: 0.20
Nodes (14): BudgetDepletionChart(), BudgetTooltip(), tooltipStyle, tooltipTextStyle, BreakdownTooltip(), COLORS, formatSignedCurrency(), formatSignedCurrency() (+6 more)

### Community 37 - "Community 37"
Cohesion: 0.16
Nodes (13): DefaultBehaviorsDialog(), save(), DefaultBehaviorsDialogProps, DEFAULT_BEHAVIOR_SETTINGS, DefaultBehaviorSettings, DefaultNetWorthChangeMode, DefaultProjectionMode, DefaultReportDateBasis (+5 more)

### Community 38 - "Community 38"
Cohesion: 0.12
Nodes (8): financeApi, AssetSnapshot, FinanceApi, FixedCost, IncomeSource, ReconciliationStatus, SavingsGoal, Window

### Community 39 - "Community 39"
Cohesion: 0.12
Nodes (17): Android Client, Electron React Client, Python Tkinter Client, Synchronized Split JSON Directory, Preferences DataStore, Android Storage Access Framework, AppState Persistence Boundary, Electron DataStore (+9 more)

### Community 40 - "Community 40"
Cohesion: 0.22
Nodes (9): CategoryDefaults, CategoryState, FixedCost, IncomeSource, Loan, SavingsGoal, TransactionType, Expense (+1 more)

### Community 41 - "Community 41"
Cohesion: 0.20
Nodes (9): FinanceAggregator, FinanceTransaction, JsonObject, YearMonth, InsightsJson, DashboardSummary, FinanceTotals, InsightsSummary (+1 more)

### Community 42 - "Community 42"
Cohesion: 0.28
Nodes (5): NetWorthChange, NetWorthSummary, AssetSnapshot, BudgetSettings, NetWorthMath

### Community 43 - "Community 43"
Cohesion: 0.23
Nodes (9): DefaultRangesDialog(), save(), DefaultRangesDialogProps, boundedNumber(), DEFAULT_RANGE_SETTINGS, DefaultRangeSettings, JourneyHorizonPreset, normalizeDefaultRangeSettings() (+1 more)

### Community 44 - "Community 44"
Cohesion: 0.30
Nodes (5): AssetBalances, AssetSnapshot, BudgetSettings, NetWorthMathTest, ProjectionServiceTest

### Community 45 - "Community 45"
Cohesion: 0.27
Nodes (6): BudgetSettings, NetWorthInterval, ProjectionMode, NetWorthTrend, TargetSavings, ProjectionService

### Community 47 - "Community 47"
Cohesion: 0.32
Nodes (11): goalsReport(), GoalsScreen(), addGoal(), archiveGoal(), saveGoals(), updateGoal(), GoalsScreenProps, newGoal() (+3 more)

### Community 48 - "Community 48"
Cohesion: 0.23
Nodes (7): _build_monthly_net_worth_change_projection(), _build_target_savings_projection(), _format_signed_euro(), projection_text(), finance_tracker/services/projection_service.py Service for generating financial…, ProjectionTab, finance_tracker/ui/tabs/projection_tab.py Tab for projecting future financial…

### Community 49 - "Community 49"
Cohesion: 0.15
Nodes (12): build, appId, directories, files, nsis, productName, output, allowToChangeInstallationDirectory (+4 more)

### Community 50 - "Community 50"
Cohesion: 0.22
Nodes (4): SettingsScreen(), SettingsScreenProps, KeyboardNavigationSettings, DataConnection

### Community 51 - "Community 51"
Cohesion: 0.24
Nodes (5): FinanceTransaction, TransactionType, YearMonth, TransactionBookingDates, TransactionUiLogic

### Community 52 - "Community 52"
Cohesion: 0.30
Nodes (10): CategoryLimitsScreen(), addCategory(), autoAssign(), removeCategory(), updateLimits(), autoAssignCategoryBudgets(), categoryBudgetPercentages(), cloneDocument() (+2 more)

### Community 53 - "Community 53"
Cohesion: 0.33
Nodes (5): formatAmountField(), hasThousandsGrouping(), parseAmountText(), LoanEditorScreen(), AmountTextTest

### Community 54 - "Community 54"
Cohesion: 0.45
Nodes (10): SavingsGoalsSummary, ActionRow(), AllocationEditor(), GoalActions(), GoalEditor(), SavingsGoal, SavingsGoalCard(), SavingsGoalsScreen() (+2 more)

### Community 55 - "Community 55"
Cohesion: 0.18
Nodes (11): lucide-react, dependencies, lucide-react, @radix-ui/react-dialog, react, react-dom, recharts, @radix-ui/react-dialog (+3 more)

### Community 56 - "Community 56"
Cohesion: 0.18
Nodes (11): scripts, build, dev, install:electron, package:win, postinstall, preview, test (+3 more)

### Community 58 - "Community 58"
Cohesion: 0.22
Nodes (3): date, MockDate, MockState

### Community 60 - "Community 60"
Cohesion: 0.22
Nodes (9): Python domain services, AI insights service, Asset tracking service, Budget calculator, Date overlap rules, Goals service, Projection service, Python feature tabs (+1 more)

### Community 61 - "Community 61"
Cohesion: 0.43
Nodes (3): FinanceJsonFileStore, FinanceDocument, StateFlow

### Community 62 - "Community 62"
Cohesion: 0.29
Nodes (7): Android finance domain, FinanceAggregator, Models.kt document model, BNPL date semantics, FinanceDocument, FinanceApi bridge contract, Modern desktop finance domain

### Community 63 - "Community 63"
Cohesion: 0.33
Nodes (6): AddTransactionTab, AppState, MainView, NetWorthTab, SettingsTab, Net Worth Snapshot

### Community 64 - "Community 64"
Cohesion: 0.33
Nodes (5): format_amount(), parse_amount(), finance_tracker/services/currency_service.py Central utility for parsing and…, Formats a float with dot as thousands separator and comma as decimal separator.…, Parses a currency string in comma notation. Example: '3.000,20' -> 3000.20,…

### Community 65 - "Community 65"
Cohesion: 0.33
Nodes (5): description, main, name, private, version

### Community 66 - "Community 66"
Cohesion: 0.33
Nodes (6): FinanceDirectoryStore, PhoneTransactionIntake, Reliable Wear delivery, Transaction lifecycle, WatchOutbox, BNPL dates

### Community 67 - "Community 67"
Cohesion: 0.40
Nodes (5): Coin, Finance App Icon, Growth Chart, Payment Card, Wallet

### Community 68 - "Community 68"
Cohesion: 0.40
Nodes (5): Finance Tracker Foreground Icon, Financial Bar Chart, Payment Card, Upward Financial Growth, Wallet

### Community 69 - "Community 69"
Cohesion: 0.50
Nodes (5): Finance Tracker App Icon, Financial Growth, Payment Card, Rising Financial Chart, Wallet

### Community 70 - "Community 70"
Cohesion: 0.40
Nodes (5): Coin, Finance Tracker App Icon, Financial Growth Chart, Payment Cards, Wallet

### Community 71 - "Community 71"
Cohesion: 0.60
Nodes (5): Behavior Date, Booking Date, BNPL Split Dates, BNPL Date Convention, BNPL Date Convention

### Community 72 - "Community 72"
Cohesion: 0.40
Nodes (5): TransactionUiLogic, Finance normalization and formulas, BNPL date and behavior_date semantics, Transactions, Unknown field preservation

### Community 73 - "Community 73"
Cohesion: 0.40
Nodes (5): Editable-control guard, Focus trapping and restoration, Native keyboard activation, Navigation mode, Radix Dialog

### Community 74 - "Community 74"
Cohesion: 0.50
Nodes (4): NetWorthChart, Allocation, Breakdown, NetWorth

### Community 75 - "Community 75"
Cohesion: 0.67
Nodes (4): Finance Tracker App Cover, Financial Growth Chart, Payment Card, Teal Wallet

### Community 76 - "Community 76"
Cohesion: 0.67
Nodes (4): Finance Tracker Launcher Icon, Financial Bar Chart, Upward Financial Growth, Wallet

### Community 77 - "Community 77"
Cohesion: 0.50
Nodes (4): Finance Tracker App Icon, Financial Growth Chart, Payment Card, Wallet

### Community 78 - "Community 78"
Cohesion: 0.67
Nodes (4): Personal Finance Tracking, Finance Tracker Launcher Icon, Rising Financial Chart, Wallet or Card Motif

### Community 79 - "Community 79"
Cohesion: 0.50
Nodes (4): Financial Growth Chart, Gold Coin, Finance Tracker App Icon, Wallet

### Community 80 - "Community 80"
Cohesion: 0.50
Nodes (4): Finance Tracker Launcher Icon, Payment Card, Upward Financial Trend, Wallet

### Community 81 - "Community 81"
Cohesion: 0.67
Nodes (4): Coin, Finance Tracker App Icon, Financial Growth Chart, Wallet

### Community 82 - "Community 82"
Cohesion: 0.50
Nodes (4): Finance Tracker Launcher Icon, Financial Bar Chart, Upward Financial Growth, Wallet

### Community 83 - "Community 83"
Cohesion: 0.83
Nodes (4): Finance App Icon, Financial Growth Chart, Payment Card, Digital Wallet

### Community 84 - "Community 84"
Cohesion: 0.50
Nodes (4): win, icon, target, nsis

### Community 85 - "Community 85"
Cohesion: 0.50
Nodes (4): Automation and release operations, Electron package scripts, OpenWiki update workflow, Pull request review boundary

### Community 86 - "Community 86"
Cohesion: 0.67
Nodes (3): OpenWiki Update Workflow, Personal Finance Tracker, OpenWiki Agent Instructions

### Community 87 - "Community 87"
Cohesion: 0.67
Nodes (3): Finance Tracker App Launcher Icon, Financial Tracking, Upward Financial Trend

### Community 88 - "Community 88"
Cohesion: 0.67
Nodes (3): Finance Tracker Launcher Icon, Upward Bar Chart, Wallet

### Community 89 - "Community 89"
Cohesion: 0.67
Nodes (3): Finance Tracker App Icon, Financial Data Visualization, Money and Currency

### Community 90 - "Community 90"
Cohesion: 0.67
Nodes (3): Ascending Financial Chart, Finance Tracker Launcher Icon, Gold Coin

### Community 92 - "Community 92"
Cohesion: 0.67
Nodes (3): Bank reconciliation workflow, CSV transaction matching, DataStore.chooseBankCsv

## Knowledge Gaps
- **248 isolated node(s):** `Budget`, `NetWorth`, `Loans`, `SavingsGoals`, `BNPL` (+243 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **45 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FinanceViewModel` connect `Community 10` to `Community 0`, `Community 3`, `Community 40`, `Community 41`, `Community 14`, `Community 53`, `Community 54`, `Community 25`, `Community 26`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `FinanceRepository` connect `Community 3` to `Community 40`, `Community 2`, `Community 10`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `CategoryState` connect `Community 40` to `Community 0`, `Community 3`, `Community 5`, `Community 10`, `Community 16`, `Community 26`, `Community 28`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `FinanceDirectoryStore` (e.g. with `.categoriesCreateDeleteRenameAndBlockUnsafeDeletion()` and `.migratedDirectory()`) actually correct?**
  _`FinanceDirectoryStore` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Budget`, `NetWorth`, `Loans` to the rest of the system?**
  _248 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.07114170969592656 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.06414414414414414 - nodes in this community are weakly interconnected._