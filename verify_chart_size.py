import matplotlib.pyplot as plt
import sys
import os
sys.path.append(os.getcwd())
from finance_tracker.ui.charts import create_budget_depletion_figure

class MockState:
    def __init__(self):
        self.budget_settings = {"daily_savings_goal": 5}
        self.incomes = []
        self.expenses = []

state = MockState()
try:
    fig = create_budget_depletion_figure(state, "2026-01")
    width, height = fig.get_size_inches()
    print(f"Figure size: {width}x{height}")
except Exception as e:
    print(f"Error: {e}")
