import tkinter as tk
from tkinter import ttk
from finance_tracker.ui.windowing import create_child_window

root = tk.Tk()
btn = ttk.Button(root, text="Test")
btn.pack()

try:
    win = create_child_window(btn, title="Test Window")
    print("Window created successfully!")
except Exception as e:
    print("Error creating window:", e)

