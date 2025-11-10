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
from .tabs.net_worth_tab import NetWorthTab

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
        self.net_worth_tab = NetWorthTab(self.notebook, self.state)
        self.projection_tab = ProjectionTab(self.notebook, self.state)

        # Help Buttons
        help_button_frame = ttk.Frame(main_frame)
        help_button_frame.pack(fill='x', pady=(5, 0))
        ttk.Button(help_button_frame, text="⌨", style="Help.TButton",
                   width=3, command=self._show_shortcuts_reference).pack(side='right', padx=(5, 0))
        ttk.Button(help_button_frame, text="?", style="Help.TButton",
                   width=3, command=lambda: show_help(self.root)).pack(side='right')
        
        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        # Enable Enter key on buttons globally
        self._setup_button_enter_key()

    def _setup_button_enter_key(self):
        """Enable Enter key to activate focused buttons"""
        def on_button_enter(event):
            widget = event.widget
            if isinstance(widget, ttk.Button):
                widget.invoke()
                return 'break'
        
        self.root.bind_class('TButton', '<Return>', on_button_enter)
        self.root.bind_class('TButton', '<KP_Enter>', on_button_enter)

    def _setup_keyboard_shortcuts(self):
        """Setup global keyboard shortcuts for the application"""
        
        # Navigation Shortcuts - Add Transaction
        self.root.bind('<Control-a>', self._shortcut_add_transaction)
        self.root.bind('<Control-A>', self._shortcut_add_transaction)
        
        # Navigation Shortcuts - Tabs
        self.root.bind('<Control-v>', lambda e: self._switch_to_tab(1))
        self.root.bind('<Control-V>', lambda e: self._switch_to_tab(1))
        self.root.bind('<Control-t>', lambda e: self._switch_to_tab(2))
        self.root.bind('<Control-T>', lambda e: self._switch_to_tab(2))
        self.root.bind('<Control-r>', lambda e: self._switch_to_tab(3))
        self.root.bind('<Control-R>', lambda e: self._switch_to_tab(3))
        self.root.bind('<Control-b>', lambda e: self._switch_to_tab(4))
        self.root.bind('<Control-B>', lambda e: self._switch_to_tab(4))
        self.root.bind('<Control-l>', lambda e: self._switch_to_tab(5))
        self.root.bind('<Control-L>', lambda e: self._switch_to_tab(5))
        self.root.bind('<Control-g>', lambda e: self._switch_to_tab(6))
        self.root.bind('<Control-G>', lambda e: self._switch_to_tab(6))
        self.root.bind('<Control-w>', lambda e: self._switch_to_tab(7))
        self.root.bind('<Control-W>', lambda e: self._switch_to_tab(7))
        self.root.bind('<Control-p>', lambda e: self._switch_to_tab(8))
        self.root.bind('<Control-P>', lambda e: self._switch_to_tab(8))
        
        # Help
        self.root.bind('<Control-h>', lambda e: show_help(self.root))
        self.root.bind('<Control-H>', lambda e: show_help(self.root))
        self.root.bind('<F1>', lambda e: show_help(self.root))
        
        # Alt+Left/Right: Navigate between tabs
        self.root.bind('<Alt-Left>', self._shortcut_previous_tab)
        self.root.bind('<Alt-Right>', self._shortcut_next_tab)
        
        # Action Shortcuts
        self.root.bind('<Control-s>', self._shortcut_save)
        self.root.bind('<Control-S>', self._shortcut_save)
        self.root.bind('<Control-n>', self._shortcut_new_transaction)
        self.root.bind('<Control-N>', self._shortcut_new_transaction)
        self.root.bind('<Control-d>', self._shortcut_delete)
        self.root.bind('<Control-D>', self._shortcut_delete)
        self.root.bind('<Control-e>', self._shortcut_edit)
        self.root.bind('<Control-E>', self._shortcut_edit)
        self.root.bind('<Delete>', self._shortcut_delete)
        self.root.bind('<F5>', self._shortcut_refresh)
        
        # Report Shortcuts
        self.root.bind('<Control-Shift-R>', self._shortcut_generate_report)
        self.root.bind('<Control-Shift-E>', self._shortcut_export)
        self.root.bind('<Control-Shift-G>', self._shortcut_budget_report)
        self.root.bind('<Control-Shift-N>', self._shortcut_net_worth_snapshot)
        
        # Quick Entry - Toggle Expense/Income
        self.root.bind('<Alt-e>', self._shortcut_toggle_type)
        self.root.bind('<Alt-E>', self._shortcut_toggle_type)
        
        # View Shortcuts
        self.root.bind('<Control-f>', self._shortcut_focus_filter)
        self.root.bind('<Control-F>', self._shortcut_focus_filter)
        
        # Escape to clear forms
        self.root.bind('<Escape>', self._shortcut_escape)
        
        # For macOS compatibility (Command key)
        self.root.bind('<Command-a>', self._shortcut_add_transaction)
        self.root.bind('<Command-A>', self._shortcut_add_transaction)
        self.root.bind('<Command-s>', self._shortcut_save)
        self.root.bind('<Command-S>', self._shortcut_save)
        self.root.bind('<Command-n>', self._shortcut_new_transaction)
        self.root.bind('<Command-N>', self._shortcut_new_transaction)
    
    def _switch_to_tab(self, index):
        """Switch to a specific tab by index"""
        total_tabs = self.notebook.index('end')
        if 0 <= index < total_tabs:
            self.notebook.select(index)
        return 'break'
    
    def _shortcut_add_transaction(self, event):
        """Handle Ctrl+A shortcut to open Add Transaction tab"""
        self.notebook.select(0)
        self.add_tab.amount_entry.focus_set()
        self.add_tab.amount_entry.select_range(0, tk.END)
        return 'break'
    
    def _shortcut_new_transaction(self, event):
        """Handle Ctrl+N shortcut to clear Add Transaction form"""
        self.notebook.select(0)
        # Clear all fields
        self.add_tab.date_entry.delete(0, tk.END)
        from datetime import datetime
        self.add_tab.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.add_tab.amount_entry.delete(0, tk.END)
        self.add_tab.description_entry.delete(0, tk.END)
        self.add_tab.transaction_type_var.set("Expense")
        self.add_tab.update_categories()
        self.add_tab.amount_entry.focus_set()
        return 'break'
    
    def _shortcut_previous_tab(self, event):
        """Handle Alt+Left shortcut to go to previous tab"""
        current_index = self.notebook.index(self.notebook.select())
        total_tabs = self.notebook.index('end')
        new_index = (current_index - 1) % total_tabs
        self.notebook.select(new_index)
        return 'break'
    
    def _shortcut_next_tab(self, event):
        """Handle Alt+Right shortcut to go to next tab"""
        current_index = self.notebook.index(self.notebook.select())
        total_tabs = self.notebook.index('end')
        new_index = (current_index + 1) % total_tabs
        self.notebook.select(new_index)
        return 'break'
    
    def _shortcut_save(self, event):
        """Handle Ctrl+S shortcut to save in current tab"""
        current_index = self.notebook.index(self.notebook.select())
        
        if current_index == 0:  # Add Transaction
            self.add_tab.add_transaction()
        elif current_index == 4:  # Budget Report (Settings)
            self.settings_tab.save_settings()
        elif current_index == 5:  # Budgets Limits
            self.budgets_tab.save_budgets()
        elif current_index == 6:  # Goals
            if self.goals_tab.selected_goal_index is not None:
                self.goals_tab.update_goal()
            else:
                self.goals_tab.add_goal()
        elif current_index == 7:  # Net Worth - record snapshot
            self.net_worth_tab.record_snapshot()
        
        return 'break'
    
    def _shortcut_delete(self, event):
        """Handle Ctrl+D or Delete shortcut to delete selected item"""
        current_index = self.notebook.index(self.notebook.select())
        
        if current_index == 1:  # View Transactions
            self.view_tab.delete_transaction()
        elif current_index == 6:  # Goals
            # Delete selected goal if any widget has focus in goals tab
            if self.goals_tab.selected_goal_index is not None:
                self.goals_tab.delete_goal(self.goals_tab.selected_goal_index)
        elif current_index == 7:  # Net Worth
            self.net_worth_tab.delete_selected_snapshot()
        
        return 'break'
    
    def _shortcut_edit(self, event):
        """Handle Ctrl+E shortcut to edit selected item"""
        current_index = self.notebook.index(self.notebook.select())
        
        if current_index == 1:  # View Transactions
            self.view_tab.open_modify_window()
        
        return 'break'
    
    def _shortcut_refresh(self, event):
        """Handle F5 shortcut to refresh current view"""
        current_index = self.notebook.index(self.notebook.select())
        
        if current_index == 1:  # View Transactions
            self.view_tab.refresh()
        elif current_index == 4:  # Budget Report
            self.settings_tab.generate_report()
        elif current_index == 5:  # Budgets Limits
            self.budgets_tab._update_monetary_labels()
        elif current_index == 6:  # Goals
            self.goals_tab.refresh_goals()
        elif current_index == 7:  # Net Worth
            self.net_worth_tab.refresh()
        
        return 'break'
    
    def _shortcut_generate_report(self, event):
        """Handle Ctrl+Shift+R to generate report in current tab"""
        current_index = self.notebook.index(self.notebook.select())
        
        if current_index == 3:  # Charts/Reports
            self.reports_tab.generate()
        elif current_index == 4:  # Budget Report
            self.settings_tab.generate_report()
        elif current_index == 6:  # Goals
            self.goals_tab.show_report()
        elif current_index == 7:  # Net Worth
            self.net_worth_tab.show_report()
        elif current_index == 8:  # Projection
            self.projection_tab.generate()
        
        return 'break'
    
    def _shortcut_export(self, event):
        """Handle Ctrl+Shift+E to export current report"""
        current_index = self.notebook.index(self.notebook.select())
        
        if current_index == 4:  # Budget Report
            self.settings_tab.export_report()
        elif current_index == 6:  # Goals
            self.goals_tab.export_report()
        elif current_index == 7:  # Net Worth
            self.net_worth_tab.export_report()
        elif current_index == 8:  # Projection
            self.projection_tab.export()
        
        return 'break'
    
    def _shortcut_budget_report(self, event):
        """Handle Ctrl+Shift+G to generate budget report"""
        self.notebook.select(4)  # Switch to Budget Report tab
        self.settings_tab.generate_report()
        return 'break'
    
    def _shortcut_net_worth_snapshot(self, event):
        """Handle Ctrl+Shift+N to record net worth snapshot"""
        self.notebook.select(7)  # Switch to Net Worth tab
        self.net_worth_tab.record_snapshot()
        return 'break'
    
    def _shortcut_toggle_type(self, event):
        """Handle Alt+E to toggle Expense/Income type in Add Transaction"""
        current_index = self.notebook.index(self.notebook.select())
        
        if current_index == 0:  # Add Transaction
            current = self.add_tab.transaction_type_var.get()
            self.add_tab.transaction_type_var.set("Income" if current == "Expense" else "Expense")
            self.add_tab.update_categories()
        
        return 'break'
    
    def _shortcut_focus_filter(self, event):
        """Handle Ctrl+F to focus filter/search field"""
        current_index = self.notebook.index(self.notebook.select())
        
        if current_index == 1:  # View Transactions
            self.view_tab.month_filter.focus_set()
            self.view_tab.month_filter.select_range(0, tk.END)
        elif current_index == 3:  # Charts
            self.reports_tab.month_entry.focus_set()
            self.reports_tab.month_entry.select_range(0, tk.END)
        elif current_index == 5:  # Budgets Limits
            self.budgets_tab.month_var.get()
        
        return 'break'
    
    def _shortcut_escape(self, event):
        """Handle Escape to clear forms or close dialogs"""
        current_index = self.notebook.index(self.notebook.select())
        
        if current_index == 0:  # Add Transaction - clear description
            self.add_tab.description_entry.delete(0, tk.END)
        elif current_index == 6:  # Goals - clear form
            self.goals_tab.clear_form()
        
        return 'break'
    
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
            ("Ctrl+T", "shortcut"), (" - Go to Transfers tab\n", "description"),
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