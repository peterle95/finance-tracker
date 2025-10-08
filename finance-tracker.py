import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime
from pathlib import Path

class FinanceTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Finance Tracker")
        self.root.geometry("900x600")
        
        # Data file
        self.data_file = Path("finance_data.json")
        self.load_data()
        
        # Create UI
        self.create_widgets()
        self.refresh_expense_list()
        self.update_summary()
    
    def load_data(self):
        """Load data from JSON file or create new structure"""
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.expenses = data.get('expenses', [])
                self.budget_settings = data.get('budget_settings', {})
        else:
            self.expenses = []
            self.budget_settings = {}
    
    def save_data(self):
        """Save data to JSON file"""
        data = {
            'expenses': self.expenses,
            'budget_settings': self.budget_settings
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_widgets(self):
        """Create all UI elements"""
        # Create notebook (tabs)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Add Expense
        self.add_expense_tab = ttk.Frame(notebook)
        notebook.add(self.add_expense_tab, text="Add Expense")
        self.create_add_expense_tab()
        
        # Tab 2: View Expenses
        self.view_expenses_tab = ttk.Frame(notebook)
        notebook.add(self.view_expenses_tab, text="View Expenses")
        self.create_view_expenses_tab()
        
        # Tab 3: Monthly Budget
        self.budget_tab = ttk.Frame(notebook)
        notebook.add(self.budget_tab, text="Monthly Budget")
        self.create_budget_tab()
    
    def create_add_expense_tab(self):
        """Create the add expense form"""
        frame = ttk.Frame(self.add_expense_tab, padding="20")
        frame.pack(fill='both', expand=True)
        
        # Date
        ttk.Label(frame, text="Date:").grid(row=0, column=0, sticky='w', pady=5)
        self.date_entry = ttk.Entry(frame, width=30)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=0, column=1, pady=5)
        ttk.Label(frame, text="(YYYY-MM-DD)", foreground="gray").grid(row=0, column=2, sticky='w', padx=5)
        
        # Amount
        ttk.Label(frame, text="Amount:").grid(row=1, column=0, sticky='w', pady=5)
        self.amount_entry = ttk.Entry(frame, width=30)
        self.amount_entry.grid(row=1, column=1, pady=5)
        
        # Category
        ttk.Label(frame, text="Category:").grid(row=2, column=0, sticky='w', pady=5)
        self.category_var = tk.StringVar()
        categories = ["Housing", "Transportation", "Food", "Utilities", "Entertainment", 
                     "Healthcare", "Insurance", "Savings", "Other"]
        self.category_combo = ttk.Combobox(frame, textvariable=self.category_var, 
                                          values=categories, width=28, state='readonly')
        self.category_combo.grid(row=2, column=1, pady=5)
        self.category_combo.set("Food")
        
        # Type (Fixed/Flexible)
        ttk.Label(frame, text="Type:").grid(row=3, column=0, sticky='w', pady=5)
        self.type_var = tk.StringVar(value="flexible")
        type_frame = ttk.Frame(frame)
        type_frame.grid(row=3, column=1, sticky='w', pady=5)
        ttk.Radiobutton(type_frame, text="Fixed Cost", variable=self.type_var, 
                       value="fixed").pack(side='left', padx=5)
        ttk.Radiobutton(type_frame, text="Flexible Cost", variable=self.type_var, 
                       value="flexible").pack(side='left', padx=5)
        
        # Description
        ttk.Label(frame, text="Description:").grid(row=4, column=0, sticky='w', pady=5)
        self.description_entry = ttk.Entry(frame, width=30)
        self.description_entry.grid(row=4, column=1, pady=5)
        
        # Add button
        ttk.Button(frame, text="Add Expense", command=self.add_expense).grid(
            row=5, column=1, pady=20, sticky='w')
        
        # Info labels
        ttk.Label(frame, text="Fixed Costs: Rent, subscriptions, insurance", 
                 foreground="gray").grid(row=6, column=0, columnspan=3, sticky='w', pady=2)
        ttk.Label(frame, text="Flexible Costs: Food, entertainment, shopping", 
                 foreground="gray").grid(row=7, column=0, columnspan=3, sticky='w')
    
    def create_view_expenses_tab(self):
        """Create the view expenses list"""
        frame = ttk.Frame(self.view_expenses_tab, padding="20")
        frame.pack(fill='both', expand=True)
        
        # Filter by month
        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill='x', pady=10)
        
        ttk.Label(filter_frame, text="Filter by month:").pack(side='left', padx=5)
        self.month_filter = ttk.Entry(filter_frame, width=15)
        self.month_filter.insert(0, datetime.now().strftime("%Y-%m"))
        self.month_filter.pack(side='left', padx=5)
        ttk.Label(filter_frame, text="(YYYY-MM)").pack(side='left')
        ttk.Button(filter_frame, text="Refresh", command=self.refresh_expense_list).pack(
            side='left', padx=10)
        
        # Treeview for expenses
        columns = ('Date', 'Amount', 'Category', 'Type', 'Description')
        self.expense_tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)
        
        # Define headings
        for col in columns:
            self.expense_tree.heading(col, text=col)
            if col == 'Amount':
                self.expense_tree.column(col, width=100)
            elif col == 'Description':
                self.expense_tree.column(col, width=200)
            else:
                self.expense_tree.column(col, width=120)
        
        self.expense_tree.pack(fill='both', expand=True, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.expense_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.expense_tree.configure(yscrollcommand=scrollbar.set)
        
        # Delete button
        ttk.Button(frame, text="Delete Selected", command=self.delete_expense).pack(pady=5)
        
        # Summary labels
        self.summary_label = ttk.Label(frame, text="", font=('Arial', 10, 'bold'))
        self.summary_label.pack(pady=10)
    
    def create_budget_tab(self):
        """Create the budget overview tab"""
        frame = ttk.Frame(self.budget_tab, padding="20")
        frame.pack(fill='both', expand=True)
        
        # Month selector
        month_frame = ttk.Frame(frame)
        month_frame.pack(fill='x', pady=10)
        
        ttk.Label(month_frame, text="Select Month:").pack(side='left', padx=5)
        self.budget_month = ttk.Entry(month_frame, width=15)
        self.budget_month.insert(0, datetime.now().strftime("%Y-%m"))
        self.budget_month.pack(side='left', padx=5)
        ttk.Button(month_frame, text="Generate Budget", 
                  command=self.generate_budget).pack(side='left', padx=10)
        
        # Budget display
        self.budget_text = tk.Text(frame, height=20, width=80, font=('Courier', 10))
        self.budget_text.pack(fill='both', expand=True, pady=10)
        
        # Set monthly income
        income_frame = ttk.Frame(frame)
        income_frame.pack(fill='x', pady=10)
        
        ttk.Label(income_frame, text="Monthly Income:").pack(side='left', padx=5)
        self.income_entry = ttk.Entry(income_frame, width=15)
        self.income_entry.pack(side='left', padx=5)
        ttk.Button(income_frame, text="Save Income", 
                  command=self.save_income).pack(side='left', padx=10)
        
        # Load saved income
        if 'monthly_income' in self.budget_settings:
            self.income_entry.insert(0, str(self.budget_settings['monthly_income']))
    
    def add_expense(self):
        """Add a new expense"""
        try:
            date = self.date_entry.get()
            amount = float(self.amount_entry.get())
            category = self.category_var.get()
            expense_type = self.type_var.get()
            description = self.description_entry.get()
            
            if not category:
                messagebox.showerror("Error", "Please select a category")
                return
            
            # Validate date format
            datetime.strptime(date, "%Y-%m-%d")
            
            expense = {
                'date': date,
                'amount': amount,
                'category': category,
                'type': expense_type,
                'description': description
            }
            
            self.expenses.append(expense)
            self.save_data()
            
            # Clear form
            self.amount_entry.delete(0, tk.END)
            self.description_entry.delete(0, tk.END)
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
            
            messagebox.showinfo("Success", "Expense added successfully!")
            self.refresh_expense_list()
            
        except ValueError as e:
            messagebox.showerror("Error", "Invalid amount or date format")
    
    def refresh_expense_list(self):
        """Refresh the expense list view"""
        # Clear existing items
        for item in self.expense_tree.get_children():
            self.expense_tree.delete(item)
        
        # Get filter month
        filter_month = self.month_filter.get()
        
        # Add filtered expenses
        filtered_expenses = [e for e in self.expenses if e['date'].startswith(filter_month)]
        
        for expense in filtered_expenses:
            self.expense_tree.insert('', 'end', values=(
                expense['date'],
                f"${expense['amount']:.2f}",
                expense['category'],
                expense['type'].capitalize(),
                expense['description']
            ))
        
        self.update_summary()
    
    def update_summary(self):
        """Update summary statistics"""
        filter_month = self.month_filter.get()
        filtered_expenses = [e for e in self.expenses if e['date'].startswith(filter_month)]
        
        total = sum(e['amount'] for e in filtered_expenses)
        fixed = sum(e['amount'] for e in filtered_expenses if e['type'] == 'fixed')
        flexible = sum(e['amount'] for e in filtered_expenses if e['type'] == 'flexible')
        
        summary_text = f"Total: ${total:.2f}  |  Fixed: ${fixed:.2f}  |  Flexible: ${flexible:.2f}"
        self.summary_label.config(text=summary_text)
    
    def delete_expense(self):
        """Delete selected expense"""
        selected = self.expense_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an expense to delete")
            return
        
        if messagebox.askyesno("Confirm", "Delete selected expense?"):
            item = self.expense_tree.item(selected[0])
            values = item['values']
            
            # Find and remove the expense
            for expense in self.expenses:
                if (expense['date'] == values[0] and 
                    f"${expense['amount']:.2f}" == values[1] and
                    expense['category'] == values[2]):
                    self.expenses.remove(expense)
                    break
            
            self.save_data()
            self.refresh_expense_list()
    
    def save_income(self):
        """Save monthly income setting"""
        try:
            income = float(self.income_entry.get())
            self.budget_settings['monthly_income'] = income
            self.save_data()
            messagebox.showinfo("Success", "Monthly income saved!")
        except ValueError:
            messagebox.showerror("Error", "Invalid income amount")
    
    def generate_budget(self):
        """Generate monthly budget report"""
        month = self.budget_month.get()
        filtered_expenses = [e for e in self.expenses if e['date'].startswith(month)]
        
        # Calculate totals by category
        category_totals = {}
        for expense in filtered_expenses:
            cat = expense['category']
            category_totals[cat] = category_totals.get(cat, 0) + expense['amount']
        
        # Calculate fixed vs flexible
        fixed_total = sum(e['amount'] for e in filtered_expenses if e['type'] == 'fixed')
        flexible_total = sum(e['amount'] for e in filtered_expenses if e['type'] == 'flexible')
        total_expenses = fixed_total + flexible_total
        
        # Generate report
        report = f"{'='*60}\n"
        report += f"MONTHLY BUDGET REPORT - {month}\n"
        report += f"{'='*60}\n\n"
        
        if 'monthly_income' in self.budget_settings:
            income = self.budget_settings['monthly_income']
            report += f"Monthly Income:        ${income:>10.2f}\n"
            report += f"Total Expenses:        ${total_expenses:>10.2f}\n"
            report += f"Remaining:             ${income - total_expenses:>10.2f}\n"
            report += f"{'-'*60}\n\n"
        
        report += f"EXPENSE BREAKDOWN\n"
        report += f"{'-'*60}\n"
        report += f"Fixed Costs:           ${fixed_total:>10.2f}\n"
        report += f"Flexible Costs:        ${flexible_total:>10.2f}\n"
        report += f"{'-'*60}\n\n"
        
        report += f"BY CATEGORY\n"
        report += f"{'-'*60}\n"
        for category, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
            report += f"{category:<20} ${amount:>10.2f}  ({percentage:>5.1f}%)\n"
        
        report += f"{'='*60}\n"
        report += f"Total Expenses:        ${total_expenses:>10.2f}\n"
        
        # Display report
        self.budget_text.delete(1.0, tk.END)
        self.budget_text.insert(1.0, report)

def main():
    root = tk.Tk()
    app = FinanceTracker(root)
    root.mainloop()

if __name__ == "__main__":
    main()