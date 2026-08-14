import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from uuid import UUID

from finance_tracker.state import AppState


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temporary_directory.name)
        self.legacy_file = self.data_dir / "finance_data.json"

    def tearDown(self):
        self.temporary_directory.cleanup()

    def read_json(self, name):
        return json.loads((self.data_dir / name).read_text(encoding="utf-8"))

    def write_json(self, name, value):
        (self.data_dir / name).write_text(json.dumps(value), encoding="utf-8")

    def state(self):
        return AppState(self.legacy_file)

    def test_migrates_legacy_once_without_touching_source(self):
        legacy = {
            "expenses": [{
                "date": "2026-01-01", "amount": 4, "category": "Café",
                "description": "Coffee", "plugin_field": 7,
            }, {
                "date": "2026-01-02", "amount": 2, "description": "Unsorted",
            }],
            "incomes": [],
            "categories": {"Expense": ["Café", "Cafe"], "Income": ["Salary"]},
            "budget_settings": {
                "monthly_income": 1000, "bank_account_balance": 20,
                "custom_setting": {"enabled": True},
            },
            "root_extension": {"version": 2},
        }
        original = json.dumps(legacy)
        self.legacy_file.write_text(original, encoding="utf-8")

        state = self.state()

        self.assertEqual(self.legacy_file.read_text(encoding="utf-8"), original)
        categories = self.read_json("categories.json")
        self.assertEqual(
            [item["file_key"] for item in categories["Expense"]],
            ["cafe", "cafe-2", "other"],
        )
        transaction = self.read_json("transactions_expense_cafe.json")[0]
        UUID(transaction["id"])
        self.assertEqual(transaction["plugin_field"], 7)
        self.assertEqual(self.read_json("transactions_expense_other.json")[0]["category"], "Other")
        preferences = self.read_json("preferences.json")
        self.assertEqual(
            preferences["_extra"]["legacy_budget_settings"]["custom_setting"],
            {"enabled": True},
        )
        self.assertEqual(
            preferences["_extra"]["legacy_root"]["root_extension"],
            {"version": 2},
        )
        reloaded = self.state()
        self.assertEqual(reloaded.expenses, state.expenses)
        self.assertEqual(reloaded.budget_settings, state.budget_settings)

    def test_category_lifecycle_and_transaction_deletion_guard(self):
        state = self.state()
        state.categories["Expense"].append("Pet Care")
        state.save()
        self.assertTrue((self.data_dir / "transactions_expense_pet-care.json").exists())

        state.categories["Expense"].remove("Pet Care")
        state.save()
        self.assertFalse((self.data_dir / "transactions_expense_pet-care.json").exists())

        state.add_transaction("Expense", "2026-01-02", 5, "Food", "Lunch")
        state.budget_settings["category_budgets"]["Expense"]["Food"] = 30
        state.save()
        state.categories["Expense"].remove("Food")
        del state.budget_settings["category_budgets"]["Expense"]["Food"]
        with self.assertRaisesRegex(ValueError, "Cannot delete category"):
            state.save()
        self.assertTrue((self.data_dir / "transactions_expense_food.json").exists())
        self.assertIn("Food", state.categories["Expense"])
        self.assertEqual(state.budget_settings["category_budgets"]["Expense"]["Food"], 30)

    def test_category_deletion_rejects_external_transaction_after_load(self):
        state = self.state()
        food_path = self.data_dir / "transactions_expense_food.json"
        self.assertEqual(self.read_json("transactions_expense_food.json"), [])
        state.budget_settings["category_budgets"]["Expense"]["Food"] = 30
        state.save()
        external_transaction = [{
            "id": "external-food-1", "date": "2026-01-02", "amount": 5,
            "category": "Food", "description": "Lunch", "behavior_date": "2026-01-01",
        }]
        raw = json.dumps(external_transaction, indent=2)
        food_path.write_text(raw, encoding="utf-8")

        state.categories["Expense"].remove("Food")
        del state.budget_settings["category_budgets"]["Expense"]["Food"]

        with self.assertRaisesRegex(
                ValueError, r"^Cannot delete category with transactions: Food$"):
            state.save()

        self.assertEqual(food_path.read_text(encoding="utf-8"), raw)
        self.assertTrue(food_path.exists())
        self.assertIn("Food", state.categories["Expense"])
        self.assertEqual(state.budget_settings["category_budgets"]["Expense"]["Food"], 30)

    def test_missing_registry_does_not_overwrite_existing_files(self):
        original = '{"wallet_balance": 321}'
        (self.data_dir / "net_worth.json").write_text(original, encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "categories.json is missing"):
            self.state()

        self.assertEqual((self.data_dir / "net_worth.json").read_text(encoding="utf-8"), original)

    def test_delete_and_add_does_not_rename_populated_category_when_position_changes(self):
        state = self.state()
        state.add_transaction("Expense", "2026-01-02", 5, "Food", "Lunch")
        state.categories["Expense"].remove("Food")
        state.categories["Expense"].append("Cafe")

        with self.assertRaisesRegex(ValueError, "Cannot delete category"):
            state.save()

        self.assertEqual(state.expenses[0]["category"], "Food")

    def test_add_and_delete_write_only_target_transaction_file(self):
        state = self.state()
        with mock.patch.object(AppState, "_atomic_write", wraps=AppState._atomic_write) as write:
            state.add_transaction("Expense", "2026-01-02", 5, "Food", "Lunch")
        self.assertEqual([call.args[0].name for call in write.call_args_list], ["transactions_expense_food.json"])

        transaction_id = state.expenses[0]["id"]
        with mock.patch.object(AppState, "_atomic_write", wraps=AppState._atomic_write) as write:
            self.assertTrue(state.delete_transaction_by_id("Expense", transaction_id))
        self.assertEqual([call.args[0].name for call in write.call_args_list], ["transactions_expense_food.json"])

    def test_feature_save_does_not_overwrite_external_cross_feature_edit(self):
        state = self.state()
        external_net_worth = self.read_json("net_worth.json")
        external_net_worth["bank_account_balance"] = 987
        external_net_worth["external_field"] = "keep"
        self.write_json("net_worth.json", external_net_worth)

        state.budget_settings["daily_savings_goal"] = 12
        with mock.patch.object(AppState, "_atomic_write", wraps=AppState._atomic_write) as write:
            state.save()

        self.assertEqual([call.args[0].name for call in write.call_args_list], ["budget.json"])
        self.assertEqual(self.read_json("net_worth.json"), external_net_worth)

    def test_data_directory_environment_is_primary(self):
        with tempfile.TemporaryDirectory() as other_directory:
            legacy = Path(other_directory) / "old-name.json"
            legacy.write_text(json.dumps({
                "expenses": [], "incomes": [], "budget_settings": {},
                "categories": {"Expense": ["Food"], "Income": ["Salary"]},
            }), encoding="utf-8")
            environment = {
                "FINANCE_DATA_DIR": str(self.data_dir),
                "FINANCE_DATA_FILE": str(legacy),
            }
            with mock.patch.dict(os.environ, environment, clear=False):
                state = AppState()
            self.assertTrue(legacy.exists())

        self.assertEqual(state.data_dir, self.data_dir)
        self.assertEqual(state.data_file, legacy)
        self.assertTrue((self.data_dir / "categories.json").exists())

    def test_static_feature_change_writes_only_its_file(self):
        state = self.state()
        state.budget_settings["loans"].append({"id": "loan-1", "custom": True})

        with mock.patch.object(AppState, "_atomic_write", wraps=AppState._atomic_write) as write:
            state.save()

        self.assertEqual([call.args[0].name for call in write.call_args_list], ["loans.json"])
        self.assertTrue(self.read_json("loans.json")[0]["custom"])

    def test_transaction_category_move_writes_source_and_destination(self):
        state = self.state()
        state.add_transaction("Expense", "2026-01-02", 5, "Food", "Lunch")
        state.expenses[0]["category"] = "Shopping"

        with mock.patch.object(AppState, "_atomic_write", wraps=AppState._atomic_write) as write:
            state.save()

        self.assertEqual(
            {call.args[0].name for call in write.call_args_list},
            {"transactions_expense_food.json", "transactions_expense_shopping.json"},
        )
        self.assertEqual(self.read_json("transactions_expense_food.json"), [])
        self.assertEqual(
            self.read_json("transactions_expense_shopping.json")[0]["category"],
            "Shopping",
        )

    def test_category_rename_keeps_file_key_and_updates_transactions(self):
        state = self.state()
        state.add_transaction("Expense", "2026-01-02", 5, "Food", "Lunch")
        state.budget_settings["category_budgets"]["Expense"]["Food"] = 25
        index = state.categories["Expense"].index("Food")
        state.categories["Expense"][index] = "Groceries"
        state.save()

        category = next(item for item in self.read_json("categories.json")["Expense"]
                        if item["name"] == "Groceries")
        self.assertEqual(category["file_key"], "food")
        self.assertEqual(state.expenses[0]["category"], "Groceries")
        self.assertEqual(state.budget_settings["category_budgets"]["Expense"]["Groceries"], 25)
        self.assertEqual(
            self.read_json("transactions_expense_food.json")[0]["category"],
            "Groceries",
        )

    def test_load_warns_for_conflicts_and_orphan_transaction_files(self):
        self.state()
        self.write_json("budget.sync-conflict-20260810.json", {})
        self.write_json("transactions_expense_old.json", [])

        warnings = self.state().persistence_warnings

        self.assertTrue(any("Sync conflict" in warning for warning in warnings))
        self.assertTrue(any("Orphan transaction" in warning for warning in warnings))

    def test_split_unknown_fields_and_missing_transaction_ids_survive(self):
        self.write_json("categories.json", {
            "Expense": [{"name": "Food", "file_key": "food", "color": "red"}],
            "Income": [{"name": "Salary", "file_key": "salary"}],
            "schema_extension": 3,
        })
        self.write_json("budget.json", {
            "monthly_income": [], "fixed_costs": [], "daily_savings_goal": 0,
            "category_budgets": {"Expense": {}, "Income": {}}, "future_budget": 4,
        })
        self.write_json("transactions_expense_food.json", [{
            "date": "2026-01-01", "amount": 1, "category": "Food",
            "description": "Snack", "future_transaction": True,
        }])

        state = self.state()

        UUID(state.expenses[0]["id"])
        self.assertEqual(self.read_json("categories.json")["schema_extension"], 3)
        self.assertEqual(self.read_json("categories.json")["Expense"][0]["color"], "red")
        self.assertEqual(self.read_json("budget.json")["_extra"]["future_budget"], 4)
        self.assertTrue(self.read_json("transactions_expense_food.json")[0]["future_transaction"])


if __name__ == "__main__":
    unittest.main()
