import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from datetime import datetime, date
from pathlib import Path
import calendar
from dateutil.relativedelta import relativedelta

## NEW ##: Import matplotlib for charting
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


class FinanceTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Finance Tracker")
        # Set a minimum size, allowing the window to be expanded
        self.root.minsize(1250, 750)

        # Data file
        self.data_file = Path("finance_data.json")
        self.load_data()

        # UI Styling
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        style.configure("TLabel", font=('Arial', 10))
        style.configure("TButton", font=('Arial', 10))
        style.configure("TRadiobutton", font=('Arial', 10))

        # Create UI
        self.create_widgets()
        self.refresh_transaction_list()
        self.refresh_fixed_costs_tree()
        self.refresh_category_list()
        self.refresh_category_budget_list()
        ## NEW ##
        self.refresh_balance_entries()

    def load_data(self):
        """Load data from JSON file or create new structure"""
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.expenses = data.get('expenses', [])
                self.incomes = data.get('incomes', [])
                self.budget_settings = data.get('budget_settings', {})
                self.categories = data.get('categories', {})
        else:
            self.expenses = []
            self.incomes = []
            self.budget_settings = {}
            self.categories = {}

        if 'fixed_costs' not in self.budget_settings:
            self.budget_settings['fixed_costs'] = []
        if 'monthly_income' not in self.budget_settings:
            self.budget_settings['monthly_income'] = 0
        if 'bank_account_balance' not in self.budget_settings:
            self.budget_settings['bank_account_balance'] = 0
        if 'savings_balance' not in self.budget_settings:
            self.budget_settings['savings_balance'] = 0
        if 'investment_balance' not in self.budget_settings:
            self.budget_settings['investment_balance'] = 0
        ## NEW ##
        if 'wallet_balance' not in self.budget_settings:
            self.budget_settings['wallet_balance'] = 0
        if 'daily_savings_goal' not in self.budget_settings:
            self.budget_settings['daily_savings_goal'] = 0

        if 'Expense' not in self.categories or not self.categories['Expense']:
            self.categories['Expense'] = ["Food", "Transportation", "Entertainment", "Utilities", "Shopping",
                                          "Healthcare", "Other"]
        if 'Income' not in self.categories or not self.categories['Income']:
            self.categories['Income'] = ["Salary", "Side Gig", "Bonus", "Gift", "Investment", "Other"]
        
        if 'category_budgets' not in self.budget_settings:
            self.budget_settings['category_budgets'] = {'Expense': {}, 'Income': {}}

    def save_data(self):
        """Save data to JSON file"""
        data = {
            'expenses': self.expenses,
            'incomes': self.incomes,
            'budget_settings': self.budget_settings,
            'categories': self.categories
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)

    def create_widgets(self):
        """Create all UI elements"""
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.add_transaction_tab = ttk.Frame(notebook)
        notebook.add(self.add_transaction_tab, text="Add Transaction")
        self.create_add_transaction_tab()

        self.view_transactions_tab = ttk.Frame(notebook)
        notebook.add(self.view_transactions_tab, text="View Transactions")
        self.create_view_transactions_tab()
        
        ## NEW ##
        self.transfers_tab = ttk.Frame(notebook)
        notebook.add(self.transfers_tab, text="Transfers")
        self.create_transfers_tab()

        self.reports_tab = ttk.Frame(notebook)
        notebook.add(self.reports_tab, text="Reports")
        self.create_reports_tab()

        self.budget_tab = ttk.Frame(notebook)
        notebook.add(self.budget_tab, text="Budget & Settings")
        self.create_budget_tab()

        self.projection_tab = ttk.Frame(notebook)
        notebook.add(self.projection_tab, text="Projection")
        self.create_projection_tab()

    def create_reports_tab(self):
        """Create the UI for the reports tab with a pie chart"""
        main_frame = ttk.Frame(self.reports_tab, padding="10")
        main_frame.pack(fill='both', expand=True)
        # Configure grid weights for responsiveness: make the chart area (row 1) expand
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)

        controls_frame = ttk.LabelFrame(main_frame, text="Chart Options", padding="10")
        controls_frame.grid(row=0, column=0, sticky='ew', pady=5)

        # --- First row of controls ---
        top_controls_row = ttk.Frame(controls_frame)
        top_controls_row.pack(fill='x', expand=True, pady=(0, 5))

        # Month Selection
        month_frame = ttk.Frame(top_controls_row)
        month_frame.pack(side='left', padx=(0, 15))
        ttk.Label(month_frame, text="Select Month:").pack(side='left')
        self.chart_month_entry = ttk.Entry(month_frame, width=15)
        self.chart_month_entry.insert(0, datetime.now().strftime("%Y-%m"))
        self.chart_month_entry.pack(side='left', padx=5)

        # Chart Type
        type_frame = ttk.Frame(top_controls_row)
        type_frame.pack(side='left', padx=(0, 15))
        ttk.Label(type_frame, text="Chart Type:").pack(side='left')
        self.chart_type_var = tk.StringVar(value="Expense")
        ttk.Radiobutton(type_frame, text="Expenses", variable=self.chart_type_var, value="Expense",
                        command=self._update_report_options_ui).pack(side='left')
        ttk.Radiobutton(type_frame, text="Incomes", variable=self.chart_type_var, value="Income",
                        command=self._update_report_options_ui).pack(side='left', padx=5)

        # Display As
        value_type_frame = ttk.Frame(top_controls_row)
        value_type_frame.pack(side='left', padx=(0, 15))
        ttk.Label(value_type_frame, text="Display As:").pack(side='left')
        self.chart_value_type_var = tk.StringVar(value="Percentage")
        ttk.Radiobutton(value_type_frame, text="Percentage", variable=self.chart_value_type_var,
                        value="Percentage").pack(side='left')
        ttk.Radiobutton(value_type_frame, text="Total Amount", variable=self.chart_value_type_var,
                        value="Total").pack(side='left', padx=5)

        # --- Second row of controls ---
        bottom_controls_row = ttk.Frame(controls_frame)
        bottom_controls_row.pack(fill='x', expand=True)
        
        # Checkboxes for inclusion
        self.fixed_item_frame = ttk.Frame(bottom_controls_row)
        self.fixed_item_frame.pack(side='left', padx=(0, 15))
        self.include_fixed_costs_var = tk.BooleanVar(value=False)
        self.fixed_costs_checkbutton = ttk.Checkbutton(self.fixed_item_frame, text="Include Fixed Costs",
                                                        variable=self.include_fixed_costs_var)
        self.include_base_income_var = tk.BooleanVar(value=False)
        self.base_income_checkbutton = ttk.Checkbutton(self.fixed_item_frame, text="Include Base Income",
                                                        variable=self.include_base_income_var)
        self._update_report_options_ui() # This handles packing the correct one

        # Show Budget Limits checkbox
        self.show_budget_lines_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(bottom_controls_row, text="Show Budget Limits", 
                        variable=self.show_budget_lines_var).pack(side='left', padx=(0,15))

        # Spacer to push the button to the far right
        spacer = ttk.Frame(bottom_controls_row)
        spacer.pack(side='left', fill='x', expand=True)

        # Generate Button
        ttk.Button(bottom_controls_row, text="Generate Chart", command=self.generate_pie_chart).pack(side='right')

        # Chart Frame (make sure it fills the available space)
        self.chart_frame = ttk.Frame(main_frame)
        self.chart_frame.grid(row=1, column=0, sticky='nsew', pady=10)
        self.canvas = None

    def _update_report_options_ui(self):
        chart_type = self.chart_type_var.get()
        self.fixed_costs_checkbutton.pack_forget()
        self.base_income_checkbutton.pack_forget()
        if chart_type == "Expense":
            self.fixed_costs_checkbutton.pack()
        else:
            self.base_income_checkbutton.pack()

    def generate_pie_chart(self):
        month_str = self.chart_month_entry.get()
        chart_type = self.chart_type_var.get()
        value_type = self.chart_value_type_var.get()
        try:
            datetime.strptime(month_str, "%Y-%m")
        except ValueError:
            messagebox.showerror("Error", "Invalid month format. Please use YYYY-MM.")
            return
        category_totals = {}
        if chart_type == "Expense":
            data = self.expenses
            title = f"Expenses for {month_str}"
            if self.include_fixed_costs_var.get():
                total_fixed_costs = sum(fc['amount'] for fc in self.budget_settings.get('fixed_costs', []))
                if total_fixed_costs > 0:
                    category_totals['Fixed Costs'] = total_fixed_costs
        else:
            data = self.incomes
            title = f"Incomes for {month_str}"
            if self.include_base_income_var.get():
                base_income = self.budget_settings.get('monthly_income', 0)
                if base_income > 0:
                    category_totals['Base Income'] = base_income
        month_data = [item for item in data if item['date'].startswith(month_str)]
        for item in month_data:
            category = item['category']
            amount = item['amount']
            category_totals[category] = category_totals.get(category, 0) + amount
        if not category_totals:
            messagebox.showinfo("No Data", f"No data to display for {month_str}.")
            return
        labels = category_totals.keys()
        sizes = category_totals.values()
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        fig = Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)
        if value_type == "Percentage":
            autopct = '%1.1f%%'
        else:
            def absolute_value(val):
                a = (val / 100.) * sum(sizes)
                return f'€{a:.2f}'
            autopct = absolute_value
        wedges, texts, autotexts = ax.pie(sizes, autopct=autopct, startangle=140, textprops=dict(color="w"))
        ax.axis('equal')
        ax.set_title(title)
        ax.legend(wedges, labels, title="Categories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        plt.setp(autotexts, size=8, weight="bold")
        # Add budget limit annotations if enabled
        if self.show_budget_lines_var.get() and chart_type == "Expense":
            expense_budgets = self.budget_settings.get('category_budgets', {}).get('Expense', {})
            budget_info = []
            for category in labels:
                if category in expense_budgets and expense_budgets[category] > 0:
                    actual = category_totals[category]
                    budget = expense_budgets[category]
                    percentage = (actual / budget) * 100
                    budget_info.append(f"{category}: {percentage:.0f}% of budget")
        
            if budget_info:
                budget_text = "\n".join(budget_info)
                ax.text(1.5, 0.5, "Budget Status:\n" + budget_text, 
                        transform=ax.transAxes, fontsize=9, verticalalignment='center',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

    def create_add_transaction_tab(self):
        # This main_frame will expand and center the form_frame within it
        main_frame = ttk.Frame(self.add_transaction_tab, padding="20")
        main_frame.pack(fill='both', expand=True)

        # The form_frame holds the form widgets and will NOT expand
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(anchor='center') # Center the form

        # --- Widgets placed inside the non-expanding form_frame ---
        ttk.Label(form_frame, text="Transaction Type:").grid(row=0, column=0, sticky='w', pady=10)
        self.transaction_type_var = tk.StringVar(value="Expense")
        type_frame = ttk.Frame(form_frame)
        type_frame.grid(row=0, column=1, sticky='w', pady=5)
        ttk.Radiobutton(type_frame, text="Expense", variable=self.transaction_type_var,
                        value="Expense", command=self.update_categories).pack(side='left', padx=5)
        ttk.Radiobutton(type_frame, text="Income", variable=self.transaction_type_var,
                        value="Income", command=self.update_categories).pack(side='left', padx=5)

        ttk.Label(form_frame, text="Date:").grid(row=1, column=0, sticky='w', pady=5)
        self.date_entry = ttk.Entry(form_frame, width=30)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=1, column=1, pady=5, sticky='w') # Use sticky 'w' (west)
        ttk.Label(form_frame, text="(YYYY-MM-DD)", foreground="gray").grid(row=1, column=2, sticky='w', padx=5)

        ttk.Label(form_frame, text="Amount:").grid(row=2, column=0, sticky='w', pady=5)
        self.amount_entry = ttk.Entry(form_frame, width=30)
        self.amount_entry.grid(row=2, column=1, pady=5, sticky='w') # Use sticky 'w' (west)

        ttk.Label(form_frame, text="Category:").grid(row=3, column=0, sticky='w', pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(form_frame, textvariable=self.category_var, width=28, state='readonly')
        self.category_combo.grid(row=3, column=1, pady=5, sticky='w') # Use sticky 'w' (west)
        self.update_categories()

        ttk.Label(form_frame, text="Description:").grid(row=4, column=0, sticky='w', pady=5)
        self.description_entry = ttk.Entry(form_frame, width=30)
        self.description_entry.grid(row=4, column=1, pady=5, sticky='w') # Use sticky 'w' (west)

        ttk.Button(form_frame, text="Add Transaction", command=self.add_transaction).grid(
            row=5, column=1, pady=20, sticky='w')

    def update_categories(self):
        transaction_type = self.transaction_type_var.get()
        categories = self.categories.get(transaction_type, [])
        self.category_combo.config(values=categories)
        if categories:
            self.category_combo.set(categories[0])
        else:
            self.category_combo.set("")

    def create_view_transactions_tab(self):
        frame = ttk.Frame(self.view_transactions_tab, padding="20")
        frame.pack(fill='both', expand=True)

        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill='x', pady=10)

        ttk.Label(filter_frame, text="Filter by month:").pack(side='left', padx=5)
        self.month_filter = ttk.Entry(filter_frame, width=15)
        self.month_filter.insert(0, datetime.now().strftime("%Y-%m"))
        self.month_filter.pack(side='left', padx=5)
        ttk.Button(filter_frame, text="Refresh", command=self.refresh_transaction_list).pack(side='left', padx=10)

        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill='both', expand=True, pady=10)

        columns = ('Date', 'Type', 'Amount', 'Category', 'Description')
        self.transaction_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        for col in columns:
            self.transaction_tree.heading(col, text=col)
            width = 120
            if col == 'Amount': width = 100
            if col == 'Description': width = 250
            if col == 'Type': width = 80
            self.transaction_tree.column(col, width=width, anchor='w')

        self.transaction_tree.tag_configure('expense', foreground='red')
        self.transaction_tree.tag_configure('income', foreground='green')
        self.transaction_tree.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.transaction_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.transaction_tree.configure(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill='x', pady=5)
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_transaction).pack(side='right')
        
        self.summary_label = ttk.Label(frame, text="", font=('Arial', 10, 'bold'))
        self.summary_label.pack(pady=10, fill='x')

    ## NEW ##
    def create_transfers_tab(self):
        """Create the UI for the new Transfers tab."""
        main_frame = ttk.Frame(self.transfers_tab, padding="20")
        main_frame.pack(fill='both', expand=True)

        form_frame = ttk.Frame(main_frame)
        form_frame.pack(anchor='center')

        ttk.Label(form_frame, text="This section allows you to record the movement of funds between your accounts.").grid(
            row=0, column=0, columnspan=3, sticky='w', pady=(0, 20))
        
        # --- FROM ACCOUNT ---
        ttk.Label(form_frame, text="From Account:").grid(row=1, column=0, sticky='w', pady=10)
        self.transfer_from_var = tk.StringVar()
        self.transfer_from_combo = ttk.Combobox(form_frame, textvariable=self.transfer_from_var, 
                                                values=["Bank", "Wallet", "Savings", "Investments"], 
                                                width=28, state='readonly')
        self.transfer_from_combo.grid(row=1, column=1, pady=5, sticky='w')

        # --- TO ACCOUNT ---
        ttk.Label(form_frame, text="To Account:").grid(row=2, column=0, sticky='w', pady=10)
        self.transfer_to_var = tk.StringVar()
        self.transfer_to_combo = ttk.Combobox(form_frame, textvariable=self.transfer_to_var,
                                              values=["Bank", "Wallet", "Savings", "Investments"],
                                              width=28, state='readonly')
        self.transfer_to_combo.grid(row=2, column=1, pady=5, sticky='w')

        # --- AMOUNT ---
        ttk.Label(form_frame, text="Amount:").grid(row=3, column=0, sticky='w', pady=5)
        self.transfer_amount_entry = ttk.Entry(form_frame, width=30)
        self.transfer_amount_entry.grid(row=3, column=1, pady=5, sticky='w')

        # --- BUTTON ---
        ttk.Button(form_frame, text="Execute Transfer", command=self.execute_transfer).grid(
            row=4, column=1, pady=20, sticky='w')

    ## NEW ##
    def execute_transfer(self):
        """Logic to handle the transfer of funds between accounts."""
        from_acc = self.transfer_from_var.get()
        to_acc = self.transfer_to_var.get()
        amount_str = self.transfer_amount_entry.get()

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
        
        # Mapping UI names to data model keys
        account_keys = {
            "Bank": "bank_account_balance",
            "Wallet": "wallet_balance",
            "Savings": "savings_balance",
            "Investments": "investment_balance"
        }
        
        from_key = account_keys[from_acc]
        to_key = account_keys[to_acc]

        # Update the budget_settings dictionary
        self.budget_settings[from_key] -= amount
        self.budget_settings[to_key] += amount
        
        self.save_data()
        self.refresh_balance_entries() # Update the UI on the Budget tab

        messagebox.showinfo("Success", f"Successfully transferred €{amount:.2f} from {from_acc} to {to_acc}.")
        self.transfer_amount_entry.delete(0, tk.END)
        self.transfer_from_var.set('')
        self.transfer_to_var.set('')

    def create_budget_tab(self):
        main_frame = ttk.Frame(self.budget_tab, padding="10")
        main_frame.pack(fill='both', expand=True)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)

        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        top_frame.columnconfigure(1, weight=1) 

        settings_frame = ttk.LabelFrame(top_frame, text="Monthly Settings & Balances", padding="10")
        settings_frame.grid(row=0, column=0, sticky='ns', padx=(0, 10))

        ttk.Label(settings_frame, text="Base Monthly Income:").grid(row=0, column=0, sticky='w', pady=5)
        self.income_entry = ttk.Entry(settings_frame, width=15)
        self.income_entry.grid(row=0, column=1, pady=5)

        ttk.Label(settings_frame, text="Bank Account Balance:").grid(row=1, column=0, sticky='w', pady=5)
        self.bank_account_entry = ttk.Entry(settings_frame, width=15)
        self.bank_account_entry.grid(row=1, column=1, pady=5)
        
        ## NEW ##
        ttk.Label(settings_frame, text="Wallet Balance:").grid(row=2, column=0, sticky='w', pady=5)
        self.wallet_entry = ttk.Entry(settings_frame, width=15)
        self.wallet_entry.grid(row=2, column=1, pady=5)

        ttk.Label(settings_frame, text="Current Savings:").grid(row=3, column=0, sticky='w', pady=5)
        self.savings_entry = ttk.Entry(settings_frame, width=15)
        self.savings_entry.grid(row=3, column=1, pady=5)

        ttk.Label(settings_frame, text="Current Investments:").grid(row=4, column=0, sticky='w', pady=5)
        self.investment_entry = ttk.Entry(settings_frame, width=15)
        self.investment_entry.grid(row=4, column=1, pady=5)

        ttk.Label(settings_frame, text="Daily Savings Goal:").grid(row=5, column=0, sticky='w', pady=5)
        self.daily_savings_entry = ttk.Entry(settings_frame, width=15)
        self.daily_savings_entry.grid(row=5, column=1, pady=5)

        ttk.Button(settings_frame, text="Save Settings", command=self.save_settings).grid(
            row=6, column=1, pady=10, sticky='e')

        management_frame = ttk.Frame(top_frame)
        management_frame.grid(row=0, column=1, sticky='nsew')
        management_frame.columnconfigure([0, 1, 2], weight=1)
        management_frame.rowconfigure(0, weight=1) # Allow row to expand vertically

        fixed_costs_frame = ttk.LabelFrame(management_frame, text="Manage Fixed Monthly Costs", padding="10")
        fixed_costs_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        fixed_costs_frame.rowconfigure(0, weight=1)
        fixed_costs_frame.columnconfigure(0, weight=1)
        fc_tree_frame = ttk.Frame(fixed_costs_frame)
        fc_tree_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')
        fc_tree_frame.columnconfigure(0, weight=1)
        fc_tree_frame.rowconfigure(0, weight=1)
        self.fixed_costs_tree = ttk.Treeview(fc_tree_frame, columns=('Description', 'Amount'), show='headings', height=5)
        self.fixed_costs_tree.heading('Description', text='Description')
        self.fixed_costs_tree.heading('Amount', text='Amount (€)')
        self.fixed_costs_tree.column('Description', width=200)
        self.fixed_costs_tree.column('Amount', width=100, anchor='e')
        self.fixed_costs_tree.grid(row=0, column=0, sticky='nsew')
        fc_scrollbar = ttk.Scrollbar(fc_tree_frame, orient='vertical', command=self.fixed_costs_tree.yview)
        fc_scrollbar.grid(row=0, column=1, sticky='ns')
        self.fixed_costs_tree.configure(yscrollcommand=fc_scrollbar.set)
        fc_form_frame = ttk.Frame(fixed_costs_frame)
        fc_form_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=10)
        ttk.Label(fc_form_frame, text="Desc:").pack(side='left', padx=(0, 5))
        self.fc_desc_entry = ttk.Entry(fc_form_frame, width=20)
        self.fc_desc_entry.pack(side='left', expand=True, fill='x')
        ttk.Label(fc_form_frame, text="Amount:").pack(side='left', padx=(10, 5))
        self.fc_amount_entry = ttk.Entry(fc_form_frame, width=10)
        self.fc_amount_entry.pack(side='left')
        fc_btn_frame = ttk.Frame(fixed_costs_frame)
        fc_btn_frame.grid(row=2, column=0, columnspan=2, sticky='ew')
        ttk.Button(fc_btn_frame, text="Add", command=self.add_fixed_cost).pack(side='left', padx=5)
        ttk.Button(fc_btn_frame, text="Update", command=self.update_fixed_cost).pack(side='left', padx=5)
        ttk.Button(fc_btn_frame, text="Delete", command=self.delete_fixed_cost).pack(side='left', padx=5)

        categories_frame = ttk.LabelFrame(management_frame, text="Manage Categories", padding="10")
        categories_frame.grid(row=0, column=1, sticky='nsew', padx=(0, 10))
        self.create_category_management_widgets(categories_frame)

        budget_limits_frame = ttk.LabelFrame(management_frame, text="Category Budget Limits", padding="10")
        budget_limits_frame.grid(row=0, column=2, sticky='nsew')
        self.create_category_budget_widgets(budget_limits_frame)
        
        report_frame = ttk.LabelFrame(main_frame, text="Daily Budget Report", padding="10")
        report_frame.grid(row=1, column=0, sticky='nsew', pady=(10, 0))
        report_frame.rowconfigure(1, weight=1)
        report_frame.columnconfigure(0, weight=1)

        month_frame = ttk.Frame(report_frame)
        month_frame.grid(row=0, column=0, sticky='ew', pady=5)
        ttk.Label(month_frame, text="Select Month:").pack(side='left', padx=5)
        self.budget_month = ttk.Entry(month_frame, width=15)
        self.budget_month.insert(0, datetime.now().strftime("%Y-%m"))
        self.budget_month.pack(side='left', padx=5)
        ttk.Button(month_frame, text="Generate Report", command=self.generate_daily_budget).pack(side='left', padx=10)
        ttk.Button(month_frame, text="Export Report", command=self.export_daily_budget_report).pack(side='left', padx=5)
        
        budget_text_frame = ttk.Frame(report_frame)
        budget_text_frame.grid(row=1, column=0, sticky='nsew', pady=(10, 0))
        budget_text_frame.rowconfigure(0, weight=1)
        budget_text_frame.columnconfigure(0, weight=1)
        self.budget_text = tk.Text(budget_text_frame, height=20, width=90, font=('Courier New', 9))
        self.budget_text.grid(row=0, column=0, sticky='nsew')
        budget_text_scrollbar = ttk.Scrollbar(budget_text_frame, orient='vertical', command=self.budget_text.yview)
        budget_text_scrollbar.grid(row=0, column=1, sticky='ns')
        self.budget_text.configure(yscrollcommand=budget_text_scrollbar.set)

    def create_category_management_widgets(self, parent_frame):
        parent_frame.rowconfigure(1, weight=1)
        parent_frame.columnconfigure(0, weight=1)

        self.cat_type_var = tk.StringVar(value="Expense")
        cat_type_frame = ttk.Frame(parent_frame)
        cat_type_frame.grid(row=0, column=0, sticky='ew', pady=2)
        ttk.Label(cat_type_frame, text="Type:").pack(side='left')
        ttk.Radiobutton(cat_type_frame, text="Expense", variable=self.cat_type_var,
                        value="Expense", command=self.refresh_category_list).pack(side='left', padx=5)
        ttk.Radiobutton(cat_type_frame, text="Income", variable=self.cat_type_var,
                        value="Income", command=self.refresh_category_list).pack(side='left', padx=5)

        cat_tree_frame = ttk.Frame(parent_frame)
        cat_tree_frame.grid(row=1, column=0, sticky='nsew', pady=5)
        cat_tree_frame.rowconfigure(0, weight=1)
        cat_tree_frame.columnconfigure(0, weight=1)
        self.category_tree = ttk.Treeview(cat_tree_frame, columns=('Category',), show='headings', height=5)
        self.category_tree.heading('Category', text='Category Name')
        self.category_tree.column('Category', width=180)
        self.category_tree.grid(row=0, column=0, sticky='nsew')
        cat_scrollbar = ttk.Scrollbar(cat_tree_frame, orient='vertical', command=self.category_tree.yview)
        cat_scrollbar.grid(row=0, column=1, sticky='ns')
        self.category_tree.configure(yscrollcommand=cat_scrollbar.set)
        
        cat_form_frame = ttk.Frame(parent_frame)
        cat_form_frame.grid(row=2, column=0, sticky='ew', pady=5)
        cat_form_frame.columnconfigure(1, weight=1)
        ttk.Label(cat_form_frame, text="Name:").grid(row=0, column=0, padx=(0, 5))
        self.cat_name_entry = ttk.Entry(cat_form_frame)
        self.cat_name_entry.grid(row=0, column=1, sticky='ew')

        cat_btn_frame = ttk.Frame(parent_frame)
        cat_btn_frame.grid(row=3, column=0, sticky='ew', pady=5)
        ttk.Button(cat_btn_frame, text="Add", command=self.add_category).pack(side='left', padx=5)
        ttk.Button(cat_btn_frame, text="Delete Selected", command=self.delete_category).pack(side='left', padx=5)

    def create_category_budget_widgets(self, parent_frame):
        """Create UI for managing category budget limits"""
        parent_frame.rowconfigure(1, weight=1)
        parent_frame.columnconfigure(0, weight=1)

        self.budget_cat_type_var = tk.StringVar(value="Expense")
        
        type_frame = ttk.Frame(parent_frame)
        type_frame.grid(row=0, column=0, sticky='ew', pady=2)
        ttk.Label(type_frame, text="Type:").pack(side='left')
        ttk.Radiobutton(type_frame, text="Expense", variable=self.budget_cat_type_var,
                        value="Expense", command=self.refresh_category_budget_list).pack(side='left', padx=5)
        
        # Tree to display categories and their budgets
        budget_tree_frame = ttk.Frame(parent_frame)
        budget_tree_frame.grid(row=1, column=0, sticky='nsew', pady=5)
        budget_tree_frame.rowconfigure(0, weight=1)
        budget_tree_frame.columnconfigure(0, weight=1)
        
        self.category_budget_tree = ttk.Treeview(budget_tree_frame, 
                                                columns=('Category', 'Budget Limit'), 
                                                show='headings', height=5)
        self.category_budget_tree.heading('Category', text='Category')
        self.category_budget_tree.heading('Budget Limit', text='Monthly Limit (€)')
        self.category_budget_tree.column('Category', width=120)
        self.category_budget_tree.column('Budget Limit', width=100, anchor='e')
        self.category_budget_tree.grid(row=0, column=0, sticky='nsew')
        
        budget_scrollbar = ttk.Scrollbar(budget_tree_frame, orient='vertical', 
                                        command=self.category_budget_tree.yview)
        budget_scrollbar.grid(row=0, column=1, sticky='ns')
        self.category_budget_tree.configure(yscrollcommand=budget_scrollbar.set)
        
        # Bind selection to populate form
        self.category_budget_tree.bind('<<TreeviewSelect>>', self.on_category_budget_select)
        
        # Form for setting budget
        form_frame = ttk.Frame(parent_frame)
        form_frame.grid(row=2, column=0, sticky='ew', pady=5)
        form_frame.columnconfigure(1, weight=1)
        ttk.Label(form_frame, text="Category:").grid(row=0, column=0, sticky='w', padx=(0, 5))
        self.budget_category_var = tk.StringVar()
        self.budget_category_combo = ttk.Combobox(form_frame, textvariable=self.budget_category_var, 
                                                 width=15, state='readonly')
        self.budget_category_combo.grid(row=0, column=1, sticky='ew', padx=5)
        
        ttk.Label(form_frame, text="Limit:").grid(row=0, column=2, padx=(10, 5))
        self.budget_limit_entry = ttk.Entry(form_frame, width=10)
        self.budget_limit_entry.grid(row=0, column=3, sticky='ew')
        
        # Buttons
        btn_frame = ttk.Frame(parent_frame)
        btn_frame.grid(row=3, column=0, sticky='ew', pady=5)
        ttk.Button(btn_frame, text="Set Budget", command=self.set_category_budget).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Remove Budget", command=self.remove_category_budget).pack(side='left', padx=5)

    def create_projection_tab(self):
        main_frame = ttk.Frame(self.projection_tab, padding="10")
        main_frame.pack(fill='both', expand=True)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)

        controls_frame = ttk.LabelFrame(main_frame, text="Projection Options", padding="10")
        controls_frame.grid(row=0, column=0, sticky='ew', pady=5)

        ttk.Label(controls_frame, text="Number of months to project:").pack(side='left', padx=5)
        self.projection_months_entry = ttk.Entry(controls_frame, width=10)
        self.projection_months_entry.insert(0, "12")
        self.projection_months_entry.pack(side='left', padx=5)

        ttk.Button(controls_frame, text="Generate Projection", command=self.generate_projection).pack(side='left', padx=20)
        ttk.Button(controls_frame, text="Export Projection", command=self.export_projection_report).pack(side='left', padx=5)

        self.projection_text = tk.Text(main_frame, height=20, width=90, font=('Courier New', 9))
        self.projection_text.grid(row=1, column=0, sticky='nsew', pady=10)

    def export_daily_budget_report(self):
        report_content = self.budget_text.get("1.0", tk.END).strip()
        if not report_content:
            messagebox.showwarning("Warning", "Please generate a report before exporting.")
            return
        month_str = self.budget_month.get()
        today_str = datetime.now().strftime("%Y-%m-%d")
        default_filename = f"day_report_{month_str}_{today_str}.txt"
        filepath = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".txt",
            filetypes=[("Text Documents", "*.txt"), ("All Files", "*.*")]
        )
        if not filepath:
            return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            messagebox.showinfo("Success", f"Report successfully exported to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export report.\nError: {e}")

    def export_projection_report(self):
        report_content = self.projection_text.get("1.0", tk.END).strip()
        if not report_content:
            messagebox.showwarning("Warning", "Please generate a projection before exporting.")
            return
        today_str = datetime.now().strftime("%Y-%m-%d")
        default_filename = f"bank_projection_{today_str}.txt"
        filepath = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".txt",
            filetypes=[("Text Documents", "*.txt"), ("All Files", "*.*")]
        )
        if not filepath:
            return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            messagebox.showinfo("Success", f"Projection successfully exported to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export projection.\nError: {e}")

    ## MODIFIED ##
    def generate_projection(self):
        try:
            num_months = int(self.projection_months_entry.get())
            if num_months <= 0:
                messagebox.showerror("Error", "Number of months must be positive.")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid number of months.")
            return

        bank_balance = self.budget_settings.get('bank_account_balance', 0)
        wallet_balance = self.budget_settings.get('wallet_balance', 0)
        savings_balance = self.budget_settings.get('savings_balance', 0)
        investment_balance = self.budget_settings.get('investment_balance', 0)
        daily_savings_goal = self.budget_settings.get('daily_savings_goal', 0)
        
        starting_total_balance = bank_balance + wallet_balance + savings_balance + investment_balance

        report = f"{'='*80}\n"
        report += f"FINANCIAL PROJECTION\n"
        report += f"{'='*80}\n\n"
        report += f"This report projects your total financial balance (Bank + Wallet + Savings + Investments).\n"
        report += f"It assumes you will meet your daily savings goal every day.\n"
        report += f"The 'Daily Savings Goal' is an indicator and does not automatically change your savings balance.\n\n"
        report += f"Bank Account Balance:      €{bank_balance:>10.2f}\n"
        report += f"Wallet Balance:            €{wallet_balance:>10.2f}\n"
        report += f"Current Savings Balance:   €{savings_balance:>10.2f}\n"
        report += f"Current Investment Balance:€{investment_balance:>10.2f}\n"
        report += f"-----------------------------------------\n"
        report += f"Total Starting Balance:    €{starting_total_balance:>10.2f}\n"
        report += f"Target Daily Savings Goal: €{daily_savings_goal:>10.2f}\n"
        report += f"{'-'*80}\n\n"
        report += f"{'Month':<15} {'Projected Monthly Savings':<30} {'Projected Total Balance'}\n"
        report += f"{'-'*80}\n"

        projected_balance = starting_total_balance
        current_date = date.today()

        for i in range(num_months):
            next_month_date = current_date + relativedelta(months=1)
            days_in_month = (next_month_date - current_date).days
            monthly_savings = daily_savings_goal * days_in_month
            projected_balance += monthly_savings
            
            report += f"{current_date.strftime('%Y-%m'):<15} €{monthly_savings:<28.2f} €{projected_balance:10.2f}\n"
            current_date = next_month_date

        report += f"{'-'*80}\n"

        self.projection_text.delete(1.0, tk.END)
        self.projection_text.insert(1.0, report)

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
            transaction = {'date': date_str, 'amount': amount, 'category': category, 'description': description}
            if trans_type == "Expense":
                self.expenses.append(transaction)
            else:
                self.incomes.append(transaction)
            self.save_data()
            self.amount_entry.delete(0, tk.END)
            self.description_entry.delete(0, tk.END)
            messagebox.showinfo("Success", f"{trans_type} added successfully!")
            self.refresh_transaction_list()
        except ValueError:
            messagebox.showerror("Error", "Invalid amount or date format (YYYY-MM-DD).")

    def refresh_transaction_list(self):
        for item in self.transaction_tree.get_children():
            self.transaction_tree.delete(item)
        filter_month = self.month_filter.get()
        all_transactions = []
        for e in self.expenses:
            if e['date'].startswith(filter_month):
                all_transactions.append({**e, 'type': 'Expense'})
        for i in self.incomes:
            if i['date'].startswith(filter_month):
                all_transactions.append({**i, 'type': 'Income'})
        all_transactions.sort(key=lambda x: x['date'])
        for trans in all_transactions:
            tag = 'expense' if trans['type'] == 'Expense' else 'income'
            self.transaction_tree.insert('', 'end', values=(
                trans['date'], trans['type'], f"€{trans['amount']:.2f}",
                trans['category'], trans['description']), tags=(tag,))
        self.update_summary()

    def update_summary(self):
        filter_month = self.month_filter.get()
        base_income = self.budget_settings.get('monthly_income', 0)
        monthly_flexible_incomes = [i['amount'] for i in self.incomes if i['date'].startswith(filter_month)]
        total_flexible_income = sum(monthly_flexible_incomes)
        total_income = base_income + total_flexible_income
        monthly_expenses = [e['amount'] for e in self.expenses if e['date'].startswith(filter_month)]
        total_flexible_expenses = sum(monthly_expenses)
        total_fixed_costs = sum(fc['amount'] for fc in self.budget_settings.get('fixed_costs', []))
        total_expenses = total_flexible_expenses + total_fixed_costs
        net = total_income - total_expenses
        
        summary_text = (f"Total Income: €{total_income:.2f}  |  "
                        f"Total Expenses: €{total_expenses:.2f}  |  "
                        f"Net: €{net:.2f}")
        
        self.summary_label.config(text=summary_text)

    def delete_transaction(self):
        selected_item = self.transaction_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a transaction to delete.")
            return
        if messagebox.askyesno("Confirm", "Are you sure you want to delete the selected transaction?"):
            item = self.transaction_tree.item(selected_item[0])
            values = item['values']
            date_str, trans_type, amount_str, category, desc = values
            target_transaction = {
                'date': date_str,
                'amount': float(amount_str.replace('€', '')),
                'category': category,
                'description': desc
            }
            if trans_type == 'Expense':
                self.expenses.remove(target_transaction)
            else:
                self.incomes.remove(target_transaction)
            self.save_data()
            self.refresh_transaction_list()

    ## NEW ##
    def refresh_balance_entries(self):
        """Updates the balance Entry widgets on the Budget tab with current values."""
        self.income_entry.delete(0, tk.END)
        self.bank_account_entry.delete(0, tk.END)
        self.wallet_entry.delete(0, tk.END)
        self.savings_entry.delete(0, tk.END)
        self.investment_entry.delete(0, tk.END)
        self.daily_savings_entry.delete(0, tk.END)

        self.income_entry.insert(0, str(self.budget_settings.get('monthly_income', 0)))
        self.bank_account_entry.insert(0, str(self.budget_settings.get('bank_account_balance', 0)))
        self.wallet_entry.insert(0, str(self.budget_settings.get('wallet_balance', 0)))
        self.savings_entry.insert(0, str(self.budget_settings.get('savings_balance', 0)))
        self.investment_entry.insert(0, str(self.budget_settings.get('investment_balance', 0)))
        self.daily_savings_entry.insert(0, str(self.budget_settings.get('daily_savings_goal', 0)))

    ## MODIFIED ##
    def save_settings(self):
        try:
            income = float(self.income_entry.get()) if self.income_entry.get() else 0
            bank_balance = float(self.bank_account_entry.get()) if self.bank_account_entry.get() else 0
            wallet = float(self.wallet_entry.get()) if self.wallet_entry.get() else 0
            savings = float(self.savings_entry.get()) if self.savings_entry.get() else 0
            investment = float(self.investment_entry.get()) if self.investment_entry.get() else 0
            savings_goal = float(self.daily_savings_entry.get()) if self.daily_savings_entry.get() else 0

            self.budget_settings['monthly_income'] = income
            self.budget_settings['bank_account_balance'] = bank_balance
            self.budget_settings['wallet_balance'] = wallet
            self.budget_settings['savings_balance'] = savings
            self.budget_settings['investment_balance'] = investment
            self.budget_settings['daily_savings_goal'] = savings_goal
            
            self.save_data()
            messagebox.showinfo("Success", "Settings saved!")
        except ValueError:
            messagebox.showerror("Error", "Invalid amount in one of the fields.")

    def refresh_fixed_costs_tree(self):
        for item in self.fixed_costs_tree.get_children():
            self.fixed_costs_tree.delete(item)
        for cost in self.budget_settings.get('fixed_costs', []):
            self.fixed_costs_tree.insert('', 'end', values=(cost['desc'], f"{cost['amount']:.2f}"))

    def add_fixed_cost(self):
        try:
            desc = self.fc_desc_entry.get()
            amount = float(self.fc_amount_entry.get())
            if not desc:
                messagebox.showerror("Error", "Description cannot be empty.")
                return
            self.budget_settings['fixed_costs'].append({'desc': desc, 'amount': amount})
            self.save_data()
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
            desc = self.fc_desc_entry.get()
            amount = float(self.fc_amount_entry.get())
            if not desc:
                messagebox.showerror("Error", "Description cannot be empty.")
                return
            original_values = self.fixed_costs_tree.item(selected[0])['values']
            for i, cost in enumerate(self.budget_settings['fixed_costs']):
                if cost['desc'] == original_values[0] and cost['amount'] == float(original_values[1]):
                    self.budget_settings['fixed_costs'][i] = {'desc': desc, 'amount': amount}
                    break
            self.save_data()
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
        self.budget_settings['fixed_costs'].remove(target_cost)
        self.save_data()
        self.refresh_fixed_costs_tree()

    def refresh_category_list(self):
        for item in self.category_tree.get_children():
            self.category_tree.delete(item)
        cat_type = self.cat_type_var.get()
        for category in self.categories.get(cat_type, []):
            self.category_tree.insert('', 'end', values=(category,))

    def add_category(self):
        cat_type = self.cat_type_var.get()
        new_cat = self.cat_name_entry.get().strip()
        if not new_cat:
            messagebox.showerror("Error", "Category name cannot be empty.")
            return
        if new_cat.lower() in [c.lower() for c in self.categories[cat_type]]:
            messagebox.showwarning("Warning", "This category already exists.")
            return
        self.categories[cat_type].append(new_cat)
        self.categories[cat_type].sort()
        self.save_data()
        self.refresh_category_list()
        self.update_categories()
        self.cat_name_entry.delete(0, tk.END)

    def delete_category(self):
        selected = self.category_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a category to delete.")
            return
        cat_type = self.cat_type_var.get()
        category_to_delete = self.category_tree.item(selected[0])['values'][0]
        if category_to_delete.lower() == "other":
            messagebox.showerror("Error", "Cannot delete the 'Other' category.")
            return
        if messagebox.askyesno("Confirm",
                               f"Are you sure you want to delete the '{category_to_delete}' category? \nExisting transactions with this category will not be changed."):
            self.categories[cat_type].remove(category_to_delete)
            self.save_data()
            self.refresh_category_list()
            self.update_categories()
            
    def refresh_category_budget_list(self):
        """Refresh the category budget tree display"""
        for item in self.category_budget_tree.get_children():
            self.category_budget_tree.delete(item)
        
        cat_type = self.budget_cat_type_var.get()
        categories = self.categories.get(cat_type, [])
        
        # Update combo box
        self.budget_category_combo.config(values=categories)
        if categories:
            self.budget_category_combo.set(categories[0])
        
        # Display categories with their budgets
        category_budgets = self.budget_settings.get('category_budgets', {}).get(cat_type, {})
        for category in categories:
            budget_limit = category_budgets.get(category, 0)
            display_limit = f"{budget_limit:.2f}" if budget_limit > 0 else "Not Set"
            self.category_budget_tree.insert('', 'end', values=(category, display_limit))

    def on_category_budget_select(self, event):
        """Populate form when a category is selected"""
        selected = self.category_budget_tree.selection()
        if selected:
            values = self.category_budget_tree.item(selected[0])['values']
            category = values[0]
            self.budget_category_var.set(category)
            
            cat_type = self.budget_cat_type_var.get()
            category_budgets = self.budget_settings.get('category_budgets', {}).get(cat_type, {})
            budget_limit = category_budgets.get(category, 0)
            
            self.budget_limit_entry.delete(0, tk.END)
            if budget_limit > 0:
                self.budget_limit_entry.insert(0, str(budget_limit))

    def set_category_budget(self):
        """Set or update a category budget limit"""
        try:
            category = self.budget_category_var.get()
            limit = float(self.budget_limit_entry.get()) if self.budget_limit_entry.get() else 0
            
            if not category:
                messagebox.showerror("Error", "Please select a category.")
                return
            
            if limit < 0:
                messagebox.showerror("Error", "Budget limit cannot be negative.")
                return
            
            cat_type = self.budget_cat_type_var.get()
            if cat_type not in self.budget_settings['category_budgets']:
                self.budget_settings['category_budgets'][cat_type] = {}
            
            self.budget_settings['category_budgets'][cat_type][category] = limit
            self.save_data()
            self.refresh_category_budget_list()
            self.update_summary() # Refresh summary to show new alerts
            messagebox.showinfo("Success", f"Budget limit set for {category}: €{limit:.2f}")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid budget limit amount.")

    def remove_category_budget(self):
        """Remove a category budget limit"""
        category = self.budget_category_var.get()
        if not category:
            messagebox.showwarning("Warning", "Please select a category.")
            return
        
        cat_type = self.budget_cat_type_var.get()
        category_budgets = self.budget_settings.get('category_budgets', {}).get(cat_type, {})
        
        if category in category_budgets:
            del self.budget_settings['category_budgets'][cat_type][category]
            self.save_data()
            self.refresh_category_budget_list()
            self.update_summary() # Refresh summary to remove alerts
            self.budget_limit_entry.delete(0, tk.END)
            messagebox.showinfo("Success", f"Budget limit removed for {category}")
        else:
            messagebox.showinfo("Info", f"No budget limit set for {category}")

    def generate_daily_budget(self):
        month_str = self.budget_month.get()
        try:
            year, month = map(int, month_str.split('-'))
        except ValueError:
            messagebox.showerror("Error", "Invalid month format. Use YYYY-MM.")
            return

        # --- Data Gathering ---
        base_income = self.budget_settings.get('monthly_income', 0)
        daily_savings_goal = self.budget_settings.get('daily_savings_goal', 0)
        flex_income_month = sum(i['amount'] for i in self.incomes if i['date'].startswith(month_str))
        total_income = base_income + flex_income_month
        fixed_costs = sum(fc['amount'] for fc in self.budget_settings.get('fixed_costs', []))
        days_in_month = calendar.monthrange(year, month)[1]

        # --- Core Calculations ---
        monthly_savings_goal = daily_savings_goal * days_in_month
        original_flexible_budget = total_income - fixed_costs
        spending_flexible_budget = original_flexible_budget - monthly_savings_goal

        if days_in_month == 0:
            messagebox.showerror("Error", "Cannot divide by zero days in month.")
            return

        spending_daily_budget = spending_flexible_budget / days_in_month

        flex_expenses_month = [e for e in self.expenses if e['date'].startswith(month_str)]
        daily_expenses = {}
        for expense in flex_expenses_month:
            expense_date = expense['date']
            daily_expenses.setdefault(expense_date, []).append(expense)

        # --- Report Generation ---
        report = f"{'='*80}\n"
        report += f"DAILY BUDGET REPORT - {calendar.month_name[month]} {year}\n"
        report += f"{'='*80}\n\n"
        report += f"Base Monthly Income:                     €{base_income:>10.2f}\n"
        report += f"Flexible Income (This Month):            €{flex_income_month:>10.2f}\n"
        report += f"TOTAL INCOME:                            €{total_income:>10.2f}\n"
        report += f"Total Fixed Costs:                      -€{fixed_costs:>10.2f}\n"
        report += f"{'-'*50}\n"
        report += f"Net Available for SPENDING:              €{spending_flexible_budget:>10.2f}\n"
        report += f"YOUR DAILY SPENDING TARGET:              €{spending_daily_budget:>10.2f}\n"
        report += f"{'-'*80}\n\n"
        report += f"DAILY BREAKDOWN (Performance against your daily target)\n"
        report += f"{'-'*80}\n"
        report += f"{'Date':<12} {'Target':<12} {'Spent':<12} {'Daily +/-':<12} {'Cumulative':<12} {'Status'}\n"
        report += f"{'-'*80}\n"

        cumulative_deficit = 0
        today = datetime.now().date()
        for day in range(1, days_in_month + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            if date_obj > today:
                break

            day_total_spent = sum(e['amount'] for e in daily_expenses.get(date_str, []))
            daily_plus_minus = spending_daily_budget - day_total_spent
            cumulative_deficit += daily_plus_minus
            
            status = "✓ On Track" if daily_plus_minus >= 0 else "✗ Overspent"
            if day_total_spent == 0: status = "- No spending"

            report += (f"{date_str:<12} €{spending_daily_budget:<10.2f} €{day_total_spent:<10.2f} "
                       f"€{daily_plus_minus:<10.2f} €{cumulative_deficit:<10.2f} {status}\n")

        report += f"{'-'*80}\n\n"

        # --- Forecast Section ---
        if today.year == year and today.month == month and today.day < days_in_month:
            remaining_days_forecast = days_in_month - today.day
            if remaining_days_forecast > 0:
                
                report += f"FORECAST FOR REMAINING {remaining_days_forecast} DAYS\n"
                report += f"{'-'*80}\n"

                daily_surplus_distribution = cumulative_deficit / remaining_days_forecast

                if daily_surplus_distribution < 0:
                    total_flexible_expenses = sum(e['amount'] for e in flex_expenses_month)
                    total_expenses = total_flexible_expenses + fixed_costs
                    net_value = total_income - total_expenses
                    
                    report += f"Your cumulative spending deficit is currently €{-cumulative_deficit:.2f}.\n\n"
                    report += f"You have overspent your flexible budget for the month.\n"
                    report += f"No further flexible budget left for the remainder of the month.\n\n"
                    report += f"--- Understanding the Key Numbers ---\n\n"
                    report += f"It's important to understand what the 'Net Value' and 'Cumulative Deficit' represent:\n\n"
                    report += f" * Summary Net Value (€{net_value:.2f}): This is your actual financial bottom line for the month.\n"
                    report += f"   It's a simple calculation: (Total Income) - (Total Expenses, both fixed and flexible).\n"
                    report += f"   It tells you if you've earned more than you spent overall.\n\n"
                    report += f" * Cumulative Deficit (€{-cumulative_deficit:.2f}): This is a BUDGETING metric, not a final cash value.\n"
                    report += f"   It specifically tracks how much you have overspent on your FLEXIBLE budget (e.g., food, shopping).\n"
                    report += f"   This number shows you exactly where your budget is breaking down.\n\n"
                    report += f"   So, while the Net Value tells you the final result of your total income\n"
                    report += f"   versus your total expenses, the Cumulative number is the\n"
                    report += f"   day-by-day indicator that helps you manage your spending to achieve\n"
                    report += f"   a good Net Value at the end of the month.\n\n"
                    report += f"   This method forces you to pay attention to the Cumulative value. The system is essentially saying,\n"
                    report += f"   \"Your goal is always €{spending_daily_budget:.2f}/day, but you are currently €{cumulative_deficit:.2f} behind schedule.\"\n\n"

                else:
                    new_recommended_budget = spending_daily_budget + daily_surplus_distribution

                    report += "You are currently under budget. Your saved amount has been redistributed.\n\n"
                    report += "Here's how we calculated your new recommended daily budget:\n"
                    report += f"  Daily Surplus Calculation: Daily Surplus = Cumulative Deficit / Remaining Days\n"
                    report += f"                            {daily_surplus_distribution:>10.2f}     = {cumulative_deficit:>10.2f}     /     {remaining_days_forecast}\n\n"
                    report += f"  Original Daily Target:         €{spending_daily_budget:>10.2f}\n"
                    report += f"  Redistributed Surplus / Day:   +€{daily_surplus_distribution:>10.2f}\n"
                    report += f"                                 -----------\n"
                    report += f"  New Recommended Daily Budget:  =€{new_recommended_budget:>10.2f}\n\n"
                    
                    report += "Explanation:\n"
                    report += "To spend your entire flexible budget by the end of the month, you can now spend\n"
                    report += f"up to €{new_recommended_budget:.2f} each day. This new amount is your original target plus\n"
                    report += "your cumulative savings spread across the remaining days.\n"

                report += f"{'-'*80}\n"

        self.budget_text.delete(1.0, tk.END)
        self.budget_text.insert(1.0, report)

def main():
    root = tk.Tk()
    app = FinanceTracker(root)
    root.mainloop()


if __name__ == "__main__":
    main()