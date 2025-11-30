"""
finance_tracker/ui/tabs/transfers_tab.py

Tab for recording fund transfers between different asset accounts.
"""

import tkinter as tk
from tkinter import ttk, messagebox

class TransfersTab:
    def __init__(self, notebook, state, on_data_changed):
        self.state = state
        self.on_data_changed = on_data_changed

        frame = ttk.Frame(notebook, padding="20")
        notebook.add(frame, text="Transfers")

        form = ttk.Frame(frame)
        form.pack(anchor='center')

        ttk.Label(form, text="This section allows you to record movement of funds between your accounts.").grid(
            row=0, column=0, columnspan=3, sticky='w', pady=(0, 20))

        account_options = ["Bank", "Wallet", "Savings", "Investments", "Money Lent"]

        ttk.Label(form, text="From Account:").grid(row=1, column=0, sticky='w', pady=10)
        self.from_var = tk.StringVar()
        self.from_combo = ttk.Combobox(form, textvariable=self.from_var, values=account_options, width=28, state='readonly')
        self.from_combo.grid(row=1, column=1, pady=5, sticky='w')

        ttk.Label(form, text="To Account:").grid(row=2, column=0, sticky='w', pady=10)
        self.to_var = tk.StringVar()
        self.to_combo = ttk.Combobox(form, textvariable=self.to_var, values=account_options, width=28, state='readonly')
        self.to_combo.grid(row=2, column=1, pady=5, sticky='w')

        ttk.Label(form, text="Amount:").grid(row=3, column=0, sticky='w', pady=5)
        self.amount_entry = ttk.Entry(form, width=30)
        self.amount_entry.grid(row=3, column=1, pady=5, sticky='w')

        ttk.Button(form, text="Execute Transfer", command=self.execute).grid(row=4, column=1, pady=20, sticky='w')

    def execute(self):
        from_acc = self.from_var.get()
        to_acc = self.to_var.get()
        amount_str = self.amount_entry.get()

        if not from_acc or not to_acc:
            messagebox.showerror("Error", "Please select both a 'From' and 'To' account.")
            return
        if from_acc == to_acc:
            messagebox.showerror("Error", "The 'From' and 'To' accounts cannot be the same.")
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showerror("Error", "Transfer amount must be positive.")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid amount entered.")
            return

        keys = {
            "Bank": "bank_account_balance",
            "Wallet": "wallet_balance",
            "Savings": "savings_balance",
            "Investments": "investment_balance",
            "Money Lent": "money_lent_balance"
        }
        from_key = keys[from_acc]
        to_key = keys[to_acc]
        self.state.budget_settings[from_key] -= amount
        self.state.budget_settings[to_key] += amount
        self.state.save()
        self.on_data_changed()
        messagebox.showinfo("Success", f"Successfully transferred €{amount:.2f} from {from_acc} to {to_acc}.")
        self.amount_entry.delete(0, tk.END)
        self.from_var.set('')
        self.to_var.set('')