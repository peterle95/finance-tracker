"""
finance_tracker/services/report_builder.py

Service for preparing data for various financial reports and charts.
"""

from datetime import date
from dateutil.relativedelta import relativedelta

def pie_data(state, month_str: str, chart_type: str, include_fixed: bool, include_base_income: bool):
    if chart_type == "Expense":
        data = state.expenses
        title = f"Expenses for {month_str}"
        category_totals = {}
        if include_fixed:
            total_fc = sum(fc['amount'] for fc in state.budget_settings.get('fixed_costs', []))
            if total_fc > 0:
                category_totals["Fixed Costs"] = total_fc
    else:
        data = state.incomes
        title = f"Incomes for {month_str}"
        category_totals = {}
        if include_base_income:
            base_income = state.budget_settings.get('monthly_income', 0)
            if base_income > 0:
                category_totals["Base Income"] = base_income

    for item in data:
        if item['date'].startswith(month_str):
            category_totals[item['category']] = category_totals.get(item['category'], 0) + item['amount']

    return title, category_totals

def history_data(state, num_months: int, chart_type: str, include_fixed: bool, include_base_income: bool):
    today = date.today()
    monthly_totals = {}
    if chart_type == "Expense":
        fixed_value = sum(fc['amount'] for fc in state.budget_settings.get('fixed_costs', [])) if include_fixed else 0
        data = state.expenses
        title = f"Historical Expenses for the Last {num_months} Months"
    else:
        fixed_value = state.budget_settings.get('monthly_income', 0) if include_base_income else 0
        data = state.incomes
        title = f"Historical Incomes for the Last {num_months} Months"

    for i in range(num_months - 1, -1, -1):
        month_date = today - relativedelta(months=i)
        key = month_date.strftime("%Y-%m")
        monthly_totals[key] = fixed_value

    for item in data:
        month = item['date'][:7]
        if month in monthly_totals:
            monthly_totals[month] += item['amount']

    labels = list(monthly_totals.keys())
    values = list(monthly_totals.values())
    return title, labels, values