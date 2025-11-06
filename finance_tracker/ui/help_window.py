import tkinter as tk
from tkinter import ttk

def show_help(root):
    help_win = tk.Toplevel(root)
    help_win.title("Help & Instructions")
    help_win.geometry("800x600")
    help_win.minsize(600, 400)

    main_frame = ttk.Frame(help_win, padding=10)
    main_frame.pack(fill='both', expand=True)

    text_frame = ttk.Frame(main_frame)
    text_frame.pack(fill='both', expand=True)

    help_text_widget = tk.Text(text_frame, wrap='word', font=('Arial', 10), spacing3=5)
    scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=help_text_widget.yview)
    help_text_widget.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side='right', fill='y')
    help_text_widget.pack(side='left', fill='both', expand=True)

    help_text_widget.tag_configure('h1', font=('Arial', 16, 'bold'), spacing1=10)
    help_text_widget.tag_configure('h2', font=('Arial', 12, 'bold'), spacing1=10)
    help_text_widget.tag_configure('bold', font=('Arial', 10, 'bold'))
    help_text_widget.tag_configure('italic', font=('Arial', 10, 'italic'))

    content = [
        ("Core Concepts", "h1"),
        ("To use this tracker effectively, it's important to understand these key ideas:", "italic"),

        ("\n• Assets (Your Accounts):", "bold"),
        (" The main ones are 'Bank', 'Wallet', 'Savings', 'Investments', and 'Money Lent'. Balances are in 'Budget & Settings'.", "none"),

        ("\n• Transactions (Income/Expense):", "bold"),
        (" Money entering/leaving your finances.", "none"),

        ("\n• Transfers:", "bold"),
        (" Move money between your accounts (doesn't change net worth).", "none"),

        ("\nHow To Use Each Tab", "h1"),

        ("\nAdd Transaction Tab", "h2"),
        ("Log income or expense with date, amount, category, description.", "none"),

        ("\nView Transactions Tab", "h2"),
        ("Filter by month, modify/delete, see monthly summary.", "none"),

        ("\nTransfers Tab", "h2"),
        ("Move funds between accounts (e.g., Bank → Wallet).", "none"),

        ("\Charts Tab", "h2"),
        ("Pie chart or historical bar chart. Optional fixed/base income, budget overlays.", "none"),

        ("\nBudget Report Tab", "h2"),
        ("Balances, fixed costs, daily budget report.", "none"),

        ("\nBudgets Limits Tab", "h2"),
        ("Manage category budget limits as % of monthly flexible budget. Auto-Assign from expenses; Normalize.", "none"),

        ("\nProjection Tab", "h2"),
        ("Project future total assets based on daily savings goal.", "none"),
    ]
    for text, tag in content:
        if tag == "none":
            help_text_widget.insert(tk.END, text)
        else:
            help_text_widget.insert(tk.END, text, tag)

    help_text_widget.config(state='disabled')