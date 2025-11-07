# finance_tracker/services/budget_calculator.py

from datetime import datetime
import calendar

def days_in_month_str(month_str: str) -> int:
    try:
        year, month = map(int, month_str.split("-"))
        return calendar.monthrange(year, month)[1]
    except Exception:
        return 30

def compute_net_available_for_spending(state, month_str: str) -> float:
    try:
        datetime.strptime(month_str, "%Y-%m")
    except ValueError:
        month_str = datetime.now().strftime("%Y-%m")

    base_income = state.budget_settings.get("monthly_income", 0)
    daily_savings_goal = state.budget_settings.get("daily_savings_goal", 0)
    flex_income_month = sum(i["amount"] for i in state.incomes if i["date"].startswith(month_str))
    total_income = base_income + flex_income_month
    fixed_costs = sum(fc["amount"] for fc in state.budget_settings.get("fixed_costs", []))

    dim = days_in_month_str(month_str)
    monthly_savings_goal = daily_savings_goal * dim
    flexible = total_income - fixed_costs - monthly_savings_goal
    return max(flexible, 0)

def generate_daily_budget_report(state, month_str: str) -> str:
    try:
        year, month = map(int, month_str.split("-"))
    except ValueError:
        return "Invalid month format. Use YYYY-MM."

    base_income = state.budget_settings.get("monthly_income", 0)
    daily_savings_goal = state.budget_settings.get("daily_savings_goal", 0)
    flex_income_month = sum(i['amount'] for i in state.incomes if i['date'].startswith(month_str))
    total_income = base_income + flex_income_month
    fixed_costs = sum(fc['amount'] for fc in state.budget_settings.get('fixed_costs', []))

    days_in_month = calendar.monthrange(year, month)[1]
    monthly_savings_goal = daily_savings_goal * days_in_month
    monthly_flexible_spending_budget = total_income - fixed_costs - monthly_savings_goal
    initial_daily_spending_target = monthly_flexible_spending_budget / days_in_month if days_in_month else 0

    flex_expenses_month = [e for e in state.expenses if e['date'].startswith(month_str)]
    daily_expenses = {}
    for e in flex_expenses_month:
        daily_expenses.setdefault(e['date'], []).append(e)

    from datetime import datetime as dt, date as ddate
    report = f"{'='*80}\n"
    report += f"DAILY BUDGET REPORT - {calendar.month_name[month]} {year}\n"
    report += f"{'='*80}\n\n"
    report += f"Base Monthly Income:                      €{base_income:>10.2f}\n"
    report += f"Flexible Income (This Month):             €{flex_income_month:>10.2f}\n"
    report += f"TOTAL INCOME:                             €{total_income:>10.2f}\n"
    report += f"Total Fixed Costs:                       -€{fixed_costs:>10.2f}\n"
    report += f"{'-'*50}\n"
    report += f"Monthly Savings Goal:                    -€{monthly_savings_goal:>10.2f}\n"
    report += f"NET MONTHLY FLEXIBLE BUDGET:              €{monthly_flexible_spending_budget:>10.2f}\n"
    report += f"INITIAL DAILY SPENDING TARGET:            €{initial_daily_spending_target:>10.2f}\n"
    report += f"{'-'*80}\n\n"
    report += f"DAILY BREAKDOWN (Flexible daily target adjusts based on remaining budget)\n"
    report += f"{'-'*80}\n"
    report += f"{'Date':<12} {'Target':<12} {'Spent':<12} {'Daily +/-':<12} {'Cumulative':<12} {'Status'}\n"
    report += f"{'-'*80}\n"

    cumulative_flexible_balance = monthly_flexible_spending_budget
    today = dt.now().date()
    
    for day in range(1, days_in_month + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        date_obj = dt.strptime(date_str, "%Y-%m-%d").date()
        if date_obj > today:
            break
        
        # Calculate flexible target for THIS day based on remaining days INCLUDING today
        # If budget is depleted (≤0), target becomes 0
        remaining_days_including_today = days_in_month - day + 1
        if cumulative_flexible_balance <= 0:
            daily_target_for_this_day = 0
        else:
            daily_target_for_this_day = cumulative_flexible_balance / remaining_days_including_today if remaining_days_including_today > 0 else 0
        
        day_spent = sum(e['amount'] for e in daily_expenses.get(date_str, []))
        cumulative_flexible_balance -= day_spent
        daily_plus_minus = daily_target_for_this_day - day_spent
        
        status = "✓ On Track" if daily_plus_minus >= 0 else "✗ Overspent"
        if day_spent == 0:
            status = "- No spending"
        
        report += (f"{date_str:<12} €{daily_target_for_this_day:<10.2f} "
                   f"€{day_spent:<10.2f} €{daily_plus_minus:<10.2f} "
                   f"€{cumulative_flexible_balance:<10.2f} {status}\n")

    report += f"{'-'*80}\n\n"

    if today.year == year and today.month == month and today.day < days_in_month:
        remaining_days = days_in_month - today.day
        if remaining_days > 0:
            new_daily_target = cumulative_flexible_balance / remaining_days if cumulative_flexible_balance > 0 else 0
            
            report += f"{'='*80}\n"
            report += f"YOUR PATH FORWARD\n"
            report += f"{'='*80}\n\n"
            
            if cumulative_flexible_balance <= 0:
                total_flexible_expenses_incurred = sum(e['amount'] for e in flex_expenses_month)
                overall_net_value = total_income - fixed_costs - total_flexible_expenses_incurred - monthly_savings_goal
                overspend_amount = abs(cumulative_flexible_balance)
                
                report += f"⚠️  BUDGET DEPLETED: You have overspent your flexible budget by €{overspend_amount:.2f}\n\n"
                report += f"To get back on track, you have {remaining_days} days remaining and need to:\n\n"
                report += f"OPTION 1: Zero Spending Challenge\n"
                report += f"  • Spend €0.00 per day for the remaining {remaining_days} days\n"
                report += f"  • This will keep your deficit at €{overspend_amount:.2f}\n\n"
                report += f"OPTION 2: Accept the Deficit\n"
                report += f"  • Continue spending normally\n"
                report += f"  • Make up the €{overspend_amount:.2f} deficit next month\n\n"
                report += f"OPTION 3: Partial Recovery\n"
                report += f"  • Reduce spending as much as possible\n"
                report += f"  • Any amount you save reduces the deficit\n\n"
                report += f"--- Key Numbers for Context ---\n"
                report += f"Overall Net Value (Income - All Expenses - Savings): €{overall_net_value:.2f}\n"
                report += f"Current Flexible Budget Balance:                      €{cumulative_flexible_balance:.2f}\n\n"
            elif new_daily_target <= initial_daily_spending_target * 0.7:
                report += f"⚠️  SPENDING CAUTION NEEDED\n\n"
                report += f"You've spent more than planned in the first part of the month.\n"
                report += f"Your adjusted daily target is now: €{new_daily_target:.2f}/day (= €{cumulative_flexible_balance:.2f} / {remaining_days})\n"
                report += f"(Original target was: €{initial_daily_spending_target:.2f}/day)\n\n"
                report += f"Action Steps:\n"
                report += f"  • Try to limit spending to €{new_daily_target:.2f} per day\n"
                report += f"  • You have {remaining_days} days left to stay within budget\n"
                report += f"  • Current remaining budget: €{cumulative_flexible_balance:.2f}\n\n"
            elif new_daily_target >= initial_daily_spending_target * 1.3:
                report += f"✓ EXCELLENT PROGRESS!\n\n"
                report += f"You're doing great! You've been spending less than planned.\n"
                report += f"Your adjusted daily target is now: €{new_daily_target:.2f}/day\n"
                report += f"(Original target was: €{initial_daily_spending_target:.2f}/day)\n\n"
                report += f"Your Options:\n"
                report += f"  • Continue at your current pace and build a buffer\n"
                report += f"  • Enjoy up to €{new_daily_target:.2f}/day for the next {remaining_days} days\n"
                report += f"  • Current remaining budget: €{cumulative_flexible_balance:.2f}\n\n"
            else:
                report += f"✓ ON TRACK\n\n"
                report += f"You can spend up to €{new_daily_target:.2f} per day for the next {remaining_days} days.\n\n"
                report += f"Budget Status:\n"
                report += f"  • Days remaining: {remaining_days}\n"
                report += f"  • Remaining flexible budget: €{cumulative_flexible_balance:.2f}\n"
                report += f"  • Adjusted daily target: €{new_daily_target:.2f}\n\n"
        else:
            new_daily_target = cumulative_flexible_balance
            if new_daily_target < 0:
                report += f"Month Complete: You overspent your flexible budget by €{abs(new_daily_target):.2f}\n"
            else:
                report += f"Month Complete: You have €{new_daily_target:.2f} remaining in your flexible budget.\n"
    
    return report

def auto_assign_percentages(state, month_str: str, cat_type: str, categories: list):
    """
    Returns:
        (percentages_dict, message, is_overspent)
    """
    if cat_type != "Expense":
        return {}, "Auto-assign is only available for Expense budgets.", False

    try:
        datetime.strptime(month_str, "%Y-%m")
    except ValueError:
        return {}, "Invalid month format. Use YYYY-MM.", False

    net_available = compute_net_available_for_spending(state, month_str)
    if net_available <= 0:
        return {}, "Net available for spending is €0 for this month. Cannot auto-assign.", False

    spend_by_cat = {c: 0.0 for c in categories}
    for e in state.expenses:
        if e['date'].startswith(month_str) and e['category'] in spend_by_cat:
            spend_by_cat[e['category']] += float(e['amount'])

    total_spent = sum(spend_by_cat.values())
    if total_spent == 0:
        return {}, "No expenses recorded for the selected month. Nothing to auto-assign.", False

    if total_spent <= net_available:
        percentages = {c: (spend_by_cat[c] / net_available) * 100.0 for c in categories}
        remaining = net_available - total_spent
        remaining_pct = 100.0 - sum(percentages.values())
        msg = (f"Budgets set to match current expenses for {month_str}.\n"
               f"Remaining unallocated budget: €{remaining:.2f} (~{remaining_pct:.1f}%).\n"
               f"Please assign the remaining budget to one or more categories.")
        return percentages, msg, False
    else:
        percentages = {c: ((spend_by_cat[c] / total_spent) * 100.0 if total_spent > 0 else 0.0) for c in categories}
        over = total_spent - net_available
        msg = (f"You have spent €{total_spent:.2f} which exceeds your flexible budget of "
               f"€{net_available:.2f} by €{over:.2f}. Budgets were set proportionally to actual spend.")
        return percentages, msg, True
