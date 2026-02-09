
from datetime import datetime
import calendar
from collections import namedtuple

# Mocking the state
class MockState:
    def __init__(self):
        self.budget_settings = {
            "monthly_income": 0, # Will mock the function return instead
            "daily_savings_goal": 0,
            "fixed_costs": []
        }
        self.incomes = []
        self.expenses = []

# Mock functions to isolate the logic
# We can't easily mock the internal functions of the module if we import the function directly.
# So I will copy the relevant parts of the function or monkeypatch the helper functions.

import finance_tracker.services.budget_calculator as bc

# Setup the specific scenario
# Date: 2026-02-09
# Income: Need enough to have 34.23 remaining on day 9.
# Month: 2026-02
# Days in month: 28
# Total days: 28.
# Target: 1.71. 34.23 / 20 = 1.7115.

# Let's set a base income such that the flexible budget corresponds to the user's situation.
# Initial daily target: 34.23? No.
# If remaining is 34.23 on day 9.
# And spent is 0 in the table.
# It means cumulative balance is 34.23.
# The table shows previous days too. The user screenshot cuts them off.
# Assume day 1-8 had spending or income such that day 9 starts with ~34.23.
# Or simpler:
# Base income = 34.23 * (28/20)? No.

# Let's just monkeypatch the helper functions to return simple values
# and set the state such that we hit the condition.

def mock_get_active_monthly_income(state, month_str):
    return 1000.0 # Arbitrary

bc.get_active_monthly_income = mock_get_active_monthly_income

def mock_get_active_fixed_costs(state, month_str):
    return []

bc.get_active_fixed_costs = mock_get_active_fixed_costs

# We need to control 'today'.
# The module uses datetime.now().date().
# We can mock datetime in the module?
# Or just mock the today variable inside the function? 
# We can't modify the local variable `today` inside the function from outside.
# We have to mock `datetime.now`.

from unittest.mock import MagicMock
import sys
from datetime import date

# Create a mock datetime class
class MockDate(date):
    @classmethod
    def today(cls):
        return cls(2026, 2, 9)

    @classmethod
    def now(cls):
        return cls(2026, 2, 9)

# We need to patch datetime in the budget_calculator module
bc.dt = MagicMock()
bc.dt.now.return_value = datetime(2026, 2, 9, 12, 0, 0)
bc.dt.strptime = datetime.strptime

# Wait, line 162: today = dt.now().date()
# line 142: from datetime import datetime as dt, date as ddate

# So we need to patch `bc.dt` (which is datetime.datetime)

# Let's setup the state so that `monthly_flexible_spending_budget` results in the desired residual.
# formula: base_income - fixed_costs - monthly_savings_goal
# 1000 - 0 - 0 = 1000.

# We want `cumulative_flexible_balance` to be 34.23 on day 9.
# We can add expenses on days 1-8 to bring it down.
# 1000 - expenses = 34.23 => expenses = 965.77
# Put this expense on day 1.

state = MockState()
state.expenses = [
    {"date": "2026-02-01", "amount": 965.77, "category": "Test"}
]

# Run the report
report = bc.generate_daily_budget_report(state, "2026-02")

print(report)

