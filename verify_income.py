from finance_tracker.state import AppState
from finance_tracker.services.budget_calculator import compute_net_available_for_spending, get_active_monthly_income
from pathlib import Path
import json
import os
import shutil

TEST_FILE = "test_finance_data.json"

def test_migration_and_calculation():
    # 1. Setup legacy data
    data = {
        "budget_settings": {
            "monthly_income": 3000.0,
            "fixed_costs": []
        },
        "expenses": [],
        "incomes": []
    }
    with open(TEST_FILE, "w") as f:
        json.dump(data, f)
    
    print("--- Testing Migration ---")
    state = AppState(Path(TEST_FILE))
    # Check if migrated
    income_data = state.budget_settings.get("monthly_income")
    print(f"Migrated Income Data: {income_data}")
    
    if isinstance(income_data, list) and len(income_data) == 1:
        print("PASS: Migration to list successful.")
        if income_data[0]['amount'] == 3000.0 and income_data[0]['start_date'] == '2000-01-01':
            print("PASS: Migration values correct.")
        else:
            print("FAIL: Migration values incorrect.")
    else:
        print("FAIL: Migration to list failed. Logic is: " + str(type(income_data)))

    print("\n--- Testing Calculation (Current Month) ---")
    current_inc = get_active_monthly_income(state, "2025-01")
    print(f"Active Income for 2025-01: {current_inc}")
    if current_inc == 3000.0:
        print("PASS: Current calculation correct.")
    else:
        print(f"FAIL: Expected 3000.0, got {current_inc}")

    print("\n--- Testing Future Income Change ---")
    # Add a raise starting next month
    new_income = {
        "description": "Raise",
        "amount": 500.0,
        "start_date": "2025-02-01",
        "end_date": None
    }
    state.budget_settings["monthly_income"].append(new_income)
    
    inc_jan = get_active_monthly_income(state, "2025-01")
    inc_feb = get_active_monthly_income(state, "2025-02")
    
    print(f"Active Income Jan 2025: {inc_jan}")
    print(f"Active Income Feb 2025: {inc_feb}")
    
    if inc_jan == 3000.0:
        print("PASS: Jan income unaffected by future raise.")
    else:
        print(f"FAIL: Jan income incorrect. Got {inc_jan}")

    if inc_feb == 3500.0:
        print("PASS: Feb income includes raise.")
    else:
        print(f"FAIL: Feb income incorrect. Expected 3500.0, got {inc_feb}")

    # Test Mid-Month Start
    print("\n--- Testing Mid-Month Start ---")
    mid_month_income = {
        "description": "Mid Month Job",
        "amount": 2000.0,
        "start_date": "2026-01-15",
        "end_date": None
    }
    state.budget_settings["monthly_income"].append(mid_month_income)
    
    # Check 2026-01
    inc_2026_01 = get_active_monthly_income(state, "2026-01")
    print(f"Active Income Jan 2026 (Should include previous + mid-month): {inc_2026_01}")
    
    # Previous was 3000 (base) + 500 (raise in Feb 2025) = 3500?
    # Wait, in the script above:
    # Base: 3000 (start 2000-01-01)
    # Raise: 500 (start 2025-02-01)
    # MidMonth: 2000 (start 2026-01-15)
    # Total for 2026-01 should be 3000 + 500 + 2000 = 5500.
    
    if inc_2026_01 == 5500.0:
        print("PASS: Mid-month income included.")
    else:
        print(f"FAIL: Expected 5500.0, got {inc_2026_01}")

    # Cleanup
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)

if __name__ == "__main__":
    test_migration_and_calculation()
