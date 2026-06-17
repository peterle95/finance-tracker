import json
import os
import tempfile
import unittest
from pathlib import Path

from finance_tracker.state import AppState


class AppStateEnvironmentTest(unittest.TestCase):
    def test_finance_data_file_environment_variable_controls_default_path(self):
        old_value = os.environ.get("FINANCE_DATA_FILE")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                data_file = Path(tmp) / "finance_data.json"
                data_file.write_text(
                    json.dumps(
                        {
                            "expenses": [
                                {
                                    "id": "expense-1",
                                    "date": "2026-06-01",
                                    "amount": 4.5,
                                    "category": "Food",
                                    "description": "Snack",
                                }
                            ],
                            "incomes": [],
                            "budget_settings": {},
                            "categories": {},
                        }
                    ),
                    encoding="utf-8",
                )
                os.environ["FINANCE_DATA_FILE"] = str(data_file)

                state = AppState()
                self.assertEqual(data_file, state.data_file)
                self.assertEqual(1, len(state.expenses))

                state.add_transaction("Income", "2026-06-02", 10.0, "Gift", "Cash")
                saved = json.loads(data_file.read_text(encoding="utf-8"))
                self.assertEqual(1, len(saved["incomes"]))
        finally:
            if old_value is None:
                os.environ.pop("FINANCE_DATA_FILE", None)
            else:
                os.environ["FINANCE_DATA_FILE"] = old_value

    def test_explicit_data_file_still_works_without_environment(self):
        old_value = os.environ.pop("FINANCE_DATA_FILE", None)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                data_file = Path(tmp) / "custom.json"
                state = AppState(data_file)
                self.assertEqual(data_file, state.data_file)
                self.assertEqual([], state.expenses)
        finally:
            if old_value is not None:
                os.environ["FINANCE_DATA_FILE"] = old_value


if __name__ == "__main__":
    unittest.main()
