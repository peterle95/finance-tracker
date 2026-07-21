import { ArrowLeft, Check, LineChart, RotateCcw, Save, TrendingUp, WalletCards, X } from "lucide-react";
import { useEffect, useState } from "react";
import {
  cloneDocument,
  formatCurrency,
  getGoals,
  goalSummary,
  isoToday,
  makeTransaction,
  netWorth,
  snapshots
} from "../../shared/finance";
import type { FinanceDocument, TransactionType } from "../../shared/types";
import { Button, Card, Metric, PageHeader } from "./ui";

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
  description: string;
  date: string;
}

function FocusedView({
  view,
  document,
  draft,
  categories,
  eventDraft,
  onBack,
  onEventDraftChange,
  onAddEvent,
  onBudgetChange
}: {
  view: Exclude<ExplorationView, "landing">;
  document: FinanceDocument;
  draft: FinanceDocument;
  categories: string[];
  eventDraft: ScenarioEventDraft;
  onBack(): void;
  onEventDraftChange(update: Partial<ScenarioEventDraft>): void;
  onAddEvent(event: React.FormEvent<HTMLFormElement>): void;
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
  const scenarioEvents = [
    ...draft.expenses.slice(document.expenses.length).map((event) => ({ ...event, type: "Expense" as const })),
    ...draft.incomes.slice(document.incomes.length).map((event) => ({ ...event, type: "Income" as const }))
  ];
  const budgetValues = draft.budget_settings.category_budgets?.Expense ?? {};

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
        <Metric label="Scenario net worth" value={formatCurrency(netWorth(draft))} detail="Temporary draft" />
        <Metric label="Workspace" value={workflow.title} detail="Drafts preserved while navigating" />
      </div>

      {view === "simulator" ? (
        <Card className="exploration-draft-card">
          <div className="card-heading"><div><p className="eyebrow">Temporary event</p><h2>Add future scenario event</h2></div><TrendingUp size={24} /></div>
          <p className="muted-copy">Only today and future dates are accepted. Event stays in memory until confirmation.</p>
          <form className="form-grid exploration-draft-form" onSubmit={onAddEvent}>
            <label><span>Type</span><select aria-label="Scenario event type" value={eventDraft.type} onChange={(event) => onEventDraftChange({ type: event.target.value as TransactionType })}><option value="Expense">Expense</option><option value="Income">Income</option></select></label>
            <label><span>Amount</span><input aria-label="Scenario event amount" type="number" min="0.01" step="0.01" value={eventDraft.amount} onChange={(event) => onEventDraftChange({ amount: event.target.value })} /></label>
            <label><span>Description</span><input aria-label="Scenario event description" value={eventDraft.description} onChange={(event) => onEventDraftChange({ description: event.target.value })} /></label>
            <label><span>Date</span><input aria-label="Scenario event date" type="date" min={isoToday()} value={eventDraft.date} onChange={(event) => onEventDraftChange({ date: event.target.value })} /></label>
            <div className="span-two form-actions"><Button type="submit"><TrendingUp size={16} /> Add temporary event</Button></div>
          </form>
          {scenarioEvents.length ? <div className="exploration-draft-list"><strong>Temporary events</strong>{scenarioEvents.map((event, index) => <div key={(event.id ?? event.date) + index}><span>{event.description || event.category} · {event.date}</span><strong className={event.type === "Expense" ? "amount-expense" : "amount-income"}>{event.type === "Expense" ? "−" : "+"}{formatCurrency(event.amount)}</strong></div>)}</div> : <p className="muted-copy">No temporary events yet.</p>}
        </Card>
      ) : null}

      {view === "balancer" ? (
        <Card className="exploration-draft-card">
          <div className="card-heading"><div><p className="eyebrow">Temporary allocation</p><h2>Adjust flexible category budgets</h2></div><WalletCards size={24} /></div>
          <p className="muted-copy">These values are a preview. Saved budget settings stay unchanged until confirmation.</p>
          <div className="form-grid exploration-budget-grid">
            {categories.map((category) => <label key={category}><span>{category}</span><input aria-label={"Draft budget for " + category} type="number" min="0" step="0.01" value={budgetValues[category] ?? 0} onChange={(event) => onBudgetChange(category, event.target.value)} /></label>)}
          </div>
        </Card>
      ) : null}

      <Card className="exploration-focus-card">
        <div className="card-heading"><div><p className="eyebrow">Coming into focus</p><h2>{detail}</h2></div><Icon size={26} /></div>
        <p className="muted-copy">This focused view shares one temporary workspace. Use the back action to switch views without losing drafts.</p>
      </Card>
    </div>
  );
}

