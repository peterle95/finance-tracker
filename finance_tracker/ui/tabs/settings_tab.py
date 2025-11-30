"""
finance_tracker/ui/tabs/settings_tab.py

Tab for configuring budget settings, fixed costs, and viewing daily reports.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from ...services.budget_calculator import generate_daily_budget_report

class SettingsTab:
    def __init__(self, notebook, state):
        self.state = state

        main = ttk.Frame(notebook, padding="10")
        notebook.add(main, text="Budget Report")
        main.rowconfigure(1, weight=1)
        main.columnconfigure(0, weight=1)

        top = ttk.Frame(main)
        top.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        top.columnconfigure(1, weight=1)

        settings = ttk.LabelFrame(top, text="Monthly Settings & Balances", padding="10")
        settings.grid(row=0, column=0, sticky='ns', padx=(0, 10))

        ttk.Label(settings, text="Base Monthly Income:").grid(row=0, column=0, sticky='w', pady=5)
        self.income_entry = ttk.Entry(settings, width=15)
        self.income_entry.grid(row=0, column=1, pady=5)

        ttk.Label(settings, text="Bank Account Balance:").grid(row=1, column=0, sticky='w', pady=5)
        self.bank_entry = ttk.Entry(settings, width=15)
        self.bank_entry.grid(row=1, column=1, pady=5)

        ttk.Label(settings, text="Wallet Balance:").grid(row=2, column=0, sticky='w', pady=5)
        self.wallet_entry = ttk.Entry(settings, width=15)
        self.wallet_entry.grid(row=2, column=1, pady=5)

        ttk.Label(settings, text="Current Savings:").grid(row=3, column=0, sticky='w', pady=5)
        self.savings_entry = ttk.Entry(settings, width=15)
        self.savings_entry.grid(row=3, column=1, pady=5)

        ttk.Label(settings, text="Current Investments:").grid(row=4, column=0, sticky='w', pady=5)
        self.investment_entry = ttk.Entry(settings, width=15)
        self.investment_entry.grid(row=4, column=1, pady=5)

        ttk.Label(settings, text="Money Lent Balance:").grid(row=5, column=0, sticky='w', pady=5)
        self.money_lent_entry = ttk.Entry(settings, width=15)
        self.money_lent_entry.grid(row=5, column=1, pady=5)

        ttk.Label(settings, text="Daily Savings Goal:").grid(row=6, column=0, sticky='w', pady=5)
        self.daily_savings_entry = ttk.Entry(settings, width=15)
        self.daily_savings_entry.grid(row=6, column=1, pady=5)

        ttk.Button(settings, text="Save Settings", command=self.save_settings).grid(row=7, column=1, pady=10, sticky='e')

        manage = ttk.Frame(top)
        manage.grid(row=0, column=1, sticky='nsew')
        manage.columnconfigure(0, weight=1)
        manage.rowconfigure(0, weight=1)

        fc_group = ttk.LabelFrame(manage, text="Manage Fixed Monthly Costs", padding="10")
        fc_group.grid(row=0, column=0, sticky='nsew')
        fc_group.rowconfigure(0, weight=1)
        fc_group.columnconfigure(0, weight=1)

        fc_tree_frame = ttk.Frame(fc_group)
        fc_tree_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')
        fc_tree_frame.columnconfigure(0, weight=1)
        fc_tree_frame.rowconfigure(0, weight=1)

        self.fixed_costs_tree = ttk.Treeview(fc_tree_frame, columns=('Description', 'Amount'), show='headings', height=5)
        self.fixed_costs_tree.heading('Description', text='Description')
        self.fixed_costs_tree.heading('Amount', text='Amount (€)')
        self.fixed_costs_tree.column('Description', width=200)
        self.fixed_costs_tree.column('Amount', width=100, anchor='e')
        self.fixed_costs_tree.grid(row=0, column=0, sticky='nsew')
        fc_scroll = ttk.Scrollbar(fc_tree_frame, orient='vertical', command=self.fixed_costs_tree.yview)
        fc_scroll.grid(row=0, column=1, sticky='ns')
        self.fixed_costs_tree.configure(yscrollcommand=fc_scroll.set)

        fc_form = ttk.Frame(fc_group)
        fc_form.grid(row=1, column=0, columnspan=2, sticky='ew', pady=10)
        ttk.Label(fc_form, text="Desc:").pack(side='left', padx=(0, 5))
        self.fc_desc_entry = ttk.Entry(fc_form, width=20)
        self.fc_desc_entry.pack(side='left', expand=True, fill='x')
        ttk.Label(fc_form, text="Amount:").pack(side='left', padx=(10, 5))
        self.fc_amount_entry = ttk.Entry(fc_form, width=10)
        self.fc_amount_entry.pack(side='left')

        fc_btns = ttk.Frame(fc_group)
        fc_btns.grid(row=2, column=0, columnspan=2, sticky='ew')
        ttk.Button(fc_btns, text="Add", command=self.add_fixed_cost).pack(side='left', padx=5)
        ttk.Button(fc_btns, text="Update", command=self.update_fixed_cost).pack(side='left', padx=5)
        ttk.Button(fc_btns, text="Delete", command=self.delete_fixed_cost).pack(side='left', padx=5)

        report = ttk.LabelFrame(main, text="Daily Budget Report", padding="10")
        report.grid(row=1, column=0, sticky='nsew', pady=(10, 0))
        report.rowconfigure(1, weight=1)
        report.columnconfigure(0, weight=1)

        month_frame = ttk.Frame(report)
        month_frame.grid(row=0, column=0, sticky='ew', pady=5)
        ttk.Label(month_frame, text="Select Month:").pack(side='left', padx=5)
        self.budget_month_entry = ttk.Entry(month_frame, width=15)
        self.budget_month_entry.insert(0, datetime.now().strftime("%Y-%m"))
        self.budget_month_entry.pack(side='left', padx=5)
        ttk.Button(month_frame, text="Generate Report", command=self.generate_report).pack(side='left', padx=10)
        ttk.Button(month_frame, text="Export Report", command=self.export_report).pack(side='left', padx=5)

        text_frame = ttk.Frame(report)
        text_frame.grid(row=1, column=0, sticky='nsew', pady=(10, 0))
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)
        self.report_text = tk.Text(text_frame, height=20, width=90, font=('Courier New', 9))
        self.report_text.grid(row=0, column=0, sticky='nsew')
        scroll = ttk.Scrollbar(text_frame, orient='vertical', command=self.report_text.yview)
        scroll.grid(row=0, column=1, sticky='ns')
        self.report_text.configure(yscrollcommand=scroll.set)

        self.refresh_balance_entries()
        self.refresh_fixed_costs_tree()

    def refresh_balance_entries(self):
        s = self.state.budget_settings
        def set_entry(entry, key):
            entry.delete(0, tk.END)
            entry.insert(0, str(s.get(key, 0)))
        set_entry(self.income_entry, 'monthly_income')
        set_entry(self.bank_entry, 'bank_account_balance')
        set_entry(self.wallet_entry, 'wallet_balance')
        set_entry(self.savings_entry, 'savings_balance')
        set_entry(self.investment_entry, 'investment_balance')
        set_entry(self.money_lent_entry, 'money_lent_balance')
        set_entry(self.daily_savings_entry, 'daily_savings_goal')

    def save_settings(self):
        try:
            s = self.state.budget_settings
            s['monthly_income'] = float(self.income_entry.get() or 0)
            s['bank_account_balance'] = float(self.bank_entry.get() or 0)
            s['wallet_balance'] = float(self.wallet_entry.get() or 0)
            s['savings_balance'] = float(self.savings_entry.get() or 0)
            s['investment_balance'] = float(self.investment_entry.get() or 0)
            s['money_lent_balance'] = float(self.money_lent_entry.get() or 0)
            s['daily_savings_goal'] = float(self.daily_savings_entry.get() or 0)
            self.state.save()
            messagebox.showinfo("Success", "Settings saved!")
        except ValueError:
            messagebox.showerror("Error", "Invalid amount in one of the fields.")

    def refresh_fixed_costs_tree(self):
        for i in self.fixed_costs_tree.get_children():
            self.fixed_costs_tree.delete(i)
        for cost in self.state.budget_settings.get('fixed_costs', []):
            self.fixed_costs_tree.insert('', 'end', values=(cost['desc'], f"{cost['amount']:.2f}"))

    def add_fixed_cost(self):
        try:
            desc = self.fc_desc_entry.get().strip()
            amount = float(self.fc_amount_entry.get())
            if not desc:
                messagebox.showerror("Error", "Description cannot be empty.")
                return
            self.state.budget_settings['fixed_costs'].append({'desc': desc, 'amount': amount})
            self.state.save()
            self.refresh_fixed_costs_tree()
            self.fc_desc_entry.delete(0, tk.END)
            self.fc_amount_entry.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Invalid amount for fixed cost.")

    def update_fixed_cost(self):
        selected = self.fixed_costs_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a fixed cost to update.")
            return
        try:
            desc = self.fc_desc_entry.get().strip()
            amount = float(self.fc_amount_entry.get())
            if not desc:
                messagebox.showerror("Error", "Description cannot be empty.")
                return
            original_values = self.fixed_costs_tree.item(selected[0])['values']
            for i, cost in enumerate(self.state.budget_settings['fixed_costs']):
                if cost['desc'] == original_values[0] and f"{cost['amount']:.2f}" == original_values[1]:
                    self.state.budget_settings['fixed_costs'][i] = {'desc': desc, 'amount': amount}
                    break
            self.state.save()
            self.refresh_fixed_costs_tree()
        except ValueError:
            messagebox.showerror("Error", "Invalid amount for fixed cost.")

    def delete_fixed_cost(self):
        selected = self.fixed_costs_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a fixed cost to delete.")
            return
        values = self.fixed_costs_tree.item(selected[0])['values']
        target_cost = {'desc': values[0], 'amount': float(values[1])}
        try:
            self.state.budget_settings['fixed_costs'].remove(target_cost)
            self.state.save()
            self.refresh_fixed_costs_tree()
        except ValueError:
            messagebox.showerror("Error", "Could not delete the selected fixed cost item.")

    def generate_report(self):
        month = self.budget_month_entry.get()
        text = generate_daily_budget_report(self.state, month)
        self.report_text.delete("1.0", tk.END)
        self.report_text.insert("1.0", text)

    def export_report(self):
        content = self.report_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Warning", "Please generate a report before exporting.")
            return
        today = datetime.now().strftime("%Y-%m-%d")
        month_str = self.budget_month_entry.get()
        default_filename = f"day_report_{month_str}_{today}.txt"
        path = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".txt",
            filetypes=[("Text Documents", "*.txt"), ("All Files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Success", f"Report successfully exported to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export report.\nError: {e}")