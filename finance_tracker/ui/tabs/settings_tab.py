"""
finance_tracker/ui/tabs/settings_tab.py

Tab for configuring budget settings, fixed costs, and viewing daily reports.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ...services.budget_calculator import (
    generate_daily_budget_report,
    get_active_fixed_costs,
    get_active_monthly_income_sources,
)
from ..charts import create_budget_depletion_figure

class SettingsTab:
    def __init__(self, notebook, state):
        self.state = state
        self._income_sort_state = {}
        self._income_current_sort = None
        self._fixed_costs_sort_state = {}
        self._fixed_costs_current_sort = None
        self.show_inactive_income_sources = tk.BooleanVar(value=False)
        self.show_inactive_fixed_costs = tk.BooleanVar(value=False)
        self.include_negative_carryover = tk.BooleanVar(value=False)

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
        
        # Base Monthly Costs Button + Readonly Display
        self.costs_btn = ttk.Button(settings, text="Base Monthly Costs:", command=self._open_fixed_costs_manager)
        self.costs_btn.grid(row=1, column=0, sticky='w', pady=5)
        self.costs_entry_display = ttk.Entry(settings, width=15, state='readonly')
        self.costs_entry_display.grid(row=1, column=1, pady=5)
        
        ttk.Label(settings, text="Bank Account Balance:").grid(row=2, column=0, sticky='w', pady=5)
        self.bank_entry = ttk.Entry(settings, width=15)
        self.bank_entry.grid(row=2, column=1, pady=5)

        ttk.Label(settings, text="Wallet Balance:").grid(row=3, column=0, sticky='w', pady=5)
        self.wallet_entry = ttk.Entry(settings, width=15)
        self.wallet_entry.grid(row=3, column=1, pady=5)

        ttk.Label(settings, text="Current Savings:").grid(row=4, column=0, sticky='w', pady=5)
        self.savings_entry = ttk.Entry(settings, width=15)
        self.savings_entry.grid(row=4, column=1, pady=5)

        ttk.Label(settings, text="Current Investments:").grid(row=5, column=0, sticky='w', pady=5)
        self.investment_entry = ttk.Entry(settings, width=15)
        self.investment_entry.grid(row=5, column=1, pady=5)

        # Money Lent: button label + readonly entry
        self.money_lent_btn = ttk.Button(settings, text="Money Lent:", command=self._open_lending_manager)
        self.money_lent_btn.grid(row=6, column=0, sticky='w', pady=5)
        self.money_lent_entry = ttk.Entry(settings, width=15, state='readonly')
        self.money_lent_entry.grid(row=6, column=1, pady=5)

        ttk.Label(settings, text="Daily Savings Goal:").grid(row=7, column=0, sticky='w', pady=5)
        self.daily_savings_entry = ttk.Entry(settings, width=15)
        self.daily_savings_entry.grid(row=7, column=1, pady=5)

        ttk.Button(settings, text="Save Settings", command=self.save_settings).grid(row=8, column=1, pady=10, sticky='e')

        # === Budget Depletion Graph ===
        manage = ttk.Frame(top)
        manage.grid(row=0, column=1, sticky='nsew')
        manage.columnconfigure(0, weight=1)
        manage.rowconfigure(0, weight=1)

        graph_frame = ttk.LabelFrame(manage, text="Budget Depletion", padding="5")
        graph_frame.grid(row=0, column=0, sticky='nsew')
        graph_frame.rowconfigure(0, weight=1)
        graph_frame.columnconfigure(0, weight=1)
        
        # Canvas placeholder for matplotlib figure
        self.budget_graph_frame = graph_frame
        self.budget_canvas = None

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
        ttk.Checkbutton(
            month_frame,
            text="Include previous month deficit",
            variable=self.include_negative_carryover,
            command=self.generate_report
        ).pack(side='left', padx=10)
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
        self._update_costs_display()
        self._refresh_budget_graph()

    def _update_income_display(self):
        """Update the readonly income display with CURRENT month's active income."""
        from ...services.budget_calculator import get_active_monthly_income
        current_month = datetime.now().strftime("%Y-%m")
        active_income = get_active_monthly_income(self.state, current_month)
        self.income_entry_display.config(state='normal')
        self.income_entry_display.delete(0, tk.END)
        self.income_entry_display.insert(0, f"{active_income:.2f}")
        self.income_entry_display.config(state='readonly')

    def _update_costs_display(self):
        """Update the readonly costs display with CURRENT month's active fixed costs."""
        from ...services.budget_calculator import get_active_fixed_costs
        current_month = datetime.now().strftime("%Y-%m")
        active_costs = get_active_fixed_costs(self.state, current_month)
        total_costs = sum(fc['amount'] for fc in active_costs)
        self.costs_entry_display.config(state='normal')
        self.costs_entry_display.delete(0, tk.END)
        self.costs_entry_display.insert(0, f"{total_costs:.2f}")
        self.costs_entry_display.config(state='readonly')

    def _refresh_budget_graph(self):
        """Render the budget depletion graph in the main UI."""
        # Use current month or the one selected in report if they match? 
        # Usually dashboard should show CURRENT month.
        current_month = datetime.now().strftime("%Y-%m")
        fig = create_budget_depletion_figure(self.state, current_month)
        
        # Clear previous canvas if exists
        if self.budget_canvas:
            self.budget_canvas.get_tk_widget().destroy()
            
        self.budget_canvas = FigureCanvasTkAgg(fig, master=self.budget_graph_frame)
        self.budget_canvas.draw()
        self.budget_canvas.get_tk_widget().pack(fill='both', expand=True)

    def _open_income_manager(self):
        win = tk.Toplevel()
        win.title("Base Monthly Income Manager")
        win.geometry("700x500")
        win.transient()
        win.grab_set()

        # Bind ESC to close window
        win.bind('<Escape>', lambda e: win.destroy())

        main = ttk.Frame(win, padding=10)
        main.pack(fill='both', expand=True)
        
        ttk.Label(main, text="Manage source of base monthly income here.\n(Historical changes will be preserved)", 
                 font=('Arial', 10, 'italic'), foreground='gray').pack(pady=(0, 10))

        filter_frame = ttk.Frame(main)
        filter_frame.pack(fill='x', pady=(0, 8))
        self.income_filter_btn = ttk.Button(
            filter_frame,
            text="Show Inactive Income",
            command=self.toggle_income_filter,
        )
        self.income_filter_btn.pack(side='left')

        # ID wrapper for refresh
        self.inc_win = win

        # Treeview
        tree_frame = ttk.Frame(main)
        tree_frame.pack(fill='both', expand=True)

        self.income_tree = ttk.Treeview(tree_frame, columns=('Description', 'Amount', 'Start Date', 'End Date'), show='headings', height=8)
        self.income_tree.heading('Description', text='Description', command=lambda: self.sort_income_by_column('Description'))
        self.income_tree.heading('Amount', text='Amount (€)', command=lambda: self.sort_income_by_column('Amount'))
        self.income_tree.heading('Start Date', text='Start Date', command=lambda: self.sort_income_by_column('Start Date'))
        self.income_tree.heading('End Date', text='End Date', command=lambda: self.sort_income_by_column('End Date'))
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

        # Bind selection to populate form
        self.income_tree.bind('<<TreeviewSelect>>', lambda e: self._populate_income_form(win))

        btns = ttk.Frame(main)
        btns.pack(fill='x')
        ttk.Button(btns, text="Add New Income", command=self.add_income).pack(side='left', padx=5)
        ttk.Button(btns, text="Update Selected", command=self.update_income).pack(side='left', padx=5)
        ttk.Button(btns, text="Delete Selected", command=self.delete_income).pack(side='left', padx=5)
        ttk.Button(btns, text="Close", command=win.destroy).pack(side='right', padx=5)

        self.refresh_income_tree()

    def _open_fixed_costs_manager(self):
        win = tk.Toplevel()
        win.title("Base Monthly Costs Manager")
        win.geometry("800x600")
        win.transient()
        win.grab_set()

        # Bind ESC to close window
        win.bind('<Escape>', lambda e: win.destroy())

        main = ttk.Frame(win, padding=10)
        main.pack(fill='both', expand=True)
        
        ttk.Label(main, text="Manage recurring fixed monthly costs here.\n(Historical changes will be preserved)", 
                 font=('Arial', 10, 'italic'), foreground='gray').pack(pady=(0, 10))

        filter_frame = ttk.Frame(main)
        filter_frame.pack(fill='x', pady=(0, 8))
        self.fixed_costs_filter_btn = ttk.Button(
            filter_frame,
            text="Show Inactive Costs",
            command=self.toggle_fixed_costs_filter,
        )
        self.fixed_costs_filter_btn.pack(side='left')

        # ID wrapper for refresh
        self.fc_win = win

        # Treeview
        tree_frame = ttk.Frame(main)
        tree_frame.pack(fill='both', expand=True)

        self.fixed_costs_tree = ttk.Treeview(tree_frame, columns=('Description', 'Amount', 'Start Date', 'End Date'), show='headings', height=10)
        self.fixed_costs_tree.heading('Description', text='Description', command=lambda: self.sort_fixed_costs_by_column('Description'))
        self.fixed_costs_tree.heading('Amount', text='Amount (€)', command=lambda: self.sort_fixed_costs_by_column('Amount'))
        self.fixed_costs_tree.heading('Start Date', text='Start Date', command=lambda: self.sort_fixed_costs_by_column('Start Date'))
        self.fixed_costs_tree.heading('End Date', text='End Date', command=lambda: self.sort_fixed_costs_by_column('End Date'))
        self.fixed_costs_tree.column('Description', width=200)
        self.fixed_costs_tree.column('Amount', width=100, anchor='e')
        self.fixed_costs_tree.column('Start Date', width=120, anchor='center')
        self.fixed_costs_tree.column('End Date', width=120, anchor='center')
        self.fixed_costs_tree.pack(side='left', fill='both', expand=True)
        
        fc_scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.fixed_costs_tree.yview)
        fc_scroll.pack(side='right', fill='y')
        self.fixed_costs_tree.configure(yscrollcommand=fc_scroll.set)

        # Form
        form = ttk.LabelFrame(main, text="Add/Edit Fixed Cost Source", padding=10)
        form.pack(fill='x', pady=10)
        
        r1 = ttk.Frame(form)
        r1.pack(fill='x', pady=2)
        ttk.Label(r1, text="Description:").pack(side='left', padx=5)
        self.fc_desc_entry = ttk.Entry(r1)
        self.fc_desc_entry.pack(side='left', expand=True, fill='x', padx=5)
        ttk.Label(r1, text="Amount:").pack(side='left', padx=5)
        self.fc_amount_entry = ttk.Entry(r1, width=15)
        self.fc_amount_entry.pack(side='left', padx=5)

        r2 = ttk.Frame(form)
        r2.pack(fill='x', pady=5)
        ttk.Label(r2, text="Start Date:").pack(side='left', padx=5)
        self.fc_start_date_entry = ttk.Entry(r2, width=15)
        self.fc_start_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.fc_start_date_entry.pack(side='left', padx=5)
        
        ttk.Label(r2, text="End Date (Optional):").pack(side='left', padx=5)
        self.fc_end_date_entry = ttk.Entry(r2, width=15)
        self.fc_end_date_entry.pack(side='left', padx=5)

        # Bind selection to populate form
        self.fixed_costs_tree.bind('<<TreeviewSelect>>', lambda e: self._populate_fixed_cost_form(win))

        btns = ttk.Frame(main)
        btns.pack(fill='x')
        ttk.Button(btns, text="Add New Cost", command=self.add_fixed_cost).pack(side='left', padx=5)
        ttk.Button(btns, text="Update Selected", command=self.update_fixed_cost).pack(side='left', padx=5)
        ttk.Button(btns, text="Delete Selected", command=self.delete_fixed_cost).pack(side='left', padx=5)
        ttk.Button(btns, text="Close", command=win.destroy).pack(side='right', padx=5)

        self.refresh_fixed_costs_tree()

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
        self.loan_balance_label.pack(pady=(0, 2))
        
        ttk.Label(main_frame, text="(Positive = Lent to others, Negative = Borrowed from others)", 
                 font=('Arial', 9, 'italic'), foreground='gray').pack(pady=(0, 10))

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
        form_frame = ttk.LabelFrame(main_frame, text="Add/Edit Loan", padding=10)
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

        # Bind selection to populate form
        self.loans_tree.bind('<<TreeviewSelect>>', lambda e: self._populate_loan_form(loan_win))

        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(0, 5))

        ttk.Button(btn_frame, text="Update Selected", command=lambda: self._update_loan(loan_win)).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Mark as Returned", command=lambda: self._mark_loan_returned(loan_win)).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Close", command=loan_win.destroy).pack(side='right', padx=5)

        # Store reference to loan window for use in other methods
        self.loan_win_ref = loan_win
        
        # Track currently editing loan ID (None when adding new)
        self.editing_loan_id = None

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

    def _populate_loan_form(self, loan_win):
        """Populate the form fields when a loan is selected in the tree."""
        selected = self.loans_tree.selection()
        if not selected:
            return
        
        loan_id = selected[0]
        loans = self.state.budget_settings.get('loans', [])
        
        for loan in loans:
            if loan['id'] == loan_id:
                # Store the loan ID being edited
                self.editing_loan_id = loan_id
                
                # Populate form fields
                self.loan_borrower_entry.delete(0, tk.END)
                self.loan_borrower_entry.insert(0, loan['borrower'])
                
                self.loan_amount_entry.delete(0, tk.END)
                self.loan_amount_entry.insert(0, str(loan['amount']))
                
                self.loan_desc_entry.delete(0, tk.END)
                self.loan_desc_entry.insert(0, loan.get('description', ''))
                break

    def _add_loan(self, loan_win):
        """Add a new loan and update the balance."""
        borrower = self.loan_borrower_entry.get().strip()
        amount_str = self.loan_amount_entry.get().strip()

        if not borrower:
            messagebox.showerror("Error", "Please enter a borrower name.", parent=loan_win)
            return

        try:
            amount = float(amount_str)
            if amount == 0:
                messagebox.showerror("Error", "Amount cannot be zero.", parent=loan_win)
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

        # Clear form and reset edit mode
        self._clear_loan_form()

        messagebox.showinfo("Success", f"Loan of €{amount:.2f} to {borrower} recorded.", parent=loan_win)

    def _clear_loan_form(self):
        """Clear the loan form fields and reset edit mode."""
        self.loan_borrower_entry.delete(0, tk.END)
        self.loan_amount_entry.delete(0, tk.END)
        self.loan_desc_entry.delete(0, tk.END)
        self.editing_loan_id = None

    def _update_loan(self, loan_win):
        """Update an existing loan with new values."""
        selected = self.loans_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a loan to update.", parent=loan_win)
            return

        loan_id = selected[0]
        borrower = self.loan_borrower_entry.get().strip()
        amount_str = self.loan_amount_entry.get().strip()

        if not borrower:
            messagebox.showerror("Error", "Please enter a borrower name.", parent=loan_win)
            return

        try:
            new_amount = float(amount_str)
            if new_amount == 0:
                messagebox.showerror("Error", "Amount cannot be zero.", parent=loan_win)
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid amount.", parent=loan_win)
            return

        loans = self.state.budget_settings.get('loans', [])
        
        # Find the loan and update it
        for i, loan in enumerate(loans):
            if loan['id'] == loan_id:
                old_amount = loan['amount']
                description = self.loan_desc_entry.get().strip()
                
                # Update loan fields
                loans[i]['borrower'] = borrower
                loans[i]['amount'] = new_amount
                loans[i]['description'] = description
                # Keep the original date unless you want to allow changing it
                
                # Update money lent balance (adjust for amount difference)
                amount_diff = new_amount - old_amount
                self.state.budget_settings['money_lent_balance'] = self.state.budget_settings.get('money_lent_balance', 0) + amount_diff
                self.state.save()

                # Refresh UI
                self._refresh_loans_tree()
                self._update_loan_balance_label()
                self._update_money_lent_button()

                # Clear form and reset edit mode
                self._clear_loan_form()

                messagebox.showinfo("Success", f"Loan updated: €{new_amount:.2f} to {borrower}.", parent=loan_win)
                return

        messagebox.showerror("Error", "Could not find the selected loan.", parent=loan_win)

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
                self.state.budget_settings['money_lent_balance'] = self.state.budget_settings.get('money_lent_balance', 0) - amount
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
        self._update_costs_display()
        
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

    def _populate_fixed_cost_form(self, win):
        """Populate the fixed cost form fields when an entry is selected in the tree."""
        selected = self.fixed_costs_tree.selection()
        if not selected:
            return
        
        # Get the values from the selected tree item
        values = self.fixed_costs_tree.item(selected[0])['values']
        if not values:
            return
        
        # Find matching fixed cost entry in the data
        fixed_costs = self.state.budget_settings.get('fixed_costs', [])
        for cost in fixed_costs:
            cost_desc = cost['desc']
            cost_amt = f"{cost['amount']:.2f}"
            
            # Match by description and amount
            if cost_desc == values[0] and cost_amt == values[1]:
                # Populate form fields
                self.fc_desc_entry.delete(0, tk.END)
                self.fc_desc_entry.insert(0, cost_desc)
                
                self.fc_amount_entry.delete(0, tk.END)
                self.fc_amount_entry.insert(0, cost_amt)
                
                self.fc_start_date_entry.delete(0, tk.END)
                self.fc_start_date_entry.insert(0, cost.get('start_date', '2000-01-01'))
                
                self.fc_end_date_entry.delete(0, tk.END)
                end_date = cost.get('end_date')
                if end_date:
                    self.fc_end_date_entry.insert(0, end_date)
                break

    def refresh_fixed_costs_tree(self):
        # Only refresh if the manager window is open (tree exists)
        if not hasattr(self, 'fixed_costs_tree'):
            return
        for i in self.fixed_costs_tree.get_children():
            self.fixed_costs_tree.delete(i)

        current_month = datetime.now().strftime("%Y-%m")
        active_cost_ids = {id(cost) for cost in get_active_fixed_costs(self.state, current_month)}
        all_costs = list(self.state.budget_settings.get('fixed_costs', []))

        if self.show_inactive_fixed_costs.get():
            costs = all_costs
        else:
            costs = [cost for cost in all_costs if id(cost) in active_cost_ids]

        if self._fixed_costs_current_sort:
            column, direction = self._fixed_costs_current_sort
            reverse = (direction == 'descending')
            if column == 'Amount':
                costs.sort(key=lambda x: float(x.get('amount', 0.0)), reverse=reverse)
            elif column == 'Description':
                costs.sort(key=lambda x: (x.get('desc') or '').lower(), reverse=reverse)
            elif column == 'Start Date':
                costs.sort(key=lambda x: x.get('start_date') or '2000-01-01', reverse=reverse)
            elif column == 'End Date':
                # Treat Active/None as far future so they group together consistently
                costs.sort(key=lambda x: x.get('end_date') or '9999-12-31', reverse=reverse)

        for cost in costs:
            end_date_display = cost.get('end_date', 'Active') or 'Active'
            self.fixed_costs_tree.insert('', 'end', values=(
                cost['desc'],
                f"{cost['amount']:.2f}",
                cost.get('start_date', '2000-01-01'),
                end_date_display
            ))

    def toggle_fixed_costs_filter(self):
        self.show_inactive_fixed_costs.set(not self.show_inactive_fixed_costs.get())
        self.fixed_costs_filter_btn.config(
            text="Hide Inactive Costs" if self.show_inactive_fixed_costs.get() else "Show Inactive Costs"
        )
        self.refresh_fixed_costs_tree()

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
            self._update_costs_display()
            self._refresh_budget_graph()
            
            self.fc_desc_entry.delete(0, tk.END)
            self.fc_amount_entry.delete(0, tk.END)
            self.fc_start_date_entry.delete(0, tk.END)
            self.fc_start_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
            self.fc_end_date_entry.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Invalid amount for fixed cost.", parent=getattr(self, 'fc_win', None))

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
            self._update_costs_display()
            self._refresh_budget_graph()
        except ValueError:
            messagebox.showerror("Error", "Invalid amount for fixed cost.", parent=getattr(self, 'fc_win', None))

        except ValueError:
            messagebox.showerror("Error", "Invalid amount for fixed cost.")

    def _populate_income_form(self, win):
        """Populate the income form fields when an entry is selected in the tree."""
        selected = self.income_tree.selection()
        if not selected:
            return
        
        # Get the values from the selected tree item
        values = self.income_tree.item(selected[0])['values']
        if not values:
            return
        
        # Find matching income entry in the data
        income_data = self.state.budget_settings.get('monthly_income', [])
        if isinstance(income_data, (int, float)):
            income_data = []
        
        for inc in income_data:
            inc_desc = inc.get('description', 'Base Income')
            inc_amt = f"{inc.get('amount', 0):.2f}"
            
            # Match by description and amount
            if inc_desc == values[0] and inc_amt == values[1]:
                # Populate form fields
                self.inc_desc_entry.delete(0, tk.END)
                self.inc_desc_entry.insert(0, inc_desc)
                
                self.inc_amount_entry.delete(0, tk.END)
                self.inc_amount_entry.insert(0, inc_amt)
                
                self.inc_start_date_entry.delete(0, tk.END)
                self.inc_start_date_entry.insert(0, inc.get('start_date', '2000-01-01'))
                
                self.inc_end_date_entry.delete(0, tk.END)
                end_date = inc.get('end_date')
                if end_date:
                    self.inc_end_date_entry.insert(0, end_date)
                break

    def refresh_income_tree(self):
        for i in self.income_tree.get_children():
            self.income_tree.delete(i)

        income_data = self.state.budget_settings.get('monthly_income', [])
        # Handle migration case just in case
        if isinstance(income_data, (int, float)):
             income_data = [] # Should have been migrated by state load, but be safe

        current_month = datetime.now().strftime("%Y-%m")
        active_income_ids = {id(inc) for inc in get_active_monthly_income_sources(self.state, current_month)}
        all_income_rows = list(income_data)

        if self.show_inactive_income_sources.get():
            income_rows = all_income_rows
        else:
            income_rows = [inc for inc in all_income_rows if id(inc) in active_income_ids]
        if self._income_current_sort:
            column, direction = self._income_current_sort
            reverse = (direction == 'descending')
            if column == 'Amount':
                income_rows.sort(key=lambda x: float(x.get('amount', 0.0)), reverse=reverse)
            elif column == 'Description':
                income_rows.sort(key=lambda x: (x.get('description') or 'Base Income').lower(), reverse=reverse)
            elif column == 'Start Date':
                income_rows.sort(key=lambda x: x.get('start_date') or '2000-01-01', reverse=reverse)
            elif column == 'End Date':
                income_rows.sort(key=lambda x: x.get('end_date') or '9999-12-31', reverse=reverse)

        for inc in income_rows:
            end_date_display = inc.get('end_date') or 'Active'
            start_date_display = inc.get('start_date') or '2000-01-01'
            self.income_tree.insert('', 'end', values=(
                inc.get('description', 'Base Income'),
                f"{inc.get('amount', 0):.2f}",
                start_date_display,
                end_date_display
            ))

    def toggle_income_filter(self):
        self.show_inactive_income_sources.set(not self.show_inactive_income_sources.get())
        self.income_filter_btn.config(
            text="Hide Inactive Income" if self.show_inactive_income_sources.get() else "Show Inactive Income"
        )
        self.refresh_income_tree()

    def sort_income_by_column(self, column: str):
        current_state = self._income_sort_state.get(column, 'none')
        if column == 'Amount':
            if current_state == 'none' or current_state == 'ascending':
                new_direction = 'descending'
            else:
                new_direction = 'ascending'
        else:
            if current_state == 'none' or current_state == 'descending':
                new_direction = 'ascending'
            else:
                new_direction = 'descending'

        self._income_sort_state[column] = new_direction
        self._income_current_sort = (column, new_direction)
        self.refresh_income_tree()

    def sort_fixed_costs_by_column(self, column: str):
        current_state = self._fixed_costs_sort_state.get(column, 'none')
        if column == 'Amount':
            if current_state == 'none' or current_state == 'ascending':
                new_direction = 'descending'
            else:
                new_direction = 'ascending'
        else:
            if current_state == 'none' or current_state == 'descending':
                new_direction = 'ascending'
            else:
                new_direction = 'descending'

        self._fixed_costs_sort_state[column] = new_direction
        self._fixed_costs_current_sort = (column, new_direction)
        self.refresh_fixed_costs_tree()

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
        self._refresh_budget_graph()
        
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
        self._refresh_budget_graph()

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
                        self._refresh_budget_graph()
                        return
                
                del incomes[i]
                self.state.save()
                self.refresh_income_tree()
                self._update_income_display()
                self._refresh_budget_graph()
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
                self._update_costs_display()
                self._refresh_budget_graph()
                return
        
        messagebox.showerror("Error", "Could not find the selected fixed cost item.", parent=getattr(self, 'fc_win', None))

    def generate_report(self):
        month = self.budget_month_entry.get()
        text = generate_daily_budget_report(
            self.state, month, include_negative_carryover=self.include_negative_carryover.get()
        )
        self.report_text.delete("1.0", tk.END)
        self.report_text.insert("1.0", text)
        
        # Also refresh graph for the selected month
        fig = create_budget_depletion_figure(
            self.state, month, include_negative_carryover=self.include_negative_carryover.get()
        )
        if self.budget_canvas:
            self.budget_canvas.get_tk_widget().destroy()
        self.budget_canvas = FigureCanvasTkAgg(fig, master=self.budget_graph_frame)
        self.budget_canvas.draw()
        self.budget_canvas.get_tk_widget().pack(fill='both', expand=True)

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
