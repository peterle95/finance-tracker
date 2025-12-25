
import sys
import os
from datetime import date, datetime

# Add project root to path
sys.path.append(os.getcwd())

from finance_tracker.services.report_builder import history_data

class MockState:
    def __init__(self):
        self.expenses = [
            {'date': datetime.now().strftime("%Y-%m-%d"), 'amount': 200, 'category': 'Food'},
            {'date': datetime.now().strftime("%Y-%m-%d"), 'amount': 300, 'category': 'Fun'}
        ]
        self.incomes = [
            {'date': datetime.now().strftime("%Y-%m-%d"), 'amount': 1000, 'category': 'Salary'}
        ]
        self.budget_settings = {
            'fixed_costs': [{'amount': 500}],
            'monthly_income': 2000
        }

def test_history_data():
    state = MockState()
    
    print("Testing Relation Chart Logic...")
    title, labels, values, annotations = history_data(state, 1, "Relation", False, False)
    
    print(f"Title: {title}")
    print(f"Labels: {labels}")
    print(f"Values: {values}")
    print(f"Annotations: {annotations}")
    
    # Check last month (index -1)
    # Flex Costs = 200 + 300 = 500
    # Flex Income = 1000
    # Expected Ratio = (500/1000)*100 = 50.0
    # Expected Annotation = "€500 / €1000"
    
    last_value = values[-1]
    last_annotation = annotations[-1]
    
    print(f"Last Value: {last_value}")
    print(f"Last Annotation: '{last_annotation}'")
    
    assert last_value == 50.0
    assert last_annotation == "€500 / €1000"
    
    print("Verification Passed!")

if __name__ == "__main__":
    test_history_data()
