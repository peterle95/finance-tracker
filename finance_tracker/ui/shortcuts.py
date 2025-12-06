"""
finance_tracker/ui/shortcuts.py

This module handles the registration and processing of keyboard shortcuts for the application.
It separates the shortcut logic from the main view to improve modularity.
"""

import tkinter as tk
from tkinter import ttk
from .help_window import show_help
from datetime import datetime

class ShortcutManager:
    def __init__(self, main_view):
        self.mv = main_view
        self.root = main_view.root
        self.notebook = main_view.notebook

    def setup_shortcuts(self):
        """Setup global keyboard shortcuts for the application"""
        
        # Navigation Shortcuts - Add Transaction
        self.root.bind('<Control-a>', self._shortcut_add_transaction)
        self.root.bind('<Control-A>', self._shortcut_add_transaction)
        
        # Navigation Shortcuts - Tabs
        self.root.bind('<Control-v>', lambda e: self._switch_to_tab(1))
        self.root.bind('<Control-V>', lambda e: self._switch_to_tab(1))
        self.root.bind('<Control-r>', lambda e: self._switch_to_tab(2))
        self.root.bind('<Control-R>', lambda e: self._switch_to_tab(2))
        self.root.bind('<Control-b>', lambda e: self._switch_to_tab(3))
        self.root.bind('<Control-B>', lambda e: self._switch_to_tab(3))
        self.root.bind('<Control-l>', lambda e: self._switch_to_tab(4))
        self.root.bind('<Control-L>', lambda e: self._switch_to_tab(4))
        self.root.bind('<Control-g>', lambda e: self._switch_to_tab(5))
        self.root.bind('<Control-G>', lambda e: self._switch_to_tab(5))
        self.root.bind('<Control-w>', lambda e: self._switch_to_tab(6))
        self.root.bind('<Control-W>', lambda e: self._switch_to_tab(6))
        self.root.bind('<Control-p>', lambda e: self._switch_to_tab(7))
        self.root.bind('<Control-P>', lambda e: self._switch_to_tab(7))
        
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
    
    def _switch_to_tab(self, index):
        """Switch to a specific tab by index"""
        total_tabs = self.notebook.index('end')
        if 0 <= index < total_tabs:
            self.notebook.select(index)
        return 'break'
    
    def _shortcut_add_transaction(self, event):
        """Handle Ctrl+A shortcut to open Add Transaction tab"""
        self.notebook.select(0)
        self.mv.add_tab.amount_entry.focus_set()
        self.mv.add_tab.amount_entry.select_range(0, tk.END)
        return 'break'
    
    def _shortcut_new_transaction(self, event):
        """Handle Ctrl+N shortcut to clear Add Transaction form"""
        self.notebook.select(0)
        # Clear all fields
        self.mv.add_tab.date_entry.delete(0, tk.END)
        self.mv.add_tab.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.mv.add_tab.amount_entry.delete(0, tk.END)
        self.mv.add_tab.description_entry.delete(0, tk.END)
        self.mv.add_tab.transaction_type_var.set("Expense")
        self.mv.add_tab.update_categories()
        self.mv.add_tab.amount_entry.focus_set()
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
            self.mv.add_tab.add_transaction()
        elif current_index == 3:  # Budget Report (Settings)
            self.mv.settings_tab.save_settings()
        elif current_index == 4:  # Budgets Limits
            self.mv.budgets_tab.save_budgets()
        elif current_index == 5:  # Goals
            if self.mv.goals_tab.selected_goal_index is not None:
                self.mv.goals_tab.update_goal()
            else:
                self.mv.goals_tab.add_goal()
        elif current_index == 6:  # Net Worth - record snapshot
            self.mv.net_worth_tab.record_snapshot()
        
        return 'break'
    
    def _shortcut_delete(self, event):
        """Handle Ctrl+D or Delete shortcut to delete selected item"""
        current_index = self.notebook.index(self.notebook.select())
        
        if current_index == 1:  # View Transactions
            self.mv.view_tab.delete_transaction()
        elif current_index == 5:  # Goals
            # Delete selected goal if any widget has focus in goals tab
            if self.mv.goals_tab.selected_goal_index is not None:
                self.mv.goals_tab.delete_goal(self.mv.goals_tab.selected_goal_index)
        elif current_index == 6:  # Net Worth
            self.mv.net_worth_tab.delete_selected_snapshot()
        
        return 'break'
    
    def _shortcut_edit(self, event):
        """Handle Ctrl+E shortcut to edit selected item"""
        current_index = self.notebook.index(self.notebook.select())
        
        if current_index == 1:  # View Transactions
            self.mv.view_tab.open_modify_window()
        
        return 'break'
    
    def _shortcut_refresh(self, event):
        """Handle F5 shortcut to refresh current view"""
        current_index = self.notebook.index(self.notebook.select())
        
        if current_index == 1:  # View Transactions
            self.mv.view_tab.refresh()
        elif current_index == 3:  # Budget Report
            self.mv.settings_tab.generate_report()
        elif current_index == 4:  # Budgets Limits
            self.mv.budgets_tab._update_monetary_labels()
        elif current_index == 5:  # Goals
            self.mv.goals_tab.refresh_goals()
        elif current_index == 6:  # Net Worth
            self.mv.net_worth_tab.refresh()
        
        return 'break'
    
    def _shortcut_generate_report(self, event):
        """Handle Ctrl+Shift+R to generate report in current tab"""
        current_index = self.notebook.index(self.notebook.select())
        
        if current_index == 2:  # Charts/Reports
            self.mv.reports_tab.generate()
        elif current_index == 3:  # Budget Report
            self.mv.settings_tab.generate_report()
        elif current_index == 5:  # Goals
            self.mv.goals_tab.show_report()
        elif current_index == 6:  # Net Worth
            self.mv.net_worth_tab.show_report()
        elif current_index == 7:  # Projection
            self.mv.projection_tab.generate()
        
        return 'break'
    
    def _shortcut_export(self, event):
        """Handle Ctrl+Shift+E to export current report"""
        current_index = self.notebook.index(self.notebook.select())
        
        if current_index == 3:  # Budget Report
            self.mv.settings_tab.export_report()
        elif current_index == 5:  # Goals
            self.mv.goals_tab.export_report()
        elif current_index == 6:  # Net Worth
            self.mv.net_worth_tab.export_report()
        elif current_index == 7:  # Projection
            self.mv.projection_tab.export()
        
        return 'break'
    
    def _shortcut_budget_report(self, event):
        """Handle Ctrl+Shift+G to generate budget report"""
        self.notebook.select(3)  # Switch to Budget Report tab
        self.mv.settings_tab.generate_report()
        return 'break'
    
    def _shortcut_net_worth_snapshot(self, event):
        """Handle Ctrl+Shift+N to record net worth snapshot"""
        self.notebook.select(6)  # Switch to Net Worth tab
        self.mv.net_worth_tab.record_snapshot()
        return 'break'
    
    def _shortcut_toggle_type(self, event):
        """Handle Alt+E to toggle Expense/Income type in Add Transaction"""
        current_index = self.notebook.index(self.notebook.select())
        
        if current_index == 0:  # Add Transaction
            current = self.mv.add_tab.transaction_type_var.get()
            self.mv.add_tab.transaction_type_var.set("Income" if current == "Expense" else "Expense")
            self.mv.add_tab.update_categories()
        
        return 'break'
    
    def _shortcut_focus_filter(self, event):
        """Handle Ctrl+F to focus filter/search field"""
        current_index = self.notebook.index(self.notebook.select())
        
        if current_index == 1:  # View Transactions
            self.mv.view_tab.month_filter.focus_set()
            self.mv.view_tab.month_filter.select_range(0, tk.END)
        elif current_index == 2:  # Charts
            self.mv.reports_tab.month_entry.focus_set()
            self.mv.reports_tab.month_entry.select_range(0, tk.END)
        elif current_index == 4:  # Budgets Limits
            self.mv.budgets_tab.month_var.get()
        
        return 'break'
    
    def _shortcut_escape(self, event):
        """Handle Escape to clear forms or close dialogs"""
        current_index = self.notebook.index(self.notebook.select())
        
        if current_index == 0:  # Add Transaction - clear description
            self.mv.add_tab.description_entry.delete(0, tk.END)
        elif current_index == 5:  # Goals - clear form
            self.mv.goals_tab.clear_form()
        
        return 'break'
