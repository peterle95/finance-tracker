import { Camera, LineChart as LineChartIcon, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { assetAllocation, cloneDocument, createSnapshot, formatCurrency, isoToday, netWorth, roundCurrency, snapshots } from "../../shared/finance";
import type { FinanceDocument } from "../../shared/types";
import { Button, Card, EmptyState, PageHeader } from "./ui";

const COLORS = ["#f5c451", "#2dd4bf", "#7dd3fc", "#8b5cf6", "#fb923c"];

export function NetWorthScreen({
  document,
  onSave,
  onExport
}: {
  document: FinanceDocument;
  onSave(document: FinanceDocument): void;
  onExport(name: string, text: string): void;
}) {
  const [note, setNote] = useState("");
  const [date, setDate] = useState(isoToday());
  const history = snapshots(document);
  const allocation = assetAllocation(document);
  const moneyLent = roundCurrency(Number(document.budget_settings.money_lent_balance ?? 0));
  const report = useMemo(() => [
    "NET WORTH REPORT",
    "",
    "Current net worth: " + formatCurrency(netWorth(document)),
    "",
    ...history.map((snapshot) => snapshot.date + ": " + formatCurrency(snapshot.net_worth) + (snapshot.note ? " — " + snapshot.note : ""))
  ].join("\n"), [document, history]);

  function recordSnapshot() {
    const next = cloneDocument(document);
    const snapshot = createSnapshot(document, date, note);
    const existing = snapshots(next).filter((entry) => entry.date !== date);
    next.budget_settings.asset_snapshots = [...existing, snapshot].sort((first, second) => first.date.localeCompare(second.date));
    onSave(next);
    setNote("");
  }

  function removeSnapshot(snapshotDate: string) {
    const next = cloneDocument(document);
    next.budget_settings.asset_snapshots = snapshots(next).filter((entry) => entry.date !== snapshotDate);
    onSave(next);
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="Long-term view"
        title="Net worth"
        description="Track the full balance of your accounts, savings, investments, lending, and amounts owed."
        action={<Button variant="secondary" onClick={() => onExport("net_worth_report_" + isoToday() + ".txt", report)}>Export report</Button>}
      />

      <div className="metric-grid">
        <Card className="metric metric-positive"><p>Net worth</p><strong>{formatCurrency(netWorth(document))}</strong><span>Live account total</span></Card>
        <Card className="metric"><p>Savings</p><strong>{formatCurrency(Number(document.budget_settings.savings_balance ?? 0))}</strong><span>Allocated to goals separately</span></Card>
        <Card className="metric"><p>Investments</p><strong>{formatCurrency(Number(document.budget_settings.investment_balance ?? 0))}</strong><span>Current entered balance</span></Card>
        <Card className={"metric " + (moneyLent < 0 ? "metric-warning" : "")}><p>{moneyLent < 0 ? "Money owed" : "Money lent"}</p><strong>{formatCurrency(moneyLent)}</strong><span>{history.length} historical snapshot(s)</span></Card>
      </div>

      <div className="two-column">
        <Card className="chart-card">
          <div className="card-heading"><div><p className="eyebrow">History</p><h2>Net worth over time</h2></div><LineChartIcon size={22} /></div>
          {history.length > 1 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={history}>
                <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                <Line type="monotone" dataKey="net_worth" stroke="#f5c451" strokeWidth={3} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : <EmptyState title="Record two snapshots to see a trend" detail="Snapshots retain your balance on the chosen day." />}
        </Card>
        <Card className="chart-card">
          <div className="card-heading"><div><p className="eyebrow">Allocation</p><h2>Where your money sits</h2></div></div>
           {allocation.assets.length ? (
             <ResponsiveContainer width="100%" height={300}>
               <PieChart>
                <Pie data={allocation.assets} dataKey="value" nameKey="name" innerRadius={65} outerRadius={100} paddingAngle={3}>
                  {allocation.assets.map((_entry, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(value) => formatCurrency(Number(value))} />
              </PieChart>
            </ResponsiveContainer>
           ) : <EmptyState title="Add account balances" detail="Balance entries from Budget will appear here." />}
          {allocation.liabilities.length ? <div className="allocation-liabilities">{allocation.liabilities.map((item) => <span key={item.name}><strong>{item.name}</strong><b>{formatCurrency(item.value)}</b><small>Shown in net worth as a liability, not as an asset slice.</small></span>)}</div> : null}
        </Card>
      </div>

      <div className="two-column">
        <Card>
          <div className="card-heading"><div><p className="eyebrow">Checkpoint</p><h2>Record a snapshot</h2></div><Camera size={22} /></div>
          <div className="form-grid compact-form">
            <label><span>Date</span><input type="date" value={date} onChange={(event) => setDate(event.target.value)} /></label>
            <label><span>Current value</span><input value={formatCurrency(netWorth(document))} readOnly /></label>
            <label className="span-two"><span>Note</span><input value={note} onChange={(event) => setNote(event.target.value)} placeholder="Month end or milestone" /></label>
            <div className="span-two form-actions"><Button onClick={recordSnapshot}>Record snapshot</Button></div>
          </div>
        </Card>
        <Card>
          <div className="card-heading"><div><p className="eyebrow">Saved history</p><h2>Snapshots</h2></div></div>
          <div className="mini-list">
            {history.length ? history.slice().reverse().map((snapshot) => (
              <div key={snapshot.date}>
                <span><strong>{snapshot.date}</strong><small>{snapshot.note || "No note"}</small></span>
                <strong>{formatCurrency(snapshot.net_worth)}</strong>
                <button className="icon-button danger-icon" onClick={() => removeSnapshot(snapshot.date)} aria-label="Delete snapshot"><Trash2 size={15} /></button>
              </div>
            )) : <p className="muted-copy">No snapshots recorded yet.</p>}
          </div>
        </Card>
      </div>
    </div>
  );
}
