import { ChevronLeft, ChevronRight, CircleDollarSign, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import {
  cloneDocument,
  currentMonth,
  dailyBudgetOverview,
  formatCurrency,
  getActiveFixedCosts,
  getMonthlyIncomeSources,
  isoToday,
  monthOffset,
  moneyLentFromLoans,
  roundCurrency
} from "../../shared/finance";
import { DEFAULT_BEHAVIOR_SETTINGS, type DefaultBehaviorSettings } from "../../shared/behavior-settings";
import type { BudgetSettings, FinanceDocument, FixedCost, IncomeSource, Loan } from "../../shared/types";
import { DEFAULT_RANGE_SETTINGS, type DefaultRangeSettings } from "../../shared/range-settings";
import { Button, Card, PageHeader } from "./ui";
import { BudgetDepletionChart } from "./BudgetDepletionChart";
import { LoanEditor } from "./LoanEditor";

interface BudgetScreenProps {
  document: FinanceDocument;
  defaultRanges?: DefaultRangeSettings;
  defaultBehaviors?: DefaultBehaviorSettings;
  onSave(document: FinanceDocument): void;
}

const emptyIncome = (): IncomeSource => ({
  amount: 0,
  description: "",
  start_date: isoToday(),
  end_date: null
});

const emptyCost = (): FixedCost => ({
  amount: 0,
  description: "",
  desc: "",
  start_date: isoToday(),
  end_date: null
});

const emptyLoan = () => ({ borrower: "", amount: "", description: "", date: isoToday() });

export function BudgetScreen({ document, defaultRanges = DEFAULT_RANGE_SETTINGS, defaultBehaviors = DEFAULT_BEHAVIOR_SETTINGS, onSave }: BudgetScreenProps) {
  const [month, setMonth] = useState(currentMonth());
  const settings = document.budget_settings;
  const [includeCarryover, setIncludeCarryover] = useState(defaultBehaviors.includeNegativeCarryover);
  const [carryoverMonths, setCarryoverMonths] = useState(defaultRanges.carryoverMonths);
  const [incomeDraft, setIncomeDraft] = useState<IncomeSource>(emptyIncome);
  const [costDraft, setCostDraft] = useState<FixedCost>(emptyCost);
  const [loanDraft, setLoanDraft] = useState(emptyLoan);
  const [editingLoan, setEditingLoan] = useState<Loan | null>(null);
  const [editingCostIndex, setEditingCostIndex] = useState<number | null>(null);
  const [showFinishedCosts, setShowFinishedCosts] = useState(false);
  const [balanceView, setBalanceView] = useState<"income" | "costs" | null>(null);
  const overview = dailyBudgetOverview(document, month, true, new Date(), "transaction", carryoverMonths);
  const incomeSources = getMonthlyIncomeSources(document, month);
  const fixedCosts = getActiveFixedCosts(document, month);
  const costsWithIndexes = (settings.fixed_costs ?? []).map((cost, index) => ({ cost, index }));
  const ongoingCosts = costsWithIndexes.filter(({ cost }) => !cost.end_date || cost.end_date >= isoToday());
  const finishedCosts = costsWithIndexes.filter(({ cost }) => Boolean(cost.end_date && cost.end_date < isoToday()));
  const displayedCosts = showFinishedCosts ? [...ongoingCosts, ...finishedCosts] : ongoingCosts;
  const visibleOverview = dailyBudgetOverview(document, month, includeCarryover, new Date(), "transaction", carryoverMonths);

  function updateSettings(update: (next: BudgetSettings) => void) {
    const next = cloneDocument(document);
    update(next.budget_settings);
    onSave(next);
  }

  function saveBalances(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    updateSettings((next) => {
      next.bank_account_balance = roundCurrency(Number(form.get("bank") ?? 0));
      next.wallet_balance = roundCurrency(Number(form.get("wallet") ?? 0));
      next.savings_balance = roundCurrency(Number(form.get("savings") ?? 0));
      next.investment_balance = roundCurrency(Number(form.get("investments") ?? 0));
      if (!(next.loans ?? []).length) {
        next.money_lent_balance = roundCurrency(Number(form.get("moneyLent") ?? 0));
      }
      next.daily_savings_goal = roundCurrency(Number(form.get("dailySavings") ?? 0));
    });
  }

  function addIncome(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!incomeDraft.description || incomeDraft.amount <= 0) {
      return;
    }
    updateSettings((next) => {
      const existing = Array.isArray(next.monthly_income)
        ? next.monthly_income
        : typeof next.monthly_income === "number"
          ? [{
            amount: next.monthly_income,
            description: "Base Income",
            start_date: "2000-01-01",
            end_date: null
          }]
          : [];
      next.monthly_income = [...existing, incomeDraft];
    });
    setIncomeDraft(emptyIncome());
  }

  function saveCost(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!costDraft.description || costDraft.amount <= 0) {
      return;
    }
    updateSettings((next) => {
      const cost = {
        ...costDraft,
        desc: costDraft.description
      };
      next.fixed_costs = editingCostIndex === null
        ? [...(next.fixed_costs ?? []), cost]
        : (next.fixed_costs ?? []).map((entry, index) => index === editingCostIndex ? cost : entry);
    });
    setCostDraft(emptyCost());
    setEditingCostIndex(null);
  }

  function editCost(cost: FixedCost, index: number) {
    setEditingCostIndex(index);
    setCostDraft({
      ...cost,
      description: cost.description ?? cost.desc ?? "",
      desc: cost.desc ?? cost.description ?? ""
    });
  }

  function saveLoan(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const amount = roundCurrency(Number(loanDraft.amount));
    if (!loanDraft.borrower || !Number.isFinite(amount) || amount === 0) {
      return;
    }
    const loan: Loan = {
      id: typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
      borrower: loanDraft.borrower,
      amount,
      description: loanDraft.description,
      date: loanDraft.date
    };
    updateSettings((next) => {
      const loans = [...(next.loans ?? []), loan];
      next.loans = loans;
      next.money_lent_balance = moneyLentFromLoans(loans);
    });
    setLoanDraft(emptyLoan());
  }

  function saveLoanChanges(loan: Loan) {
    updateSettings((next) => {
      const loans = (next.loans ?? []).map((entry) => entry.id === loan.id ? loan : entry);
      next.loans = loans;
      next.money_lent_balance = moneyLentFromLoans(loans);
    });
    setEditingLoan(null);
  }

  function markLoanReturned(loan: Loan) {
    updateSettings((next) => {
      const loans = (next.loans ?? []).filter((entry) => entry.id !== loan.id);
      next.loans = loans;
      next.money_lent_balance = moneyLentFromLoans(loans);
    });
    if (editingLoan?.id === loan.id) {
      setEditingLoan(null);
    }
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="Monthly plan"
        title="Budget"
        description="Balance accounts, recurring commitments, flexible limits, and lending in one clear plan."
        action={<div className="budget-month-navigation" aria-label="Budget month navigation">
          <Button type="button" variant="ghost" aria-label="Previous month" onClick={() => setMonth(monthOffset(month, -1))}><ChevronLeft size={17} /></Button>
          <input aria-label="Budget month" type="month" value={month} onChange={(event) => {
            if (event.target.value) {
              setMonth(event.target.value);
            }
          }} />
          <Button type="button" variant="ghost" aria-label="Next month" onClick={() => setMonth(monthOffset(month, 1))}><ChevronRight size={17} /></Button>
        </div>}
      />

      <div className="metric-grid">
        <Card className="metric"><p>Base income</p><strong>{formatCurrency(overview.baseIncome)}</strong><span>{incomeSources.length} active source(s)</span></Card>
        <Card className="metric"><p>Fixed costs</p><strong>{formatCurrency(overview.fixedCosts)}</strong><span>{fixedCosts.length} active commitment(s)</span></Card>
        <Card className={"metric " + (visibleOverview.dailyTarget > 0 ? "metric-positive" : "metric-warning")}><p>Today's Target</p><strong>{formatCurrency(visibleOverview.dailyTarget)}</strong><span>{visibleOverview.daysRemaining} days left</span></Card>
        <Card className={"metric " + (visibleOverview.remainingBudget < 0 ? "metric-warning" : "metric-positive")}><p>Flexible balance</p><strong>{formatCurrency(visibleOverview.remainingBudget)}</strong><span>{includeCarryover ? "Negative carryover included" : "No carryover"}</span></Card>
      </div>

      <div className="two-column">
        <Card>
          <div className="card-heading">
            <div><p className="eyebrow">Daily pace</p><h2>Spend with a target</h2></div>
            <CircleDollarSign size={24} />
          </div>
          <dl className="summary-list">
            <div><dt>Base income</dt><dd>{formatCurrency(visibleOverview.baseIncome)}</dd></div>
            <div><dt>Flexible income</dt><dd>{formatCurrency(visibleOverview.flexibleIncome)}</dd></div>
            <div><dt>Fixed costs</dt><dd>−{formatCurrency(visibleOverview.fixedCosts)}</dd></div>
            <div><dt>Monthly savings target</dt><dd>−{formatCurrency(visibleOverview.savingsGoal)}</dd></div>
            {includeCarryover ? <div><dt>Negative carryover ({carryoverMonths} months)</dt><dd>{formatCurrency(visibleOverview.carryover)}</dd></div> : null}
          </dl>
          <div className="carryover-controls">
            <label className="check-row">
              <input type="checkbox" checked={includeCarryover} onChange={(event) => setIncludeCarryover(event.target.checked)} />
              <span>Include previous deficits</span>
            </label>
            {includeCarryover ? <label className="control-label carryover-months"><span>Months back</span><input aria-label="Carryover months" type="number" min="1" max="24" value={carryoverMonths} onChange={(event) => {
              const value = Number(event.target.value);
              setCarryoverMonths(Number.isFinite(value) ? Math.min(24, Math.max(1, Math.floor(value))) : 1);
            }} /></label> : null}
          </div>
        </Card>

        <Card>
          <div className="card-heading">
            <div><p className="eyebrow">Balances</p><h2>What you own today</h2></div>
            <div className="button-group">
              <Button type="button" variant="ghost" onClick={() => setBalanceView("income")}>Fixed income</Button>
              <Button type="button" variant="ghost" onClick={() => setBalanceView("costs")}>Fixed costs</Button>
            </div>
          </div>
          <form className="form-grid compact-form" onSubmit={saveBalances}>
            <label><span>Bank</span><input name="bank" type="number" step="0.01" defaultValue={settings.bank_account_balance ?? 0} /></label>
            <label><span>Wallet</span><input name="wallet" type="number" step="0.01" defaultValue={settings.wallet_balance ?? 0} /></label>
            <label><span>Savings</span><input name="savings" type="number" step="0.01" defaultValue={settings.savings_balance ?? 0} /></label>
            <label><span>Investments</span><input name="investments" type="number" step="0.01" defaultValue={settings.investment_balance ?? 0} /></label>
            <label><span>Money lent / owed</span><input name="moneyLent" type="number" step="0.01" defaultValue={settings.money_lent_balance ?? 0} disabled={(settings.loans ?? []).length > 0} />{(settings.loans ?? []).length ? <small>Calculated from active loan entries.</small> : null}</label>
            <label><span>Daily savings goal</span><input name="dailySavings" type="number" step="0.01" min="0" defaultValue={settings.daily_savings_goal ?? 0} /></label>
            <div className="span-two form-actions"><Button type="submit">Save balances</Button></div>
          </form>
        </Card>
      </div>

      <Card>
        <div className="card-heading"><div><p className="eyebrow">Lending</p><h2>Money lent and owed</h2></div></div>
        <div className="mini-list">
          {(settings.loans ?? []).length ? (settings.loans ?? []).map((loan) => (
            <div
              key={loan.id}
              className="loan-row"
            >
              <span>
                <strong>{loan.borrower}</strong>
                <small>{loan.description || loan.date}</small>
              </span>
              <strong>{formatCurrency(loan.amount)}</strong>
              <Button variant="ghost" aria-label={"Modify loan for " + loan.borrower} onClick={() => setEditingLoan(loan)}>modify</Button>
              <Button variant="ghost" onClick={() => markLoanReturned(loan)}>Returned</Button>
            </div>
          )) : <p className="muted-copy">No active loans.</p>}
        </div>
        <form className="inline-form loan-form" onSubmit={saveLoan}>
          <input value={loanDraft.borrower} onChange={(event) => setLoanDraft({ ...loanDraft, borrower: event.target.value })} placeholder="Borrower" />
          <input value={loanDraft.amount} onChange={(event) => setLoanDraft({ ...loanDraft, amount: event.target.value })} type="number" step="0.01" placeholder="Amount (negative if owed)" />
          <input value={loanDraft.description} onChange={(event) => setLoanDraft({ ...loanDraft, description: event.target.value })} placeholder="Description" />
          <input value={loanDraft.date} onChange={(event) => setLoanDraft({ ...loanDraft, date: event.target.value })} type="date" />
          <Button type="submit" variant="secondary"><Plus size={16} /> Add loan</Button>
        </form>
      </Card>
      <LoanEditor
        open={editingLoan !== null}
        loan={editingLoan}
        onOpenChange={(open) => { if (!open) setEditingLoan(null); }}
        onSave={saveLoanChanges}
      />
      {balanceView === "income" ? <Card className="budget-detail-view">
          <div className="card-heading">
            <div><p className="eyebrow">Fixed income</p><h2>Income sources</h2></div>
            <Button type="button" variant="ghost" onClick={() => setBalanceView(null)}>Close fixed income</Button>
          </div>
          <div className="mini-list">
            {Array.isArray(settings.monthly_income) && settings.monthly_income.length ? settings.monthly_income.map((income, index) => (
              <div key={income.description + index}>
                <span><strong>{income.description}</strong><small>{income.start_date} → {income.end_date ?? "ongoing"}</small></span>
                <strong>{formatCurrency(income.amount)}</strong>
                <button className="icon-button danger-icon" onClick={() => updateSettings((next) => {
                  next.monthly_income = (Array.isArray(next.monthly_income) ? next.monthly_income : []).filter((_entry, row) => row !== index);
                })} aria-label="Remove income source"><Trash2 size={15} /></button>
              </div>
            )) : <p className="muted-copy">No recurring income sources yet.</p>}
          </div>
          <form className="inline-form" onSubmit={addIncome}>
            <input value={incomeDraft.description} onChange={(event) => setIncomeDraft({ ...incomeDraft, description: event.target.value })} placeholder="Description" />
            <input value={incomeDraft.amount || ""} onChange={(event) => setIncomeDraft({ ...incomeDraft, amount: Number(event.target.value) })} type="number" step="0.01" placeholder="Amount" />
            <input value={incomeDraft.start_date} onChange={(event) => setIncomeDraft({ ...incomeDraft, start_date: event.target.value })} type="date" />
            <input value={incomeDraft.end_date ?? ""} onChange={(event) => setIncomeDraft({ ...incomeDraft, end_date: event.target.value || null })} type="date" />
            <Button type="submit" variant="secondary"><Plus size={16} /> Add</Button>
          </form>
        </Card> : null}

      {balanceView === "costs" ? <Card className="budget-detail-view">
          <div className="card-heading">
            <div><p className="eyebrow">Fixed costs</p><h2>Recurring costs</h2></div>
            <Button type="button" variant="ghost" onClick={() => setBalanceView(null)}>Close fixed costs</Button>
            {finishedCosts.length ? <Button type="button" variant="ghost" onClick={() => setShowFinishedCosts((value) => !value)}>
              {showFinishedCosts ? "Hide finished" : "Show finished (" + finishedCosts.length + ")"}
            </Button> : null}
          </div>
          <div className="mini-list">
            {displayedCosts.length ? displayedCosts.map(({ cost, index }) => (
              <div key={(cost.description ?? cost.desc ?? "Cost") + index} className={editingCostIndex === index ? "loan-row selected" : "loan-row"}>
                <button type="button" className="loan-edit-target" aria-label={"Edit fixed cost " + (cost.description ?? cost.desc ?? "")} onClick={() => editCost(cost, index)}>
                <span><strong>{cost.description ?? cost.desc}</strong><small>{cost.start_date} → {cost.end_date ?? "ongoing"}</small></span>
                <strong>{formatCurrency(cost.amount)}</strong>
                </button>
                <button className="icon-button danger-icon" onClick={() => updateSettings((next) => {
                  next.fixed_costs = (next.fixed_costs ?? []).filter((_entry, row) => row !== index);
                })} aria-label="Remove fixed cost"><Trash2 size={15} /></button>
              </div>
            )) : <p className="muted-copy">{showFinishedCosts ? "No recurring costs yet." : "No ongoing recurring costs."}</p>}
          </div>
          <form className="inline-form" onSubmit={saveCost}>
            <input value={costDraft.description} onChange={(event) => setCostDraft({ ...costDraft, description: event.target.value, desc: event.target.value })} placeholder="Description" />
            <input value={costDraft.amount || ""} onChange={(event) => setCostDraft({ ...costDraft, amount: Number(event.target.value) })} type="number" step="0.01" placeholder="Amount" />
            <input value={costDraft.start_date} onChange={(event) => setCostDraft({ ...costDraft, start_date: event.target.value })} type="date" />
            <input value={costDraft.end_date ?? ""} onChange={(event) => setCostDraft({ ...costDraft, end_date: event.target.value || null })} type="date" />
            <Button type="submit" variant="secondary"><Plus size={16} /> {editingCostIndex === null ? "Add" : "Save changes"}</Button>
            {editingCostIndex !== null ? <Button type="button" variant="ghost" onClick={() => {
              setEditingCostIndex(null);
              setCostDraft(emptyCost());
            }}>Cancel</Button> : null}
          </form>
        </Card> : null}

      <BudgetDepletionChart document={document} month={month} includeNegativeCarryover={includeCarryover} carryoverMonths={carryoverMonths} />

    </div>
  );
}
