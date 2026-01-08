"""
finance_tracker/state.py

Manages the application state, including data loading, saving, and transaction management.
"""

from pathlib import Path
from datetime import datetime
import json

DEFAULT_EXPENSE_CATEGORIES = [
    "Food", "Transportation", "Entertainment", "Utilities",
    "Shopping", "Healthcare", "Money Lent", "Other"
]
DEFAULT_INCOME_CATEGORIES = ["Salary", "Side Gig", "Bonus", "Gift", "Investment", "Other"]

class AppState:
    def __init__(self, data_file: Path = Path("finance_data.json")):
        self.data_file = data_file
        self.expenses = []
        self.incomes = []
        self.budget_settings = {}
        self.categories = {}
        self.load()

    def load(self):
        if self.data_file.exists():
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        self.expenses = data.get("expenses", [])
        self.incomes = data.get("incomes", [])
        self.budget_settings = data.get("budget_settings", {})
        self.categories = data.get("categories", {})

        # Ensure defaults
        bs = self.budget_settings
        bs.setdefault("fixed_costs", [])
        bs.setdefault("fixed_costs", [])
        
        # KEY CHANGE: "monthly_income" might be a float (old) or a list (new)
        # We want to normalize it to a list of dicts: 
        # [{"amount": float, "description": str, "start_date": str, "end_date": str|None}]
        current_income = bs.get("monthly_income")
        if current_income is None:
            # Default to empty list if not present
            bs["monthly_income"] = []
        elif isinstance(current_income, (int, float)):
            # MIgrate old single value to list
            if current_income > 0:
                bs["monthly_income"] = [{
                    "amount": float(current_income),
                    "description": "Base Income",
                    "start_date": "2025-01-01",
                    "end_date": None
                }]
            else:
                bs["monthly_income"] = []
        # else: it's already a list (hopefully), or we assume it is correct
            
        bs.setdefault("bank_account_balance", 0)
        bs.setdefault("savings_balance", 0)
        bs.setdefault("investment_balance", 0)
        bs.setdefault("wallet_balance", 0)
        bs.setdefault("daily_savings_goal", 0)
        bs.setdefault("money_lent_balance", 0)
        bs.setdefault("category_budgets", {"Expense": {}, "Income": {}})
        bs.setdefault("loans", [])  # Each loan: {"id": str, "borrower": str, "amount": float, "description": str, "date": str}

        # Migrate fixed costs to include start_date and end_date
        for fc in bs.get("fixed_costs", []):
            if 'start_date' not in fc:
                fc['start_date'] = '2000-01-01'  # Default to a very early date for existing costs
            if 'end_date' not in fc:
                fc['end_date'] = None  # None means still active
        
        if "Expense" not in self.categories or not self.categories["Expense"]:
            self.categories["Expense"] = DEFAULT_EXPENSE_CATEGORIES.copy()
        if "Income" not in self.categories or not self.categories["Income"]:
            self.categories["Income"] = DEFAULT_INCOME_CATEGORIES.copy()

    def save(self):
        data = {
            "expenses": self.expenses,
            "incomes": self.incomes,
            "budget_settings": self.budget_settings,
            "categories": self.categories,
        }
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def add_transaction(self, trans_type: str, date_str: str, amount: float, category: str, description: str):
        trans_id = f"{datetime.now().timestamp()}"
        record = {"id": trans_id, "date": date_str, "amount": amount, "category": category, "description": description}
        if trans_type == "Expense":
            self.expenses.append(record)
        else:
            self.incomes.append(record)
        self.save()

    def delete_transaction_by_id(self, trans_type: str, trans_id: str) -> bool:
        target = self.expenses if trans_type == "Expense" else self.incomes
        for i, t in enumerate(target):
            if t.get("id") == trans_id:
                del target[i]
                self.save()
                return True
        return False