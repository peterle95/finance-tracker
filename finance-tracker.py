import tkinter as tk
from tkinter import ttk, messagebox
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
        self.root.geometry("1250x750")

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
        if 'daily_savings_goal' not in self.budget_settings:
            self.budget_settings['daily_savings_goal'] = 0

        if 'Expense' not in self.categories or not self.categories['Expense']:
            self.categories['Expense'] = ["Food", "Transportation", "Entertainment", "Utilities", "Shopping",
                                          "Healthcare", "Other"]
        if 'Income' not in self.categories or not self.categories['Income']:
            self.categories['Income'] = ["Salary", "Side Gig", "Bonus", "Gift", "Investment", "Other"]

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

        controls_frame = ttk.LabelFrame(main_frame, text="Chart Options", padding="10")
        controls_frame.pack(fill='x', pady=5)

        # Month selection
        month_frame = ttk.Frame(controls_frame)
        month_frame.pack(side='left', padx=10, fill='y')
        ttk.Label(month_frame, text="Select Month:").pack(side='left')
        self.chart_month_entry = ttk.Entry(month_frame, width=15)
        self.chart_month_entry.insert(0, datetime.now().strftime("%Y-%m"))
        self.chart_month_entry.pack(side='left', padx=5)

        # Transaction type selection
        type_frame = ttk.Frame(controls_frame)
        type_frame.pack(side='left', padx=10, fill='y')
        ttk.Label(type_frame, text="Chart Type:").pack(side='left')
        self.chart_type_var = tk.StringVar(value="Expense")
        ttk.Radiobutton(type_frame, text="Expenses", variable=self.chart_type_var, value="Expense",
                        command=self._update_report_options_ui).pack(side='left')
        ttk.Radiobutton(type_frame, text="Incomes", variable=self.chart_type_var, value="Income",
                        command=self._update_report_options_ui).pack(side='left', padx=5)

        self.fixed_item_frame = ttk.Frame(controls_frame)
        self.fixed_item_frame.pack(side='left', padx=10, fill='y')
        self.include_fixed_costs_var = tk.BooleanVar(value=False)
        self.fixed_costs_checkbutton = ttk.Checkbutton(self.fixed_item_frame, text="Include Fixed Costs",
                                                      variable=self.include_fixed_costs_var)
        self.include_base_income_var = tk.BooleanVar(value=False)
        self.base_income_checkbutton = ttk.Checkbutton(self.fixed_item_frame, text="Include Base Income",
                                                       variable=self.include_base_income_var)
        self._update_report_options_ui()

        # Value type selection
        value_type_frame = ttk.Frame(controls_frame)
        value_type_frame.pack(side='left', padx=10, fill='y')
        ttk.Label(value_type_frame, text="Display As:").pack(side='left')
        self.chart_value_type_var = tk.StringVar(value="Percentage")
        ttk.Radiobutton(value_type_frame, text="Percentage", variable=self.chart_value_type_var,
                        value="Percentage").pack(side='left')
        ttk.Radiobutton(value_type_frame, text="Total Amount", variable=self.chart_value_type_var,
                        value="Total").pack(side='left', padx=5)

        ttk.Button(controls_frame, text="Generate Chart", command=self.generate_pie_chart).pack(side='left', padx=20,
                                                                                                 fill='y')

        self.chart_frame = ttk.Frame(main_frame)
        self.chart_frame.pack(fill='both', expand=True, pady=10)
        self.canvas = None

    def _update_report_options_ui(self):
        """Shows or hides the relevant checkbutton based on the selected chart type."""
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

        wedges, texts, autotexts = ax.pie(sizes, autopct=autopct, startangle=140,
                                          textprops=dict(color="w"))
        ax.axis('equal')
        ax.set_title(title)
        ax.legend(wedges, labels, title="Categories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        plt.setp(autotexts, size=8, weight="bold")
        fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

    def create_add_transaction_tab(self):
        frame = ttk.Frame(self.add_transaction_tab, padding="20")
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text="Transaction Type:").grid(row=0, column=0, sticky='w', pady=10)
        self.transaction_type_var = tk.StringVar(value="Expense")
        type_frame = ttk.Frame(frame)
        type_frame.grid(row=0, column=1, sticky='w', pady=5)
        ttk.Radiobutton(type_frame, text="Expense", variable=self.transaction_type_var,
                        value="Expense", command=self.update_categories).pack(side='left', padx=5)
        ttk.Radiobutton(type_frame, text="Income", variable=self.transaction_type_var,
                        value="Income", command=self.update_categories).pack(side='left', padx=5)
        ttk.Label(frame, text="Date:").grid(row=1, column=0, sticky='w', pady=5)
        self.date_entry = ttk.Entry(frame, width=30)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=1, column=1, pady=5)
        ttk.Label(frame, text="(YYYY-MM-DD)", foreground="gray").grid(row=1, column=2, sticky='w', padx=5)
        ttk.Label(frame, text="Amount:").grid(row=2, column=0, sticky='w', pady=5)
        self.amount_entry = ttk.Entry(frame, width=30)
        self.amount_entry.grid(row=2, column=1, pady=5)
        ttk.Label(frame, text="Category:").grid(row=3, column=0, sticky='w', pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(frame, textvariable=self.category_var, width=28, state='readonly')
        self.category_combo.grid(row=3, column=1, pady=5)
        self.update_categories()
        ttk.Label(frame, text="Description:").grid(row=4, column=0, sticky='w', pady=5)
        self.description_entry = ttk.Entry(frame, width=30)
        self.description_entry.grid(row=4, column=1, pady=5)
        ttk.Button(frame, text="Add Transaction", command=self.add_transaction).grid(
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
        columns = ('Date', 'Type', 'Amount', 'Category', 'Description')
        self.transaction_tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)
        for col in columns:
            self.transaction_tree.heading(col, text=col)
            width = 120
            if col == 'Amount': width = 100
            if col == 'Description': width = 250
            if col == 'Type': width = 80
            self.transaction_tree.column(col, width=width, anchor='w')
        self.transaction_tree.tag_configure('expense', foreground='red')
        self.transaction_tree.tag_configure('income', foreground='green')
        self.transaction_tree.pack(fill='both', expand=True, pady=10)
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.transaction_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.transaction_tree.configure(yscrollcommand=scrollbar.set)
        ttk.Button(frame, text="Delete Selected", command=self.delete_transaction).pack(pady=5, anchor='e')
        self.summary_label = ttk.Label(frame, text="", font=('Arial', 10, 'bold'))
        self.summary_label.pack(pady=10, fill='x')

    def create_budget_tab(self):
        main_frame = ttk.Frame(self.budget_tab, padding="10")
        main_frame.pack(fill='both', expand=True)
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill='x', pady=(0, 10))
        settings_frame = ttk.LabelFrame(top_frame, text="Monthly Settings", padding="10")
        settings_frame.pack(side='left', fill='y', padx=(0, 10), anchor='n')

        ttk.Label(settings_frame, text="Base Monthly Income:").grid(row=0, column=0, sticky='w', pady=5)
        self.income_entry = ttk.Entry(settings_frame, width=15)
        self.income_entry.grid(row=0, column=1, pady=5)
        if 'monthly_income' in self.budget_settings:
            self.income_entry.insert(0, str(self.budget_settings['monthly_income']))

        ttk.Label(settings_frame, text="Bank Account Balance:").grid(row=1, column=0, sticky='w', pady=5)
        self.bank_account_entry = ttk.Entry(settings_frame, width=15)
        self.bank_account_entry.grid(row=1, column=1, pady=5)
        if 'bank_account_balance' in self.budget_settings:
            self.bank_account_entry.insert(0, str(self.budget_settings['bank_account_balance']))

        ttk.Label(settings_frame, text="Daily Savings Goal:").grid(row=2, column=0, sticky='w', pady=5)
        self.daily_savings_entry = ttk.Entry(settings_frame, width=15)
        self.daily_savings_entry.grid(row=2, column=1, pady=5)
        if 'daily_savings_goal' in self.budget_settings:
            self.daily_savings_entry.insert(0, str(self.budget_settings['daily_savings_goal']))

        ttk.Button(settings_frame, text="Save Settings", command=self.save_settings).grid(
            row=3, column=1, pady=10, sticky='e')

        management_frame = ttk.Frame(top_frame)
        management_frame.pack(side='left', fill='both', expand=True)
        fixed_costs_frame = ttk.LabelFrame(management_frame, text="Manage Fixed Monthly Costs", padding="10")
        fixed_costs_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        fc_tree_frame = ttk.Frame(fixed_costs_frame)
        fc_tree_frame.pack(fill='x')
        self.fixed_costs_tree = ttk.Treeview(fc_tree_frame, columns=('Description', 'Amount'), show='headings', height=5)
        self.fixed_costs_tree.heading('Description', text='Description')
        self.fixed_costs_tree.heading('Amount', text='Amount (€)')
        self.fixed_costs_tree.column('Description', width=200)
        self.fixed_costs_tree.column('Amount', width=100, anchor='e')
        self.fixed_costs_tree.pack(side='left', fill='x', expand=True)
        fc_scrollbar = ttk.Scrollbar(fc_tree_frame, orient='vertical', command=self.fixed_costs_tree.yview)
        fc_scrollbar.pack(side='right', fill='y')
        self.fixed_costs_tree.configure(yscrollcommand=fc_scrollbar.set)
        fc_form_frame = ttk.Frame(fixed_costs_frame)
        fc_form_frame.pack(fill='x', pady=10)
        ttk.Label(fc_form_frame, text="Desc:").pack(side='left', padx=(0, 5))
        self.fc_desc_entry = ttk.Entry(fc_form_frame, width=20)
        self.fc_desc_entry.pack(side='left')
        ttk.Label(fc_form_frame, text="Amount:").pack(side='left', padx=(10, 5))
        self.fc_amount_entry = ttk.Entry(fc_form_frame, width=10)
        self.fc_amount_entry.pack(side='left')
        fc_btn_frame = ttk.Frame(fixed_costs_frame)
        fc_btn_frame.pack(fill='x')
        ttk.Button(fc_btn_frame, text="Add", command=self.add_fixed_cost).pack(side='left', padx=5)
        ttk.Button(fc_btn_frame, text="Update", command=self.update_fixed_cost).pack(side='left', padx=5)
        ttk.Button(fc_btn_frame, text="Delete", command=self.delete_fixed_cost).pack(side='left', padx=5)
        categories_frame = ttk.LabelFrame(management_frame, text="Manage Categories", padding="10")
        categories_frame.pack(side='left', fill='both', expand=True)
        self.create_category_management_widgets(categories_frame)
        report_frame = ttk.LabelFrame(main_frame, text="Daily Budget Report", padding="10")
        report_frame.pack(fill='both', expand=True)
        month_frame = ttk.Frame(report_frame)
        month_frame.pack(fill='x', pady=5)
        ttk.Label(month_frame, text="Select Month:").pack(side='left', padx=5)
        self.budget_month = ttk.Entry(month_frame, width=15)
        self.budget_month.insert(0, datetime.now().strftime("%Y-%m"))
        self.budget_month.pack(side='left', padx=5)
        ttk.Button(month_frame, text="Generate Report", command=self.generate_daily_budget).pack(side='left',
                                                                                                  padx=10)
        self.budget_text = tk.Text(report_frame, height=20, width=90, font=('Courier New', 9))
        self.budget_text.pack(fill='both', expand=True, pady=10)

    def create_projection_tab(self):
        main_frame = ttk.Frame(self.projection_tab, padding="10")
        main_frame.pack(fill='both', expand=True)

        controls_frame = ttk.LabelFrame(main_frame, text="Projection Options", padding="10")
        controls_frame.pack(fill='x', pady=5)

        ttk.Label(controls_frame, text="Number of months to project:").pack(side='left', padx=5)
        self.projection_months_entry = ttk.Entry(controls_frame, width=10)
        self.projection_months_entry.insert(0, "12")
        self.projection_months_entry.pack(side='left', padx=5)

        ttk.Button(controls_frame, text="Generate Projection", command=self.generate_projection).pack(side='left',
                                                                                                        padx=20)

        self.projection_text = tk.Text(main_frame, height=20, width=90, font=('Courier New', 9))
        self.projection_text.pack(fill='both', expand=True, pady=10)

    def generate_projection(self):
        try:
            num_months = int(self.projection_months_entry.get())
            if num_months <= 0:
                messagebox.showerror("Error", "Number of months must be positive.")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid number of months.")
            return

        current_balance = self.budget_settings.get('bank_account_balance', 0)
        daily_savings_goal = self.budget_settings.get('daily_savings_goal', 0)

        report = f"{'='*80}\n"
        report += f"BANK ACCOUNT PROJECTION\n"
        report += f"{'='*80}\n\n"
        report += f"This report projects your bank balance based on your current settings,\n"
        report += f"assuming you meet your daily savings goal every day.\n\n"
        report += f"Starting Balance:          €{current_balance:>10.2f}\n"
        report += f"Target Daily Savings:      €{daily_savings_goal:>10.2f}\n"
        report += f"{'-'*80}\n\n"
        report += f"{'Month':<15} {'Monthly Change':<20} {'Projected Balance'}\n"
        report += f"{'-'*80}\n"

        projected_balance = current_balance
        current_date = date.today()

        for i in range(num_months):
            next_month_date = current_date + relativedelta(months=1)
            days_in_month = (next_month_date - current_date).days
            monthly_savings = daily_savings_goal * days_in_month
            projected_balance += monthly_savings
            
            report += f"{current_date.strftime('%Y-%m'):<15} €{monthly_savings:<18.2f} €{projected_balance:10.2f}\n"
            current_date = next_month_date


        report += f"{'-'*80}\n"

        self.projection_text.delete(1.0, tk.END)
        self.projection_text.insert(1.0, report)

    def create_category_management_widgets(self, parent_frame):
        self.cat_type_var = tk.StringVar(value="Expense")
        cat_type_frame = ttk.Frame(parent_frame)
        cat_type_frame.pack(fill='x', pady=2)
        ttk.Label(cat_type_frame, text="Type:").pack(side='left')
        ttk.Radiobutton(cat_type_frame, text="Expense", variable=self.cat_type_var,
                        value="Expense", command=self.refresh_category_list).pack(side='left', padx=5)
        ttk.Radiobutton(cat_type_frame, text="Income", variable=self.cat_type_var,
                        value="Income", command=self.refresh_category_list).pack(side='left', padx=5)
        cat_tree_frame = ttk.Frame(parent_frame)
        cat_tree_frame.pack(fill='x', pady=5)
        self.category_tree = ttk.Treeview(cat_tree_frame, columns=('Category',), show='headings', height=5)
        self.category_tree.heading('Category', text='Category Name')
        self.category_tree.column('Category', width=180)
        self.category_tree.pack(side='left', fill='x', expand=True)
        cat_scrollbar = ttk.Scrollbar(cat_tree_frame, orient='vertical', command=self.category_tree.yview)
        cat_scrollbar.pack(side='right', fill='y')
        self.category_tree.configure(yscrollcommand=cat_scrollbar.set)
        cat_form_frame = ttk.Frame(parent_frame)
        cat_form_frame.pack(fill='x', pady=5)
        ttk.Label(cat_form_frame, text="Name:").pack(side='left', padx=(0, 5))
        self.cat_name_entry = ttk.Entry(cat_form_frame, width=25)
        self.cat_name_entry.pack(side='left')
        cat_btn_frame = ttk.Frame(parent_frame)
        cat_btn_frame.pack(fill='x', pady=5)
        ttk.Button(cat_btn_frame, text="Add", command=self.add_category).pack(side='left', padx=5)
        ttk.Button(cat_btn_frame, text="Delete Selected", command=self.delete_category).pack(side='left', padx=5)

    def add_transaction(self):
        try:
            date = self.date_entry.get()
            datetime.strptime(date, "%Y-%m-%d")
            amount = float(self.amount_entry.get())
            category = self.category_var.get()
            description = self.description_entry.get()
            trans_type = self.transaction_type_var.get()
            if not category:
                messagebox.showerror("Error", "Please select a category.")
                return
            transaction = {'date': date, 'amount': amount, 'category': category, 'description': description}
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
            date, trans_type, amount_str, category, desc = values
            target_transaction = {
                'date': date,
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

    def save_settings(self):
        try:
            income = float(self.income_entry.get()) if self.income_entry.get() else 0
            bank_balance = float(self.bank_account_entry.get()) if self.bank_account_entry.get() else 0
            savings_goal = float(self.daily_savings_entry.get()) if self.daily_savings_entry.get() else 0

            self.budget_settings['monthly_income'] = income
            self.budget_settings['bank_account_balance'] = bank_balance
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

    ## MODIFIED ##: Removed the 50% target column and adjusted formatting
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
        
        original_daily_budget = original_flexible_budget / days_in_month
        spending_daily_budget = spending_flexible_budget / days_in_month
        
        flex_expenses_month = [e for e in self.expenses if e['date'].startswith(month_str)]
        daily_expenses = {}
        for expense in flex_expenses_month:
            date = expense['date']
            daily_expenses.setdefault(date, []).append(expense)

        # --- Report Generation ---
        report = f"{'='*80}\n"
        report += f"DAILY BUDGET REPORT - {calendar.month_name[month]} {year}\n"
        report += f"{'='*80}\n\n"
        report += f"Base Monthly Income:                     €{base_income:>10.2f}\n"
        report += f"Flexible Income (This Month):            €{flex_income_month:>10.2f}\n"
        report += f"TOTAL INCOME:                            €{total_income:>10.2f}\n"
        report += f"Total Fixed Costs:                      -€{fixed_costs:>10.2f}\n"
        report += f"{'-'*50}\n"
        report += f"Original Available for Spending:         €{original_flexible_budget:>10.2f} (Original Daily: €{original_daily_budget:.2f})\n"
        report += f"Target Monthly Savings Goal:            -€{monthly_savings_goal:>10.2f} (Daily Goal: €{daily_savings_goal:.2f})\n"
        report += f"{'-'*50}\n"
        report += f"Net Available for SPENDING:              €{spending_flexible_budget:>10.2f} (TARGET DAILY SPENDING: €{spending_daily_budget:.2f})\n"
        report += f"{'-'*80}\n\n"
        report += f"DAILY BREAKDOWN (Based on your TARGET DAILY SPENDING budget)\n"
        report += f"{'-'*80}\n"
        report += f"{'Date':<12} {'Budget':<12} {'Spent':<12} {'Saved':<12} {'Cumulative':<12} {'Status'}\n"
        report += f"{'-'*80}\n"

        cumulative_savings = 0
        today = datetime.now().date()
        for day in range(1, days_in_month + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            if date_obj > today:
                break
            
            remaining_days = days_in_month - day
            # Adjusts budget for the rest of the month based on past performance
            if remaining_days > 0:
                adjusted_spending_budget = spending_daily_budget + (cumulative_savings / (remaining_days + 1))
            else:
                adjusted_spending_budget = spending_daily_budget + cumulative_savings
            
            day_total_spent = sum(e['amount'] for e in daily_expenses.get(date_str, []))
            day_savings = adjusted_spending_budget - day_total_spent
            cumulative_savings += day_savings
            status = "✓ Under" if day_savings > 0 else ("✗ Over" if day_savings < 0 else "✓ Exact")
            if day_total_spent == 0: status = "- No spending"

            report += (f"{date_str:<12} €{adjusted_spending_budget:<10.2f} €{day_total_spent:<10.2f} "
                       f"€{day_savings:<10.2f} €{cumulative_savings:<10.2f} {status}\n")
        report += f"{'-'*80}\n\n"

        # --- Forecast Section ---
        if today.year == year and today.month == month and today.day < days_in_month:
            remaining_days_forecast = days_in_month - today.day
            if remaining_days_forecast > 0:
                future_daily_budget = spending_daily_budget + (cumulative_savings / remaining_days_forecast)
                report += f"FORECAST FOR REMAINING {remaining_days_forecast} DAYS\n"
                report += f"{'-'*80}\n"
                report += f"Your new recommended daily SPENDING budget is: €{future_daily_budget:.2f}\n"
                if cumulative_savings > 0:
                    report += "Great job! Your savings have been spread out, giving you more to spend each day.\n"
                else:
                    report += "You're over budget. Try to stick to this lower daily amount to get back on track.\n"
                report += f"{'-'*80}\n"

        self.budget_text.delete(1.0, tk.END)
        self.budget_text.insert(1.0, report)


def main():
    root = tk.Tk()
    app = FinanceTracker(root)
    root.mainloop()


if __name__ == "__main__":
    main()