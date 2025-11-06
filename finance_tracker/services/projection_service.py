from datetime import date
from dateutil.relativedelta import relativedelta

def projection_text(state, num_months: int) -> str:
    bank_balance = state.budget_settings.get('bank_account_balance', 0)
    wallet_balance = state.budget_settings.get('wallet_balance', 0)
    savings_balance = state.budget_settings.get('savings_balance', 0)
    investment_balance = state.budget_settings.get('investment_balance', 0)
    money_lent_balance = state.budget_settings.get('money_lent_balance', 0)
    daily_savings_goal = state.budget_settings.get('daily_savings_goal', 0)

    starting_total_balance = (bank_balance + wallet_balance + savings_balance +
                              investment_balance + money_lent_balance)

    report = f"{'='*80}\n"
    report += f"FINANCIAL PROJECTION\n"
    report += f"{'='*80}\n\n"
    report += f"This report projects your total financial balance (Bank + Wallet + Savings + Investments + Money Lent).\n"
    report += f"It assumes you will meet your daily savings goal every day.\n\n"
    report += f"Bank Account Balance:       €{bank_balance:>10.2f}\n"
    report += f"Wallet Balance:             €{wallet_balance:>10.2f}\n"
    report += f"Current Savings Balance:    €{savings_balance:>10.2f}\n"
    report += f"Current Investment Balance: €{investment_balance:>10.2f}\n"
    report += f"Money Lent Balance:         €{money_lent_balance:>10.2f}\n"
    report += f"-----------------------------------------\n"
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
        report += f"{current_date.strftime('%Y-%m'):<15} €{monthly_savings:<28.2f} €{projected_balance:10.2f}\n"
        current_date = next_month_date

    report += f"{'-'*80}\n"
    return report