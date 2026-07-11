import { Archive, ArrowRight, Plus, Sparkles, Trash2 } from "lucide-react";
import { useState } from "react";
import {
  autoDistributeGoals,
  cloneDocument,
  formatCurrency,
  getGoals,
  goalSummary,
  isoToday
} from "../../shared/finance";
import type { FinanceDocument, SavingsGoal } from "../../shared/types";
import { Button, Card, EmptyState, PageHeader } from "./ui";

interface GoalsScreenProps {
  document: FinanceDocument;
  onSave(document: FinanceDocument): void;
  onExport(defaultName: string, text: string): void;
}

const newGoal = (): SavingsGoal => ({
  name: "",
  target_amount: 0,
  allocated_amount: 0,
  priority: "Medium",
  description: "",
  target_date: ""
});

function goalsReport(document: FinanceDocument): string {
  const goals = getGoals(document);
  const summary = goalSummary(document);
  const rows = [
    "SAVINGS GOALS REPORT",
    "",
    "Total savings: " + formatCurrency(summary.totalSavings),
    "Allocated: " + formatCurrency(summary.allocated),
    "Unallocated: " + formatCurrency(summary.unallocated),
    "",
    ...goals.map((goal) => {
      const progress = goal.target_amount ? Math.min((goal.allocated_amount / goal.target_amount) * 100, 100) : 0;
      return goal.name + ": " + formatCurrency(goal.allocated_amount) + " / "
        + formatCurrency(goal.target_amount) + " (" + progress.toFixed(1) + "%)";
    })
  ];
  return rows.join("\n");
}

