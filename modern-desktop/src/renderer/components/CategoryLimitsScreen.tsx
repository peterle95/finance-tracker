import { CircleDollarSign, Plus, RefreshCw, Trash2 } from "lucide-react";
import { useState } from "react";
import {
  autoAssignCategoryBudgets,
  categoryBudgetPercentages,
  cloneDocument,
  computeNetAvailableForSpending,
  currentMonth,
  formatCurrency
} from "../../shared/finance";
import type { FinanceDocument } from "../../shared/types";
import { Button, Card, PageHeader } from "./ui";

export function CategoryLimitsScreen({
  document,
  onSave
}: {
  document: FinanceDocument;
  onSave(document: FinanceDocument): void;
}) {
  const month = currentMonth();
  const [categoryDraft, setCategoryDraft] = useState("");
  const [message, setMessage] = useState("");
  const limits = categoryBudgetPercentages(document);
  const flexibleBudget = computeNetAvailableForSpending(document, month);
  const allocatedPercent = document.categories.Expense.reduce((total, category) => total + (limits[category] ?? 0), 0);
  const remainingPercent = 100 - allocatedPercent;

  function updateLimits(category: string, rawValue: number) {
    const value = Math.max(0, Math.min(100, Math.round(rawValue * 10) / 10));
    const next = cloneDocument(document);
    next.budget_settings.category_budgets = {
      ...(next.budget_settings.category_budgets ?? {}),
      Expense: {
        ...(next.budget_settings.category_budgets?.Expense ?? {}),
        [category]: value
      }
    };
    onSave(next);
  }

  function autoAssign() {
    const result = autoAssignCategoryBudgets(document, month);
    setMessage(result.message);
    if (!Object.keys(result.percentages).length) {
      return;
    }
    const next = cloneDocument(document);
    next.budget_settings.category_budgets = {
      ...(next.budget_settings.category_budgets ?? {}),
      Expense: result.percentages
    };
    onSave(next);
  }

  function addCategory(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const category = categoryDraft.trim();
    if (!category || document.categories.Expense.includes(category)) {
      return;
    }
    const next = cloneDocument(document);
    next.categories.Expense.push(category);
    next.budget_settings.category_budgets = {
      ...(next.budget_settings.category_budgets ?? {}),
      Expense: {
        ...(next.budget_settings.category_budgets?.Expense ?? {}),
        [category]: 0
      }
    };
    onSave(next);
    setCategoryDraft("");
  }

  function removeCategory(category: string) {
    if (document.categories.Expense.length <= 1) {
      setMessage("Keep at least one expense category.");
      return;
    }
    const next = cloneDocument(document);
    next.categories.Expense = next.categories.Expense.filter((entry) => entry !== category);
    const nextLimits = { ...(next.budget_settings.category_budgets?.Expense ?? {}) };
    delete nextLimits[category];
    next.budget_settings.category_budgets = {
      ...(next.budget_settings.category_budgets ?? {}),
      Expense: nextLimits
    };
    onSave(next);
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="Budget allocation"
        title="Category limits"
        description="Turn this month’s flexible budget into clear category envelopes with a visible euro amount for every limit."
        action={<Button variant="secondary" onClick={autoAssign}><RefreshCw size={16} /> Auto-assign from spending</Button>}
      />

      <div className="metric-grid">
        <Card className="metric"><p>Flexible budget</p><strong>{formatCurrency(flexibleBudget)}</strong><span>{month}</span></Card>
        <Card className="metric metric-positive"><p>Allocated</p><strong>{allocatedPercent.toFixed(1)}%</strong><span>{formatCurrency(flexibleBudget * allocatedPercent / 100)}</span></Card>
        <Card className={"metric " + (remainingPercent < 0 ? "metric-warning" : "")}><p>{remainingPercent < 0 ? "Over-allocated" : "Unallocated"}</p><strong>{Math.abs(remainingPercent).toFixed(1)}%</strong><span>{formatCurrency(Math.abs(flexibleBudget * remainingPercent / 100))}</span></Card>
        <Card className="metric"><p>Categories</p><strong>{document.categories.Expense.length}</strong><span>Expense envelopes</span></Card>
      </div>

      <Card className="category-limits-card">
        <div className="card-heading">
          <div><p className="eyebrow">Visible allocations</p><h2>How your flexible budget is split</h2></div>
          <CircleDollarSign size={22} />
        </div>
        <div className="category-limit-head">
          <span>Category</span><span>Limit</span><span>Allocation</span><span />
        </div>
        <div className="category-limit-list">
          {document.categories.Expense.map((category) => {
            const percentage = limits[category] ?? 0;
            const allocation = flexibleBudget * percentage / 100;
            return (
              <div className="category-limit-row" key={category}>
                <div><strong>{category}</strong><small>{formatCurrency(allocation)} of this month’s flexible budget</small></div>
                <div className="limit-control">
                  <input aria-label={category + " limit"} type="range" min="0" max="100" step="0.5" value={percentage} onChange={(event) => updateLimits(category, Number(event.target.value))} />
                  <input aria-label={category + " percentage"} type="number" min="0" max="100" step="0.5" value={percentage} onChange={(event) => updateLimits(category, Number(event.target.value))} />
                  <span>%</span>
                </div>
                <strong className="allocation-value">{formatCurrency(allocation)}</strong>
                <button className="icon-button danger-icon" onClick={() => removeCategory(category)} aria-label={"Remove " + category}><Trash2 size={16} /></button>
              </div>
            );
          })}
        </div>
      </Card>

      <div className="two-column">
        <Card>
          <div className="card-heading"><div><p className="eyebrow">Add category</p><h2>Create another envelope</h2></div></div>
          <form className="inline-form short-form" onSubmit={addCategory}>
            <input value={categoryDraft} onChange={(event) => setCategoryDraft(event.target.value)} placeholder="New expense category" />
            <Button type="submit"><Plus size={16} /> Add category</Button>
          </form>
        </Card>
        <Card className="allocation-note">
          <p className="eyebrow">Allocation guide</p>
          <h2>Every percentage maps to spendable money</h2>
          <p>Limits are based on monthly income, flexible income, recurring costs, and the daily savings target. Keep the total at or below 100% to avoid assigning the same euro twice.</p>
          {message ? <p className="status-message">{message}</p> : null}
        </Card>
      </div>
    </div>
  );
}
