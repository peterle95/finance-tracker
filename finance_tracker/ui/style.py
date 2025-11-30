"""
finance_tracker/ui/style.py

Defines and applies custom Tkinter styles for the application.
"""

from tkinter import ttk

def apply_styles():
    style = ttk.Style()
    style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
    style.configure("TLabel", font=('Arial', 10))
    style.configure("TButton", font=('Arial', 10))
    style.configure("TRadiobutton", font=('Arial', 10))
    style.configure("Help.TButton", font=('Arial', 12, 'bold'))
    
    # Style for completed goals
    style.configure("Complete.TFrame", background='#e8f5e9')