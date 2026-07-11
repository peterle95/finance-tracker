import { Download, TrendingUp } from "lucide-react";
import { useMemo, useState } from "react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatCurrency, isoToday, projection } from "../../shared/finance";
import type { FinanceDocument } from "../../shared/types";
import { Button, Card, PageHeader } from "./ui";

export function ProjectionScreen({
  document,
  onExport
}: {
  document: FinanceDocument;
  onExport(name: string, text: string): void;
}) {
  const [months, setMonths] = useState(12);
  const rows = projection(document, months);
  const report = useMemo(() => [
    "TARGET SAVINGS PROJECTION",
    "",
    ...rows.map((row) => row.month + ": " + formatCurrency(row.balance) + " (" + formatCurrency(row.change) + " target)")
  ].join("\n"), [rows]);

  return (
    <div className="page">
      <PageHeader
        eyebrow="Forward view"
        title="Projection"
        description="See how your daily savings target accumulates across your complete financial balance."
        action={<Button variant="secondary" onClick={() => onExport("financial_projection_" + isoToday() + ".txt", report)}><Download size={16} /> Export projection</Button>}
      />

      <div className="two-column">
        <Card className="projection-hero">
          <div className="card-heading"><div><p className="eyebrow">Target savings mode</p><h2>Steady progress, month by month</h2></div><TrendingUp size={26} /></div>
          <p>Your projection adds the monthly amount implied by the daily savings goal to today’s current net worth.</p>
          <label className="range-control"><span>Months to project<strong>{months}</strong></span><input type="range" min="3" max="36" step="1" value={months} onChange={(event) => setMonths(Number(event.target.value))} /></label>
          <div className="projection-total"><span>Projected balance</span><strong>{formatCurrency(rows.at(-1)?.balance ?? 0)}</strong></div>
        </Card>
        <Card className="chart-card">
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={rows}>
              <defs><linearGradient id="projectionGradient" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#2dd4bf" stopOpacity={0.8} /><stop offset="100%" stopColor="#2dd4bf" stopOpacity={0.04} /></linearGradient></defs>
              <XAxis dataKey="month" tickLine={false} axisLine={false} />
              <YAxis tickFormatter={(value) => "€" + Math.round(value)} tickLine={false} axisLine={false} width={70} />
              <Tooltip formatter={(value) => formatCurrency(Number(value))} />
              <Area type="monotone" dataKey="balance" stroke="#2dd4bf" strokeWidth={3} fill="url(#projectionGradient)" />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card className="table-card">
        <div className="card-heading"><div><p className="eyebrow">Schedule</p><h2>Projection details</h2></div></div>
        <div className="table-scroll">
          <table>
            <thead><tr><th>Month</th><th className="number">Savings target</th><th className="number">Projected balance</th></tr></thead>
            <tbody>{rows.map((row) => <tr key={row.month}><td>{row.month}</td><td className="number">{formatCurrency(row.savingsTarget)}</td><td className="number amount-income">{formatCurrency(row.balance)}</td></tr>)}</tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
