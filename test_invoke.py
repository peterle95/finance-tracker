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

try:
    print("Invoking income_btn...")
    tab.income_btn.invoke()
    print("Invoked successfully.")
except Exception as e:
    print("Error during invoke:", e)

