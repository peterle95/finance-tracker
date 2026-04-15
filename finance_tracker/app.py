"""
finance_tracker/app.py

Main application entry point and initialization.
"""

import tkinter as tk
import traceback

from .state import AppState
from .ui.main_view import MainView


def main():
    root = tk.Tk()

    def report_callback_exception(exc, val, tb):
        traceback.print_exception(exc, val, tb)

    root.report_callback_exception = report_callback_exception

    state = AppState()
    MainView(root, state)
    root.mainloop()
