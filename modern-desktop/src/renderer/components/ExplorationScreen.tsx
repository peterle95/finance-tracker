import { ArrowLeft, Check, LineChart, Pencil, RotateCcw, Save, Trash2, TrendingUp, Undo2, WalletCards, X } from "lucide-react";
import { useEffect, useState } from "react";
import {
  cloneDocument,
  currentMonth,
  formatCurrency,
  getActiveFixedCosts,
  getGoals,
  goalSummary,
  isoToday,
  makeTransaction,
  monthOffset,
  netWorth,
  projection,
  rawNetAvailableForSpending,
  roundCurrency,
  snapshots
} from "../../shared/finance";
import type { FinanceDocument, FinanceTransaction, TransactionType } from "../../shared/types";
import { Button, Card, Metric, PageHeader } from "./ui";
import { JourneyChart } from "./JourneyChart";

type ExplorationView = "landing" | "simulator" | "journey" | "balancer";

const workflows = [
  {
    view: "simulator" as const,
    eyebrow: "Scenario lab",
    title: "Future Simulator",
    description: "Test future income, spending, and decisions without changing your saved finance file.",
    action: "Open Future Simulator",
    icon: TrendingUp
  },
  {
    view: "journey" as const,
    eyebrow: "Long view",
    title: "Net-Worth Journey",
    description: "Trace your balance history and see how today’s position can shape what comes next.",
    action: "Open Net-Worth Journey",
    icon: LineChart
  },
  {
    view: "balancer" as const,
    eyebrow: "Trade-off lab",
    title: "Budget Balancer",
    description: "Preview how shifting flexible spending could affect cash flow and future goals.",
    action: "Open Budget Balancer",
    icon: WalletCards
  }
];

interface ExplorationScreenProps {
  document: FinanceDocument;
  onConfirm?(document: FinanceDocument): void;
  onDirtyChange?(dirty: boolean): void;
}

interface ScenarioEventDraft {
  type: TransactionType;
  amount: string;
  category: string;
  description: string;
  date: string;
}

interface ScenarioEventChange extends FinanceTransaction {
  type: TransactionType;
}

interface BudgetChange {
  category: string;
  from: number;
  to: number;
}

interface BudgetPreview {
  values: Record<string, number>;
  plannedPercent: number;
  flexibleBudget: number;
  projectedCash: number;
  emergencyBuffer: number;
  goalShortfall: number;
  reducedEmergencyBuffer: boolean;
  negativeCash: boolean;
}

interface ScenarioDriverChange {
  label: string;
  baseline: number;
  scenario: number;
}

interface ScenarioComparison {
  baselineNetWorth: number;
  scenarioNetWorth: number;
  netWorthDifference: number;
  baselineCashFlow: number;
  scenarioCashFlow: number;
  cashFlowDifference: number;
  baselineGoalDate: string;
  scenarioGoalDate: string;
  goalDateChange: string;
  drivers: ScenarioDriverChange[];
}

const PROTECTED_CATEGORY_PATTERN = /rent|mortgage|utility|utilities|debt|loan|insurance|saving|savings|commitment|obligation|tax|minimum/i;

function isProtectedCategory(category: string): boolean {
  return PROTECTED_CATEGORY_PATTERN.test(category);
}

function shiftIsoDate(value: string, days: number): string {
  const date = new Date(value + "T12:00:00Z");
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || Number.isNaN(date.getTime()) || date.toISOString().slice(0, 10) !== value) {
    return "No target date";
  }
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

function goalDateComparison(document: FinanceDocument, scenarioNet: number): Pick<ScenarioComparison, "baselineGoalDate" | "scenarioGoalDate" | "goalDateChange"> {
  const goal = getGoals(document)
    .filter((entry) => entry.target_date && shiftIsoDate(entry.target_date, 0) !== "No target date")
    .sort((first, second) => (first.target_date ?? "").localeCompare(second.target_date ?? ""))[0];
  const baselineGoalDate = goal?.target_date ?? "No target date";
  if (!goal || scenarioNet === 0) {
    return { baselineGoalDate, scenarioGoalDate: baselineGoalDate, goalDateChange: "Unchanged" };
  }
  const dailyFunding = Math.max(goal.target_amount / 365, 1);
  const shift = Math.round(scenarioNet / dailyFunding);
  if (shift === 0) {
    return { baselineGoalDate, scenarioGoalDate: baselineGoalDate, goalDateChange: "Unchanged" };
  }
  const scenarioGoalDate = shiftIsoDate(baselineGoalDate, -shift);
  const absoluteShift = Math.abs(shift);
  return {
    baselineGoalDate,
    scenarioGoalDate,
    goalDateChange: shift > 0 ? "Earlier by " + absoluteShift + " day(s)" : "Later by " + absoluteShift + " day(s)"
  };
}

