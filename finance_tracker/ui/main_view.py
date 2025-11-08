import tkinter as tk
from tkinter import ttk

from .style import apply_styles
from .help_window import show_help

from .tabs.add_transaction_tab import AddTransactionTab
from .tabs.view_transactions_tab import ViewTransactionsTab
from .tabs.transfers_tab import TransfersTab
from .tabs.reports_tab import ReportsTab
from .tabs.settings_tab import SettingsTab
from .tabs.budgets_tab import BudgetsTab
from .tabs.projection_tab import ProjectionTab
from .tabs.goals_tab import GoalsTab  # Add this import

class MainView:
    def __init__(self, root, state):
        self.root = root
        self.root.title("Personal Finance Tracker")
        self.root.minsize(1250, 750)
        apply_styles()

        self.state = state

        main_frame = ttk.Frame(root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)

        # Callback to refresh UI after data changes
        def on_data_changed():
            self.view_tab.refresh()
            self.settings_tab.refresh_fixed_costs_tree()
            self.settings_tab.refresh_balance_entries()
            self.goals_tab.refresh_goals()  # Add this line
        self.on_data_changed = on_data_changed

        # Tabs
        self.add_tab = AddTransactionTab(self.notebook, self.state, self.on_data_changed)
        self.view_tab = ViewTransactionsTab(self.notebook, self.state, self.on_data_changed)
        self.transfers_tab = TransfersTab(self.notebook, self.state, self.on_data_changed)
        self.reports_tab = ReportsTab(self.notebook, self.state)
        self.settings_tab = SettingsTab(self.notebook, self.state)
        self.budgets_tab = BudgetsTab(self.notebook, self.state)
        self.goals_tab = GoalsTab(self.notebook, self.state)  # Add this line
        self.projection_tab = ProjectionTab(self.notebook, self.state)

        # Help Button
        help_button_frame = ttk.Frame(main_frame)
        help_button_frame.pack(fill='x', pady=(5, 0))
        ttk.Button(help_button_frame, text="?", style="Help.TButton",
                   width=3, command=lambda: show_help(self.root)).pack(side='right')