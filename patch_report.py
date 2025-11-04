import sys
import re
from datetime import datetime

def insert_after_line(s, needle, insertion):
    idx = s.find(needle)
    if idx == -1:
        return None
    end_of_line = s.find('\n', idx)
    if end_of_line == -1:
        end_of_line = len(s)
    return s[:end_of_line+1] + insertion + s[end_of_line+1:]


def main():
    path = 'finance-tracker.py'
    try:
        with open(path, 'r', encoding='utf-8') as f:
            s = f.read()
    except Exception as e:
        print(f'ERROR: Failed to read {path}: {e}', file=sys.stderr)
        sys.exit(1)

    modified = s

    # 1) Insert remaining budget computation after spending_daily_budget calculation and header line
    if "Remaining Flexible Budget (to month end)" not in modified:
        needle1 = "spending_daily_budget = spending_flexible_budget / days_in_month"
        insertion1 = (
            "\n"
            "        spent_so_far = sum(\n"
            "            e['amount']\n"
            "            for e in self.expenses\n"
            "            if e['date'].startswith(month_str) and datetime.strptime(e['date'], \"%Y-%m-%d\").date() <= datetime.now().date()\n"
            "        )\n"
            "        remaining_flexible_budget = max(spending_flexible_budget - spent_so_far, 0)\n"
        )
        tmp = insert_after_line(modified, needle1, insertion1)
        if tmp is not None:
            modified = tmp
        else:
            print("WARN: Could not locate spending_daily_budget line; skipping insertion1", file=sys.stderr)

        needle2 = 'report += f"YOUR DAILY SPENDING TARGET:              €{spending_daily_budget:>10.2f}\\n"'
        insertion2 = '        report += f"Remaining Flexible Budget (to month end): €{remaining_flexible_budget:>10.2f}\\n"\n'
        tmp = insert_after_line(modified, needle2, insertion2)
        if tmp is not None:
            modified = tmp
        else:
            print("WARN: Could not locate header target line; skipping insertion2", file=sys.stderr)

    # 2) Replace forecast block to use remaining budget logic
    start_marker = "daily_surplus_distribution = cumulative_deficit / remaining_days_forecast"
    end_marker = 'report += f"{\'-\'*80}\\n"'
    start_idx = modified.find(start_marker)
    if start_idx != -1:
        end_idx = modified.find(end_marker, start_idx)
        if end_idx != -1:
            end_idx += len(end_marker)
            replacement = (
                "                # Total spent so far (flexible) and remaining flexible budget\n"
                "                total_spent_so_far = sum(\n"
                "                    e['amount'] for e in flex_expenses_month\n"
                "                    if datetime.strptime(e['date'], \"%Y-%m-%d\").date() <= today\n"
                "                )\n"
                "                remaining_budget = max(spending_flexible_budget - total_spent_so_far, 0)\n"
                "\n"
                "                if remaining_budget <= 0:\n"
                "                    # No budget left\n"
                "                    total_flexible_expenses = sum(e['amount'] for e in flex_expenses_month)\n"
                "                    total_expenses = total_flexible_expenses + fixed_costs\n"
                "                    net_value = total_income - total_expenses\n"
                "\n"
                "                    report += f\"Your cumulative spending deficit is currently €{abs(cumulative_deficit):.2f}.\\n\\n\"\n"
                "                    report += f\"You have fully used your flexible budget for the month.\\n\"\n"
                "                    report += f\"No further flexible budget left for the remainder of the month.\\n\\n\"\n"
                "                    report += f\"--- Understanding the Key Numbers ---\\n\\n\"\n"
                "                    report += f\"It's important to understand what the 'Net Value' and 'Cumulative' represent:\\n\\n\"\n"
                "                    report += f\" * Summary Net Value (€{net_value:.2f}): This is your actual financial bottom line for the month.\\n\"\n"
                "                    report += f\"   (Total Income) - (Total Expenses, both fixed and flexible).\\n\\n\"\n"
                "                    report += f\" * Cumulative (€{abs(cumulative_deficit):.2f} behind): This is a scheduling metric.\\n\"\n"
                "                    report += f\"   It shows how your daily flexible spending compares to your target.\\n\\n\"\n"
                "                    report += f\"   The system is essentially saying: \\\"Your goal is €{spending_daily_budget:.2f}/day,\\n\"\n"
                "                    report += f\"   but you are currently €{abs(cumulative_deficit):.2f} behind schedule.\\\"\\n\\n\"\n"
                "                else:\n"
                "                    # Budget remains: recommend a new daily target for remaining days\n"
                "                    new_recommended_budget = remaining_budget / remaining_days_forecast\n"
                "                    if cumulative_deficit < 0:\n"
                "                        report += f\"You are behind schedule by €{abs(cumulative_deficit):.2f}, but\\n\"\n"
                "                        report += f\"you still have €{remaining_budget:.2f} of flexible budget left.\\n\\n\"\n"
                "                    else:\n"
                "                        report += f\"You are under budget by €{cumulative_deficit:.2f}.\\n\\n\"\n"
                "\n"
                "                    report += \"Here's your adjusted plan to finish the month within budget:\\n\"\n"
                "                    report += f\"  Remaining Flexible Budget:      €{remaining_budget:>10.2f}\\n\"\n"
                "                    report += f\"  Remaining Days:                 {remaining_days_forecast:>10}\\n\"\n"
                "                    report += f\"  New Recommended Daily Budget:   €{new_recommended_budget:>10.2f}\\n\\n\"\n"
                "                    report += \"Explanation:\\n\"\n"
                "                    report += f\"Spend up to €{new_recommended_budget:.2f} per day for the rest of the month to\\n\"\n"
                "                    report += \"use your remaining flexible budget without overspending.\\n\"\n"
                "                report += f\"{'-'*80}\\n\"\n"
            )
            modified = modified[:start_idx] + replacement + modified[end_idx:]
        else:
            print("WARN: Could not locate forecast end marker; skipping forecast replacement", file=sys.stderr)
    else:
        print("WARN: Could not locate forecast start marker; skipping forecast replacement", file=sys.stderr)

    if modified != s:
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(modified)
            print("Patched finance-tracker.py successfully.")
        except Exception as e:
            print(f"ERROR: Failed to write {path}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("No changes applied; perhaps already patched.")

if __name__ == '__main__':
    main()