function rebalanceBudgetValues(
  current: Record<string, number>,
  category: string,
  requested: number,
  protectedCategories: Set<string>
): Record<string, number> {
  if (protectedCategories.has(category)) {
    return { ...current };
  }
  const entries = Object.entries(current);
  const total = entries.reduce((sum, [, value]) => sum + value, 0);
  const protectedTotal = entries
    .filter(([name]) => protectedCategories.has(name))
    .reduce((sum, [, value]) => sum + value, 0);
  const rounded = (value: number) => Math.round(value * 10) / 10;
  const boundedRequest = Math.max(0, Math.min(Number.isFinite(requested) ? requested : 0, 100));
  const plannedTotal = total === 0 ? 100 : total;
  const target = Math.max(0, Math.min(boundedRequest, plannedTotal - protectedTotal));

  const others = entries.filter(([name]) => name !== category && !protectedCategories.has(name));
  if (others.length === 0) {
    return { ...current };
  }
  const result = { ...current, [category]: rounded(target) };
  const remaining = Math.max(0, plannedTotal - protectedTotal - target);
  const currentOtherTotal = others.reduce((sum, [, value]) => sum + value, 0);
  let assigned = 0;
  others.forEach(([name, value], index) => {
    const nextValue = index === others.length - 1
      ? remaining - assigned
      : currentOtherTotal > 0 ? remaining * value / currentOtherTotal : index === 0 ? remaining : 0;
    result[name] = rounded(nextValue);
    assigned += result[name];
  });
  return result;
}

function signedCurrency(value: number): string {
  return (value >= 0 ? "+" : "−") + formatCurrency(Math.abs(value));
}

function ScenarioComparisonCard({ comparison }: { comparison: ScenarioComparison }) {
  return (
    <Card className="scenario-comparison-card">
      <div className="card-heading"><div><p className="eyebrow">Scenario comparison</p><h2>Baseline versus active scenario</h2></div><TrendingUp size={24} /></div>
      <div className="scenario-compare-grid">
        <div><p className="eyebrow">Baseline projection</p><strong>{formatCurrency(comparison.baselineNetWorth)}</strong><small>12-month projection</small></div>
        <div className="scenario-active"><p className="eyebrow">Active scenario</p><strong>{formatCurrency(comparison.scenarioNetWorth)}</strong><small>Projection plus draft events</small></div>
      </div>
      <div className="scenario-difference-grid">
        <Metric label="Net-worth difference" value={signedCurrency(comparison.netWorthDifference)} detail="Baseline to scenario" tone={comparison.netWorthDifference < 0 ? "warning" : "positive"} />
        <Metric label="Cash-flow difference" value={signedCurrency(comparison.cashFlowDifference)} detail="12-month projection" tone={comparison.cashFlowDifference < 0 ? "warning" : "positive"} />
        <Metric label="Goal-date change" value={comparison.goalDateChange} detail={comparison.baselineGoalDate + " → " + comparison.scenarioGoalDate} tone={comparison.goalDateChange.startsWith("Later") ? "warning" : "default"} />
      </div>
      <div className="scenario-driver-list">
        <p className="eyebrow">Driver differences</p>
        {comparison.drivers.map((driver) => <div key={driver.label}><span>{driver.label}</span><strong>{signedCurrency(driver.scenario - driver.baseline)}</strong></div>)}
      </div>
      <div className="scenario-comparison-actions">
        <Button variant="secondary" disabled>Compare another scenario</Button>
        <small>One active scenario supported. Multi-scenario comparison is coming later.</small>
      </div>
    </Card>
  );
}

