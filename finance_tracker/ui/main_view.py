"""
finance_tracker/ui/main_view.py

Main application window and tab management.
"""

import tkinter as tk
from tkinter import ttk

from .style import apply_styles
from .help_window import show_help
from .shortcuts import ShortcutManager

from .tabs.add_transaction_tab import AddTransactionTab
from .tabs.view_transactions_tab import ViewTransactionsTab
from .tabs.reports_tab import ReportsTab
from .tabs.settings_tab import SettingsTab
from .tabs.budgets_tab import BudgetsTab
from .tabs.projection_tab import ProjectionTab
from .tabs.goals_tab import GoalsTab
from .tabs.net_worth_tab import NetWorthTab

class MainView:
    def __init__(self, root, state):
        self.root = root
        self.root.title("Personal Finance Tracker")
        
        # Set initial window size and position
        self.root.geometry("1250x750")
        
        # Ensure window is visible and on top initially
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)
        
        # Force window to normal state (not minimized)
        self.root.state('normal')
        
        # Make sure window is visible
        self.root.deiconify()
        
        self.root.minsize(1250, 750)
        apply_styles()

        self.state = state

        main_frame = ttk.Frame(root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Help Buttons - pack at bottom first
        help_button_frame = ttk.Frame(main_frame)
        help_button_frame.pack(side='bottom', fill='x', pady=(5, 0))
        
        ttk.Button(help_button_frame, text="⌨", width=3,
                   command=self._show_shortcuts_reference).pack(side='right', padx=(5, 0))
        ttk.Button(help_button_frame, text="?", width=3,
                   command=lambda: show_help(self.root)).pack(side='right')

        # Notebook - pack after help buttons
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
        self.reports_tab = ReportsTab(self.notebook, self.state)
        self.settings_tab = SettingsTab(self.notebook, self.state)
        self.budgets_tab = BudgetsTab(self.notebook, self.state)
        self.goals_tab = GoalsTab(self.notebook, self.state)
        self.net_worth_tab = NetWorthTab(self.notebook, self.state)
        self.projection_tab = ProjectionTab(self.notebook, self.state)
        
        # Setup keyboard shortcuts
        self.shortcut_manager = ShortcutManager(self)
        self.shortcut_manager.setup_shortcuts()

    def _show_shortcuts_reference(self):
        """Show keyboard shortcuts reference window"""
        shortcuts_win = tk.Toplevel(self.root)
        shortcuts_win.title("Keyboard Shortcuts Reference")
        shortcuts_win.geometry("700x650")
        shortcuts_win.minsize(600, 500)
        
        # Bind ESC to close window
        shortcuts_win.bind('<Escape>', lambda e: shortcuts_win.destroy())

        main_frame = ttk.Frame(shortcuts_win, padding=10)
        main_frame.pack(fill='both', expand=True)

        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill='both', expand=True)

        shortcuts_text = tk.Text(text_frame, wrap='word', font=('Arial', 10), spacing3=5)
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=shortcuts_text.yview)
        shortcuts_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        shortcuts_text.pack(side='left', fill='both', expand=True)

        # Configure tags
        shortcuts_text.tag_configure('title', font=('Arial', 14, 'bold'), spacing1=10)
        shortcuts_text.tag_configure('section', font=('Arial', 11, 'bold'), spacing1=8, foreground='#0066cc')
        shortcuts_text.tag_configure('shortcut', font=('Courier New', 9, 'bold'), background='#f0f0f0')
        shortcuts_text.tag_configure('description', font=('Arial', 9))
        
        # Content
        content = [
            ("KEYBOARD SHORTCUTS REFERENCE\n\n", "title"),
            
            ("Navigation Shortcuts\n", "section"),
            ("Ctrl+A", "shortcut"), (" - Open Add Transaction tab and focus amount field\n", "description"),
            ("Ctrl+V", "shortcut"), (" - Go to View Transactions tab\n", "description"),
            ("Ctrl+R", "shortcut"), (" - Go to Charts/Reports tab\n", "description"),
            ("Ctrl+B", "shortcut"), (" - Go to Budget Report tab\n", "description"),
            ("Ctrl+L", "shortcut"), (" - Go to Budgets Limits tab\n", "description"),
            ("Ctrl+G", "shortcut"), (" - Go to Savings Goals tab\n", "description"),
            ("Ctrl+P", "shortcut"), (" - Go to Projection tab\n", "description"),
            ("Alt+Left", "shortcut"), (" - Go to previous tab\n", "description"),
            ("Alt+Right", "shortcut"), (" - Go to next tab\n\n", "description"),
            
            ("Action Shortcuts\n", "section"),
            ("Ctrl+S", "shortcut"), (" - Save current form/settings (context-aware)\n", "description"),
            ("Ctrl+N", "shortcut"), (" - New transaction (clears Add Transaction form)\n", "description"),
            ("Ctrl+D", "shortcut"), (" - Delete selected item\n", "description"),
            ("Delete", "shortcut"), (" - Delete selected item\n", "description"),
            ("Ctrl+E", "shortcut"), (" - Edit/Modify selected transaction\n", "description"),
            ("F5", "shortcut"), (" - Refresh current view\n", "description"),
            ("Escape", "shortcut"), (" - Clear current form or close dialog windows\n", "description"),
            ("Tab", "shortcut"), (" - Navigate between fields and buttons\n", "description"),
            ("Enter", "shortcut"), (" - Activate focused button\n\n", "description"),
            
            ("Report Shortcuts\n", "section"),
            ("Ctrl+Shift+R", "shortcut"), (" - Generate report in current tab\n", "description"),
            ("Ctrl+Shift+E", "shortcut"), (" - Export current report\n", "description"),
            ("Ctrl+Shift+G", "shortcut"), (" - Generate and view budget report\n\n", "description"),
            
            ("Quick Entry Shortcuts\n", "section"),
            ("Alt+E", "shortcut"), (" - Toggle Expense/Income type (in Add Transaction)\n\n", "description"),
            
            ("View Shortcuts\n", "section"),
            ("Ctrl+F", "shortcut"), (" - Focus search/filter field\n\n", "description"),
            
            ("Help\n", "section"),
            ("Ctrl+H", "shortcut"), (" - Show Help & Instructions\n", "description"),
            ("F1", "shortcut"), (" - Show Help & Instructions\n\n", "description"),
            
            ("Notes:\n", "section"),
            ("• On macOS, use ", "description"), ("Cmd", "shortcut"), (" instead of ", "description"), 
            ("Ctrl", "shortcut"), (" for most shortcuts\n", "description"),
            ("• Context-aware shortcuts behave differently based on the active tab\n", "description"),
            ("• Some shortcuts work globally, others only in specific tabs\n", "description"),
            ("• Press ", "description"), ("Escape", "shortcut"), (" to close this window\n", "description"),
        ]
        
        for text, tag in content:
            shortcuts_text.insert(tk.END, text, tag)

        shortcuts_text.config(state='disabled')
        
        # Close button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        ttk.Button(button_frame, text="Close", command=shortcuts_win.destroy).pack(side='right')