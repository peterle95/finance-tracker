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
from .tabs.goals_tab import GoalsTab

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
            self.goals_tab.refresh_goals()
        self.on_data_changed = on_data_changed

        # Tabs
        self.add_tab = AddTransactionTab(self.notebook, self.state, self.on_data_changed)
        self.view_tab = ViewTransactionsTab(self.notebook, self.state, self.on_data_changed)
        self.transfers_tab = TransfersTab(self.notebook, self.state, self.on_data_changed)
        self.reports_tab = ReportsTab(self.notebook, self.state)
        self.settings_tab = SettingsTab(self.notebook, self.state)
        self.budgets_tab = BudgetsTab(self.notebook, self.state)
        self.goals_tab = GoalsTab(self.notebook, self.state)
        self.projection_tab = ProjectionTab(self.notebook, self.state)

        # Help Button
        help_button_frame = ttk.Frame(main_frame)
        help_button_frame.pack(fill='x', pady=(5, 0))
        ttk.Button(help_button_frame, text="?", style="Help.TButton",
                   width=3, command=lambda: show_help(self.root)).pack(side='right')
        
        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()

    def _setup_keyboard_shortcuts(self):
        """Setup global keyboard shortcuts for the application"""
        
        # Ctrl+A: Open Add Transaction tab and focus on amount field
        self.root.bind('<Control-a>', self._shortcut_add_transaction)
        self.root.bind('<Control-A>', self._shortcut_add_transaction)
        
        # Alt+Left/Right: Navigate between tabs
        self.root.bind('<Alt-Left>', self._shortcut_previous_tab)
        self.root.bind('<Alt-Right>', self._shortcut_next_tab)
        
        # For macOS compatibility (Command key)
        self.root.bind('<Command-a>', self._shortcut_add_transaction)
        self.root.bind('<Command-A>', self._shortcut_add_transaction)
    
    def _shortcut_add_transaction(self, event):
        """Handle Ctrl+A shortcut to open Add Transaction tab"""
        # Switch to Add Transaction tab (index 0)
        self.notebook.select(0)
        
        # Focus on the amount field
        self.add_tab.amount_entry.focus_set()
        
        # Select all text in amount field if any exists
        self.add_tab.amount_entry.select_range(0, tk.END)
        
        # Prevent default behavior (select all in current widget)
        return 'break'
    
    def _shortcut_previous_tab(self, event):
        """Handle Alt+Left shortcut to go to previous tab"""
        current_index = self.notebook.index(self.notebook.select())
        total_tabs = self.notebook.index('end')
        
        # Go to previous tab, wrapping around to last tab if at first
        new_index = (current_index - 1) % total_tabs
        self.notebook.select(new_index)
        
        return 'break'
    
    def _shortcut_next_tab(self, event):
        """Handle Alt+Right shortcut to go to next tab"""
        current_index = self.notebook.index(self.notebook.select())
        total_tabs = self.notebook.index('end')
        
        # Go to next tab, wrapping around to first tab if at last
        new_index = (current_index + 1) % total_tabs
        self.notebook.select(new_index)
        
        return 'break'