function FocusedView({
  view,
  document,
  categories,
  eventCategories,
  scenarioEvents,
  editingEventId,
  budgetPreview,
  comparison,
  protectedCategories,
  eventDraft,
  onBack,
  onEventDraftChange,
  onAddEvent,
  onEditEvent,
  onRemoveEvent,
  onCancelEventEdit,
  onBudgetChange
}: {
  view: Exclude<ExplorationView, "landing">;
  document: FinanceDocument;
  categories: string[];
  eventCategories: Record<TransactionType, string[]>;
  scenarioEvents: ScenarioEventChange[];
  editingEventId: string | null;
  budgetPreview: BudgetPreview;
  comparison: ScenarioComparison;
  protectedCategories: Set<string>;
  eventDraft: ScenarioEventDraft;
  onBack(): void;
  onEventDraftChange(update: Partial<ScenarioEventDraft>): void;
  onAddEvent(event: React.FormEvent<HTMLFormElement>): void;
  onEditEvent(event: ScenarioEventChange): void;
  onRemoveEvent(event: ScenarioEventChange): void;
  onCancelEventEdit(): void;
  onBudgetChange(category: string, value: string): void;
}) {
  const workflow = workflows.find((entry) => entry.view === view)!;
  const Icon = workflow.icon;
  const copy = view === "simulator"
    ? "Build temporary what-if plans here. Scenario edits will stay in memory until you explicitly review and confirm them."
    : view === "journey"
      ? "Inspect recorded balances and future direction here. Historical data remains separate from projected outcomes."
      : "Preview flexible budget trade-offs here. Saved budgets remain unchanged while you compare options.";
  const detail = view === "simulator"
    ? "Add future events without touching saved transactions."
    : view === "journey"
      ? "Net-Worth Journey tools are ready for the next Exploration phase."
      : "Adjust temporary category allocations without changing saved budgets.";
  const [feedbackActive, setFeedbackActive] = useState(false);

  useEffect(() => {
    if (view !== "balancer") {
      return;
    }
    setFeedbackActive(false);
    const frame = window.requestAnimationFrame(() => setFeedbackActive(true));
    const timeout = window.setTimeout(() => setFeedbackActive(false), 320);
    return () => {
      window.cancelAnimationFrame(frame);
      window.clearTimeout(timeout);
    };
  }, [budgetPreview.emergencyBuffer, budgetPreview.goalShortfall, budgetPreview.projectedCash, view]);
  return (
    <div className="page exploration-page">
      <PageHeader
        eyebrow={workflow.eyebrow}
        title={workflow.title}
        description={copy}
        action={<Button variant="secondary" onClick={onBack}><ArrowLeft size={16} /> Back to Exploration</Button>}
      />
      <div className="exploration-context-grid">
        <Metric label="Saved net worth" value={formatCurrency(netWorth(document))} detail="Saved finance data" tone="positive" />
        <Metric label="Scenario events" value={String(scenarioEvents.length)} detail="Temporary draft" />
        <Metric label="Workspace" value={workflow.title} detail="Drafts preserved while navigating" />
      </div>

      {view === "simulator" ? (
        <>
          <Card className="exploration-draft-card">
            <div className="card-heading"><div><p className="eyebrow">Temporary event</p><h2>Add future scenario event</h2></div><TrendingUp size={24} /></div>
            <p className="muted-copy">Only today and future dates are accepted. Event stays in memory until confirmation.</p>
            <form className="form-grid exploration-draft-form" onSubmit={onAddEvent}>
              <label><span>Type</span><select aria-label="Scenario event type" value={eventDraft.type} onChange={(event) => onEventDraftChange({ type: event.target.value as TransactionType })}><option value="Expense">Expense</option><option value="Income">Income</option></select></label>
              <label><span>Amount</span><input aria-label="Scenario event amount" type="number" min="0.01" step="0.01" value={eventDraft.amount} onChange={(event) => onEventDraftChange({ amount: event.target.value })} /></label>
              <label><span>Category</span><select aria-label="Scenario event category" value={eventDraft.category} onChange={(event) => onEventDraftChange({ category: event.target.value })}>{eventCategories[eventDraft.type].map((category) => <option key={category} value={category}>{category}</option>)}</select></label>
              <label><span>Description</span><input aria-label="Scenario event description" value={eventDraft.description} onChange={(event) => onEventDraftChange({ description: event.target.value })} /></label>
              <label><span>Date</span><input aria-label="Scenario event date" type="date" value={eventDraft.date} onChange={(event) => onEventDraftChange({ date: event.target.value })} /></label>
              <div className="span-two form-actions"><Button type="submit"><TrendingUp size={16} /> {editingEventId ? "Save event changes" : "Add temporary event"}</Button>{editingEventId ? <Button type="button" variant="ghost" onClick={onCancelEventEdit}>Cancel edit</Button> : null}</div>
            </form>
            {scenarioEvents.length ? <div className="exploration-draft-list"><strong>Temporary events</strong>{scenarioEvents.map((event) => <div key={event.id ?? event.date}><span><span>{event.description || event.category} · {event.date}</span><small>{event.category}</small></span><strong className={event.type === "Expense" ? "amount-expense" : "amount-income"}>{event.type === "Expense" ? "−" : "+"}{formatCurrency(event.amount)}</strong><span className="button-group"><button type="button" className="icon-button" aria-label={"Edit temporary event " + (event.description || event.category)} onClick={() => onEditEvent(event)}><Pencil size={15} /></button><button type="button" className="icon-button danger-icon" aria-label={"Remove temporary event " + (event.description || event.category)} onClick={() => onRemoveEvent(event)}><Trash2 size={15} /></button></span></div>)}</div> : <p className="muted-copy">No temporary events yet.</p>}
          </Card>
          <ScenarioComparisonCard comparison={comparison} />
        </>
      ) : null}

      {view === "journey" ? <JourneyChart document={document} /> : null}

      {view === "balancer" ? (
        <Card className="exploration-draft-card">
          <div className="card-heading"><div><p className="eyebrow">Temporary allocation</p><h2>Adjust flexible category budgets</h2></div><WalletCards size={24} /></div>
          <p className="muted-copy">These values are a preview. Saved budget settings stay unchanged until confirmation.</p>
          <div className="balancer-impact-grid">
            <Metric label="Projected cash" value={formatCurrency(budgetPreview.projectedCash)} detail={budgetPreview.negativeCash ? "Save blocked" : "After planned categories"} tone={budgetPreview.negativeCash ? "warning" : "positive"} />
            <Metric label="Emergency buffer" value={formatCurrency(budgetPreview.emergencyBuffer)} detail={budgetPreview.reducedEmergencyBuffer ? "Reduced by this preview" : "Preserved by this preview"} tone={budgetPreview.reducedEmergencyBuffer ? "warning" : "default"} />
            <Metric label="Goal shortfall" value={formatCurrency(budgetPreview.goalShortfall)} detail="Unfunded target amount" tone={budgetPreview.goalShortfall > 0 ? "warning" : "positive"} />
          </div>
          <p className={"balancer-feedback" + (feedbackActive ? " is-active" : "")} data-feedback="spring" role="status">Total planned budget stays at {budgetPreview.plannedPercent.toFixed(1)}%. Drag discretionary categories to reallocate it.</p>
          {budgetPreview.negativeCash ? <p className="balancer-warning" role="alert">Negative projected cash blocks save. Reduce planned categories before confirming.</p> : null}
          {budgetPreview.goalShortfall > 0 ? <p className="balancer-warning">Goal shortfall: {formatCurrency(budgetPreview.goalShortfall)} remains unfunded.</p> : null}
          {budgetPreview.reducedEmergencyBuffer ? <p className="balancer-warning">Emergency buffer is reduced by this preview.</p> : null}
          <div className="exploration-budget-grid">
            {categories.map((category) => protectedCategories.has(category) ? (
              <div className="balancer-category protected" key={category} aria-label={"Protected budget category " + category}>
                <span><strong>{category}</strong><small>Protected obligation</small></span>
                <strong>{budgetPreview.values[category] ?? 0}% · Locked</strong>
              </div>
            ) : (
              <label className="balancer-category" key={category}><span><strong>{category}</strong><small>Discretionary · {formatCurrency(budgetPreview.flexibleBudget * (budgetPreview.values[category] ?? 0) / 100)}</small></span><input aria-label={"Drag draft budget for " + category} type="range" min="0" max={Math.max(100, budgetPreview.plannedPercent)} step="0.5" value={budgetPreview.values[category] ?? 0} onChange={(event) => onBudgetChange(category, event.target.value)} /><input aria-label={"Draft budget percentage for " + category} type="number" min="0" max="100" step="0.5" value={budgetPreview.values[category] ?? 0} onChange={(event) => onBudgetChange(category, event.target.value)} /></label>
            ))}
          </div>
        </Card>
      ) : null}

      {view !== "journey" ? <Card className="exploration-focus-card">
        <div className="card-heading"><div><p className="eyebrow">Coming into focus</p><h2>{detail}</h2></div><Icon size={26} /></div>
        <p className="muted-copy">This focused view shares one temporary workspace. Use the back action to switch views without losing drafts.</p>
      </Card> : null}
    </div>
  );
}

