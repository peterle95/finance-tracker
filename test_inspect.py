import sys
import tkinter as tk
from tkinter import ttk
from unittest.mock import MagicMock
import finance_tracker.ui.tabs.settings_tab as st
import finance_tracker.ui.tabs.view_transactions_tab as vt

root = tk.Tk()
state = MagicMock()
state.budget_settings = {}
notebook = ttk.Notebook(root)

try:
    settings_tab = st.SettingsTab(notebook, state)
    print("Income button command:", settings_tab.income_btn.cget('command'))
    print("Income button state:", settings_tab.income_btn.state())
except Exception as e:
    print("Settings error:", e)

try:
    view_tab = vt.ViewTransactionsTab(notebook, state, MagicMock())
    for child in view_tab.frame.winfo_children():
        if isinstance(child, ttk.Frame):
            for c in child.winfo_children():
                if isinstance(c, ttk.Button) and c.cget('text') == 'Modify Selected':
                    print("Modify Selected command:", c.cget('command'))
                    print("Modify Selected state:", c.state())
except Exception as e:
    print("View error:", e)

