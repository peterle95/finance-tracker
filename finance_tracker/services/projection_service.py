"""
finance_tracker/services/projection_service.py

Service for generating financial projections based on current data.
"""

from datetime import date

from dateutil.relativedelta import relativedelta


def _format_signed_euro(value: float) -> str:
    sign = "+" if value >= 0 else "-"
    return f"{sign}€{abs(value):,.2f}"


def _build_target_savings_projection(state, num_months: int) -> str:
    bank_balance = state.budget_settings.get("bank_account_balance", 0)
    wallet_balance = state.budget_settings.get("wallet_balance", 0)
    savings_balance = state.budget_settings.get("savings_balance", 0)
    investment_balance = state.budget_settings.get("investment_balance", 0)
    money_lent_balance = state.budget_settings.get("money_lent_balance", 0)
    daily_savings_goal = state.budget_settings.get("daily_savings_goal", 0)

    starting_total_balance = (
        bank_balance
        + wallet_balance
        + savings_balance
        + investment_balance
        + money_lent_balance
    )

    report = f"{'='*80}\n"
    report += "FINANCIAL PROJECTION (TARGET SAVINGS)\n"
    report += f"{'='*80}\n\n"
    report += "This report projects your total financial balance (Bank + Wallet + Savings + Investments + Money Lent).\n"
    report += "It assumes you will meet your daily savings goal every day.\n\n"
    report += f"Bank Account Balance:       €{bank_balance:>10.2f}\n"
    report += f"Wallet Balance:             €{wallet_balance:>10.2f}\n"
    report += f"Current Savings Balance:    €{savings_balance:>10.2f}\n"
    report += f"Current Investment Balance: €{investment_balance:>10.2f}\n"
    report += f"Money Lent Balance:         €{money_lent_balance:>10.2f}\n"
    report += "-----------------------------------------\n"
    report += f"Total Starting Balance:     €{starting_total_balance:>10.2f}\n"
    report += f"Target Daily Savings Goal:  €{daily_savings_goal:>10.2f}\n"
    report += f"{'-'*80}\n\n"
    report += f"{'Month':<15} {'Projected Monthly Savings':<30} {'Projected Total Balance'}\n"
    report += f"{'-'*80}\n"

    projected_balance = starting_total_balance
    current_date = date.today()

    for _ in range(num_months):
        next_month_date = current_date + relativedelta(months=1)
        days_in_month = (next_month_date - current_date).days
        monthly_savings = daily_savings_goal * days_in_month
        projected_balance += monthly_savings
        report += (
            f"{current_date.strftime('%Y-%m'):<15} "
            f"€{monthly_savings:<28.2f} "
            f"€{projected_balance:10.2f}\n"
        )
        current_date = next_month_date

    report += f"{'-'*80}\n"
    return report


def _build_monthly_net_worth_change_projection(state, num_months: int, history_months: int) -> str:
    snapshots = state.budget_settings.get("asset_snapshots", [])

    report = f"{'='*80}\n"
    report += "FINANCIAL PROJECTION (NET WORTH TREND)\n"
    report += f"{'='*80}\n\n"
    report += (
        "This report projects your net worth using the average month-by-month "
        "change from your snapshot history.\n\n"
    )

    if len(snapshots) < 2:
        report += "Not enough snapshot history to calculate a month-by-month trend.\n"
        report += "Please record at least two net worth snapshots and try again.\n"
        return report

    all_intervals = []
    for i in range(1, len(snapshots)):
        current = snapshots[i]
        previous = snapshots[i - 1]
        change = current["net_worth"] - previous["net_worth"]
        all_intervals.append(
            {
                "from_date": previous["date"],
                "to_date": current["date"],
                "change": change,
            }
        )

    months_requested = max(1, history_months)
    intervals_used = all_intervals[-months_requested:]
    used_changes = [interval["change"] for interval in intervals_used]
    total_change = sum(used_changes)
    avg_monthly_change = total_change / len(used_changes)

    latest_snapshot = snapshots[-1]
    projected_net_worth = latest_snapshot["net_worth"]
    current_date = date.today()

    report += f"Snapshots available: {len(snapshots)}\n"
    report += f"Month-to-month changes available: {len(all_intervals)}\n"
    report += f"Months requested for analysis: {months_requested}\n"
    report += f"Months used for analysis: {len(intervals_used)}\n"
    report += f"Latest snapshot date: {latest_snapshot['date']}\n"
    report += f"Latest net worth: €{latest_snapshot['net_worth']:,.2f}\n"
    report += f"{'-'*80}\n"
    report += "AVERAGE CALCULATION DETAILS\n"
    report += f"{'Period':<27} {'Net Worth Change'}\n"
    report += f"{'-'*80}\n"

    for interval in intervals_used:
        period = f"{interval['from_date']} → {interval['to_date']}"
        report += f"{period:<27} {_format_signed_euro(interval['change'])}\n"

    change_terms = " + ".join(f"€{v:+,.2f}" for v in used_changes)
    report += f"{'-'*80}\n"
    report += f"Average month-by-month change = ({change_terms}) / {len(used_changes)}\n"
    report += f"Average month-by-month change = {_format_signed_euro(avg_monthly_change)}\n"
    report += f"{'-'*80}\n\n"

    report += f"{'Month':<15} {'Projected Net Worth Change':<30} {'Projected Net Worth'}\n"
    report += f"{'-'*80}\n"

    for _ in range(num_months):
        projected_net_worth += avg_monthly_change
        report += (
            f"{current_date.strftime('%Y-%m'):<15} "
            f"{_format_signed_euro(avg_monthly_change):<30} "
            f"€{projected_net_worth:10.2f}\n"
        )
        current_date += relativedelta(months=1)

    report += f"{'-'*80}\n"
    return report


def projection_text(state, num_months: int, mode: str = "target_savings", history_months: int = 6) -> str:
    if mode == "net_worth_change":
        return _build_monthly_net_worth_change_projection(state, num_months, history_months)
    return _build_target_savings_projection(state, num_months)
