import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime, timedelta
from pathlib import Path
import calendar

class FinanceTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Finance Tracker")
        self.root.geometry("1000x700")

        # Data file
        self.data_file = Path("finance_data_v2.json")
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

    def load_data(self):
        """Load data from JSON file or create new structure"""
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.expenses = data.get('expenses', [])
                self.incomes = data.get('incomes', [])
                # Ensure backward compatibility and new structure
                self.budget_settings = data.get('budget_settings', {})
                if 'fixed_costs' not in self.budget_settings:
                    self.budget_settings['fixed_costs'] = []
                if 'monthly_income' not in self.budget_settings:
                    self.budget_settings['monthly_income'] = 0
        else:
            self.expenses = []
            self.incomes = []
            self.budget_settings = {'monthly_income': 0, 'fixed_costs': []}

    def save_data(self):
        """Save data to JSON file"""
        data = {
            'expenses': self.expenses,
            'incomes': self.incomes,
            'budget_settings': self.budget_settings
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

        self.budget_tab = ttk.Frame(notebook)
        notebook.add(self.budget_tab, text="Budget & Settings")
        self.create_budget_tab()

    def create_add_transaction_tab(self):
        """Create the add transaction form for both expenses and income"""
        frame = ttk.Frame(self.add_transaction_tab, padding="20")
        frame.pack(fill='both', expand=True)

        # Transaction Type
        ttk.Label(frame, text="Transaction Type:").grid(row=0, column=0, sticky='w', pady=10)
        self.transaction_type_var = tk.StringVar(value="Expense")
        type_frame = ttk.Frame(frame)
        type_frame.grid(row=0, column=1, sticky='w', pady=5)
        ttk.Radiobutton(type_frame, text="Expense", variable=self.transaction_type_var,
                        value="Expense", command=self.update_categories).pack(side='left', padx=5)
        ttk.Radiobutton(type_frame, text="Income", variable=self.transaction_type_var,
                        value="Income", command=self.update_categories).pack(side='left', padx=5)

        # Date
        ttk.Label(frame, text="Date:").grid(row=1, column=0, sticky='w', pady=5)
        self.date_entry = ttk.Entry(frame, width=30)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=1, column=1, pady=5)
        ttk.Label(frame, text="(YYYY-MM-DD)", foreground="gray").grid(row=1, column=2, sticky='w', padx=5)

        # Amount
        ttk.Label(frame, text="Amount:").grid(row=2, column=0, sticky='w', pady=5)
        self.amount_entry = ttk.Entry(frame, width=30)
        self.amount_entry.grid(row=2, column=1, pady=5)

        # Category
        ttk.Label(frame, text="Category:").grid(row=3, column=0, sticky='w', pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(frame, textvariable=self.category_var, width=28, state='readonly')
        self.category_combo.grid(row=3, column=1, pady=5)
        self.update_categories() # Initial population

        # Description
        ttk.Label(frame, text="Description:").grid(row=4, column=0, sticky='w', pady=5)
        self.description_entry = ttk.Entry(frame, width=30)
        self.description_entry.grid(row=4, column=1, pady=5)

        # Add button
        ttk.Button(frame, text="Add Transaction", command=self.add_transaction).grid(
            row=5, column=1, pady=20, sticky='w')

    def update_categories(self):
        """Updates the category combobox based on transaction type"""
        transaction_type = self.transaction_type_var.get()
        if transaction_type == "Expense":
            categories = ["Food", "Transportation", "Entertainment", "Utilities", "Shopping", "Healthcare", "Other"]
            self.category_combo.config(values=categories)
            self.category_combo.set("Food")
        else: # Income
            categories = ["Salary", "Side Gig", "Bonus", "Gift", "Investment", "Other"]
            self.category_combo.config(values=categories)
            self.category_combo.set("Side Gig")

    def create_view_transactions_tab(self):
        """Create the view transactions list for expenses and income"""
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
        """Create the daily budget and settings tab"""
        main_frame = ttk.Frame(self.budget_tab, padding="10")
        main_frame.pack(fill='both', expand=True)

        # Top frame for settings and fixed costs
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill='x', pady=(0, 10))

        # --- Settings Frame ---
        settings_frame = ttk.LabelFrame(top_frame, text="Monthly Settings", padding="10")
        settings_frame.pack(side='left', fill='y', padx=(0, 10), anchor='n')

        ttk.Label(settings_frame, text="Base Monthly Income:").grid(row=0, column=0, sticky='w', pady=5)
        self.income_entry = ttk.Entry(settings_frame, width=15)
        self.income_entry.grid(row=0, column=1, pady=5)
        if 'monthly_income' in self.budget_settings:
            self.income_entry.insert(0, str(self.budget_settings['monthly_income']))

        ttk.Button(settings_frame, text="Save Income", command=self.save_base_income).grid(
            row=1, column=1, pady=10, sticky='e')

        # --- Fixed Costs Frame ---
        fixed_costs_frame = ttk.LabelFrame(top_frame, text="Manage Fixed Monthly Costs", padding="10")
        fixed_costs_frame.pack(side='left', fill='both', expand=True)

        # Treeview for fixed costs
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
        
        # Entry form for new/updated fixed costs
        fc_form_frame = ttk.Frame(fixed_costs_frame)
        fc_form_frame.pack(fill='x', pady=10)
        ttk.Label(fc_form_frame, text="Desc:").pack(side='left', padx=(0,5))
        self.fc_desc_entry = ttk.Entry(fc_form_frame, width=20)
        self.fc_desc_entry.pack(side='left')
        ttk.Label(fc_form_frame, text="Amount:").pack(side='left', padx=(10,5))
        self.fc_amount_entry = ttk.Entry(fc_form_frame, width=10)
        self.fc_amount_entry.pack(side='left')
        
        fc_btn_frame = ttk.Frame(fixed_costs_frame)
        fc_btn_frame.pack(fill='x')
        ttk.Button(fc_btn_frame, text="Add", command=self.add_fixed_cost).pack(side='left', padx=5)
        ttk.Button(fc_btn_frame, text="Update Selected", command=self.update_fixed_cost).pack(side='left', padx=5)
        ttk.Button(fc_btn_frame, text="Delete Selected", command=self.delete_fixed_cost).pack(side='left', padx=5)


        # --- Report Generation Frame ---
        report_frame = ttk.LabelFrame(main_frame, text="Daily Budget Report", padding="10")
        report_frame.pack(fill='both', expand=True)

        month_frame = ttk.Frame(report_frame)
        month_frame.pack(fill='x', pady=5)
        ttk.Label(month_frame, text="Select Month:").pack(side='left', padx=5)
        self.budget_month = ttk.Entry(month_frame, width=15)
        self.budget_month.insert(0, datetime.now().strftime("%Y-%m"))
        self.budget_month.pack(side='left', padx=5)
        ttk.Button(month_frame, text="Generate Report", command=self.generate_daily_budget).pack(side='left', padx=10)

        self.budget_text = tk.Text(report_frame, height=20, width=90, font=('Courier New', 9))
        self.budget_text.pack(fill='both', expand=True, pady=10)

    def add_transaction(self):
        """Add a new expense or income"""
        try:
            date = self.date_entry.get()
            datetime.strptime(date, "%Y-%m-%d") # Validate date
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
            else: # Income
                self.incomes.append(transaction)
            
            self.save_data()

            self.amount_entry.delete(0, tk.END)
            self.description_entry.delete(0, tk.END)
            messagebox.showinfo("Success", f"{trans_type} added successfully!")
            self.refresh_transaction_list()
        except ValueError:
            messagebox.showerror("Error", "Invalid amount or date format (YYYY-MM-DD).")

    def refresh_transaction_list(self):
        """Refresh the transaction list view with both incomes and expenses"""
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

        # Sort by date
        all_transactions.sort(key=lambda x: x['date'])

        for trans in all_transactions:
            tag = 'expense' if trans['type'] == 'Expense' else 'income'
            self.transaction_tree.insert('', 'end', values=(
                trans['date'], trans['type'], f"€{trans['amount']:.2f}",
                trans['category'], trans['description']), tags=(tag,))
        
        self.update_summary()

    def update_summary(self):
        """Update summary statistics for the filtered month"""
        filter_month = self.month_filter.get()

        # Get base income from settings, default to 0 if not set
        base_income = self.budget_settings.get('monthly_income', 0)
        
        # Calculate flexible income (from transactions) for the month
        monthly_flexible_incomes = [i['amount'] for i in self.incomes if i['date'].startswith(filter_month)]
        total_flexible_income = sum(monthly_flexible_incomes)
        
        # Total income is base + flexible
        total_income = base_income + total_flexible_income

        # Calculate expenses for the month
        monthly_expenses = [e['amount'] for e in self.expenses if e['date'].startswith(filter_month)]
        total_expenses = sum(monthly_expenses)
        
        # Calculate net result
        net = total_income - total_expenses
        
        summary_text = (f"Total Income: €{total_income:.2f}  |  "
                        f"Total Expenses: €{total_expenses:.2f}  |  "
                        f"Net: €{net:.2f}")
        self.summary_label.config(text=summary_text)


    def delete_transaction(self):
        """Delete selected transaction"""
        selected_item = self.transaction_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a transaction to delete.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete the selected transaction?"):
            item = self.transaction_tree.item(selected_item[0])
            values = item['values']
            date, trans_type, amount_str, category, desc = values

            # Recreate the dictionary to find and remove
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

    def save_base_income(self):
        """Save just the base monthly income"""
        try:
            income = float(self.income_entry.get()) if self.income_entry.get() else 0
            self.budget_settings['monthly_income'] = income
            self.save_data()
            messagebox.showinfo("Success", "Base monthly income saved!")
        except ValueError:
            messagebox.showerror("Error", "Invalid income amount.")
    
    def refresh_fixed_costs_tree(self):
        """Populate the fixed costs treeview"""
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

            # Find the original item to update it
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

    def generate_daily_budget(self):
        """Generate daily budget report based on all settings and transactions"""
        month_str = self.budget_month.get()
        try:
            year, month = map(int, month_str.split('-'))
        except ValueError:
            messagebox.showerror("Error", "Invalid month format. Use YYYY-MM.")
            return

        base_income = self.budget_settings.get('monthly_income', 0)
        flex_income_month = sum(i['amount'] for i in self.incomes if i['date'].startswith(month_str))
        total_income = base_income + flex_income_month

        fixed_costs = sum(fc['amount'] for fc in self.budget_settings.get('fixed_costs', []))
        days_in_month = calendar.monthrange(year, month)[1]
        
        flexible_budget = total_income - fixed_costs
        if days_in_month == 0:
             messagebox.showerror("Error", "Cannot divide by zero days in month.")
             return
        base_daily_budget = flexible_budget / days_in_month
        
        flex_expenses_month = [e for e in self.expenses if e['date'].startswith(month_str)]
        
        daily_expenses = {}
        for expense in flex_expenses_month:
            date = expense['date']
            daily_expenses.setdefault(date, []).append(expense)

        report = f"{'='*80}\n"
        report += f"DAILY BUDGET REPORT - {calendar.month_name[month]} {year}\n"
        report += f"{'='*80}\n\n"
        report += f"Base Monthly Income:       €{base_income:>10.2f}\n"
        report += f"Flexible Income (Month):   €{flex_income_month:>10.2f}\n"
        report += f"TOTAL INCOME:              €{total_income:>10.2f}\n"
        report += f"Total Fixed Costs:        -€{fixed_costs:>10.2f}\n"
        report += f"{'-'*35}\n"
        report += f"Available for Spending:    €{flexible_budget:>10.2f}\n"
        report += f"Base Daily Budget:         €{base_daily_budget:>10.2f} (for {days_in_month} days)\n"
        report += f"{'-'*80}\n\n"

        report += f"DAILY BREAKDOWN\n"
        report += f"{'-'*80}\n"
        report += f"{'Date':<12} {'Budget':<12} {'Spent':<12} {'Saved':<12} {'Cumulative':<12} {'Status'}\n"
        report += f"{'-'*80}\n"

        cumulative_savings = 0
        today = datetime.now().date()
        
        for day in range(1, days_in_month + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Stop report for future days in the current month
            if date_obj > today:
                break
            
            remaining_days = days_in_month - day
            
            # Adjusted budget spreads cumulative savings over remaining days
            if remaining_days > 0:
                adjusted_budget = base_daily_budget + (cumulative_savings / (remaining_days + 1))
            else:
                adjusted_budget = base_daily_budget + cumulative_savings

            day_total_spent = sum(e['amount'] for e in daily_expenses.get(date_str, []))
            day_savings = adjusted_budget - day_total_spent
            cumulative_savings += day_savings

            status = "✓ Under" if day_savings > 0 else ("✗ Over" if day_savings < 0 else "✓ Exact")
            if day_total_spent == 0: status = "- No spending"

            report += (f"{date_str:<12} €{adjusted_budget:<10.2f} €{day_total_spent:<10.2f} "
                       f"€{day_savings:<10.2f} €{cumulative_savings:<10.2f} {status}\n")

        report += f"{'-'*80}\n\n"
        
        # Forecast for remaining days of the current month
        if today.year == year and today.month == month and today.day < days_in_month:
            remaining_days_forecast = days_in_month - today.day
            if remaining_days_forecast > 0:
                future_daily_budget = base_daily_budget + (cumulative_savings / remaining_days_forecast)
                report += f"FORECAST FOR REMAINING {remaining_days_forecast} DAYS\n"
                report += f"{'-'*80}\n"
                report += f"Your new recommended daily budget is: €{future_daily_budget:.2f}\n"
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