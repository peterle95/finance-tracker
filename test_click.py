import sys
import tkinter as tk
from tkinter import ttk
from unittest.mock import MagicMock
import finance_tracker.ui.tabs.view_transactions_tab as vt

root = tk.Tk()
state = MagicMock()
notebook = ttk.Notebook(root)

try:
    view_tab = vt.ViewTransactionsTab(notebook, state, MagicMock())
    # Click Modify Selected
    for child in view_tab.frame.winfo_children():
        if isinstance(child, ttk.Frame):
            for c in child.winfo_children():
                if isinstance(c, ttk.Button) and c.cget('text') == 'Modify Selected':
                    print("Invoking Modify Selected...")
                    c.invoke()
                    print("Invoked Modify Selected successfully.")
except Exception as e:
    import traceback
    traceback.print_exc()