function DraftControls({
  dirty,
  reviewing,
  scenarioEventCount,
  budgetChangeCount,
  onCancel,
  onReset,
  onReview,
  onConfirm,
  onKeepEditing
}: {
  dirty: boolean;
  reviewing: boolean;
  scenarioEventCount: number;
  budgetChangeCount: number;
  onCancel(): void;
  onReset(): void;
  onReview(): void;
  onConfirm(): void;
  onKeepEditing(): void;
}) {
  if (!dirty) {
    return null;
  }

  return (
    <Card className="exploration-draft-controls">
      <div className="card-heading"><div><p className="eyebrow">Unsaved Exploration drafts</p><h2>Saved finance data is unchanged</h2></div><Save size={24} /></div>
      <p className="muted-copy">{scenarioEventCount} temporary event(s) and {budgetChangeCount} budget change(s) remain in memory.</p>
      <div className="button-group exploration-draft-actions">
        <Button variant="ghost" onClick={onCancel}><X size={16} /> Cancel drafts</Button>
        <Button variant="danger" onClick={onReset}><RotateCcw size={16} /> Reset drafts</Button>
        <Button onClick={onReview}><Check size={16} /> Review and confirm</Button>
      </div>
      {reviewing ? (
        <div className="exploration-review" role="dialog" aria-label="Review Exploration changes">
          <p className="eyebrow">Final diff</p>
          <h3>Confirm changes to shared finance data?</h3>
          <p className="muted-copy">Confirmation is the only action that sends this draft through the existing save flow.</p>
          <div className="button-group exploration-draft-actions">
            <Button variant="ghost" onClick={onKeepEditing}>Keep editing</Button>
            <Button onClick={onConfirm}>Confirm and save</Button>
          </div>
        </div>
      ) : null}
    </Card>
  );
}

export function ExplorationScreen({ document, onConfirm, onDirtyChange }: ExplorationScreenProps) {
  const [view, setView] = useState<ExplorationView>("landing");
  const [draft, setDraft] = useState(() => cloneDocument(document));
  const [reviewing, setReviewing] = useState(false);
  const [message, setMessage] = useState("");
  const [eventDraft, setEventDraft] = useState<ScenarioEventDraft>(() => ({
    type: "Expense",
    amount: "",
    description: "",
    date: isoToday()
  }));
  const dirty = JSON.stringify(draft) !== JSON.stringify(document);
  const savedBudgets = document.budget_settings.category_budgets?.Expense ?? {};
  const draftBudgets = draft.budget_settings.category_budgets?.Expense ?? {};
  const categories = Array.from(new Set([...document.categories.Expense, ...Object.keys(savedBudgets), ...Object.keys(draftBudgets)]));
  const budgetChangeCount = categories.filter((category) => (draftBudgets[category] ?? 0) !== (savedBudgets[category] ?? 0)).length;
  const scenarioEventCount = Math.max(0, draft.expenses.length - document.expenses.length) + Math.max(0, draft.incomes.length - document.incomes.length);
  const historyCount = snapshots(document).length;
  const goals = goalSummary(document);
  const goalCount = getGoals(document).length;

  useEffect(() => {
    onDirtyChange?.(dirty);
  }, [dirty, onDirtyChange]);

  function updateDraft(update: (next: FinanceDocument) => void) {
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
    if (!eventDraft.date || eventDraft.date < isoToday()) {
      setMessage("Scenario events must use today or a future date.");
      return;
    }
    updateDraft((next) => {
      const transaction = makeTransaction(eventDraft.type, {
        date: eventDraft.date,
        amount,
        category: next.categories[eventDraft.type][0] ?? "Other",
        description: eventDraft.description.trim()
      });
      (eventDraft.type === "Expense" ? next.expenses : next.incomes).push(transaction);
    });
    setEventDraft({ ...eventDraft, amount: "", description: "" });
    setMessage("Temporary event added.");
  }

  function updateBudget(category: string, value: string) {
    const amount = Number(value);
    updateDraft((next) => {
      next.budget_settings.category_budgets = {
        ...(next.budget_settings.category_budgets ?? {}),
        Expense: {
          ...(next.budget_settings.category_budgets?.Expense ?? {}),
          [category]: Number.isFinite(amount) && amount >= 0 ? amount : 0
        }
      };
    });
  }

  function resetDrafts(ask = true) {
    if (dirty && ask && !window.confirm("Reset all temporary Exploration drafts?")) {
      return false;
    }
    setDraft(cloneDocument(document));
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
    onConfirm?.(draft);
    setReviewing(false);
  }

  if (view !== "landing") {
    return (
      <>
        <FocusedView
          view={view}
          document={document}
          draft={draft}
          categories={categories}
          eventDraft={eventDraft}
          onBack={() => setView("landing")}
          onEventDraftChange={(update) => setEventDraft((current) => ({ ...current, ...update }))}
          onAddEvent={addScenarioEvent}
          onBudgetChange={updateBudget}
        />
        {message ? <p className="exploration-status" role="status">{message}</p> : null}
        <DraftControls dirty={dirty} reviewing={reviewing} scenarioEventCount={scenarioEventCount} budgetChangeCount={budgetChangeCount} onCancel={cancelDrafts} onReset={() => { resetDrafts(); }} onReview={reviewDrafts} onConfirm={confirmDrafts} onKeepEditing={() => setReviewing(false)} />
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
      <DraftControls dirty={dirty} reviewing={reviewing} scenarioEventCount={scenarioEventCount} budgetChangeCount={budgetChangeCount} onCancel={cancelDrafts} onReset={() => { resetDrafts(); }} onReview={reviewDrafts} onConfirm={confirmDrafts} onKeepEditing={() => setReviewing(false)} />
    </>
  );
}
