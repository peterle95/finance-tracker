import tkinter as tk
from .state import AppState
from .ui.main_view import MainView

def main():
    root = tk.Tk()
    state = AppState()
    MainView(root, state)
    root.mainloop()