
import sys
import os
from datetime import datetime
import calendar
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Mocking the simplified environment for testing create_budget_depletion_figure logic
class MockState:
    def __init__(self):
        self.budget_settings = {"daily_savings_goal": 0}
        self.incomes = []
        self.expenses = []

# Mock services that charts.py depends on
def get_active_monthly_income(state, month_str):
    return 1000

def get_active_fixed_costs(state, month_str):
    return []

# Inject mocks into the namespace where charts.py would import them
# This is a bit hacky but avoids needing the full project structure for a unit-like test
import finance_tracker.ui.charts as charts
charts.get_active_monthly_income = get_active_monthly_income
charts.get_active_fixed_costs = get_active_fixed_costs

def verify():
    state = MockState()
    month_str = "2026-02"
    
    # We want to test the case where today is the first of the month
    # But since the code uses datetime.now(), we might have to monkeypatch datetime or trust the logic
    # Actually, the loop uses 'day in range(1, days_in_month + 1)' and 'if date_obj > today: break'
    
    # Let's run the figure generation
    fig = charts.create_budget_depletion_figure(state, month_str)
    ax = fig.get_axes()[0]
    
    xlim = ax.get_xlim()
    print(f"X-axis limits: {xlim}")
    
    start_date = mdates.num2date(xlim[0]).date()
    end_date = mdates.num2date(xlim[1]).date()
    
    print(f"X-axis dates: {start_date} to {end_date}")
    
    expected_start = datetime(2026, 2, 1).date()
    expected_end = datetime(2026, 2, 28).date()
    
    assert start_date == expected_start, f"Expected {expected_start}, got {start_date}"
    assert end_date == expected_end, f"Expected {expected_end}, got {end_date}"
    
    # Check ticks
    major_ticks = ax.xaxis.get_majorticklocs()
    print(f"Number of major ticks: {len(major_ticks)}")
    assert len(major_ticks) <= 31, f"Too many ticks: {len(major_ticks)}"
    
    print("Verification SUCCESSFUL")

if __name__ == "__main__":
    # Add project root to path
    sys.path.append(os.getcwd())
    verify()
