import tkinter as tk
from .state import AppState
from .ui.main_view import MainView
from .ui.style import DARK_BG

def main():
    root = tk.Tk()
    root.configure(background=DARK_BG)  # Add this line
    state = AppState()
    MainView(root, state)
    root.mainloop()