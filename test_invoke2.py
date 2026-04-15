import sys
import tkinter as tk
from tkinter import ttk
from unittest.mock import MagicMock
import finance_tracker.ui.tabs.settings_tab as st

root = tk.Tk()
state = MagicMock()
state.budget_settings = {}
notebook = ttk.Notebook(root)
tab = st.SettingsTab(notebook, state)

print("Invoking income_btn...")
try:
    tab.income_btn.invoke()
    print("Invoked successfully.")
except Exception as e:
    import traceback
    traceback.print_exc()