function DraftControls({
  dirty,
  reviewing,
  canUndo,
  confirmBlocked,
  comparison,
  scenarioChanges,
  budgetChanges,
  onCancel,
  onReset,
  onUndo,
  onReview,
  onConfirm,
  onKeepEditing
}: {
  dirty: boolean;
  reviewing: boolean;
  canUndo: boolean;
  confirmBlocked: boolean;
  comparison: ScenarioComparison;
  scenarioChanges: ScenarioEventChange[];
  budgetChanges: BudgetChange[];
  onCancel(): void;
  onReset(): void;
  onUndo(): void;
  onReview(): void;
  onConfirm(): void;
  onKeepEditing(): void;
}) {
  if (!dirty && !canUndo) {
    return null;
  }

  return (
    <Card className="exploration-draft-controls">
      <div className="card-heading"><div><p className="eyebrow">Unsaved Exploration drafts</p><h2>Saved finance data is unchanged</h2></div><Save size={24} /></div>
      <p className="muted-copy">{scenarioChanges.length} temporary event(s) and {budgetChanges.length} budget change(s) remain in memory.</p>
      <div className="button-group exploration-draft-actions">
        {canUndo ? <Button variant="ghost" onClick={onUndo}><Undo2 size={16} /> Undo last edit</Button> : null}
        <Button variant="ghost" onClick={onCancel}><X size={16} /> Cancel drafts</Button>
        <Button variant="danger" onClick={onReset}><RotateCcw size={16} /> Reset drafts</Button>
        <Button onClick={onReview}><Check size={16} /> Review and confirm</Button>
      </div>
      {reviewing ? (
        <div className="exploration-review" role="dialog" aria-label="Review Exploration changes">
          <p className="eyebrow">Final diff</p>
           <h3>Confirm changes to shared finance data?</h3>
           <p className="muted-copy">Confirmation is the only action that sends this draft through the existing save flow.</p>
           <p className="scenario-review-summary">Net worth: {formatCurrency(comparison.baselineNetWorth)} → {formatCurrency(comparison.scenarioNetWorth)} · Cash flow: {formatCurrency(comparison.baselineCashFlow)} → {formatCurrency(comparison.scenarioCashFlow)} · Goal date: {comparison.baselineGoalDate} → {comparison.scenarioGoalDate}</p>
          <div className="exploration-review-list">
            {scenarioChanges.map((event, index) => <div key={(event.id ?? event.date) + index}><span>{event.type} · {event.description || event.category} · {event.date}</span><strong>{event.type === "Expense" ? "−" : "+"}{formatCurrency(event.amount)}</strong></div>)}
            {budgetChanges.map((change) => <div key={change.category}><span>{change.category} percentage</span><strong>{change.from}% → {change.to}%</strong></div>)}
          </div>
          <div className="button-group exploration-draft-actions">
            <Button variant="ghost" onClick={onKeepEditing}>Keep editing</Button>
            <Button disabled={confirmBlocked} onClick={onConfirm}>Confirm and save</Button>
          </div>
        </div>
      ) : null}
    </Card>
  );
}

