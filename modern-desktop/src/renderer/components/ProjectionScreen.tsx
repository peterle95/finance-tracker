import { Download, TrendingUp } from "lucide-react";
import { useState } from "react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatCurrency, isoToday, netWorthTrendProjection, projection } from "../../shared/finance";
import { DEFAULT_BEHAVIOR_SETTINGS, type DefaultBehaviorSettings } from "../../shared/behavior-settings";
import { DEFAULT_RANGE_SETTINGS, type DefaultRangeSettings } from "../../shared/range-settings";
import type { FinanceDocument } from "../../shared/types";
import { tooltipStyle, tooltipTextStyle } from "./chartStyles";
import { Button, Card, PageHeader } from "./ui";

type ProjectionMode = "target" | "net-worth";

function formatSignedCurrency(value: number): string {
  return (value >= 0 ? "+" : "−") + formatCurrency(Math.abs(value));
}

export function ProjectionScreen({
  document,
  defaultRanges = DEFAULT_RANGE_SETTINGS,
  defaultBehaviors = DEFAULT_BEHAVIOR_SETTINGS,
  onExport
}: {
  document: FinanceDocument;
  defaultRanges?: DefaultRangeSettings;
  defaultBehaviors?: DefaultBehaviorSettings;
  onExport(name: string, text: string): void;
}) {
  const [months, setMonths] = useState(defaultRanges.projectionMonths);
  const [mode, setMode] = useState<ProjectionMode>(defaultBehaviors.projectionMode);
  const [historyMonths, setHistoryMonths] = useState(defaultRanges.projectionHistoryMonths);
  const targetRows = projection(document, months);
  const trend = netWorthTrendProjection(document, months, historyMonths);
  const rows = mode === "target" ? targetRows : trend?.rows ?? [];
  const report = mode === "target"
    ? [
      "TARGET SAVINGS PROJECTION",
      "",
      ...targetRows.map((row) => row.month + ": " + formatCurrency(row.balance) + " (" + formatCurrency(row.change) + " target)")
    ].join("\n")
    : [
      "NET WORTH TREND PROJECTION",
      "",
      ...(trend ? [
        "Latest snapshot: " + trend.latestSnapshot.date + " " + formatCurrency(trend.latestSnapshot.net_worth),
        "Average month-by-month change: " + formatSignedCurrency(trend.averageMonthlyChange),
        "Intervals used: " + trend.intervals.length + " of " + trend.availableIntervals,
        "",
        ...trend.rows.map((row) => row.month + ": " + formatCurrency(row.balance) + " (" + formatSignedCurrency(row.change) + ")")
      ] : ["Record at least two net worth snapshots to calculate a trend."])
    ].join("\n");

  return (
    <div className="page">
      <PageHeader
        eyebrow="Forward view"
        title="Projection"
        description="Project target savings or continue the average month-by-month trend from your net worth snapshots."
        action={<Button variant="secondary" onClick={() => onExport("financial_projection_" + isoToday() + ".txt", report)}><Download size={16} /> Export projection</Button>}
      />

      <Card className="report-controls">
        <div className="segmented-control" aria-label="Projection mode">
          <button className={mode === "target" ? "selected" : ""} onClick={() => setMode("target")}>Target savings</button>
          <button className={mode === "net-worth" ? "selected" : ""} onClick={() => setMode("net-worth")}>Net worth trend</button>
        </div>
        {mode === "net-worth" ? (
          <label className="control-label">Months to analyze<input type="number" min="1" max="120" value={historyMonths} onChange={(event) => {
            const value = Number(event.target.value);
            setHistoryMonths(Number.isFinite(value) ? Math.max(1, Math.floor(value)) : 1);
          }} /></label>
        ) : null}
      </Card>

      <div className="two-column">
        <Card className="projection-hero">
          <div className="card-heading"><div><p className="eyebrow">{mode === "target" ? "Target savings mode" : "Snapshot trend mode"}</p><h2>{mode === "target" ? "Steady progress, month by month" : "Continue your recorded trajectory"}</h2></div><TrendingUp size={26} /></div>
          <p>{mode === "target"
            ? "Projection adds monthly amount implied by daily savings goal to today’s current net worth."
            : "Projection applies average change across recent net worth snapshot intervals to latest recorded snapshot."}</p>
          <label className="range-control"><span>Months to project<strong>{months}</strong></span><input type="range" min="3" max="36" step="1" value={months} onChange={(event) => setMonths(Number(event.target.value))} /></label>
          <div className="projection-total"><span>Projected balance</span><strong>{formatCurrency(rows.at(-1)?.balance ?? 0)}</strong></div>
          {mode === "net-worth" && trend ? <small>{trend.intervals.length} of {trend.availableIntervals} available changes analyzed. Average {formatSignedCurrency(trend.averageMonthlyChange)} per month.</small> : null}
        </Card>
        <Card className="chart-card">
          {rows.length ? (
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={rows}>
                <defs><linearGradient id="projectionGradient" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#2dd4bf" stopOpacity={0.8} /><stop offset="100%" stopColor="#2dd4bf" stopOpacity={0.04} /></linearGradient></defs>
                <XAxis dataKey="month" tickLine={false} axisLine={false} />
                <YAxis tickFormatter={(value) => "€" + Math.round(value)} tickLine={false} axisLine={false} width={70} />
                <Tooltip contentStyle={tooltipStyle} labelStyle={tooltipTextStyle} itemStyle={tooltipTextStyle} formatter={(value) => formatCurrency(Number(value))} />
                <Area type="monotone" dataKey="balance" stroke="#2dd4bf" strokeWidth={3} fill="url(#projectionGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : <p className="muted-copy">Record at least two net worth snapshots to calculate a month-by-month trend.</p>}
        </Card>
      </div>

      <Card className="table-card">
        <div className="card-heading"><div><p className="eyebrow">Schedule</p><h2>Projection details</h2></div></div>
        <div className="table-scroll">
          <table>
            <thead><tr><th>Month</th><th className="number">{mode === "target" ? "Savings target" : "Projected change"}</th><th className="number">Projected balance</th></tr></thead>
            <tbody>{rows.map((row) => <tr key={row.month}><td>{row.month}</td><td className="number">{mode === "target" && "savingsTarget" in row ? formatCurrency(Number(row.savingsTarget)) : formatSignedCurrency(row.change)}</td><td className="number amount-income">{formatCurrency(row.balance)}</td></tr>)}</tbody>
          </table>
        </div>
      </Card>

      {mode === "net-worth" && trend ? (
        <Card>
          <div className="card-heading"><div><p className="eyebrow">Average calculation</p><h2>Snapshot intervals used</h2></div></div>
          <div className="mini-list">
            {trend.intervals.map((interval) => (
              <div key={interval.fromDate + interval.toDate}>
                <span><strong>{interval.fromDate} → {interval.toDate}</strong></span>
                <strong className={interval.change >= 0 ? "amount-income" : "amount-expense"}>{formatSignedCurrency(interval.change)}</strong>
              </div>
            ))}
          </div>
        </Card>
      ) : null}
    </div>
  );
}
