import { ArrowDownRight, ArrowUpRight, Plus, WalletCards } from "lucide-react";
import {
  categoryTotals,
  computeNetAvailableForSpending,
  currentMonth,
  dailyBudgetOverview,
  formatCurrency,
  netWorth
} from "../../shared/finance";
import { DEFAULT_BEHAVIOR_SETTINGS, type DefaultBehaviorSettings } from "../../shared/behavior-settings";
import { DEFAULT_RANGE_SETTINGS, type DefaultRangeSettings } from "../../shared/range-settings";
import type { FinanceDocument, TransactionType } from "../../shared/types";
import { Button, Card, EmptyState, Metric, PageHeader } from "./ui";

export function DashboardScreen({
  document,
  defaultBehaviors = DEFAULT_BEHAVIOR_SETTINGS,
  defaultRanges = DEFAULT_RANGE_SETTINGS,
  onAddTransaction,
  onNavigate
}: {
  document: FinanceDocument;
  defaultBehaviors?: DefaultBehaviorSettings;
  defaultRanges?: DefaultRangeSettings;
  onAddTransaction(type: TransactionType): void;
  onNavigate(page: string): void;
}) {
  const month = currentMonth();
  const available = computeNetAvailableForSpending(document, month);
  const daily = dailyBudgetOverview(
    document,
    month,
    defaultBehaviors.includeNegativeCarryover,
    new Date(),
    "transaction",
    defaultRanges.carryoverMonths
  );
  const flexibleBalance = daily.remainingBudget;
  const currentNetWorth = netWorth(document);
  const recent = [...document.expenses, ...document.incomes]
    .sort((first, second) => second.date.localeCompare(first.date))
    .slice(0, 6);
  const categories = categoryTotals(document, "Expense", month, month, false).slice(0, 5);
  const topCategory = categories[0];

  return (
    <div className="page dashboard-page">
      <PageHeader
        eyebrow={month}
        title="Your money, clearly"
        description="A live view of the shared finance file and this month’s room to spend."
        action={
          <div className="button-group">
            <Button variant="secondary" onClick={() => onAddTransaction("Income")}>
              <ArrowUpRight size={16} /> Add income
            </Button>
            <Button onClick={() => onAddTransaction("Expense")}>
              <Plus size={16} /> Add expense
            </Button>
          </div>
        }
      />

      <div className="metric-grid">
        <Metric label="Net worth" value={formatCurrency(currentNetWorth)} detail="Across all tracked balances" tone={currentNetWorth > 0 ? "positive" : currentNetWorth < 0 ? "warning" : undefined} />
        <Metric label="Flexible budget" value={formatCurrency(available)} detail="After recurring costs and savings" />
        <Metric label="Today’s target" value={formatCurrency(daily.dailyTarget)} detail={daily.daysRemaining + " days remaining"} tone={daily.dailyTarget > 0 ? "positive" : "warning"} />
        <Metric label="Flexible balance" value={formatCurrency(flexibleBalance)} detail={defaultBehaviors.includeNegativeCarryover ? "After fixed costs, savings, and carryover" : "After fixed costs and savings"} tone={flexibleBalance > 0 ? "positive" : flexibleBalance < 0 ? "warning" : undefined} />
      </div>

      <div className="dashboard-grid">
        <Card className="dashboard-focus">
          <div className="card-heading">
            <div>
              <p className="eyebrow">Spending pace</p>
              <h2>{daily.remainingBudget > 0 ? "You are in control" : "Time to reset the pace"}</h2>
            </div>
            <WalletCards size={24} />
          </div>
          <p>
            {daily.remainingBudget > 0
              ? "You can spend up to " + formatCurrency(daily.dailyTarget) + " each remaining day."
              : "Your flexible budget is depleted. Keep upcoming spending at zero to avoid widening the deficit."}
          </p>
          <div className="budget-track" aria-label="Budget remaining">
            <span style={{ width: Math.max(0, Math.min(100, available ? (daily.remainingBudget / available) * 100 : 0)) + "%" }} />
          </div>
          <div className="card-action-row">
            <span>{formatCurrency(Math.max(daily.remainingBudget, 0))} left</span>
            <Button variant="ghost" onClick={() => onNavigate("budget")}>View budget</Button>
          </div>
        </Card>

        <Card>
          <div className="card-heading">
            <div>
              <p className="eyebrow">Top spending</p>
              <h2>{topCategory?.name ?? "No expenses yet"}</h2>
            </div>
            <ArrowDownRight size={24} />
          </div>
          {categories.length ? (
            <div className="rank-list">
              {categories.map((category) => (
                <div key={category.name}>
                  <span>{category.name}</span>
                  <strong>{formatCurrency(category.value)}</strong>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted-copy">Expense categories will appear here after your first entry.</p>
          )}
        </Card>
      </div>

      <Card className="recent-card">
        <div className="card-heading">
          <div>
            <p className="eyebrow">Latest activity</p>
            <h2>Recent transactions</h2>
          </div>
          <Button variant="ghost" onClick={() => onNavigate("transactions")}>View all</Button>
        </div>
        {recent.length ? (
          <div className="transaction-list">
            {recent.map((transaction, index) => {
              const expense = document.expenses.includes(transaction);
              return (
                <div className="transaction-row" key={transaction.id ?? transaction.date + index}>
                  <div className={"transaction-icon " + (expense ? "expense" : "income")}>
                    {expense ? <ArrowDownRight size={17} /> : <ArrowUpRight size={17} />}
                  </div>
                  <div>
                    <strong>{transaction.description || transaction.category}</strong>
                    <span>{transaction.category} · {transaction.date}</span>
                  </div>
                  <strong className={expense ? "amount-expense" : "amount-income"}>
                    {expense ? "−" : "+"}{formatCurrency(transaction.amount)}
                  </strong>
                </div>
              );
            })}
          </div>
        ) : (
          <EmptyState
            title="Start with your first transaction"
            detail="Income and expenses added here are immediately saved into the selected JSON file."
            action={<Button onClick={() => onAddTransaction("Expense")}>Add an expense</Button>}
          />
        )}
      </Card>
    </div>
  );
}
