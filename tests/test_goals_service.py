import unittest
from types import SimpleNamespace

from finance_tracker.services.goals_service import auto_distribute_savings


class GoalsServiceTest(unittest.TestCase):
    def test_auto_distribution_clears_monthly_allocation_marker(self):
        state = SimpleNamespace(budget_settings={
            "savings_balance": 100,
            "savings_goals": [{
                "name": "Emergency fund",
                "target_amount": 100,
                "allocated_amount": 20,
                "monthly_allocation": {
                    "month": "2026-01",
                    "amount": 20,
                    "allocated_amount_before": 0,
                },
            }],
        })

        success, _ = auto_distribute_savings(state)

        self.assertTrue(success)
        self.assertEqual(state.budget_settings["savings_goals"][0]["allocated_amount"], 100)
        self.assertNotIn("monthly_allocation", state.budget_settings["savings_goals"][0])
