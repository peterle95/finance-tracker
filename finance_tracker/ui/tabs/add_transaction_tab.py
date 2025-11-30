"""
finance_tracker/ui/tabs/add_transaction_tab.py

Tab for adding new income or expense transactions.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class AddTransactionTab:
    def __init__(self, notebook, state, on_data_changed):
        self.state = state
        self.on_data_changed = on_data_changed

        self.frame = ttk.Frame(notebook, padding="20")
        notebook.add(self.frame, text="Add Transaction")

        form = ttk.Frame(self.frame)
        form.pack(anchor='center')

        ttk.Label(form, text="Transaction Type:").grid(row=0, column=0, sticky='w', pady=10)
        self.transaction_type_var = tk.StringVar(value="Expense")
        type_frame = ttk.Frame(form)
        type_frame.grid(row=0, column=1, sticky='w', pady=5)
        ttk.Radiobutton(type_frame, text="Expense", variable=self.transaction_type_var,
                        value="Expense", command=self.update_categories).pack(side='left', padx=5)
        ttk.Radiobutton(type_frame, text="Income", variable=self.transaction_type_var,
                        value="Income", command=self.update_categories).pack(side='left', padx=5)

        ttk.Label(form, text="Date:").grid(row=1, column=0, sticky='w', pady=5)
        self.date_entry = ttk.Entry(form, width=30)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=1, column=1, pady=5, sticky='w')
        ttk.Label(form, text="(YYYY-MM-DD)", foreground="gray").grid(row=1, column=2, sticky='w', padx=5)

        ttk.Label(form, text="Amount:").grid(row=2, column=0, sticky='w', pady=5)
        self.amount_entry = ttk.Entry(form, width=30)
        self.amount_entry.grid(row=2, column=1, pady=5, sticky='w')

        ttk.Label(form, text="Category:").grid(row=3, column=0, sticky='w', pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(form, textvariable=self.category_var, width=28, state='readonly')
        self.category_combo.grid(row=3, column=1, pady=5, sticky='w')

        ttk.Label(form, text="Description:").grid(row=4, column=0, sticky='w', pady=5)
        self.description_entry = ttk.Entry(form, width=30)
        self.description_entry.grid(row=4, column=1, pady=5, sticky='w')

        ttk.Button(form, text="Add Transaction", command=self.add_transaction).grid(row=5, column=1, pady=20, sticky='w')

        self.update_categories()

    def update_categories(self):
        t = self.transaction_type_var.get()
        categories = self.state.categories.get(t, [])
        self.category_combo.config(values=categories)
        self.category_combo.set(categories[0] if categories else "")

    def add_transaction(self):
        try:
            date_str = self.date_entry.get()
            datetime.strptime(date_str, "%Y-%m-%d")
            amount = float(self.amount_entry.get())
            category = self.category_var.get()
            description = self.description_entry.get()
            trans_type = self.transaction_type_var.get()

            if not category:
                messagebox.showerror("Error", "Please select a category.")
                return

            self.state.add_transaction(trans_type, date_str, amount, category, description)
            self.amount_entry.delete(0, tk.END)
            self.description_entry.delete(0, tk.END)
            messagebox.showinfo("Success", f"{trans_type} added successfully!")
            self.on_data_changed()
        except ValueError:
            messagebox.showerror("Error", "Invalid amount or date format (YYYY-MM-DD).")