export function GoalsScreen({ document, onSave, onExport }: GoalsScreenProps) {
  const goals = getGoals(document);
  const summary = goalSummary(document);
  const [draft, setDraft] = useState<SavingsGoal>(newGoal);

  function saveGoals(nextGoals: SavingsGoal[]) {
    const next = cloneDocument(document);
    next.budget_settings.savings_goals = nextGoals;
    onSave(next);
  }

  function addGoal(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!draft.name.trim() || draft.target_amount <= 0) {
      return;
    }
    saveGoals([...goals, { ...draft, name: draft.name.trim() }]);
    setDraft(newGoal());
  }

  function updateGoal(index: number, update: (goal: SavingsGoal) => SavingsGoal) {
    saveGoals(goals.map((goal, row) => row === index ? update(goal) : goal));
  }

  function archiveGoal(index: number) {
    const goal = goals[index];
    const next = cloneDocument(document);
    next.budget_settings.savings_goals = goals.filter((_goal, row) => row !== index);
    const archived = Array.isArray(next.budget_settings.archived_savings_goals)
      ? next.budget_settings.archived_savings_goals
      : [];
    next.budget_settings.archived_savings_goals = [...archived, { ...goal, archived_at: isoToday() }];
    onSave(next);
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="Purposeful saving"
        title="Savings goals"
        description="Allocate the savings balance you already own toward the things that matter most."
        action={
          <div className="button-group">
            <Button variant="secondary" onClick={() => onExport("savings_goals_report_" + isoToday() + ".txt", goalsReport(document))}>
              Export report
            </Button>
            <Button onClick={() => saveGoals(autoDistributeGoals(document))}><Sparkles size={16} /> Auto-distribute</Button>
          </div>
        }
      />

      <div className="metric-grid">
        <Card className="metric"><p>Total savings</p><strong>{formatCurrency(summary.totalSavings)}</strong><span>Managed in Budget</span></Card>
        <Card className="metric metric-positive"><p>Allocated</p><strong>{formatCurrency(summary.allocated)}</strong><span>{summary.completedGoals} complete goal(s)</span></Card>
        <Card className="metric"><p>Still available</p><strong>{formatCurrency(summary.unallocated)}</strong><span>Ready to allocate</span></Card>
        <Card className="metric"><p>Active goals</p><strong>{summary.activeGoals}</strong><span>{summary.totalGoals} total</span></Card>
      </div>

      <div className="two-column goals-layout">
        <div className="goal-stack">
          {goals.length ? goals
            .map((goal, index) => ({ goal, index }))
            .sort((first, second) => (first.goal.priority === "High" ? -1 : 1) - (second.goal.priority === "High" ? -1 : 1))
            .map(({ goal, index }) => {
              const progress = goal.target_amount ? Math.min((goal.allocated_amount / goal.target_amount) * 100, 100) : 0;
              return (
                <Card className="goal-card" key={goal.name + index}>
                  <div className="card-heading">
                    <div>
                      <p className="eyebrow">{goal.priority ?? "Medium"} priority</p>
                      <h2>{goal.name}</h2>
                    </div>
                    <div className="row-actions">
                      <button className="icon-button" onClick={() => archiveGoal(index)} aria-label="Archive goal"><Archive size={16} /></button>
                      <button className="icon-button danger-icon" onClick={() => saveGoals(goals.filter((_goal, row) => row !== index))} aria-label="Delete goal"><Trash2 size={16} /></button>
                    </div>
                  </div>
                  {goal.description ? <p className="muted-copy">{goal.description}</p> : null}
                  <div className="goal-progress-label">
                    <strong>{formatCurrency(goal.allocated_amount)}</strong>
                    <span>of {formatCurrency(goal.target_amount)}</span>
                  </div>
                  <div className="budget-track goal-track"><span style={{ width: progress + "%" }} /></div>
                  <div className="goal-controls">
                    <label><span>Allocated</span><input type="number" step="0.01" value={goal.allocated_amount} onChange={(event) => updateGoal(index, (current) => ({ ...current, allocated_amount: Number(event.target.value) }))} /></label>
                    <label><span>Target</span><input type="number" step="0.01" value={goal.target_amount} onChange={(event) => updateGoal(index, (current) => ({ ...current, target_amount: Number(event.target.value) }))} /></label>
                    <label><span>Target date</span><input type="date" value={goal.target_date ?? ""} onChange={(event) => updateGoal(index, (current) => ({ ...current, target_date: event.target.value }))} /></label>
                  </div>
                  <div className="card-action-row">
                    <span>{progress.toFixed(0)}% complete</span>
                    {goal.target_date ? <span>{goal.target_date}</span> : <span>No target date</span>}
                  </div>
                </Card>
              );
            }) : (
            <EmptyState title="Give your savings a purpose" detail="Create a goal, then allocate part of the savings balance to it." />
          )}
        </div>

        <Card className="sticky-card">
          <div className="card-heading"><div><p className="eyebrow">New goal</p><h2>What are you saving for?</h2></div><ArrowRight size={22} /></div>
          <form className="form-grid" onSubmit={addGoal}>
            <label className="span-two"><span>Name</span><input value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} placeholder="Emergency fund" /></label>
            <label><span>Target amount</span><input type="number" step="0.01" min="0" value={draft.target_amount || ""} onChange={(event) => setDraft({ ...draft, target_amount: Number(event.target.value) })} /></label>
            <label><span>Priority</span><select value={draft.priority} onChange={(event) => setDraft({ ...draft, priority: event.target.value as SavingsGoal["priority"] })}><option>High</option><option>Medium</option><option>Low</option></select></label>
            <label className="span-two"><span>Target date</span><input type="date" value={draft.target_date ?? ""} onChange={(event) => setDraft({ ...draft, target_date: event.target.value })} /></label>
            <label className="span-two"><span>Note</span><textarea value={draft.description ?? ""} onChange={(event) => setDraft({ ...draft, description: event.target.value })} placeholder="Why this matters" rows={4} /></label>
            <div className="span-two form-actions"><Button type="submit"><Plus size={16} /> Create goal</Button></div>
          </form>
        </Card>
      </div>
    </div>
  );
}
