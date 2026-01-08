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

        settings.grid(row=0, column=0, sticky='ns', padx=(0, 10))

        # Base Monthly Income Button + Readonly Display
        self.income_btn = ttk.Button(settings, text="Base Monthly Income:", command=self._open_income_manager)
        self.income_btn.grid(row=0, column=0, sticky='w', pady=5)
        self.income_entry_display = ttk.Entry(settings, width=15, state='readonly')
        self.income_entry_display.grid(row=0, column=1, pady=5)
        
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

        # Money Lent: button label + readonly entry
        self.money_lent_btn = ttk.Button(settings, text="Money Lent:", command=self._open_lending_manager)
        self.money_lent_btn.grid(row=5, column=0, sticky='w', pady=5)
        self.money_lent_entry = ttk.Entry(settings, width=15, state='readonly')
        self.money_lent_entry.grid(row=5, column=1, pady=5)

        ttk.Label(settings, text="Daily Savings Goal:").grid(row=6, column=0, sticky='w', pady=5)
        self.daily_savings_entry = ttk.Entry(settings, width=15)
        self.daily_savings_entry.grid(row=6, column=1, pady=5)

        ttk.Button(settings, text="Save Settings", command=self.save_settings).grid(row=7, column=1, pady=10, sticky='e')

        manage = ttk.Frame(top)
        manage.grid(row=0, column=1, sticky='nsew')
        manage.columnconfigure(0, weight=1)
        manage.rowconfigure(0, weight=1)

        # === Manage Fixed Monthly Costs ===
        fc_group = ttk.LabelFrame(manage, text="Manage Fixed Monthly Costs", padding="10")
        fc_group.grid(row=0, column=0, sticky='nsew')
        fc_group.rowconfigure(0, weight=1)
        fc_group.columnconfigure(0, weight=1)



        fc_tree_frame = ttk.Frame(fc_group)
        fc_tree_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')
        fc_tree_frame.columnconfigure(0, weight=1)
        fc_tree_frame.rowconfigure(0, weight=1)

        self.fixed_costs_tree = ttk.Treeview(fc_tree_frame, columns=('Description', 'Amount', 'Start Date', 'End Date'), show='headings', height=5)
        self.fixed_costs_tree.heading('Description', text='Description')
        self.fixed_costs_tree.heading('Amount', text='Amount (€)')
        self.fixed_costs_tree.heading('Start Date', text='Start Date')
        self.fixed_costs_tree.heading('End Date', text='End Date')
        self.fixed_costs_tree.column('Description', width=150)
        self.fixed_costs_tree.column('Amount', width=100, anchor='e')
        self.fixed_costs_tree.column('Start Date', width=100, anchor='center')
        self.fixed_costs_tree.column('End Date', width=100, anchor='center')
        self.fixed_costs_tree.grid(row=0, column=0, sticky='nsew')
        fc_scroll = ttk.Scrollbar(fc_tree_frame, orient='vertical', command=self.fixed_costs_tree.yview)
        fc_scroll.grid(row=0, column=1, sticky='ns')
        self.fixed_costs_tree.configure(yscrollcommand=fc_scroll.set)

        fc_form = ttk.Frame(fc_group)
        fc_form.grid(row=1, column=0, columnspan=2, sticky='ew', pady=10)
        
        # Row 1: Description and Amount
        fc_form_row1 = ttk.Frame(fc_form)
        fc_form_row1.pack(fill='x', pady=(0, 5))
        ttk.Label(fc_form_row1, text="Desc:").pack(side='left', padx=(0, 5))
        self.fc_desc_entry = ttk.Entry(fc_form_row1, width=20)
        self.fc_desc_entry.pack(side='left', expand=True, fill='x')
        ttk.Label(fc_form_row1, text="Amount:").pack(side='left', padx=(10, 5))
        self.fc_amount_entry = ttk.Entry(fc_form_row1, width=10)
        self.fc_amount_entry.pack(side='left')
        
        # Row 2: Start Date and End Date
        fc_form_row2 = ttk.Frame(fc_form)
        fc_form_row2.pack(fill='x')
        ttk.Label(fc_form_row2, text="Start Date (YYYY-MM-DD):").pack(side='left', padx=(0, 5))
        self.fc_start_date_entry = ttk.Entry(fc_form_row2, width=12)
        self.fc_start_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.fc_start_date_entry.pack(side='left')
        ttk.Label(fc_form_row2, text="End Date (optional):").pack(side='left', padx=(10, 5))
        self.fc_end_date_entry = ttk.Entry(fc_form_row2, width=12)
        self.fc_end_date_entry.pack(side='left')
        ttk.Label(fc_form_row2, text="(leave empty if still active)", font=('Arial', 8, 'italic'), foreground='gray').pack(side='left', padx=(5, 0))

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
        # self.refresh_income_tree() # Moved to manager window
        self.refresh_fixed_costs_tree()

    def _update_income_display(self):
        """Update the readonly income display with CURRENT month's active income."""
        from ...services.budget_calculator import get_active_monthly_income
        current_month = datetime.now().strftime("%Y-%m")
        active_income = get_active_monthly_income(self.state, current_month)
        self.income_entry_display.config(state='normal')
        self.income_entry_display.delete(0, tk.END)
        self.income_entry_display.insert(0, f"{active_income:.2f}")
        self.income_entry_display.config(state='readonly')

    def _open_income_manager(self):
        win = tk.Toplevel()
        win.title("Base Monthly Income Manager")
        win.geometry("700x500")
        win.transient()
        win.grab_set()

        main = ttk.Frame(win, padding=10)
        main.pack(fill='both', expand=True)
        
        ttk.Label(main, text="Manage source of base monthly income here.\n(Historical changes will be preserved)", 
                 font=('Arial', 10, 'italic'), foreground='gray').pack(pady=(0, 10))

        # ID wrapper for refresh
        self.inc_win = win

        # Treeview
        tree_frame = ttk.Frame(main)
        tree_frame.pack(fill='both', expand=True)

        self.income_tree = ttk.Treeview(tree_frame, columns=('Description', 'Amount', 'Start Date', 'End Date'), show='headings', height=8)
        self.income_tree.heading('Description', text='Description')
        self.income_tree.heading('Amount', text='Amount (€)')
        self.income_tree.heading('Start Date', text='Start Date')
        self.income_tree.heading('End Date', text='End Date')
        self.income_tree.column('Description', width=150)
        self.income_tree.column('Amount', width=100, anchor='e')
        self.income_tree.column('Start Date', width=100, anchor='center')
        self.income_tree.column('End Date', width=100, anchor='center')
        self.income_tree.pack(side='left', fill='both', expand=True)
        
        inc_scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.income_tree.yview)
        inc_scroll.pack(side='right', fill='y')
        self.income_tree.configure(yscrollcommand=inc_scroll.set)

        # Form
        form = ttk.LabelFrame(main, text="Add/Edit Income Source", padding=10)
        form.pack(fill='x', pady=10)
        
        r1 = ttk.Frame(form)
        r1.pack(fill='x', pady=2)
        ttk.Label(r1, text="Description:").pack(side='left', padx=5)
        self.inc_desc_entry = ttk.Entry(r1)
        self.inc_desc_entry.pack(side='left', expand=True, fill='x', padx=5)
        ttk.Label(r1, text="Amount:").pack(side='left', padx=5)
        self.inc_amount_entry = ttk.Entry(r1, width=15)
        self.inc_amount_entry.pack(side='left', padx=5)

        r2 = ttk.Frame(form)
        r2.pack(fill='x', pady=5)
        ttk.Label(r2, text="Start Date:").pack(side='left', padx=5)
        self.inc_start_date_entry = ttk.Entry(r2, width=15)
        self.inc_start_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.inc_start_date_entry.pack(side='left', padx=5)
        
        ttk.Label(r2, text="End Date (Optional):").pack(side='left', padx=5)
        self.inc_end_date_entry = ttk.Entry(r2, width=15)
        self.inc_end_date_entry.pack(side='left', padx=5)

        btns = ttk.Frame(main)
        btns.pack(fill='x')
        ttk.Button(btns, text="Add New Income", command=self.add_income).pack(side='left', padx=5)
        ttk.Button(btns, text="Update Selected", command=self.update_income).pack(side='left', padx=5)
        ttk.Button(btns, text="Delete Selected", command=self.delete_income).pack(side='left', padx=5)
        ttk.Button(btns, text="Close", command=win.destroy).pack(side='right', padx=5)

        self.refresh_income_tree()

    def _update_money_lent_button(self):
        """Update the money lent entry with current balance."""
        balance = self.state.budget_settings.get('money_lent_balance', 0)
        self.money_lent_entry.config(state='normal')
        self.money_lent_entry.delete(0, tk.END)
        self.money_lent_entry.insert(0, f"{balance:.2f}")
        self.money_lent_entry.config(state='readonly')

    def _open_lending_manager(self):
        """Open the lending manager window to manage individual loans."""
        loan_win = tk.Toplevel()
        loan_win.title("Lending Manager")
        loan_win.geometry("800x600")
        loan_win.minsize(600, 500)
        loan_win.transient()
        loan_win.grab_set()
        
        # Bind ESC to close window
        loan_win.bind('<Escape>', lambda e: loan_win.destroy())

        main_frame = ttk.Frame(loan_win, padding=10)
        main_frame.pack(fill='both', expand=True)

        # Current balance display
        balance = self.state.budget_settings.get('money_lent_balance', 0)
        self.loan_balance_label = ttk.Label(main_frame, text=f"Total Money Lent: €{balance:.2f}", font=('Arial', 12, 'bold'))
        self.loan_balance_label.pack(pady=(0, 10))

        # Loans treeview
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill='both', expand=True)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self.loans_tree = ttk.Treeview(tree_frame, columns=('Borrower', 'Amount', 'Description', 'Date'), show='headings', height=8)
        self.loans_tree.heading('Borrower', text='Borrower')
        self.loans_tree.heading('Amount', text='Amount (€)')
        self.loans_tree.heading('Description', text='Description')
        self.loans_tree.heading('Date', text='Date')
        self.loans_tree.column('Borrower', width=120)
        self.loans_tree.column('Amount', width=80, anchor='e')
        self.loans_tree.column('Description', width=150)
        self.loans_tree.column('Date', width=90, anchor='center')
        self.loans_tree.grid(row=0, column=0, sticky='nsew')
        
        loans_scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.loans_tree.yview)
        loans_scroll.grid(row=0, column=1, sticky='ns')
        self.loans_tree.configure(yscrollcommand=loans_scroll.set)

        # Add loan form
        form_frame = ttk.LabelFrame(main_frame, text="Add New Loan", padding=10)
        form_frame.pack(fill='x', pady=10)

        ttk.Label(form_frame, text="Borrower:").grid(row=0, column=0, sticky='w', padx=5)
        self.loan_borrower_entry = ttk.Entry(form_frame, width=15)
        self.loan_borrower_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Amount:").grid(row=0, column=2, sticky='w', padx=5)
        self.loan_amount_entry = ttk.Entry(form_frame, width=10)
        self.loan_amount_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form_frame, text="Description:").grid(row=0, column=4, sticky='w', padx=5)
        self.loan_desc_entry = ttk.Entry(form_frame, width=20)
        self.loan_desc_entry.grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(form_frame, text="Add Loan", command=lambda: self._add_loan(loan_win)).grid(row=0, column=6, padx=10)

        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(0, 5))

        ttk.Button(btn_frame, text="Mark as Returned", command=lambda: self._mark_loan_returned(loan_win)).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Close", command=loan_win.destroy).pack(side='right', padx=5)

        # Populate loans list
        self._refresh_loans_tree()

    def _refresh_loans_tree(self):
        """Refresh the loans treeview with current data."""
        for item in self.loans_tree.get_children():
            self.loans_tree.delete(item)
        
        loans = self.state.budget_settings.get('loans', [])
        for loan in loans:
            self.loans_tree.insert('', 'end', iid=loan['id'], 
                                   values=(loan['borrower'], f"{loan['amount']:.2f}", loan.get('description', ''), loan['date']))

    def _add_loan(self, loan_win):
        """Add a new loan and update the balance."""
        borrower = self.loan_borrower_entry.get().strip()
        amount_str = self.loan_amount_entry.get().strip()

        if not borrower:
            messagebox.showerror("Error", "Please enter a borrower name.", parent=loan_win)
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be positive.", parent=loan_win)
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid amount.", parent=loan_win)
            return

        # Create loan record
        loan_id = f"{datetime.now().timestamp()}"
        description = self.loan_desc_entry.get().strip()
        loan = {
            'id': loan_id,
            'borrower': borrower,
            'amount': amount,
            'description': description,
            'date': datetime.now().strftime("%Y-%m-%d")
        }

        # Add to loans list
        if 'loans' not in self.state.budget_settings:
            self.state.budget_settings['loans'] = []
        self.state.budget_settings['loans'].append(loan)

        # Update money lent balance
        self.state.budget_settings['money_lent_balance'] = self.state.budget_settings.get('money_lent_balance', 0) + amount
        self.state.save()

        # Refresh UI
        self._refresh_loans_tree()
        self._update_loan_balance_label()
        self._update_money_lent_button()

        # Clear form
        self.loan_borrower_entry.delete(0, tk.END)
        self.loan_amount_entry.delete(0, tk.END)
        self.loan_desc_entry.delete(0, tk.END)

        messagebox.showinfo("Success", f"Loan of €{amount:.2f} to {borrower} recorded.", parent=loan_win)

    def _mark_loan_returned(self, loan_win):
        """Mark a loan as returned and update the balance."""
        selected = self.loans_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a loan to mark as returned.", parent=loan_win)
            return

        loan_id = selected[0]
        loans = self.state.budget_settings.get('loans', [])

        # Find and remove the loan
        for i, loan in enumerate(loans):
            if loan['id'] == loan_id:
                amount = loan['amount']
                borrower = loan['borrower']
                del loans[i]
                
                # Update money lent balance
                self.state.budget_settings['money_lent_balance'] = max(0, 
                    self.state.budget_settings.get('money_lent_balance', 0) - amount)
                self.state.save()

                # Refresh UI
                self._refresh_loans_tree()
                self._update_loan_balance_label()
                self._update_money_lent_button()

                messagebox.showinfo("Success", f"Loan of €{amount:.2f} from {borrower} marked as returned.", parent=loan_win)
                return

        messagebox.showerror("Error", "Could not find the selected loan.", parent=loan_win)

    def _update_loan_balance_label(self):
        """Update the balance label in the lending manager window."""
        balance = self.state.budget_settings.get('money_lent_balance', 0)
        self.loan_balance_label.config(text=f"Total Money Lent: €{balance:.2f}")

    def refresh_balance_entries(self):
        s = self.state.budget_settings
        def set_entry(entry, key):
            entry.delete(0, tk.END)
            entry.delete(0, tk.END)
            entry.insert(0, str(s.get(key, 0)))
        
        self._update_income_display() # New display update logic
        
        set_entry(self.bank_entry, 'bank_account_balance')
        set_entry(self.wallet_entry, 'wallet_balance')
        set_entry(self.savings_entry, 'savings_balance')
        set_entry(self.investment_entry, 'investment_balance')
        set_entry(self.daily_savings_entry, 'daily_savings_goal')
        self._update_money_lent_button()

    def save_settings(self):
        try:
            s = self.state.budget_settings
            # s['monthly_income'] = float(self.income_entry.get() or 0) # REMOVED
            s['bank_account_balance'] = float(self.bank_entry.get() or 0)
            s['wallet_balance'] = float(self.wallet_entry.get() or 0)
            s['savings_balance'] = float(self.savings_entry.get() or 0)
            s['investment_balance'] = float(self.investment_entry.get() or 0)
            s['daily_savings_goal'] = float(self.daily_savings_entry.get() or 0)
            self.state.save()
            messagebox.showinfo("Success", "Settings saved!")
        except ValueError:
            messagebox.showerror("Error", "Invalid amount in one of the fields.")

    def refresh_fixed_costs_tree(self):
        for i in self.fixed_costs_tree.get_children():
            self.fixed_costs_tree.delete(i)
        for cost in self.state.budget_settings.get('fixed_costs', []):
            end_date_display = cost.get('end_date', 'Active') or 'Active'
            self.fixed_costs_tree.insert('', 'end', values=(
                cost['desc'], 
                f"{cost['amount']:.2f}",
                cost.get('start_date', '2000-01-01'),
                end_date_display
            ))

    def add_fixed_cost(self):
        try:
            desc = self.fc_desc_entry.get().strip()
            amount = float(self.fc_amount_entry.get())
            start_date = self.fc_start_date_entry.get().strip()
            end_date = self.fc_end_date_entry.get().strip()
            
            if not desc:
                messagebox.showerror("Error", "Description cannot be empty.")
                return
            
            # Validate start date
            if not start_date:
                messagebox.showerror("Error", "Start date is required.")
                return
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid start date format. Use YYYY-MM-DD.")
                return
            
            # Validate end date if provided
            if end_date:
                try:
                    datetime.strptime(end_date, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Error", "Invalid end date format. Use YYYY-MM-DD.")
                    return
            else:
                end_date = None
            
            self.state.budget_settings['fixed_costs'].append({
                'desc': desc, 
                'amount': amount,
                'start_date': start_date,
                'end_date': end_date
            })
            self.state.save()
            self.refresh_fixed_costs_tree()
            self.fc_desc_entry.delete(0, tk.END)
            self.fc_amount_entry.delete(0, tk.END)
            self.fc_start_date_entry.delete(0, tk.END)
            self.fc_start_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
            self.fc_end_date_entry.delete(0, tk.END)
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
            start_date = self.fc_start_date_entry.get().strip()
            end_date = self.fc_end_date_entry.get().strip()
            
            if not desc:
                messagebox.showerror("Error", "Description cannot be empty.")
                return
            
            # Validate dates
            if not start_date:
                messagebox.showerror("Error", "Start date is required.")
                return
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid start date format. Use YYYY-MM-DD.")
                return
            
            if end_date:
                try:
                    datetime.strptime(end_date, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Error", "Invalid end date format. Use YYYY-MM-DD.")
                    return
            else:
                end_date = None
            
            original_values = self.fixed_costs_tree.item(selected[0])['values']
            for i, cost in enumerate(self.state.budget_settings['fixed_costs']):
                if cost['desc'] == original_values[0] and f"{cost['amount']:.2f}" == original_values[1]:
                    self.state.budget_settings['fixed_costs'][i] = {
                        'desc': desc, 
                        'amount': amount,
                        'start_date': start_date,
                        'end_date': end_date
                    }
                    break
            self.state.save()
            self.refresh_fixed_costs_tree()
        except ValueError:
            messagebox.showerror("Error", "Invalid amount for fixed cost.")

        except ValueError:
            messagebox.showerror("Error", "Invalid amount for fixed cost.")

    def refresh_income_tree(self):
        for i in self.income_tree.get_children():
            self.income_tree.delete(i)
        
        income_data = self.state.budget_settings.get('monthly_income', [])
        # Handle migration case just in case
        if isinstance(income_data, (int, float)):
             income_data = [] # Should have been migrated by state load, but be safe
        
        for inc in income_data:
            end_date_display = inc.get('end_date') or 'Active'
            start_date_display = inc.get('start_date') or '2000-01-01'
            self.income_tree.insert('', 'end', values=(
                inc.get('description', 'Base Income'), 
                f"{inc.get('amount', 0):.2f}",
                start_date_display,
                end_date_display
            ))

    def _validate_income_input(self):
        desc = self.inc_desc_entry.get().strip()
        amount_str = self.inc_amount_entry.get()
        start_date = self.inc_start_date_entry.get().strip()
        end_date = self.inc_end_date_entry.get().strip()

        parent = getattr(self, 'inc_win', None)

        if not desc:
            messagebox.showerror("Error", "Description cannot be empty.", parent=parent)
            return None
        
        try:
            amount = float(amount_str)
        except ValueError:
            messagebox.showerror("Error", "Invalid amount.", parent=parent)
            return None

        if not start_date:
            messagebox.showerror("Error", "Start date is required.", parent=parent)
            return None
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid start date format. Use YYYY-MM-DD.", parent=parent)
            return None
        
        if end_date:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid end date format. Use YYYY-MM-DD.", parent=parent)
                return None
        else:
            end_date = None

        return {
            'description': desc,
            'amount': amount,
            'start_date': start_date,
            'end_date': end_date
        }

    def add_income(self):
        data = self._validate_income_input()
        if not data:
            return

        # Ensure it's a list
        if not isinstance(self.state.budget_settings.get('monthly_income'), list):
             self.state.budget_settings['monthly_income'] = []

        self.state.budget_settings['monthly_income'].append(data)
        self.state.save()
        self.refresh_income_tree()
        self._update_income_display()
        
        self.inc_desc_entry.delete(0, tk.END)
        self.inc_amount_entry.delete(0, tk.END)
        self.inc_start_date_entry.delete(0, tk.END)
        self.inc_start_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.inc_end_date_entry.delete(0, tk.END)

    def update_income(self):
        selected = self.income_tree.selection()
        parent = getattr(self, 'inc_win', None)
        if not selected:
            messagebox.showwarning("Warning", "Please select an income source to update.", parent=parent)
            return
        
        data = self._validate_income_input()
        if not data:
            return

        original_values = self.income_tree.item(selected[0])['values']
        # Find match - this is slightly fragile if duplicates exist, but sufficient for this scope
        incomes = self.state.budget_settings.get('monthly_income', [])
        for i, inc in enumerate(incomes):
            # Compare basic fields to identify
            orig_desc = inc.get('description', 'Base Income')
            orig_amt = f"{inc.get('amount', 0):.2f}"
            if orig_desc == original_values[0] and orig_amt == original_values[1]:
                incomes[i] = data
                break
        
        self.state.save()
        self.refresh_income_tree()
        self._update_income_display()

    def delete_income(self):
        selected = self.income_tree.selection()
        parent = getattr(self, 'inc_win', None)
        if not selected:
            messagebox.showwarning("Warning", "Please select an income source to delete.", parent=parent)
            return
        
        values = self.income_tree.item(selected[0])['values']
        desc_to_del = values[0]
        amt_to_del = values[1]

        incomes = self.state.budget_settings.get('monthly_income', [])
        for i, inc in enumerate(incomes):
            if inc.get('description', 'Base Income') == desc_to_del and f"{inc.get('amount', 0):.2f}" == amt_to_del:
                
                # Archive option
                if inc.get('end_date') is None:
                    response = messagebox.askyesnocancel(
                        "Delete or Archive?",
                        f"Do you want to:\n\n"
                        f"YES - Set an end date (archives it)\n"
                        f"NO - Permanently delete\n"
                        f"CANCEL - Keep it",
                        parent=parent
                    )
                    if response is None: return
                    elif response:
                        inc['end_date'] = datetime.now().strftime("%Y-%m-%d")
                        self.state.save()
                        self.refresh_income_tree()
                        self._update_income_display()
                        return
                
                del incomes[i]
                self.state.save()
                self.refresh_income_tree()
                self._update_income_display()
                return

    def delete_fixed_cost(self):
        selected = self.fixed_costs_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a fixed cost to delete.")
            return
        
        values = self.fixed_costs_tree.item(selected[0])['values']
        desc_to_delete = values[0]
        amount_to_delete = float(values[1])
        
        # Find and remove the matching cost
        for i, cost in enumerate(self.state.budget_settings['fixed_costs']):
            if cost['desc'] == desc_to_delete and cost['amount'] == amount_to_delete:
                # Instead of deleting, ask if user wants to set end date
                if cost.get('end_date') is None:
                    response = messagebox.askyesnocancel(
                        "Delete or Archive?",
                        f"Do you want to:\n\n"
                        f"YES - Set an end date (archives the cost)\n"
                        f"NO - Permanently delete this cost\n"
                        f"CANCEL - Keep the cost as-is"
                    )
                    if response is None:  # Cancel
                        return
                    elif response:  # Yes - set end date
                        end_date = datetime.now().strftime("%Y-%m-%d")
                        cost['end_date'] = end_date
                        self.state.save()
                        self.refresh_fixed_costs_tree()
                        messagebox.showinfo("Success", f"Cost archived with end date: {end_date}")
                        return
                    # else: fall through to delete
                
                # Permanently delete
                del self.state.budget_settings['fixed_costs'][i]
                self.state.save()
                self.refresh_fixed_costs_tree()
                return
        
        messagebox.showerror("Error", "Could not find the selected fixed cost item.")

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