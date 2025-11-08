import tkinter as tk
from tkinter import ttk
import os

from .style import apply_styles
from .help_window import show_help
from .theme_manager import theme_manager

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
        
        # Set window icon if it exists
        try:
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Could not load window icon: {e}")
        
        # Apply initial styles
        self.style = apply_styles(self.root)
        
        # Store references to all themed widgets for updates
        self.themed_widgets = []
        
        self.state = state

        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        self.themed_widgets.append(self.main_frame)

        # Notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill='both', expand=True)
        self.themed_widgets.append(self.notebook)

        # Callback to refresh UI after data changes
        def on_data_changed():
            self.view_tab.refresh()
            self.settings_tab.refresh_fixed_costs_tree()
            self.settings_tab.refresh_balance_entries()
            self.goals_tab.refresh_goals()
        self.on_data_changed = on_data_changed

        # Create tabs
        self.create_tabs()
        
        # Theme toggle button
        self.create_theme_controls()
        
        # Register for theme changes
        theme_manager.register_callback(self.on_theme_changed)
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_tabs(self):
        """Create all application tabs"""
        # Tabs
        self.add_tab = AddTransactionTab(self.notebook, self.state, self.on_data_changed)
        self.view_tab = ViewTransactionsTab(self.notebook, self.state, self.on_data_changed)
        self.transfers_tab = TransfersTab(self.notebook, self.state, self.on_data_changed)
        self.reports_tab = ReportsTab(self.notebook, self.state)
        self.settings_tab = SettingsTab(self.notebook, self.state)
        self.budgets_tab = BudgetsTab(self.notebook, self.state)
        self.goals_tab = GoalsTab(self.notebook, self.state)
        self.projection_tab = ProjectionTab(self.notebook, self.state)
        
        # Store tab references for theme updates
        self.tabs = [
            self.add_tab, self.view_tab, self.transfers_tab, 
            self.reports_tab, self.settings_tab, self.budgets_tab,
            self.goals_tab, self.projection_tab
        ]
    
    def create_theme_controls(self):
        """Create theme toggle controls"""
        # Create a frame for the theme toggle and help button
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill='x', pady=(5, 0))
        
        # Theme toggle button
        self.theme_button = ttk.Button(
            control_frame, 
            text="☀️" if theme_manager.dark_mode else "🌙",
            command=self.toggle_theme,
            width=3,
            style="TButton"
        )
        self.theme_button.pack(side='left', padx=(0, 5))
        
        # Help button
        help_button = ttk.Button(
            control_frame, 
            text="?", 
            style="Help.TButton",
            width=3, 
            command=lambda: show_help(self.root)
        )
        help_button.pack(side='right')
        
        # Add to themed widgets
        self.themed_widgets.extend([control_frame, self.theme_button, help_button])
    
    def toggle_theme(self):
        """Toggle between dark and light theme"""
        theme_manager.toggle_theme()
    
    def on_theme_changed(self, dark_mode):
        """Handle theme change event"""
        # Update theme button icon
        self.theme_button.config(text="☀️" if dark_mode else "🌙")
        
        # Re-apply styles
        self.style = apply_styles(self.root)
        
        # Update all tabs
        for tab in self.tabs:
            if hasattr(tab, 'on_theme_changed'):
                tab.on_theme_changed(dark_mode)
        
        # Force update of all widgets
        self.root.update_idletasks()
    
    def on_close(self):
        """Handle window close event"""
        # Unregister from theme manager
        theme_manager.unregister_callback(self.on_theme_changed)
        # Close the window
        self.root.destroy()