export function ExplorationScreen({ document, onConfirm, onDirtyChange }: ExplorationScreenProps) {
  const [view, setView] = useState<ExplorationView>("landing");
  const [draft, setDraft] = useState(() => cloneDocument(document));
  const [undoStack, setUndoStack] = useState<FinanceDocument[]>([]);
  const [reviewing, setReviewing] = useState(false);
  const [editingEventId, setEditingEventId] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [eventDraft, setEventDraft] = useState<ScenarioEventDraft>(() => ({
    type: "Expense",
    amount: "",
    category: document.categories.Expense[0] ?? "Other",
    description: "",
    date: isoToday()
  }));
  const dirty = JSON.stringify(draft) !== JSON.stringify(document);
  const savedBudgets = document.budget_settings.category_budgets?.Expense ?? {};
  const draftBudgets = draft.budget_settings.category_budgets?.Expense ?? {};
  const categories = Array.from(new Set([...document.categories.Expense, ...Object.keys(savedBudgets), ...Object.keys(draftBudgets)]));
  const budgetChanges = categories
    .filter((category) => (draftBudgets[category] ?? 0) !== (savedBudgets[category] ?? 0))
    .map((category) => ({ category, from: savedBudgets[category] ?? 0, to: draftBudgets[category] ?? 0 }));
  const savedEventIds = new Set([...document.expenses, ...document.incomes].map((event) => event.id).filter((id): id is string => Boolean(id)));
  const scenarioChanges: ScenarioEventChange[] = [
    ...draft.expenses.filter((event) => Boolean(event.id) && !savedEventIds.has(event.id ?? "")).map((event) => ({ ...event, type: "Expense" as const })),
    ...draft.incomes.filter((event) => Boolean(event.id) && !savedEventIds.has(event.id ?? "")).map((event) => ({ ...event, type: "Income" as const }))
  ];
  const historyCount = snapshots(document).length;
  const goals = goalSummary(document);
  const goalCount = getGoals(document).length;
  const month = currentMonth();
  const fixedCostCategories = getActiveFixedCosts(document, month)
    .map((cost) => cost.description ?? cost.desc ?? "")
    .filter((category) => categories.includes(category));
  const protectedCategories = new Set([...categories.filter(isProtectedCategory), ...fixedCostCategories]);
  const budgetValues = Object.fromEntries(categories.map((category) => {
    const value = Number(draftBudgets[category] ?? 0);
    return [category, Number.isFinite(value) ? value : 0];
  }));
  const savedBudgetValues = Object.fromEntries(categories.map((category) => {
    const value = Number(savedBudgets[category] ?? 0);
    return [category, Number.isFinite(value) ? value : 0];
  }));
  const flexibleBudget = rawNetAvailableForSpending(document, month);
  const baseGoalShortfall = getGoals(document).reduce((total, goal) => total + Math.max(goal.target_amount - goal.allocated_amount, 0), 0);
  const plannedPercent = roundCurrency(Object.values(budgetValues).reduce((total, value) => total + value, 0));
  const savedPlannedPercent = roundCurrency(Object.values(savedBudgetValues).reduce((total, value) => total + value, 0));
  const scenarioNet = scenarioChanges.reduce((total, event) => total + (event.type === "Income" ? event.amount : -event.amount), 0);
  const projectionMonths = 12;
  const projectionEndMonth = monthOffset(month, projectionMonths - 1);
  const horizonEvents = scenarioChanges.filter((event) => {
    const eventMonth = event.date.slice(0, 7);
    return eventMonth >= month && eventMonth <= projectionEndMonth;
  });
  const horizonScenarioNet = horizonEvents.reduce((total, event) => total + (event.type === "Income" ? event.amount : -event.amount), 0);
  const baselineProjection = projection(document, projectionMonths, month);
  const baselineNetWorth = roundCurrency(baselineProjection.at(-1)?.balance ?? netWorth(document));
  const scenarioNetWorth = roundCurrency(baselineNetWorth + horizonScenarioNet);
  const baselineCashFlow = roundCurrency(Array.from({ length: projectionMonths }, (_, index) => rawNetAvailableForSpending(document, monthOffset(month, index))).reduce((total, value) => total + value, 0));
  const scenarioCashFlow = roundCurrency(baselineCashFlow + horizonScenarioNet);
  const goalDates = goalDateComparison(document, horizonScenarioNet);
  const comparison: ScenarioComparison = {
    baselineNetWorth,
    scenarioNetWorth,
    netWorthDifference: roundCurrency(scenarioNetWorth - baselineNetWorth),
    baselineCashFlow,
    scenarioCashFlow,
    cashFlowDifference: roundCurrency(scenarioCashFlow - baselineCashFlow),
    ...goalDates,
    drivers: [
      { label: "Income events", baseline: 0, scenario: horizonEvents.filter((event) => event.type === "Income").reduce((total, event) => total + event.amount, 0) },
      { label: "Expense events", baseline: 0, scenario: horizonEvents.filter((event) => event.type === "Expense").reduce((total, event) => total + event.amount, 0) },
      { label: "Planned budget", baseline: savedPlannedPercent, scenario: plannedPercent }
    ]
  };
  const plannedCashBase = Math.max(flexibleBudget, 0);
  const projectedCash = roundCurrency(flexibleBudget - plannedCashBase * plannedPercent / 100 + scenarioNet);
  const baselineProjectedCash = roundCurrency(flexibleBudget - plannedCashBase * savedPlannedPercent / 100 + scenarioNet);
  const emergencyBuffer = roundCurrency(Number(document.budget_settings.savings_balance ?? 0) + projectedCash);
  const baselineEmergencyBuffer = roundCurrency(Number(document.budget_settings.savings_balance ?? 0) + baselineProjectedCash);
  const budgetPreview: BudgetPreview = {
    values: budgetValues,
    plannedPercent,
    flexibleBudget,
    projectedCash,
    emergencyBuffer,
    goalShortfall: roundCurrency(Math.max(baseGoalShortfall - Math.max(projectedCash, 0), 0)),
    reducedEmergencyBuffer: emergencyBuffer < baselineEmergencyBuffer,
    negativeCash: projectedCash < 0
  };

  useEffect(() => {
    onDirtyChange?.(dirty);
  }, [dirty, onDirtyChange]);

  function updateDraft(update: (next: FinanceDocument) => void) {
    setUndoStack((entries) => [...entries, cloneDocument(draft)]);
    setDraft((current) => {
      const next = cloneDocument(current);
      update(next);
      return next;
    });
    setMessage("");
  }

  function addScenarioEvent(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const amount = Number(eventDraft.amount);
    if (!eventDraft.description.trim() || !Number.isFinite(amount) || amount <= 0) {
      setMessage("Enter event description and positive amount.");
      return;
    }
    const parsedDate = new Date(eventDraft.date + "T12:00:00");
    const validDate = /^\d{4}-\d{2}-\d{2}$/.test(eventDraft.date)
      && !Number.isNaN(parsedDate.getTime())
      && parsedDate.toISOString().slice(0, 10) === eventDraft.date;
    if (!validDate || eventDraft.date < isoToday()) {
      setMessage("Scenario events must use today or a future date.");
      return;
    }
    updateDraft((next) => {
      const existing = editingEventId
        ? [...next.expenses, ...next.incomes].find((transaction) => transaction.id === editingEventId)
        : undefined;
      const transaction = existing
        ? { ...existing, date: eventDraft.date, amount, category: eventDraft.category, description: eventDraft.description.trim() }
        : makeTransaction(eventDraft.type, {
          date: eventDraft.date,
          amount,
          category: eventDraft.category,
          description: eventDraft.description.trim()
        });
      if (existing) {
        next.expenses = next.expenses.filter((entry) => entry.id !== editingEventId);
        next.incomes = next.incomes.filter((entry) => entry.id !== editingEventId);
      }
      (eventDraft.type === "Expense" ? next.expenses : next.incomes).push(transaction);
    });
    setEditingEventId(null);
    setEventDraft({ ...eventDraft, amount: "", description: "" });
    setMessage(editingEventId ? "Temporary event updated." : "Temporary event added.");
  }

  function editScenarioEvent(event: ScenarioEventChange) {
    setEditingEventId(event.id ?? null);
    setEventDraft({ type: event.type, amount: String(event.amount), category: event.category, description: event.description, date: event.date });
    setView("simulator");
    setMessage("");
  }

  function updateEventDraft(update: Partial<ScenarioEventDraft>) {
    setEventDraft((current) => {
      const next = { ...current, ...update };
      if (update.type && !document.categories[update.type].includes(next.category)) {
        next.category = document.categories[update.type][0] ?? "Other";
      }
      return next;
    });
  }

  function removeScenarioEvent(event: ScenarioEventChange) {
    if (!event.id) {
      return;
    }
    updateDraft((next) => {
      next.expenses = next.expenses.filter((entry) => entry.id !== event.id);
      next.incomes = next.incomes.filter((entry) => entry.id !== event.id);
    });
    if (editingEventId === event.id) {
      setEditingEventId(null);
    }
    setMessage("Temporary event removed.");
  }

  function updateBudget(category: string, value: string) {
    const nextValues = rebalanceBudgetValues(budgetValues, category, Number(value), protectedCategories);
    updateDraft((next) => {
      const expenseBudgets = { ...(next.budget_settings.category_budgets?.Expense ?? {}) };
      Object.entries(nextValues).forEach(([name, amount]) => {
        if (amount === 0 && expenseBudgets[name] === undefined) {
          return;
        }
        expenseBudgets[name] = amount;
      });
      next.budget_settings.category_budgets = {
        ...(next.budget_settings.category_budgets ?? {}),
        Expense: expenseBudgets
      };
    });
  }

  function resetDrafts(ask = true) {
    if (dirty && ask && !window.confirm("Reset all temporary Exploration drafts?")) {
      return false;
    }
    setDraft(cloneDocument(document));
    setUndoStack([]);
    setEditingEventId(null);
    setReviewing(false);
    setMessage("Exploration drafts reset to saved baseline.");
    return true;
  }

  function cancelDrafts() {
    if (resetDrafts()) {
      setView("landing");
    }
  }

  function reviewDrafts() {
    setReviewing(true);
    setMessage("");
  }

  function confirmDrafts() {
    if (budgetChanges.length > 0 && budgetPreview.negativeCash) {
      setMessage("Negative projected cash blocks budget confirmation.");
      return;
    }
    onConfirm?.(draft);
    setReviewing(false);
    setUndoStack([]);
  }

  function undoDraft() {
    const previous = undoStack.at(-1);
    if (!previous) {
      return;
    }
    setDraft(cloneDocument(previous));
    setUndoStack(undoStack.slice(0, -1));
    setReviewing(false);
    setMessage("Last Exploration edit undone.");
  }

  const draftControls = <DraftControls dirty={dirty} reviewing={reviewing} canUndo={undoStack.length > 0} confirmBlocked={budgetChanges.length > 0 && budgetPreview.negativeCash} comparison={comparison} scenarioChanges={scenarioChanges} budgetChanges={budgetChanges} onCancel={cancelDrafts} onReset={() => { resetDrafts(); }} onUndo={undoDraft} onReview={reviewDrafts} onConfirm={confirmDrafts} onKeepEditing={() => setReviewing(false)} />;

  if (view !== "landing") {
    return (
      <>
        <FocusedView
          view={view}
          document={document}
          categories={categories}
          eventCategories={document.categories}
          scenarioEvents={scenarioChanges}
          editingEventId={editingEventId}
          eventDraft={eventDraft}
          budgetPreview={budgetPreview}
          comparison={comparison}
          protectedCategories={protectedCategories}
          onBack={() => setView("landing")}
          onEventDraftChange={updateEventDraft}
          onAddEvent={addScenarioEvent}
          onEditEvent={editScenarioEvent}
          onRemoveEvent={removeScenarioEvent}
          onCancelEventEdit={() => { setEditingEventId(null); setEventDraft({ ...eventDraft, amount: "", description: "" }); }}
          onBudgetChange={updateBudget}
        />
        {message ? <p className="exploration-status" role="status">{message}</p> : null}
        {draftControls}
      </>
    );
  }

  return (
    <>
      <div className="page exploration-page">
        <PageHeader
          eyebrow="Data lab"
          title="Explore what comes next"
          description="Understand your financial direction through safe, focused experiments. Saved data stays unchanged while you explore."
        />

        <div className="exploration-context-grid">
          <Metric label="Current net worth" value={formatCurrency(netWorth(document))} detail="Across tracked balances" tone="positive" />
          <Metric label="Scenario status" value={dirty ? "Draft changes" : "Baseline only"} detail={dirty ? "Temporary edits in memory" : "No temporary edits"} tone={dirty ? "warning" : "default"} />
          <Metric label="Active horizon" value="12 months" detail="Default Exploration view" />
        </div>

        {message ? <p className="exploration-status" role="status">{message}</p> : null}

        <section aria-labelledby="exploration-workflows-heading">
          <div className="section-heading">
            <div><p className="eyebrow">Choose a lens</p><h2 id="exploration-workflows-heading">Three ways to explore</h2></div>
            <span className="section-heading-note">One workspace · no accidental saves</span>
          </div>
          <div className="exploration-entry-grid">
            {workflows.map((workflow) => {
              const Icon = workflow.icon;
              return (
                <Card className="exploration-entry" key={workflow.view}>
                  <div className="exploration-entry-icon"><Icon size={22} /></div>
                  <p className="eyebrow">{workflow.eyebrow}</p>
                  <h2>{workflow.title}</h2>
                  <p>{workflow.description}</p>
                  <Button variant="secondary" onClick={() => setView(workflow.view)}>{workflow.action}</Button>
                </Card>
              );
            })}
          </div>
        </section>

        <div className="exploration-summary-grid">
          <Card>
            <div className="card-heading"><div><p className="eyebrow">Context</p><h2>What informs this workspace</h2></div></div>
            <div className="summary-list">
              <div><dt>Recorded net-worth snapshots</dt><dd>{historyCount}</dd></div>
              <div><dt>Savings goals</dt><dd>{goalCount}</dd></div>
              <div><dt>Allocated toward goals</dt><dd>{formatCurrency(goals.allocated)}</dd></div>
            </div>
          </Card>
          <Card className="exploration-safety-card">
            <div className="card-heading"><div><p className="eyebrow">Safe by default</p><h2>Explore without editing reality</h2></div></div>
            <p className="muted-copy">Future scenarios and budget previews remain temporary. Existing finance data changes only after a later explicit confirmation step.</p>
          </Card>
        </div>
      </div>
      {draftControls}
    </>
  );
}
