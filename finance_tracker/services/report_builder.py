"""
finance_tracker/services/report_builder.py

Service for preparing data for various financial reports and charts.
"""

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from .budget_calculator import get_active_fixed_costs, get_active_monthly_income

def _month_range(start_month: str, end_month: str) -> list[str]:
    start = datetime.strptime(start_month + "-01", "%Y-%m-%d").date()
    end = datetime.strptime(end_month + "-01", "%Y-%m-%d").date()
    if start > end:
        start, end = end, start
    months = []
    cur = start
    while cur <= end:
        months.append(cur.strftime("%Y-%m"))
        cur = cur + relativedelta(months=1)
    return months

def pie_data(state, month_str: str, chart_type: str, include_fixed: bool, include_base_income: bool):
    if chart_type == "Expense":
        data = state.expenses
        title = f"Expenses for {month_str}"
        category_totals = {}
        if include_fixed:
            total_fc = sum(fc['amount'] for fc in get_active_fixed_costs(state, month_str))
            if total_fc > 0:
                category_totals["Fixed Costs"] = total_fc
    else:
        data = state.incomes
        title = f"Incomes for {month_str}"
        category_totals = {}
        if include_base_income:
            base_income = get_active_monthly_income(state, month_str)
            if base_income > 0:
                category_totals["Base Income"] = base_income

    for item in data:
        if item['date'].startswith(month_str):
            category_totals[item['category']] = category_totals.get(item['category'], 0) + item['amount']

    return title, category_totals

def pie_data_range(state, start_month_str: str, end_month_str: str, chart_type: str, include_fixed: bool, include_base_income: bool):
    months = _month_range(start_month_str, end_month_str)
    if not months:
        return "", {}

    if chart_type == "Expense":
        data = state.expenses
        title = f"Expenses for {months[0]} to {months[-1]}"
        category_totals = {}
        if include_fixed:
            total_fc = 0.0
            for m in months:
                total_fc += sum(fc['amount'] for fc in get_active_fixed_costs(state, m))
            if total_fc > 0:
                category_totals["Fixed Costs"] = total_fc
    else:
        data = state.incomes
        title = f"Incomes for {months[0]} to {months[-1]}"
        category_totals = {}
        if include_base_income:
            total_base_income = 0.0
            for m in months:
                total_base_income += get_active_monthly_income(state, m)
            if total_base_income > 0:
                category_totals["Base Income"] = total_base_income

    month_set = set(months)
    for item in data:
        month = item['date'][:7]
        if month in month_set:
            category_totals[item['category']] = category_totals.get(item['category'], 0) + item['amount']

    return title, category_totals

def history_data(state, num_months: int, chart_type: str, include_fixed: bool, include_base_income: bool):
    today = date.today()
    monthly_totals = {}
    if chart_type == "Expense":
        fixed_value = 0
        if include_fixed:
            # For historical data, we need to get active costs for each specific month
            # We'll handle this in the loop below
            pass
        data = state.expenses
        title = f"Historical Expenses for the Last {num_months} Months"
    else:
        # fixed_value = state.budget_settings.get('monthly_income', 0) if include_base_income else 0 # REMOVED
        data = state.incomes
        title = f"Historical Incomes for the Last {num_months} Months"

    for i in range(num_months - 1, -1, -1):
        month_date = today - relativedelta(months=i)
        key = month_date.strftime("%Y-%m")
        # Get fixed costs active in this specific month
        if chart_type == "Expense" and include_fixed:
            month_fixed = sum(fc['amount'] for fc in get_active_fixed_costs(state, key))
            monthly_totals[key] = month_fixed
        elif chart_type == "Income" and include_base_income:
            monthly_totals[key] = get_active_monthly_income(state, key)
        else:
            monthly_totals[key] = 0

    for item in data:
        month = item['date'][:7]
        if month in monthly_totals:
            monthly_totals[month] += item['amount']

    labels = list(monthly_totals.keys())
    values = list(monthly_totals.values())
    return title, labels, values

def line_expense_category_range(state, start_month_str: str, end_month_str: str, categories: list[str]):
    months = _month_range(start_month_str, end_month_str)
    if not months:
        return "", [], {}

    title = f"Expense Categories from {months[0]} to {months[-1]}"
    if not categories:
        return title, months, {}
    category_series = {category: [0.0] * len(months) for category in categories}

    month_index = {month: idx for idx, month in enumerate(months)}
    for item in state.expenses:
        month = item['date'][:7]
        if month in month_index:
            category = item['category']
            if category not in category_series:
                category_series[category] = [0.0] * len(months)
            category_series[category][month_index[month]] += item['amount']

    has_data = any(sum(values) > 0 for values in category_series.values())
    if not has_data:
        return title, months, {}

    return title, months, category_series
