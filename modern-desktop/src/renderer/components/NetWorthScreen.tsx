import { Camera, LineChart as LineChartIcon, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { DEFAULT_BEHAVIOR_SETTINGS, type DefaultBehaviorSettings } from "../../shared/behavior-settings";
import { assetAllocation, cloneDocument, createSnapshot, formatCurrency, isoToday, netWorth, roundCurrency, snapshotChanges, snapshots } from "../../shared/finance";
import type { SnapshotChangeMode } from "../../shared/finance";
import type { FinanceDocument } from "../../shared/types";
import { tooltipStyle, tooltipTextStyle } from "./chartStyles";
import { Button, Card, EmptyState, PageHeader } from "./ui";

const COLORS = ["#f5c451", "#2dd4bf", "#7dd3fc", "#8b5cf6", "#fb923c"];

function formatSignedCurrency(value: number): string {
  return (value >= 0 ? "+" : "-") + formatCurrency(Math.abs(value));
}

function BreakdownTooltip({
  active,
  payload,
  label
}: {
  active?: boolean;
  payload?: Array<{ color?: string; name?: string; value?: number | string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;

  return (
    <div style={{ ...tooltipStyle, padding: "10px 14px" }}>
      <p style={{ ...tooltipTextStyle, margin: "0 0 8px" }}>{label}</p>
      {[...payload].sort((first, second) => Number(second.value) - Number(first.value)).map((entry) => (
        <p key={entry.name} style={{ color: entry.color ?? "#ffffff", margin: "4px 0" }}>
          {entry.name}: {formatCurrency(Number(entry.value))}
        </p>
      ))}
    </div>
  );
}

export function NetWorthScreen({
  document,
  defaultBehaviors = DEFAULT_BEHAVIOR_SETTINGS,
  defaultNetWorthPeriod,
  defaultNetWorthBreakdownPeriod,
  onSave,
  onExport
}: {
  document: FinanceDocument;
  defaultBehaviors?: DefaultBehaviorSettings;
  defaultNetWorthPeriod?: number | "All";
  defaultNetWorthBreakdownPeriod?: number | "All";
  onSave(document: FinanceDocument): void;
  onExport(name: string, text: string): void;
}) {
  const [date, setDate] = useState(isoToday());
  const [changeMode, setChangeMode] = useState<SnapshotChangeMode>(defaultBehaviors.netWorthChangeMode);
  const [historyPeriod, setHistoryPeriod] = useState<number | "All">(defaultNetWorthPeriod ?? 12);
  const [breakdownPeriod, setBreakdownPeriod] = useState<number | "All">(defaultNetWorthBreakdownPeriod ?? 12);
  const allHistory = snapshots(document);
  const history = historyPeriod === "All" ? allHistory : allHistory.slice(-historyPeriod);
  const breakdown = breakdownPeriod === "All" ? allHistory : allHistory.slice(-breakdownPeriod);
  const changeRows = snapshotChanges(history, changeMode);
  const changeByDate = new Map(changeRows.map((row) => [row.date, row.change]));
  const allocation = assetAllocation(document);
  const currentNetWorth = netWorth(document);
  const moneyLent = roundCurrency(Number(document.budget_settings.money_lent_balance ?? 0));
  const report = useMemo(() => [
    "NET WORTH REPORT",
    "",
    "Current net worth: " + formatCurrency(netWorth(document)),
    "",
    ...allHistory.map((snapshot) => snapshot.date + ": " + formatCurrency(snapshot.net_worth))
  ].join("\n"), [document, allHistory]);

  function recordSnapshot() {
    const next = cloneDocument(document);
    const snapshot = createSnapshot(document, date);
    const existing = snapshots(next).filter((entry) => entry.date !== date);
    next.budget_settings.asset_snapshots = [...existing, snapshot].sort((first, second) => first.date.localeCompare(second.date));
    onSave(next);
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
        <Card className={"metric " + (currentNetWorth > 0 ? "metric-positive" : currentNetWorth < 0 ? "metric-warning" : "")}><p>Net worth</p><strong>{formatCurrency(currentNetWorth)}</strong><span>Live account total</span></Card>
        <Card className="metric"><p>Savings</p><strong>{formatCurrency(Number(document.budget_settings.savings_balance ?? 0))}</strong><span>Allocated to goals separately</span></Card>
        <Card className="metric"><p>Investments</p><strong>{formatCurrency(Number(document.budget_settings.investment_balance ?? 0))}</strong><span>Current entered balance</span></Card>
        <Card className={"metric " + (moneyLent < 0 ? "metric-warning" : "")}><p>{moneyLent < 0 ? "Money owed" : "Money lent"}</p><strong>{formatCurrency(moneyLent)}</strong><span>{history.length} historical snapshot(s)</span></Card>
      </div>

      <div className="two-column">
        <Card className="chart-card"><div className="card-heading"><div><p className="eyebrow">Breakdown</p><h2>Assets over time</h2></div><select aria-label="Default Net Worth Breakdown" value={String(breakdownPeriod)} onChange={(e) => setBreakdownPeriod(e.target.value === "All" ? "All" : Number(e.target.value))}><option>3</option><option>6</option><option>12</option><option>24</option><option>All</option></select></div>{breakdown.length > 1 ? <ResponsiveContainer width="100%" height={300}><LineChart data={breakdown}><XAxis dataKey="date" /><YAxis /><Tooltip content={<BreakdownTooltip />} /><Line dataKey="bank_balance" name="Bank" stroke={COLORS[0]} /><Line dataKey="wallet_balance" name="Wallet" stroke={COLORS[1]} /><Line dataKey="savings_balance" name="Savings" stroke={COLORS[2]} /><Line dataKey="investment_balance" name="Investments" stroke={COLORS[3]} /><Line dataKey="money_lent_balance" name="Money Lent" stroke={COLORS[4]} /></LineChart></ResponsiveContainer> : <EmptyState title="Record two snapshots to see breakdown" detail="Snapshots retain each asset balance." />}</Card>
        <Card className="chart-card">
          <div className="card-heading"><div><p className="eyebrow">Allocation</p><h2>Where your money sits</h2></div></div>
           {allocation.assets.length ? (
             <ResponsiveContainer width="100%" height={300}>
               <PieChart>
                <Pie data={allocation.assets} dataKey="value" nameKey="name" innerRadius={65} outerRadius={100} paddingAngle={3}>
                  {allocation.assets.map((_entry, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} labelStyle={tooltipTextStyle} itemStyle={tooltipTextStyle} formatter={(value) => formatCurrency(Number(value))} />
              </PieChart>
            </ResponsiveContainer>
           ) : <EmptyState title="Add account balances" detail="Balance entries from Budget will appear here." />}
          {allocation.liabilities.length ? <div className="allocation-liabilities">{allocation.liabilities.map((item) => <span key={item.name}><strong>{item.name}</strong><b>{formatCurrency(item.value)}</b><small>Shown in net worth as a liability, not as an asset slice.</small></span>)}</div> : null}
        </Card>
      </div>

      <div className="two-column">
      <Card>
        <div className="card-heading"><div><p className="eyebrow">Snapshots</p><h2>Record and review snapshots</h2></div><Camera size={22} /></div>
        <div className="card-heading"><div><p className="eyebrow">Checkpoint</p><h2>Record a snapshot</h2></div></div>
        <div className="form-grid compact-form">
          <label><span>Date</span><input type="date" value={date} onChange={(event) => setDate(event.target.value)} /></label>
          <label><span>Current value</span><input value={formatCurrency(netWorth(document))} readOnly /></label>
          <div className="span-two form-actions"><Button onClick={recordSnapshot}>Record snapshot</Button></div>
        </div>
        <div className="card-heading"><div><p className="eyebrow">Saved history</p><h2>Snapshots</h2></div></div>
        <div className="mini-list snapshot-history-list">
           {allHistory.length ? allHistory.slice().reverse().map((snapshot) => (
            <div key={snapshot.date}>
              <span>
                <strong>{snapshot.date}</strong>
                <small className={snapshot.date === history[0]?.date ? "" : (changeByDate.get(snapshot.date) ?? 0) >= 0 ? "amount-income" : "amount-expense"}>
                  {snapshot.date === history[0]?.date
                    ? "Starting point"
                    : (changeMode === "month-by-month" ? "Since previous: " : "Since beginning: ") + formatSignedCurrency(changeByDate.get(snapshot.date) ?? 0)}
                </small>
              </span>
              <strong>{formatCurrency(snapshot.net_worth)}</strong>
              <button className="icon-button danger-icon" onClick={() => removeSnapshot(snapshot.date)} aria-label="Delete snapshot"><Trash2 size={15} /></button>
            </div>
          )) : <p className="muted-copy">No snapshots recorded yet.</p>}
        </div>
      </Card>
      <Card className="chart-card">
        <div className="card-heading"><div><p className="eyebrow">Snapshot flow</p><h2>Changes over time</h2></div><select aria-label="Default Net Worth" value={String(historyPeriod)} onChange={(e) => setHistoryPeriod(e.target.value === "All" ? "All" : Number(e.target.value))}><option>3</option><option>6</option><option>12</option><option>24</option><option>All</option></select></div>
        <div className="segmented-control" aria-label="Snapshot change mode">
          <button type="button" aria-pressed={changeMode === "month-by-month"} className={changeMode === "month-by-month" ? "selected" : ""} onClick={() => setChangeMode("month-by-month")}>Month-by-month</button>
          <button type="button" aria-pressed={changeMode === "from-beginning"} className={changeMode === "from-beginning" ? "selected" : ""} onClick={() => setChangeMode("from-beginning")}>Since beginning</button>
        </div>
        {history.length > 1 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={changeRows}>
              <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fill: "#a2c4bb", fontSize: 12 }} />
              <YAxis tickFormatter={(value) => (Number(value) >= 0 ? "+" : "-") + "\u20AC" + Math.round(Math.abs(Number(value)))} tickLine={false} axisLine={false} width={80} tick={{ fill: "#a2c4bb", fontSize: 12 }} />
              <Tooltip contentStyle={tooltipStyle} labelStyle={tooltipTextStyle} itemStyle={tooltipTextStyle} formatter={(value) => formatSignedCurrency(Number(value))} />
              <Line type="monotone" dataKey="change" name={changeMode === "month-by-month" ? "Change from previous snapshot" : "Change since beginning"} stroke="#f5c451" strokeWidth={3} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        ) : <EmptyState title="Record two snapshots to see changes" detail="Snapshots retain your balance on the chosen day." />}
      </Card>
      </div>
    </div>
  );
}
