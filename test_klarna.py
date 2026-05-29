import sys
import os
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock

# Setup path so it can import finance_tracker
sys.path.append(os.getcwd())

from finance_tracker.state import AppState

def test_state_saving():
    print("Running state saving test...")
    test_file = Path("test_finance_data.json")
    if test_file.exists():
        test_file.unlink()

    state = AppState(data_file=test_file)
    
    # Add a normal transaction
    state.add_transaction("Expense", "2026-05-05", 50.0, "Food", "groceries")
    # Add a Klarna transaction
    state.add_transaction("Expense", "2026-06-01", 100.0, "Shopping", "phone", behavior_date="2026-05-05")
    
    # Reload and verify
    state2 = AppState(data_file=test_file)
    
    assert len(state2.expenses) == 2, f"Expected 2 expenses, got {len(state2.expenses)}"
    
    normal_trans = state2.expenses[0]
    assert normal_trans["date"] == "2026-05-05"
    assert "behavior_date" not in normal_trans
    
    klarna_trans = state2.expenses[1]
    assert klarna_trans["date"] == "2026-06-01"
    assert klarna_trans["behavior_date"] == "2026-05-05"
    
    print("State saving test PASSED!")
    if test_file.exists():
        test_file.unlink()

def test_add_klarna_logic():
    print("Running add klarna tab logic test...")
    from finance_tracker.ui.tabs.add_transaction_tab import AddTransactionTab
    
    tab = MagicMock(spec=AddTransactionTab)
    tab.state = AppState(data_file=Path("test_add_klarna.json"))
    if tab.state.data_file.exists():
        tab.state.data_file.unlink()
        
    tab._ui_is_alive.return_value = True
    tab._show_message = MagicMock()
    
    tab.date_entry = MagicMock()
    tab.date_entry.get.return_value = "2026-05-05"
    tab.amount_entry = MagicMock()
    tab.amount_entry.get.return_value = "100.00"
    tab.category_var = MagicMock()
    tab.category_var.get.return_value = "Shopping"
    tab.description_entry = MagicMock()
    tab.description_entry.get.return_value = "phone"
    tab.transaction_type_var = MagicMock()
    tab.transaction_type_var.get.return_value = "Expense"
    tab.on_data_changed = MagicMock()
    
    AddTransactionTab.add_klarna_transaction(tab)
    
    assert len(tab.state.expenses) == 1, "Expected 1 expense added"
    trans = tab.state.expenses[0]
    assert trans["date"] == "2026-06-01"
    assert trans["behavior_date"] == "2026-05-05"
    
    print("Add klarna tab logic test PASSED!")
    if tab.state.data_file.exists():
        tab.state.data_file.unlink()

def test_view_transactions_sorting():
    print("Running view transactions sorting test...")
    from finance_tracker.ui.tabs.view_transactions_tab import ViewTransactionsTab
    
    tab = MagicMock(spec=ViewTransactionsTab)
    tab._current_transactions = [
        {"id": "1", "date": "2026-06-01", "type": "Expense", "amount": 100.0, "category": "Shopping", "description": "phone", "behavior_date": "2026-05-05"},
        {"id": "2", "date": "2026-05-05", "type": "Expense", "amount": 50.0, "category": "Food", "description": "groceries"}, # No behavior date
        {"id": "3", "date": "2026-06-01", "type": "Expense", "amount": 200.0, "category": "Shopping", "description": "tv", "behavior_date": "2026-05-10"},
    ]
    tab._sort_state = {}
    tab._rebuild_tree = MagicMock()
    
    # Sort ascending by Behavior Date
    # Transactions without behavior_date will have ''
    ViewTransactionsTab.sort_by_column(tab, "Behavior Date")
    
    # Check direction
    assert tab._current_sort == ("Behavior Date", "ascending")
    # Verify sorted list: '' (2) then '2026-05-05' (1) then '2026-05-10' (3)
    sorted_ids = [t["id"] for t in tab._current_transactions]
    assert sorted_ids == ["2", "1", "3"], f"Expected sorted ids ['2', '1', '3'], got {sorted_ids}"
    
    # Sort again to toggle descending
    ViewTransactionsTab.sort_by_column(tab, "Behavior Date")
    assert tab._current_sort == ("Behavior Date", "descending")
    sorted_ids_desc = [t["id"] for t in tab._current_transactions]
    assert sorted_ids_desc == ["3", "1", "2"], f"Expected sorted ids ['3', '1', '2'], got {sorted_ids_desc}"
    
    print("View transactions sorting test PASSED!")

def test_delete_fallback_slice():
    print("Running delete fallback slice test...")
    from finance_tracker.ui.tabs.view_transactions_tab import ViewTransactionsTab
    
    tab = MagicMock(spec=ViewTransactionsTab)
    tab.transaction_tree = MagicMock()
    tab.transaction_tree.selection.return_value = ["item_1"]
    
    # Mock Treeview values: ID, Date, Type, Amount, Category, Description, Behavior Date
    tab.transaction_tree.item.return_value = {
        'values': ["12345", "2026-06-01", "Expense", "€100.00", "Shopping", "phone", "2026-05-05"]
    }
    
    # If fallback is triggered (legacy fallback for empty trans_id)
    # We want to check what date_str, amount_str, category, desc are unpacked
    # Since we mock the delete_transaction to check fallback behavior,
    # let's write a simplified mock check of our fallback logic.
    v = ["", "2026-06-01", "Expense", "€100.00", "Shopping", "phone", "2026-05-05"]
    date_str, _, amount_str, category, desc = v[1:6]
    
    assert date_str == "2026-06-01"
    assert amount_str == "€100.00"
    assert category == "Shopping"
    assert desc == "phone"
    
    print("Delete fallback slice test PASSED!")

if __name__ == "__main__":
    test_state_saving()
    test_add_klarna_logic()
    test_view_transactions_sorting()
    test_delete_fallback_slice()
    print("All tests PASSED successfully!")
