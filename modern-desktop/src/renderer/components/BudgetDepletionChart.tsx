import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { dailyBudgetDevelopment, formatCurrency, monthDays } from "../../shared/finance";
import type { FinanceDocument } from "../../shared/types";
import { tooltipStyle, tooltipTextStyle } from "./chartStyles";
import { Card } from "./ui";

function BudgetTooltip({
  active,
  payload,
  label
}: {
  active?: boolean;
  payload?: Array<{ dataKey?: string | number; value?: string | number }>;
  label?: string | number;
}) {
  if (!active || !payload?.length) {
    return null;
  }

  const dailyTarget = payload.find((entry) => entry.dataKey === "dailyTarget")?.value ?? 0;
  const remainingBudget = payload.find((entry) => entry.dataKey === "remainingBudget")?.value ?? 0;
  return (
    <div style={{ ...tooltipStyle, padding: "0.65rem 0.8rem" }}>
      <p style={{ margin: "0 0 0.35rem", fontWeight: 700 }}>Day {label}</p>
      <p style={{ ...tooltipTextStyle, margin: "0.2rem 0" }}>Daily target: {formatCurrency(Number(dailyTarget))}</p>
      <p style={{ ...tooltipTextStyle, margin: "0.2rem 0" }}>Remaining budget: {formatCurrency(Number(remainingBudget))}</p>
    </div>
  );
}

export function BudgetDepletionChart({
  document,
  month,
  includeNegativeCarryover = false,
  carryoverMonths = 1
}: {
  document: FinanceDocument;
  month: string;
  includeNegativeCarryover?: boolean;
  carryoverMonths?: number;
}) {
  const points = dailyBudgetDevelopment(document, month, includeNegativeCarryover, new Date(), carryoverMonths);
  const today = new Date();
  const todayMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;
  const chartData = points.map((point) => ({
    ...point,
    positiveBalance: Math.max(point.remainingBudget, 0),
    negativeBalance: Math.min(point.remainingBudget, 0)
  }));

  return (
    <Card className="chart-card budget-depletion-card">
      <div className="card-heading">
        <div><p className="eyebrow">Daily development</p><h2>Budget depletion</h2></div>
      </div>
      {chartData.length ? (
        <ResponsiveContainer width="100%" height={350}>
          <ComposedChart data={chartData} margin={{ top: 12, right: 18, left: 6, bottom: 8 }}>
            <CartesianGrid stroke="rgba(162, 196, 187, 0.12)" strokeDasharray="3 3" />
            <XAxis type="number" dataKey="day" domain={[1, monthDays(month)]} allowDecimals={false} tickLine={false} axisLine={false} label={{ value: "Day of month", position: "insideBottom", offset: -4 }} />
            <YAxis tickFormatter={(value) => formatCurrency(Number(value))} tickLine={false} axisLine={false} width={82} />
            <Tooltip content={<BudgetTooltip />} />
            <Legend />
            <ReferenceLine y={0} stroke="#94a3b8" />
            {month === todayMonth && <ReferenceLine x={today.getDate()} stroke="#f5c451" strokeWidth={2} label={{ value: "Today", position: "insideTop", fill: "#f5c451" }} />}
            <Area type="monotone" dataKey="positiveBalance" name="Positive balance" stroke="transparent" fill="#2dd4bf" fillOpacity={0.16} isAnimationActive={false} />
            <Area type="monotone" dataKey="negativeBalance" name="Negative balance" stroke="transparent" fill="#fb7185" fillOpacity={0.2} isAnimationActive={false} />
            <Line type="monotone" dataKey="remainingBudget" name="Remaining budget" stroke="#2dd4bf" strokeWidth={3} dot={{ r: 3 }} isAnimationActive={false} />
            <Line type="monotone" dataKey="dailyTarget" name="Daily target" stroke="#f5c451" strokeWidth={2} strokeDasharray="7 5" dot={{ r: 3 }} isAnimationActive={false} />
          </ComposedChart>
        </ResponsiveContainer>
      ) : <p className="muted-copy">No data for this month yet.</p>}
    </Card>
  );
}
