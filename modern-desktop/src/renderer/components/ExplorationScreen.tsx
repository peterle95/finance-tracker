import { ArrowLeft, LineChart, TrendingUp, WalletCards } from "lucide-react";
import { useState } from "react";
import { formatCurrency, getGoals, goalSummary, netWorth, snapshots } from "../../shared/finance";
import type { FinanceDocument } from "../../shared/types";
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

function FocusedView({
  view,
  document,
  onBack
}: {
  view: Exclude<ExplorationView, "landing">;
  document: FinanceDocument;
  onBack(): void;
}) {
  const workflow = workflows.find((entry) => entry.view === view)!;
  const Icon = workflow.icon;
  const copy = view === "simulator"
    ? "Build temporary what-if plans here. Scenario edits will stay in memory until you explicitly review and confirm them."
    : view === "journey"
      ? "Inspect recorded balances and future direction here. Historical data remains separate from projected outcomes."
      : "Preview flexible budget trade-offs here. Saved budgets remain unchanged while you compare options."
  const detail = view === "simulator"
    ? "Future Simulator tools are ready for the next Exploration phase."
    : view === "journey"
      ? "Net-Worth Journey tools are ready for the next Exploration phase."
      : "Budget Balancer tools are ready for the next Exploration phase.";

  return (
    <div className="page exploration-page">
      <PageHeader
        eyebrow={workflow.eyebrow}
        title={workflow.title}
        description={copy}
        action={<Button variant="secondary" onClick={onBack}><ArrowLeft size={16} /> Back to Exploration</Button>}
      />
      <div className="exploration-context-grid">
        <Metric label="Current net worth" value={formatCurrency(netWorth(document))} detail="Saved finance data" tone="positive" />
        <Metric label="Scenario status" value="Baseline only" detail="No temporary edits" />
        <Metric label="Workspace" value={workflow.title} detail="Exploration view" />
      </div>
      <Card className="exploration-focus-card">
        <div className="card-heading"><div><p className="eyebrow">Coming into focus</p><h2>{detail}</h2></div><Icon size={26} /></div>
        <p className="muted-copy">This focused view is isolated from existing tabs. Use the back action to return to the Exploration landing page.</p>
      </Card>
    </div>
  );
}

export function ExplorationScreen({ document }: { document: FinanceDocument }) {
  const [view, setView] = useState<ExplorationView>("landing");
  const historyCount = snapshots(document).length;
  const goals = goalSummary(document);
  const goalCount = getGoals(document).length;

  if (view !== "landing") {
    return <FocusedView view={view} document={document} onBack={() => setView("landing")} />;
  }

  return (
    <div className="page exploration-page">
      <PageHeader
        eyebrow="Data lab"
        title="Explore what comes next"
        description="Understand your financial direction through safe, focused experiments. Saved data stays unchanged while you explore."
      />

      <div className="exploration-context-grid">
        <Metric label="Current net worth" value={formatCurrency(netWorth(document))} detail="Across tracked balances" tone="positive" />
        <Metric label="Scenario status" value="Baseline only" detail="No temporary edits" />
        <Metric label="Active horizon" value="12 months" detail="Default Exploration view" />
      </div>

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
  );
}
