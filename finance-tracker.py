import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from datetime import datetime, date
from pathlib import Path
import calendar
from dateutil.relativedelta import relativedelta
import random

## NEW/MODIFIED ##: Import matplotlib and numpy for charting
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np


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
        ## NEW ##
        style.configure("Help.TButton", font=('Arial', 12, 'bold'))


        # Main frame to hold the notebook and the help button
        main_frame = ttk.Frame(root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Create UI
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)

        self.create_widgets()
        self.refresh_transaction_list()
        self.refresh_fixed_costs_tree()

        self.refresh_balance_entries()

        ## NEW ## - Help Button
        help_button_frame = ttk.Frame(main_frame)
        help_button_frame.pack(fill='x', pady=(5,0))
        self.help_button = ttk.Button(help_button_frame, text="?", command=self.show_help_window, style="Help.TButton", width=3)
        self.help_button.pack(side='right')


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
        if 'wallet_balance' not in self.budget_settings:
            self.budget_settings['wallet_balance'] = 0
        if 'daily_savings_goal' not in self.budget_settings:
            self.budget_settings['daily_savings_goal'] = 0
        ## NEW ##
        if 'money_lent_balance' not in self.budget_settings:
            self.budget_settings['money_lent_balance'] = 0

        if 'Expense' not in self.categories or not self.categories['Expense']:
            ## MODIFIED ##
            self.categories['Expense'] = ["Food", "Transportation", "Entertainment", "Utilities", "Shopping",
                                          "Healthcare", "Money Lent", "Other"]
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
        self.add_transaction_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.add_transaction_tab, text="Add Transaction")
        self.create_add_transaction_tab()

        self.view_transactions_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.view_transactions_tab, text="View Transactions")
        self.create_view_transactions_tab()
        
        self.transfers_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.transfers_tab, text="Transfers")
        self.create_transfers_tab()

        self.reports_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_tab, text="Reports")
        self.create_reports_tab()

        self.budget_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.budget_tab, text="Budget & Settings")
        self.create_budget_tab()

        self.projection_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.projection_tab, text="Projection")
        self.create_projection_tab()
    
    def show_help_window(self):
        """Creates and displays the help pop-up window."""
        help_win = tk.Toplevel(self.root)
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

        # --- Define text styles ---
        help_text_widget.tag_configure('h1', font=('Arial', 16, 'bold'), spacing1=10)
        help_text_widget.tag_configure('h2', font=('Arial', 12, 'bold'), spacing1=10)
        help_text_widget.tag_configure('bold', font=('Arial', 10, 'bold'))
        help_text_widget.tag_configure('italic', font=('Arial', 10, 'italic'))

        # --- Help Content ---
        help_content = [
            ("Core Concepts", "h1"),
            ("To use this tracker effectively, it's important to understand these key ideas:", "italic"),
            
            ("\n•  Assets (Your Accounts):", "bold"),
            (" These are the containers that hold your money. The main ones are 'Bank', 'Wallet', 'Savings', 'Investments', and 'Money Lent'. You can see their balances in the 'Budget & Settings' tab.", "none"),
            
            ("\n•  Transactions (Income/Expense):", "bold"),
            (" A transaction is any money that ENTERS or LEAVES your financial world. A salary is income; buying groceries is an expense. These change your total net worth.", "none"),
            
            ("\n•  Transfers:", "bold"),
            (" A transfer is moving money BETWEEN your own accounts. Withdrawing cash from an ATM is a transfer from 'Bank' to 'Wallet'. A transfer does NOT change your total net worth; it just moves it around.", "none"),
            
            ("\nHow To Use Each Tab", "h1"),

            ("\nAdd Transaction Tab", "h2"),
            ("Use this tab when you receive money from an external source or spend money on a good or service.", "none"),
            ("\n1.  ", "none"), ("Choose 'Expense' or 'Income'.", "bold"),
            ("\n2.  Fill in the date, amount, category, and a brief description.", "none"),
            ("\n3.  Click 'Add Transaction'. This will be logged and used in all reports.", "none"),

            ("\nView Transactions Tab", "h2"),
            ("This is your history book. It shows all the transactions you've logged for a specific month.", "none"),
            ("\n•  ", "none"), ("Filter by Month:", "bold"), (" Enter a month in YYYY-MM format to see only transactions from that period.", "none"),
            ("\n•  ", "none"), ("Summary:", "bold"), (" At the bottom, you can see your total income, total expenses, and the net result for the filtered month.", "none"),
            ("\n•  ", "none"), ("Modify/Delete:", "bold"), (" Select a transaction in the list and click the appropriate button to edit its details or remove it permanently.", "none"),

            ("\nTransfers Tab", "h2"),
            ("Use this tab ONLY when moving money between your own accounts. This is NOT for recording spending.", "none"),
            ("\n•  ", "none"), ("Example: Lending Money to a Friend:", "bold"),
            ("\n    - From Account: Bank", "none"),
            ("\n    - To Account: Money Lent", "none"),
            ("\n    - Amount: 50", "none"),
            ("\n•  ", "none"), ("Result:", "bold"), (" Your Bank Balance will decrease, and your Money Lent Balance will increase. No income or expense is recorded because it's still your asset.", "none"),
            ("\n   This action will automatically update the balances in the 'Budget & Settings' tab.", "italic"),
            ## MODIFIED ##
            ("\n   ", "none"), ("Important:", "bold"), (" Only perform this transfer when the money has actually left one of your accounts (e.g., your bank account was charged). If you lend cash from your wallet, the transfer should be from 'Wallet' to 'Money Lent'.", "none"),

            ("\nReports Tab", "h2"),
            ("Visualize your finances with a pie chart to see where your money is going or coming from.", "none"),
            ("\n•  ", "none"), ("Generate Chart:", "bold"), (" Select the month, type (Expenses/Incomes), and other options, then click the button. The chart shows the proportion of each category.", "none"),

            ("\nBudget & Settings Tab", "h2"),
            ("This is your control center.", "none"),
            ("\n•  ", "none"), ("Balances (Bank, Wallet, etc.):", "bold"), (" These are snapshots of your assets. You must update them manually after you spend money or after a transfer. For the tracker to be accurate, these numbers should reflect reality.", "none"),
            ("\n•  ", "none"), ("Fixed Monthly Costs:", "bold"), (" Add recurring expenses that are the same each month, like rent or subscriptions. These are automatically included in your monthly expense totals.", "none"),
            ("\n•  ", "none"), ("Manage Categories:", "bold"), (" Customize the dropdown lists for income and expense categories.", "none"),
            ("\n•  ", "none"), ("Daily Budget Report:", "bold"), (" This is a powerful tool to manage your day-to-day flexible spending. It calculates a 'Daily Spending Target' based on your income minus your fixed costs and savings goals. The 'Cumulative' column shows if you are on track or overspending over time.", "none"),

            ("\nProjection Tab", "h2"),
            ("Forecast your financial future.", "none"),
            ("\n•  ", "none"), ("Logic:", "bold"), (" The projection takes your TOTAL current assets (Bank + Wallet + Savings + Investments + Money Lent) and calculates their future value by adding your 'Daily Savings Goal' for each day of the projection period.", "none"),
            
            ("\nCommon Scenarios", "h1"),
            
            ("\nHow do I handle a cash purchase?", "h2"),
            ("This is a two-step process:", "none"),
            ("\n1.  ", "none"), ("Record the Expense:", "bold"), (" Go to the 'Add Transaction' tab and log the expense just like you would with a card purchase (e.g., Amount: 5, Category: Food). This is for your budget.", "none"),
            ("\n2.  ", "none"), ("Update the Asset:", "bold"), (" Go to the 'Budget & Settings' tab and manually decrease your 'Wallet Balance' by the amount you spent. (e.g., if it was 50, change it to 45).", "none"),
            
            ("\nWhat's the difference between 'Net' and 'Cumulative Deficit'?", "h2"),
            ("\n•  ", "none"), ("'Net' (on View Transactions tab):", "bold"), (" This is your simple, final result for the month: Total Income - Total Expenses. It tells you if you saved money or not overall.", "none"),
            ("\n•  ", "none"), ("'Cumulative Deficit' (in Daily Budget Report):", "bold"), (" This is a BUDGETING metric. It tracks how well you are sticking to your daily flexible spending target. It's an early warning system to help you achieve a good 'Net' result at the end of the month.", "none"),
        ]

        for text, style in help_content:
            help_text_widget.insert(tk.END, text, style)

        help_text_widget.config(state='disabled') # Make it read-only

    ## NEW/MODIFIED ##
    def create_reports_tab(self):
        """Create the UI for the reports tab with multiple chart options."""
        main_frame = ttk.Frame(self.reports_tab, padding="10")
        main_frame.pack(fill='both', expand=True)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)

        controls_frame = ttk.LabelFrame(main_frame, text="Chart Options", padding="10")
        controls_frame.grid(row=0, column=0, sticky='ew', pady=5)

        # --- Top Row of Controls ---
        top_controls_row = ttk.Frame(controls_frame)
        top_controls_row.pack(fill='x', expand=True, pady=(0, 10))

        # Chart Style Selection (Pie, Bar, etc.)
        style_frame = ttk.Frame(top_controls_row)
        style_frame.pack(side='left', padx=(0, 20))
        ttk.Label(style_frame, text="Chart Style:").pack(side='left', anchor='n')
        self.report_style_var = tk.StringVar(value="Pie Chart")
        ttk.Radiobutton(style_frame, text="Pie Chart", variable=self.report_style_var, value="Pie Chart",
                        command=self._update_report_controls_visibility).pack(anchor='w')
        ttk.Radiobutton(style_frame, text="Historical Bar Chart", variable=self.report_style_var, value="Bar Chart",
                        command=self._update_report_controls_visibility).pack(anchor='w')

        # Transaction Type Selection (Income/Expense)
        type_frame = ttk.Frame(top_controls_row)
        type_frame.pack(side='left', padx=(0, 20))
        ttk.Label(type_frame, text="Data Type:").pack(side='left')
        self.chart_type_var = tk.StringVar(value="Expense")
        ttk.Radiobutton(type_frame, text="Expenses", variable=self.chart_type_var, value="Expense",
                        command=self._update_report_options_ui).pack(side='left')
        ttk.Radiobutton(type_frame, text="Incomes", variable=self.chart_type_var, value="Income",
                        command=self._update_report_options_ui).pack(side='left', padx=5)

        # --- Dynamic Controls based on Chart Style ---
        self.pie_chart_controls = ttk.Frame(top_controls_row)
        self.pie_chart_controls.pack(side='left', padx=(0, 15))
        ttk.Label(self.pie_chart_controls, text="Select Month:").pack(side='left')
        self.chart_month_entry = ttk.Entry(self.pie_chart_controls, width=15)
        self.chart_month_entry.insert(0, datetime.now().strftime("%Y-%m"))
        self.chart_month_entry.pack(side='left', padx=5)
        ttk.Label(self.pie_chart_controls, text="Display As:").pack(side='left', padx=(10,0))
        self.chart_value_type_var = tk.StringVar(value="Percentage")
        ttk.Radiobutton(self.pie_chart_controls, text="%", variable=self.chart_value_type_var,
                        value="Percentage").pack(side='left')
        ttk.Radiobutton(self.pie_chart_controls, text="€", variable=self.chart_value_type_var,
                        value="Total").pack(side='left', padx=5)

        self.bar_chart_controls = ttk.Frame(top_controls_row)
        # Packed later by _update_report_controls_visibility
        ttk.Label(self.bar_chart_controls, text="Number of Months:").pack(side='left')
        self.history_months_entry = ttk.Entry(self.bar_chart_controls, width=10)
        self.history_months_entry.insert(0, "6")
        self.history_months_entry.pack(side='left', padx=5)

        # --- Bottom Row of Controls ---
        bottom_controls_row = ttk.Frame(controls_frame)
        bottom_controls_row.pack(fill='x', expand=True)
        
        self.fixed_item_frame = ttk.Frame(bottom_controls_row)
        self.fixed_item_frame.pack(side='left', padx=(0, 15))
        self.include_fixed_costs_var = tk.BooleanVar(value=False)
        self.fixed_costs_checkbutton = ttk.Checkbutton(self.fixed_item_frame, text="Include Fixed Costs",
                                                        variable=self.include_fixed_costs_var)
        self.include_base_income_var = tk.BooleanVar(value=False)
        self.base_income_checkbutton = ttk.Checkbutton(self.fixed_item_frame, text="Include Base Income",
                                                        variable=self.include_base_income_var)
        self._update_report_options_ui()

        self.show_budget_lines_var = tk.BooleanVar(value=False)
        self.budget_lines_checkbutton = ttk.Checkbutton(bottom_controls_row, text="Show Budget Limits", 
                        variable=self.show_budget_lines_var)
        self.budget_lines_checkbutton.pack(side='left', padx=(0,15))

        spacer = ttk.Frame(bottom_controls_row)
        spacer.pack(side='left', fill='x', expand=True)

        ttk.Button(bottom_controls_row, text="Generate Chart", command=self.generate_report).pack(side='right')

        self.chart_frame = ttk.Frame(main_frame)
        self.chart_frame.grid(row=1, column=0, sticky='nsew', pady=10)
        self.canvas = None

        self._update_report_controls_visibility() # Initial setup

    ## NEW/MODIFIED ##
    def _update_report_controls_visibility(self):
        """Shows or hides UI elements based on the selected chart style."""
        style = self.report_style_var.get()
        # Forget all dynamic controls first
        self.pie_chart_controls.pack_forget()
        self.bar_chart_controls.pack_forget()
        self.budget_lines_checkbutton.pack_forget()

        if style == "Pie Chart":
            self.pie_chart_controls.pack(side='left', padx=(0, 15))
            self.budget_lines_checkbutton.pack(side='left', padx=(0,15))
        elif style == "Bar Chart":
            self.bar_chart_controls.pack(side='left', padx=(0, 15))

    ## NEW/MODIFIED ##
    def generate_report(self):
        """Dispatcher function that calls the correct chart generation method."""
        style = self.report_style_var.get()
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
            
        if style == "Pie Chart":
            self.generate_pie_chart()
        elif style == "Bar Chart":
            self.generate_history_chart()

    def _update_report_options_ui(self):
        chart_type = self.chart_type_var.get()
        self.fixed_costs_checkbutton.pack_forget()
        self.base_income_checkbutton.pack_forget()
        if chart_type == "Expense":
            self.fixed_costs_checkbutton.pack()
        else:
            self.base_income_checkbutton.pack()

    ## NEW/MODIFIED ##
    def generate_history_chart(self):
        """Generates and displays a bar chart of historical data with a trend line."""
        try:
            num_months = int(self.history_months_entry.get())
            if num_months <= 1:
                messagebox.showerror("Error", "Number of months must be greater than 1 for a historical chart.")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid number of months. Please enter an integer.")
            return

        chart_type = self.chart_type_var.get()
        
        # Determine data source and fixed values
        if chart_type == "Expense":
            data = self.expenses
            title = f"Historical Expenses for the Last {num_months} Months"
            fixed_value = sum(fc['amount'] for fc in self.budget_settings.get('fixed_costs', [])) if self.include_fixed_costs_var.get() else 0
        else: # Income
            data = self.incomes
            title = f"Historical Incomes for the Last {num_months} Months"
            fixed_value = self.budget_settings.get('monthly_income', 0) if self.include_base_income_var.get() else 0

        # Aggregate data by month
        today = date.today()
        monthly_totals = {}
        for i in range(num_months - 1, -1, -1):
            month_date = today - relativedelta(months=i)
            month_key = month_date.strftime("%Y-%m")
            monthly_totals[month_key] = fixed_value

        for item in data:
            item_month = item['date'][:7]
            if item_month in monthly_totals:
                monthly_totals[item_month] += item['amount']
        
        if not any(monthly_totals.values()):
            messagebox.showinfo("No Data", f"No data to display for the selected period.")
            return

        labels = list(monthly_totals.keys())
        values = list(monthly_totals.values())

        # Create the plot
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)

        ax.bar(labels, values, label=f'Monthly Totals')
        
        # Calculate and plot the trend line
        if len(values) > 1:
            x_axis = np.arange(len(labels))
            slope, intercept = np.polyfit(x_axis, values, 1)
            trend_line = slope * x_axis + intercept
            ax.plot(labels, trend_line, color='red', linestyle='--', label='Trend Line')

        ax.set_title(title)
        ax.set_ylabel("Total Amount (€)")
        ax.legend()
        fig.autofmt_xdate(rotation=45)
        fig.tight_layout()

        # Embed the plot in Tkinter
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)


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
        if self.show_budget_lines_var.get() and chart_type == "Expense":
            expense_budgets = self.budget_settings.get('category_budgets', {}).get('Expense', {})
            budget_info = []
            # Compute net available for the selected month
            net_available = self._compute_net_available_for_spending(month_str)
            for category in labels:
                percent_limit = expense_budgets.get(category, 0)
                if percent_limit > 0 and net_available > 0 and category in category_totals:
                    actual = category_totals[category]
                    budget_amount = (percent_limit / 100.0) * net_available
                    used_pct = (actual / budget_amount) * 100 if budget_amount > 0 else 0
                    remaining = max(budget_amount - actual, 0)
                    budget_info.append(f"{category}: {used_pct:.0f}% of budget, left: €{remaining:.2f}")
        
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
        main_frame = ttk.Frame(self.add_transaction_tab, padding="20")
        main_frame.pack(fill='both', expand=True)

        form_frame = ttk.Frame(main_frame)
        form_frame.pack(anchor='center')

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
        self.date_entry.grid(row=1, column=1, pady=5, sticky='w')
        ttk.Label(form_frame, text="(YYYY-MM-DD)", foreground="gray").grid(row=1, column=2, sticky='w', padx=5)

        ttk.Label(form_frame, text="Amount:").grid(row=2, column=0, sticky='w', pady=5)
        self.amount_entry = ttk.Entry(form_frame, width=30)
        self.amount_entry.grid(row=2, column=1, pady=5, sticky='w')

        ttk.Label(form_frame, text="Category:").grid(row=3, column=0, sticky='w', pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(form_frame, textvariable=self.category_var, width=28, state='readonly')
        self.category_combo.grid(row=3, column=1, pady=5, sticky='w')
        self.update_categories()

        ttk.Label(form_frame, text="Description:").grid(row=4, column=0, sticky='w', pady=5)
        self.description_entry = ttk.Entry(form_frame, width=30)
        self.description_entry.grid(row=4, column=1, pady=5, sticky='w')

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

    ## MODIFIED ##
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

        columns = ('ID', 'Date', 'Type', 'Amount', 'Category', 'Description')
        self.transaction_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        for col in columns:
            self.transaction_tree.heading(col, text=col)
            width = 120
            if col == 'Amount': width = 100
            if col == 'Description': width = 250
            if col == 'Type': width = 80
            self.transaction_tree.column(col, width=width, anchor='w')
        
        # Hide the ID column
        self.transaction_tree.column('ID', width=0, stretch=tk.NO)

        self.transaction_tree.tag_configure('expense', foreground='red')
        self.transaction_tree.tag_configure('income', foreground='green')
        self.transaction_tree.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.transaction_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.transaction_tree.configure(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill='x', pady=5)
        # Add a spacer to push buttons to the right
        spacer = ttk.Frame(button_frame)
        spacer.pack(side='left', expand=True, fill='x')
        ttk.Button(button_frame, text="Modify Selected", command=self.open_modify_window).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_transaction).pack(side='left')
        
        self.summary_label = ttk.Label(frame, text="", font=('Arial', 10, 'bold'))
        self.summary_label.pack(pady=10, fill='x')

    ## MODIFIED ##
    def create_transfers_tab(self):
        """Create the UI for the new Transfers tab."""
        main_frame = ttk.Frame(self.transfers_tab, padding="20")
        main_frame.pack(fill='both', expand=True)

        form_frame = ttk.Frame(main_frame)
        form_frame.pack(anchor='center')

        ttk.Label(form_frame, text="This section allows you to record the movement of funds between your accounts.").grid(
            row=0, column=0, columnspan=3, sticky='w', pady=(0, 20))
        
        account_options = ["Bank", "Wallet", "Savings", "Investments", "Money Lent"]

        ttk.Label(form_frame, text="From Account:").grid(row=1, column=0, sticky='w', pady=10)
        self.transfer_from_var = tk.StringVar()
        self.transfer_from_combo = ttk.Combobox(form_frame, textvariable=self.transfer_from_var, 
                                                values=account_options, 
                                                width=28, state='readonly')
        self.transfer_from_combo.grid(row=1, column=1, pady=5, sticky='w')

        ttk.Label(form_frame, text="To Account:").grid(row=2, column=0, sticky='w', pady=10)
        self.transfer_to_var = tk.StringVar()
        self.transfer_to_combo = ttk.Combobox(form_frame, textvariable=self.transfer_to_var,
                                              values=account_options,
                                              width=28, state='readonly')
        self.transfer_to_combo.grid(row=2, column=1, pady=5, sticky='w')

        ttk.Label(form_frame, text="Amount:").grid(row=3, column=0, sticky='w', pady=5)
        self.transfer_amount_entry = ttk.Entry(form_frame, width=30)
        self.transfer_amount_entry.grid(row=3, column=1, pady=5, sticky='w')

        ttk.Button(form_frame, text="Execute Transfer", command=self.execute_transfer).grid(
            row=4, column=1, pady=20, sticky='w')

    ## MODIFIED ##
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
        
        account_keys = {
            "Bank": "bank_account_balance",
            "Wallet": "wallet_balance",
            "Savings": "savings_balance",
            "Investments": "investment_balance",
            "Money Lent": "money_lent_balance"
        }
        
        from_key = account_keys[from_acc]
        to_key = account_keys[to_acc]

        self.budget_settings[from_key] -= amount
        self.budget_settings[to_key] += amount
        
        self.save_data()
        self.refresh_balance_entries()

        messagebox.showinfo("Success", f"Successfully transferred €{amount:.2f} from {from_acc} to {to_acc}.")
        self.transfer_amount_entry.delete(0, tk.END)
        self.transfer_from_var.set('')
        self.transfer_to_var.set('')

    ## MODIFIED ##
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
        
        ttk.Label(settings_frame, text="Wallet Balance:").grid(row=2, column=0, sticky='w', pady=5)
        self.wallet_entry = ttk.Entry(settings_frame, width=15)
        self.wallet_entry.grid(row=2, column=1, pady=5)

        ttk.Label(settings_frame, text="Current Savings:").grid(row=3, column=0, sticky='w', pady=5)
        self.savings_entry = ttk.Entry(settings_frame, width=15)
        self.savings_entry.grid(row=3, column=1, pady=5)

        ttk.Label(settings_frame, text="Current Investments:").grid(row=4, column=0, sticky='w', pady=5)
        self.investment_entry = ttk.Entry(settings_frame, width=15)
        self.investment_entry.grid(row=4, column=1, pady=5)

        ttk.Label(settings_frame, text="Money Lent Balance:").grid(row=5, column=0, sticky='w', pady=5)
        self.money_lent_entry = ttk.Entry(settings_frame, width=15)
        self.money_lent_entry.grid(row=5, column=1, pady=5)

        ttk.Label(settings_frame, text="Daily Savings Goal:").grid(row=6, column=0, sticky='w', pady=5)
        self.daily_savings_entry = ttk.Entry(settings_frame, width=15)
        self.daily_savings_entry.grid(row=6, column=1, pady=5)

        ttk.Button(settings_frame, text="Save Settings", command=self.save_settings).grid(
            row=7, column=1, pady=10, sticky='e')

        management_frame = ttk.Frame(top_frame)
        management_frame.grid(row=0, column=1, sticky='nsew')
        management_frame.columnconfigure([0, 1, 2], weight=1)
        management_frame.rowconfigure(0, weight=1)

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



    def create_category_budget_widgets(self, parent_frame):
        """Create UI for managing category budget limits using sliders."""
        parent_frame.rowconfigure(2, weight=1)
        parent_frame.columnconfigure(0, weight=1)

        self.budget_cat_type_var = tk.StringVar(value="Expense")
        
        type_frame = ttk.Frame(parent_frame)
        type_frame.grid(row=0, column=0, sticky='ew', pady=2)
        ttk.Label(type_frame, text="Type:").pack(side='left')
        ttk.Radiobutton(type_frame, text="Expense", variable=self.budget_cat_type_var,
                        value="Expense", command=self._create_budget_sliders).pack(side='left', padx=5)
        ttk.Radiobutton(type_frame, text="Income", variable=self.budget_cat_type_var,
                        value="Income", command=self._create_budget_sliders).pack(side='left', padx=5)

        # Frame for adding/removing categories
        management_frame = ttk.Frame(parent_frame)
        management_frame.grid(row=1, column=0, sticky='ew', pady=5)

        ttk.Label(management_frame, text="New Category:").pack(side='left', padx=(0, 5))
        self.new_cat_entry = ttk.Entry(management_frame, width=20)
        self.new_cat_entry.pack(side='left')
        ttk.Button(management_frame, text="Add", command=self.add_category_from_budget).pack(side='left', padx=5)

        ttk.Label(management_frame, text="Remove Category:").pack(side='left', padx=(10, 5))
        self.remove_cat_combo = ttk.Combobox(management_frame, width=20, state='readonly')
        self.remove_cat_combo.pack(side='left')
        ttk.Button(management_frame, text="Remove", command=self.remove_category_from_budget).pack(side='left', padx=5)
        
        self.sliders_frame = ttk.Frame(parent_frame)
        self.sliders_frame.grid(row=2, column=0, sticky='nsew', pady=5)
        
        btn_frame = ttk.Frame(parent_frame)
        btn_frame.grid(row=3, column=0, sticky='ew', pady=5)
        ttk.Button(btn_frame, text="Save Budgets", command=self.save_category_budgets).pack(side='left', padx=5)
        
        self.budget_sliders = {}
        self._create_budget_sliders()

    def _create_budget_sliders(self):
        """Create and arrange the budget sliders for each category."""
        for widget in self.sliders_frame.winfo_children():
            widget.destroy()
            
        self.budget_sliders = {}
        cat_type = self.budget_cat_type_var.get()
        categories = self.categories.get(cat_type, [])
        category_budgets = self.budget_settings.get('category_budgets', {}).get(cat_type, {})

        # Distribute 100% among categories that have no budget yet
        unbudgeted_categories = [c for c in categories if c not in category_budgets]
        total_budgeted = sum(category_budgets.values())
        
        if unbudgeted_categories and total_budgeted < 100:
            remaining_percentage = 100 - total_budgeted
            per_category_share = remaining_percentage / len(unbudgeted_categories)
            for category in unbudgeted_categories:
                category_budgets[category] = per_category_share

        # Normalize to 100% if the total is off
        total_budgeted = sum(category_budgets.values())
        if total_budgeted > 0:
            for category in category_budgets:
                category_budgets[category] = (category_budgets[category] / total_budgeted) * 100

        self.remove_cat_combo['values'] = categories
        for i, category in enumerate(categories):
            frame = ttk.Frame(self.sliders_frame)
            frame.pack(fill='x', pady=2)
            
            ttk.Label(frame, text=category, width=15).pack(side='left')
            
            var = tk.DoubleVar(value=category_budgets.get(category, 0))
            
            slider = ttk.Scale(frame, from_=0, to=100, orient='horizontal', variable=var,
                               command=lambda v, cat=category: self._on_slider_change(cat, float(v)))
            slider.pack(side='left', fill='x', expand=True, padx=5)
            
            label = ttk.Label(frame, text=f"{var.get():.1f}%", width=7)
            label.pack(side='left')
            
            self.budget_sliders[category] = {'var': var, 'slider': slider, 'label': label}

    def _on_slider_change(self, changed_category, new_value):
        """Callback for when a slider's value changes."""
        # Lock to prevent recursive updates
        if hasattr(self, '_slider_lock') and self._slider_lock:
            return
            
        self._slider_lock = True
        
        # Get the old value from the variable
        old_value = self.budget_sliders[changed_category]['var'].get()
        self.budget_sliders[changed_category]['var'].set(new_value)
        
        # Update the label for the changed slider
        self.budget_sliders[changed_category]['label'].config(text=f"{new_value:.1f}%")
        
        # Distribute the change among other sliders
        self._adjust_other_sliders(changed_category, new_value, old_value)
        
        self._slider_lock = False

    def _adjust_other_sliders(self, changed_category, new_value, old_value):
        """Adjust other sliders to maintain a total of 100%."""
        delta = new_value - old_value
        other_sliders = {cat: self.budget_sliders[cat] for cat in self.budget_sliders if cat != changed_category}
        
        # Total value of other sliders
        other_total = sum(s['var'].get() for s in other_sliders.values())
        
        if other_total > 0:
            for category, slider_info in other_sliders.items():
                current_val = slider_info['var'].get()
                # Distribute the delta proportionally
                adjustment = delta * (current_val / other_total)
                new_slider_val = max(0, min(100, current_val - adjustment))
                slider_info['var'].set(new_slider_val)
                slider_info['label'].config(text=f"{new_slider_val:.1f}%")
        else:
            # If all other sliders are at 0, distribute the change equally
            if len(other_sliders) > 0:
                per_slider_adjustment = delta / len(other_sliders)
                for category, slider_info in other_sliders.items():
                    new_slider_val = max(0, min(100, slider_info['var'].get() - per_slider_adjustment))
                    slider_info['var'].set(new_slider_val)
                    slider_info['label'].config(text=f"{new_slider_val:.1f}%")

        # Final normalization pass to ensure it's exactly 100%
        self._normalize_sliders()

    def _normalize_sliders(self):
        """Ensure the total of all sliders is exactly 100%."""
        total = sum(s['var'].get() for s in self.budget_sliders.values())
        if total == 0: return # Avoid division by zero
        
        if abs(total - 100.0) > 0.01: # Only normalize if there's a significant deviation
            for slider_info in self.budget_sliders.values():
                current_val = slider_info['var'].get()
                normalized_val = (current_val / total) * 100
                slider_info['var'].set(normalized_val)
                slider_info['label'].config(text=f"{normalized_val:.1f}%")

    def save_category_budgets(self):
        """Save the current slider values to the budget settings."""
        cat_type = self.budget_cat_type_var.get()
        if cat_type not in self.budget_settings['category_budgets']:
            self.budget_settings['category_budgets'][cat_type] = {}
            
        for category, slider_info in self.budget_sliders.items():
            self.budget_settings['category_budgets'][cat_type][category] = slider_info['var'].get()
            
        self.save_data()
        self._create_budget_sliders()
        messagebox.showinfo("Success", "Category budgets have been saved.")

    def add_category_from_budget(self):
        cat_type = self.budget_cat_type_var.get()
        new_cat = self.new_cat_entry.get().strip()
        if not new_cat:
            messagebox.showerror("Error", "Category name cannot be empty.")
            return
        if new_cat.lower() in [c.lower() for c in self.categories[cat_type]]:
            messagebox.showwarning("Warning", "This category already exists.")
            return
        self.categories[cat_type].append(new_cat)
        self.categories[cat_type].sort()
        self.save_data()
        self._create_budget_sliders()
        self.update_categories()
        self.new_cat_entry.delete(0, tk.END)

    def remove_category_from_budget(self):
        cat_type = self.budget_cat_type_var.get()
        category_to_delete = self.remove_cat_combo.get()
        if not category_to_delete:
            messagebox.showwarning("Warning", "Please select a category to delete.")
            return
        if category_to_delete.lower() == "other":
            messagebox.showerror("Error", "Cannot delete the 'Other' category.")
            return
        if messagebox.askyesno("Confirm",
                               f"Are you sure you want to delete the '{category_to_delete}' category? \nExisting transactions with this category will not be changed."):
            self.categories[cat_type].remove(category_to_delete)
            # Also remove from budget settings
            if cat_type in self.budget_settings['category_budgets'] and category_to_delete in self.budget_settings['category_budgets'][cat_type]:
                del self.budget_settings['category_budgets'][cat_type][category_to_delete]
            self.save_data()
            self._create_budget_sliders()
            self.update_categories()

    def add_category_from_budget(self):
        cat_type = self.budget_cat_type_var.get()
        new_cat = self.new_cat_entry.get().strip()
        if not new_cat:
            messagebox.showerror("Error", "Category name cannot be empty.")
            return
        if new_cat.lower() in [c.lower() for c in self.categories[cat_type]]:
            messagebox.showwarning("Warning", "This category already exists.")
            return
        self.categories[cat_type].append(new_cat)
        self.categories[cat_type].sort()
        self.save_data()
        self._create_budget_sliders()
        self.update_categories()
        self.new_cat_entry.delete(0, tk.END)

    def remove_category_from_budget(self):
        cat_type = self.budget_cat_type_var.get()
        category_to_delete = self.remove_cat_combo.get()
        if not category_to_delete:
            messagebox.showwarning("Warning", "Please select a category to delete.")
            return
        if category_to_delete.lower() == "other":
            messagebox.showerror("Error", "Cannot delete the 'Other' category.")
            return
        if messagebox.askyesno("Confirm",
                               f"Are you sure you want to delete the '{category_to_delete}' category? \nExisting transactions with this category will not be changed."):
            self.categories[cat_type].remove(category_to_delete)
            # Also remove from budget settings
            if cat_type in self.budget_settings['category_budgets'] and category_to_delete in self.budget_settings['category_budgets'][cat_type]:
                del self.budget_settings['category_budgets'][cat_type][category_to_delete]
            self.save_data()
            self._create_budget_sliders()
            self.update_categories()

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
        money_lent_balance = self.budget_settings.get('money_lent_balance', 0)
        daily_savings_goal = self.budget_settings.get('daily_savings_goal', 0)
        
        starting_total_balance = (bank_balance + wallet_balance + savings_balance + 
                                  investment_balance + money_lent_balance)

        report = f"{'='*80}\n"
        report += f"FINANCIAL PROJECTION\n"
        report += f"{'='*80}\n\n"
        report += f"This report projects your total financial balance (Bank + Wallet + Savings + Investments + Money Lent).\n"
        report += f"It assumes you will meet your daily savings goal every day.\n\n"
        report += f"Bank Account Balance:      €{bank_balance:>10.2f}\n"
        report += f"Wallet Balance:            €{wallet_balance:>10.2f}\n"
        report += f"Current Savings Balance:   €{savings_balance:>10.2f}\n"
        report += f"Current Investment Balance:€{investment_balance:>10.2f}\n"
        report += f"Money Lent Balance:        €{money_lent_balance:>10.2f}\n"
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

    ## MODIFIED ##
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

            # Add a unique ID to each transaction
            trans_id = f"{datetime.now().timestamp()}-{random.randint(1000, 9999)}"
            transaction = {'id': trans_id, 'date': date_str, 'amount': amount, 'category': category, 'description': description}

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

    ## MODIFIED ##
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
            # Ensure an ID exists for older transactions if needed, though new ones will have it.
            trans_id = trans.get('id', '') 
            self.transaction_tree.insert('', 'end', values=(
                trans_id, trans['date'], trans['type'], f"€{trans['amount']:.2f}",
                trans['category'], trans['description']), tags=(tag,))
        self.update_summary()

    def update_summary(self):
        filter_month = self.month_filter.get()
        base_income = self.budget_settings.get('monthly_income', 0)
        
        # Calculate flexible income for the current month
        monthly_flexible_incomes = [i['amount'] for i in self.incomes if i['date'].startswith(filter_month)]
        total_flexible_income = sum(monthly_flexible_incomes)
        total_income = base_income + total_flexible_income
        
        # Calculate flexible expenses for the current month
        monthly_expenses = [e['amount'] for e in self.expenses if e['date'].startswith(filter_month)]
        total_flexible_expenses = sum(monthly_expenses)
        
        # Total fixed costs are constant regardless of month
        total_fixed_costs = sum(fc['amount'] for fc in self.budget_settings.get('fixed_costs', []))
        
        total_expenses = total_flexible_expenses + total_fixed_costs
        
        # The 'flexible_costs' in budget_settings seems to be an old/unused key in your data structure.
        # Based on your daily budget report, 'Net Available for SPENDING' is what you consider flexible.
        # Let's calculate the 'Net Available for Spending' for the current month.
        
        # Get days in the current month for daily savings goal calculation
        try:
            year, month = map(int, filter_month.split('-'))
            days_in_month = calendar.monthrange(year, month)[1]
        except ValueError:
            # Fallback for invalid month format, or if month_filter is empty
            days_in_month = 30 

        daily_savings_goal = self.budget_settings.get('daily_savings_goal', 0)
        monthly_savings_goal = daily_savings_goal * days_in_month
        
        # "Flexible Costs" in the context of the summary should represent the actual flexible expenses incurred
        flexible_costs_incurred = total_flexible_expenses 

        # Net is the total income minus total expenses (fixed + flexible + savings goal)
        # However, your current `net` calculation is just `total_income - total_expenses`.
        # If "Flexible Costs" refers to actual flexible spending, `net` calculation should match the daily budget report's definition of "Net Available for SPENDING"
        # Let's use the definition: Total Income - Total Fixed Costs - Monthly Savings Goal - Actual Flexible Expenses (if that's what you want for 'net')
        # Or if `net` is meant to be simple (Income - Expenses), then keep it as is.
        # For consistency with the report, let's keep it as `total_income - total_expenses` here.
        net = total_income - total_expenses
        
        summary_text = (f"Total Income: €{total_income:.2f}  |  "
                        f"Total Expenses: €{total_expenses:.2f}  |  "
                        f"Flexible Costs Incurred: €{flexible_costs_incurred:.2f}  |  "
                        f"Net: €{net:.2f}")
        
        self.summary_label.config(text=summary_text)

    ## MODIFIED ##
    def delete_transaction(self):
        selected_item = self.transaction_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a transaction to delete.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete the selected transaction?"):
            item_values = self.transaction_tree.item(selected_item[0])['values']
            trans_id = item_values[0]
            trans_type = item_values[2]

            target_list = self.expenses if trans_type == 'Expense' else self.incomes
            transaction_found = False
            
            for i, trans in enumerate(target_list):
                if trans.get('id') == trans_id:
                    del target_list[i]
                    transaction_found = True
                    break
            
            # Fallback for old data without IDs
            if not transaction_found:
                date_str, _, amount_str, category, desc = item_values[1:]
                target_transaction = {
                    'date': date_str,
                    'amount': float(amount_str.replace('€', '')),
                    'category': category,
                    'description': desc
                }
                try:
                    target_list.remove(target_transaction)
                except ValueError:
                    messagebox.showerror("Error", "Could not delete the transaction (fallback failed). It might have been modified externally.")
                    return

            self.save_data()
            self.refresh_transaction_list()
            
    ## NEW ##
    def open_modify_window(self):
        """Opens a new window to modify the selected transaction."""
        selected_item = self.transaction_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a transaction to modify.")
            return

        item_values = self.transaction_tree.item(selected_item[0])['values']
        trans_id = item_values[0]

        original_transaction = None
        original_list_name = None
        
        for t in self.expenses:
            if t.get('id') == trans_id:
                original_transaction = t
                original_list_name = 'Expense'
                break
        if not original_transaction:
            for t in self.incomes:
                if t.get('id') == trans_id:
                    original_transaction = t
                    original_list_name = 'Income'
                    break
        
        if not original_transaction:
            messagebox.showerror("Error", "Could not find the selected transaction in the data. It may be legacy data without an ID.")
            return

        modify_win = tk.Toplevel(self.root)
        modify_win.title("Modify Transaction")
        modify_win.transient(self.root)
        modify_win.grab_set()

        form_frame = ttk.Frame(modify_win, padding="20")
        form_frame.pack(fill='both', expand=True)

        ttk.Label(form_frame, text="Transaction Type:").grid(row=0, column=0, sticky='w', pady=10)
        mod_transaction_type_var = tk.StringVar(value=original_list_name)
        type_frame = ttk.Frame(form_frame)
        type_frame.grid(row=0, column=1, sticky='w', pady=5)
        
        def update_mod_categories():
            trans_type = mod_transaction_type_var.get()
            categories = self.categories.get(trans_type, [])
            mod_category_combo.config(values=categories)
            if categories:
                # If the original category is still valid, use it. Otherwise, default to first.
                if mod_category_var.get() in categories:
                    mod_category_combo.set(mod_category_var.get())
                else:
                    mod_category_combo.set(categories[0])
            else:
                mod_category_combo.set("")

        ttk.Radiobutton(type_frame, text="Expense", variable=mod_transaction_type_var,
                        value="Expense", command=update_mod_categories).pack(side='left', padx=5)
        ttk.Radiobutton(type_frame, text="Income", variable=mod_transaction_type_var,
                        value="Income", command=update_mod_categories).pack(side='left', padx=5)

        ttk.Label(form_frame, text="Date:").grid(row=1, column=0, sticky='w', pady=5)
        mod_date_entry = ttk.Entry(form_frame, width=30)
        mod_date_entry.insert(0, original_transaction.get('date', ''))
        mod_date_entry.grid(row=1, column=1, pady=5, sticky='w')

        ttk.Label(form_frame, text="Amount:").grid(row=2, column=0, sticky='w', pady=5)
        mod_amount_entry = ttk.Entry(form_frame, width=30)
        mod_amount_entry.insert(0, original_transaction.get('amount', ''))
        mod_amount_entry.grid(row=2, column=1, pady=5, sticky='w')

        ttk.Label(form_frame, text="Category:").grid(row=3, column=0, sticky='w', pady=5)
        mod_category_var = tk.StringVar(value=original_transaction.get('category', ''))
        mod_category_combo = ttk.Combobox(form_frame, textvariable=mod_category_var, width=28, state='readonly')
        mod_category_combo.grid(row=3, column=1, pady=5, sticky='w')
        update_mod_categories() # Initial population

        ttk.Label(form_frame, text="Description:").grid(row=4, column=0, sticky='w', pady=5)
        mod_description_entry = ttk.Entry(form_frame, width=30)
        mod_description_entry.insert(0, original_transaction.get('description', ''))
        mod_description_entry.grid(row=4, column=1, pady=5, sticky='w')

        def save_changes():
            try:
                new_date = mod_date_entry.get()
                datetime.strptime(new_date, "%Y-%m-%d")
                new_amount = float(mod_amount_entry.get())
                new_category = mod_category_var.get()
                new_description = mod_description_entry.get()
                new_type = mod_transaction_type_var.get()

                if not new_category:
                    messagebox.showerror("Error", "Please select a category.", parent=modify_win)
                    return

                # Find the transaction again to modify it
                transaction_to_update = None
                current_list = None
                if original_list_name == 'Expense':
                    current_list = self.expenses
                else:
                    current_list = self.incomes
                
                for t in current_list:
                    if t.get('id') == trans_id:
                        transaction_to_update = t
                        break
                
                # Update the transaction's values
                transaction_to_update['date'] = new_date
                transaction_to_update['amount'] = new_amount
                transaction_to_update['category'] = new_category
                transaction_to_update['description'] = new_description

                # Handle if the type changed
                if new_type != original_list_name:
                    current_list.remove(transaction_to_update)
                    if new_type == 'Expense':
                        self.expenses.append(transaction_to_update)
                    else:
                        self.incomes.append(transaction_to_update)

                self.save_data()
                self.refresh_transaction_list()
                modify_win.destroy()

            except ValueError:
                messagebox.showerror("Error", "Invalid amount or date format (YYYY-MM-DD).", parent=modify_win)

        ttk.Button(form_frame, text="Save Changes", command=save_changes).grid(row=5, column=1, pady=20, sticky='w')

    ## MODIFIED ##
    def refresh_balance_entries(self):
        """Updates the balance Entry widgets on the Budget tab with current values."""
        self.income_entry.delete(0, tk.END)
        self.bank_account_entry.delete(0, tk.END)
        self.wallet_entry.delete(0, tk.END)
        self.savings_entry.delete(0, tk.END)
        self.investment_entry.delete(0, tk.END)
        self.money_lent_entry.delete(0, tk.END)
        self.daily_savings_entry.delete(0, tk.END)

        self.income_entry.insert(0, str(self.budget_settings.get('monthly_income', 0)))
        self.bank_account_entry.insert(0, str(self.budget_settings.get('bank_account_balance', 0)))
        self.wallet_entry.insert(0, str(self.budget_settings.get('wallet_balance', 0)))
        self.savings_entry.insert(0, str(self.budget_settings.get('savings_balance', 0)))
        self.investment_entry.insert(0, str(self.budget_settings.get('investment_balance', 0)))
        self.money_lent_entry.insert(0, str(self.budget_settings.get('money_lent_balance', 0)))
        self.daily_savings_entry.insert(0, str(self.budget_settings.get('daily_savings_goal', 0)))

    ## MODIFIED ##
    def save_settings(self):
        try:
            income = float(self.income_entry.get()) if self.income_entry.get() else 0
            bank_balance = float(self.bank_account_entry.get()) if self.bank_account_entry.get() else 0
            wallet = float(self.wallet_entry.get()) if self.wallet_entry.get() else 0
            savings = float(self.savings_entry.get()) if self.savings_entry.get() else 0
            investment = float(self.investment_entry.get()) if self.investment_entry.get() else 0
            money_lent = float(self.money_lent_entry.get()) if self.money_lent_entry.get() else 0
            savings_goal = float(self.daily_savings_entry.get()) if self.daily_savings_entry.get() else 0

            self.budget_settings['monthly_income'] = income
            self.budget_settings['bank_account_balance'] = bank_balance
            self.budget_settings['wallet_balance'] = wallet
            self.budget_settings['savings_balance'] = savings
            self.budget_settings['investment_balance'] = investment
            self.budget_settings['money_lent_balance'] = money_lent
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


            




    def _compute_net_available_for_spending(self, month_str: str) -> float:
        """Compute Net Available for Spending for a given month (YYYY-MM)."""
        try:
            datetime.strptime(month_str, "%Y-%m")
        except ValueError:
            month_str = datetime.now().strftime("%Y-%m")

        base_income = self.budget_settings.get('monthly_income', 0)
        daily_savings_goal = self.budget_settings.get('daily_savings_goal', 0)
        flex_income_month = sum(i['amount'] for i in self.incomes if i['date'].startswith(month_str))
        total_income = base_income + flex_income_month
        fixed_costs = sum(fc['amount'] for fc in self.budget_settings.get('fixed_costs', []))

        try:
            year, month = map(int, month_str.split('-'))
            days_in_month = calendar.monthrange(year, month)[1]
        except Exception:
            days_in_month = 30

        monthly_savings_goal = daily_savings_goal * days_in_month
        spending_flexible_budget = total_income - fixed_costs - monthly_savings_goal
        return max(spending_flexible_budget, 0)

    def generate_daily_budget(self):
        month_str = self.budget_month.get()
        try:
            year, month = map(int, month_str.split('-'))
        except ValueError:
            messagebox.showerror("Error", "Invalid month format. Use YYYY-MM.")
            return

        base_income = self.budget_settings.get('monthly_income', 0)
        daily_savings_goal = self.budget_settings.get('daily_savings_goal', 0)
        flex_income_month = sum(i['amount'] for i in self.incomes if i['date'].startswith(month_str))
        total_income = base_income + flex_income_month
        fixed_costs = sum(fc['amount'] for fc in self.budget_settings.get('fixed_costs', []))
        
        # Calculate days in the selected month
        try:
            days_in_month = calendar.monthrange(year, month)[1]
        except calendar.IllegalMonthError:
            messagebox.showerror("Error", "Invalid month number in date.")
            return

        monthly_savings_goal = daily_savings_goal * days_in_month
        
        # This is the total pool for flexible spending for the month
        monthly_flexible_spending_budget = total_income - fixed_costs - monthly_savings_goal

        if days_in_month == 0:
            messagebox.showerror("Error", "Cannot divide by zero days in month.")
            return

        # Initial daily target based on the full monthly flexible budget
        initial_daily_spending_target = monthly_flexible_spending_budget / days_in_month

        flex_expenses_month = [e for e in self.expenses if e['date'].startswith(month_str)]
        daily_expenses = {}
        for expense in flex_expenses_month:
            expense_date = expense['date']
            daily_expenses.setdefault(expense_date, []).append(expense)

        report = f"{'='*80}\n"
        report += f"DAILY BUDGET REPORT - {calendar.month_name[month]} {year}\n"
        report += f"{'='*80}\n\n"
        report += f"Base Monthly Income:                     €{base_income:>10.2f}\n"
        report += f"Flexible Income (This Month):            €{flex_income_month:>10.2f}\n"
        report += f"TOTAL INCOME:                            €{total_income:>10.2f}\n"
        report += f"Total Fixed Costs:                      -€{fixed_costs:>10.2f}\n"
        report += f"{'-'*50}\n"
        report += f"Monthly Savings Goal:                   -€{monthly_savings_goal:>10.2f}\n" # Mark as deduction
        report += f"NET MONTHLY FLEXIBLE BUDGET:             €{monthly_flexible_spending_budget:>10.2f}\n" # Renamed for clarity
        report += f"INITIAL DAILY SPENDING TARGET:           €{initial_daily_spending_target:>10.2f}\n" # Renamed for clarity
        report += f"{'-'*80}\n\n"
        report += f"DAILY BREAKDOWN (Performance against your initial daily target)\n" # Updated header
        report += f"{'-'*80}\n"
        report += f"{'Date':<12} {'Target':<12} {'Spent':<12} {'Daily +/-':<12} {'Cumulative':<12} {'Status'}\n"
        report += f"{'-'*80}\n"

        cumulative_flexible_balance = monthly_flexible_spending_budget # Track the actual flexible balance
        
        today = datetime.now().date()
        current_month_start_date = date(year, month, 1)
        
        # Loop through each day of the month up to today
        for day in range(1, days_in_month + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            if date_obj > today: # Stop at the current day for past performance
                break

            day_total_spent = sum(e['amount'] for e in daily_expenses.get(date_str, []))
            
            # Update the cumulative flexible balance directly
            cumulative_flexible_balance -= day_total_spent

            # For 'Daily +/-', compare to the *initial* daily target
            daily_plus_minus_from_target = initial_daily_spending_target - day_total_spent
            
            # Status based on daily performance vs initial target
            status = "✓ On Track" if daily_plus_minus_from_target >= 0 else "✗ Overspent"
            if day_total_spent == 0: status = "- No spending"

            report += (f"{date_str:<12} €{initial_daily_spending_target:<10.2f} €{day_total_spent:<10.2f} "
                       f"€{daily_plus_minus_from_target:<10.2f} €{cumulative_flexible_balance:<10.2f} {status}\n") # Use cumulative_flexible_balance here

        report += f"{'-'*80}\n\n"

        # Forecast for remaining days
        if today.year == year and today.month == month and today.day < days_in_month:
            days_passed_this_month = today.day - current_month_start_date.day + 1
            remaining_days_forecast = days_in_month - days_passed_this_month

            report += f"FORECAST FOR REMAINING {remaining_days_forecast} DAYS\n"
            report += f"{'-'*80}\n"

            if remaining_days_forecast > 0:
                new_daily_spending_target = cumulative_flexible_balance / remaining_days_forecast
            else: # No remaining days, but still in the forecast block if today is the last day
                new_daily_spending_target = cumulative_flexible_balance # whatever is left is for today

            if new_daily_spending_target < 0:
                report += f"Your current flexible budget balance is €{cumulative_flexible_balance:.2f}.\n\n"
                report += f"You have overspent your **monthly flexible budget**.\n"
                report += f"You need to reduce future spending or pull from other sources.\n\n"
                
                report += f"To cover your deficit for the remainder of the month, you would need to\n"
                report += f"spend €{new_daily_spending_target:.2f} per day, which is not possible.\n\n"
                
                # Re-calculating net_value with consistent elements
                total_flexible_expenses_incurred = sum(e['amount'] for e in flex_expenses_month)
                
                # The "Net" as in total financial bottom line for the month, including savings goal
                overall_net_value_including_savings = total_income - fixed_costs - total_flexible_expenses_incurred - monthly_savings_goal
                
                report += f"--- Understanding the Key Numbers ---\n\n"
                report += f" * Overall Net Value (Including Savings Goal): €{overall_net_value_including_savings:.2f}\n"
                report += f"   This is your actual financial bottom line for the month if you meet your goals.\n\n"
                report += f" * Your Current Flexible Budget Balance: €{cumulative_flexible_balance:.2f}\n"
                report += f"   This is the remaining portion of your `NET MONTHLY FLEXIBLE BUDGET` after your spending.\n"
                report += f"   A negative value indicates you have spent more than your monthly flexible budget allows\n"
                report += f"   (after fixed costs and savings goal).\n\n"
                report += f"   The system is showing that you've overspent your flexible allowance for the month.\n"
                report += f"   You will need to adjust your spending or allocate funds from elsewhere to avoid debt or missing your savings goal.\n\n"

            else:
                report += f"Your current flexible budget balance is €{cumulative_flexible_balance:.2f}.\n"
                if remaining_days_forecast > 0:
                    report += f"You can now spend up to €{new_daily_spending_target:.2f} each day for the remaining {remaining_days_forecast} days.\n\n"
                    report += f"Here's how we calculated your new recommended daily budget:\n"
                    report += f"  New Daily Target = Remaining Flexible Budget / Remaining Days\n"
                    report += f"                   €{new_daily_spending_target:>10.2f} = €{cumulative_flexible_balance:>10.2f} / {remaining_days_forecast}\n"
                else: # today is the last day of the month
                    report += f"Today is the last day of the month. You have €{new_daily_spending_target:.2f} left to spend.\n"
                report += f"{'-'*80}\n"

        self.budget_text.delete(1.0, tk.END)
        self.budget_text.insert(1.0, report)

def main():
    root = tk.Tk()
    app = FinanceTracker(root)
    root.mainloop()


if __name__ == "__main__":
    main()