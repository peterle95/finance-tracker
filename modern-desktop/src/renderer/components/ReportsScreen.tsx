import { Download, PieChart as PieChartIcon } from "lucide-react";
import { useMemo, useState, type CSSProperties } from "react";
import {
  Bar,
  BarChart,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import {
  categoryTotals,
  currentMonth,
  dayOfWeekHeatmap,
  formatCurrency,
  historicalTotals,
  monthOffset,
  monthTransactions,
  spendingPace
} from "../../shared/finance";
import type { TransactionDateBasis } from "../../shared/finance";
import type { FinanceDocument, TransactionType } from "../../shared/types";
import { Button, Card, PageHeader } from "./ui";

const COLORS = ["#f5c451", "#2dd4bf", "#7dd3fc", "#8b5cf6", "#fb7185", "#fb923c", "#84cc16"];
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

type ChartKind = "pie" | "history" | "line" | "heatmap" | "pace";

function lineRows(
  document: FinanceDocument,
  start: string,
  end: string,
  categories: string[],
  dateBasis: TransactionDateBasis
) {
  const rows: Array<Record<string, string | number>> = [];
  let month = start;
  while (month <= end) {
    const row: Record<string, string | number> = { month };
    categories.forEach((category) => {
      row[category] = monthTransactions(document, "Expense", month, dateBasis)
        .filter((transaction) => transaction.category === category)
        .reduce((total, transaction) => total + transaction.amount, 0);
    });
    rows.push(row);
    month = monthOffset(month, 1);
  }
  return rows;
}

export function ReportsScreen({
  document,
  onExport
}: {
  document: FinanceDocument;
  onExport(name: string, text: string): void;
}) {
  const [kind, setKind] = useState<ChartKind>("pie");
  const [type, setType] = useState<TransactionType>("Expense");
  const [month, setMonth] = useState(currentMonth());
  const [rangeStart, setRangeStart] = useState(monthOffset(currentMonth(), -5));
  const [rangeEnd, setRangeEnd] = useState(currentMonth());
  const [selectedCategories, setSelectedCategories] = useState<string[]>(document.categories.Expense.slice(0, 3));
  const [historyMonths, setHistoryMonths] = useState(6);
  const [dateBasis, setDateBasis] = useState<TransactionDateBasis>("transaction");
  const pieData = categoryTotals(document, type, month, month, true, dateBasis);
  const historyData = historicalTotals(document, type, historyMonths, currentMonth(), dateBasis);
  const categoryLine = useMemo(
    () => lineRows(document, rangeStart, rangeEnd, selectedCategories, dateBasis),
    [document, rangeStart, rangeEnd, selectedCategories, dateBasis]
  );
  const heatmap = dayOfWeekHeatmap(document, historyMonths, currentMonth(), dateBasis);
  const pace = spendingPace(document, month, dateBasis);
  const report = [
    "FINANCE REPORT",
    "",
    "View: " + kind,
    "Date basis: " + (dateBasis === "behavior" ? "Spend date (metadata)" : "Transaction date"),
    "Period: " + (kind === "pie" || kind === "pace" ? month : rangeStart + " to " + rangeEnd),
    "",
    ...pieData.map((entry) => entry.name + ": " + formatCurrency(entry.value))
  ].join("\n");

  function toggleCategory(category: string) {
    setSelectedCategories((current) => current.includes(category)
      ? current.filter((entry) => entry !== category)
      : [...current, category]);
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="Visual analysis"
        title="Reports"
        description="Turn the shared ledger into focused answers about spending, income, and pace."
        action={<Button variant="secondary" onClick={() => onExport("finance_report_" + month + ".txt", report)}><Download size={16} /> Export report</Button>}
      />

      <Card className="report-controls">
        <div className="segmented-control" aria-label="Chart type">
          {([
            ["pie", "Breakdown"],
            ["history", "History"],
            ["line", "Categories"],
            ["heatmap", "Weekdays"],
            ["pace", "Pace"]
          ] as Array<[ChartKind, string]>).map(([value, label]) => (
            <button key={value} className={kind === value ? "selected" : ""} onClick={() => setKind(value)}>{label}</button>
          ))}
        </div>
        <div className="toolbar">
          <select
            aria-label="Report date basis"
            value={dateBasis}
            onChange={(event) => setDateBasis(event.target.value as TransactionDateBasis)}
          >
            <option value="transaction">Transaction date</option>
            <option value="behavior">Spend date (metadata)</option>
          </select>
          {(kind === "pie" || kind === "history") ? (
            <select value={type} onChange={(event) => setType(event.target.value as TransactionType)}>
              <option value="Expense">Expenses</option>
              <option value="Income">Income</option>
            </select>
          ) : null}
          {kind === "pie" || kind === "pace" ? <input type="month" value={month} onChange={(event) => setMonth(event.target.value)} /> : null}
          {kind === "history" || kind === "heatmap" ? <label className="control-label">Months<input type="number" min="1" max="24" value={historyMonths} onChange={(event) => setHistoryMonths(Math.max(1, Number(event.target.value)))} /></label> : null}
          {kind === "line" ? (
            <>
              <label className="control-label">From<input type="month" value={rangeStart} onChange={(event) => setRangeStart(event.target.value)} /></label>
              <label className="control-label">To<input type="month" value={rangeEnd} onChange={(event) => setRangeEnd(event.target.value)} /></label>
            </>
          ) : null}
        </div>
      </Card>

      {kind === "pie" ? (
        <Card className="chart-card report-chart">
          <div className="card-heading"><div><p className="eyebrow">{month}</p><h2>{type} by category</h2></div><PieChartIcon size={22} /></div>
          {pieData.length ? (
            <ResponsiveContainer width="100%" height={420}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={145} innerRadius={75} paddingAngle={3}>
                  {pieData.map((_entry, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(value) => formatCurrency(Number(value))} />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="muted-copy">No data for this month.</p>}
          <div className="legend-list">{pieData.map((entry, index) => <span key={entry.name}><i style={{ backgroundColor: COLORS[index % COLORS.length] }} />{entry.name}<strong>{formatCurrency(entry.value)}</strong></span>)}</div>
        </Card>
      ) : null}

      {kind === "history" ? (
        <Card className="chart-card report-chart">
          <div className="card-heading"><div><p className="eyebrow">Last {historyMonths} months</p><h2>{type} history</h2></div></div>
          <ResponsiveContainer width="100%" height={420}>
            <BarChart data={historyData}>
              <XAxis dataKey="month" tickLine={false} axisLine={false} />
              <YAxis tickFormatter={(value) => "€" + Math.round(value)} tickLine={false} axisLine={false} width={70} />
              <Tooltip formatter={(value) => formatCurrency(Number(value))} />
              <Bar dataKey="value" radius={[8, 8, 0, 0]} fill={type === "Expense" ? "#fb7185" : "#2dd4bf"} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      ) : null}

      {kind === "line" ? (
        <Card className="chart-card report-chart">
          <div className="card-heading"><div><p className="eyebrow">Selected categories</p><h2>Expense trends</h2></div></div>
          <div className="chip-list">
            {document.categories.Expense.map((category) => <button key={category} className={selectedCategories.includes(category) ? "selected-chip" : ""} onClick={() => toggleCategory(category)}>{category}</button>)}
          </div>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={categoryLine}>
              <XAxis dataKey="month" tickLine={false} axisLine={false} />
              <YAxis tickFormatter={(value) => "€" + Math.round(value)} tickLine={false} axisLine={false} width={70} />
              <Tooltip formatter={(value) => formatCurrency(Number(value))} />
              {selectedCategories.map((category, index) => <Line key={category} type="monotone" dataKey={category} stroke={COLORS[index % COLORS.length]} strokeWidth={3} dot={{ r: 3 }} />)}
            </LineChart>
          </ResponsiveContainer>
        </Card>
      ) : null}

      {kind === "heatmap" ? (
        <Card>
          <div className="card-heading"><div><p className="eyebrow">Last {historyMonths} months</p><h2>Spending by weekday</h2></div></div>
          <div className="heatmap">
            {heatmap.map((entry) => {
              const maximum = Math.max(...heatmap.map((value) => value.value), 1);
              return <div key={entry.day} style={{ "--heat": String(entry.value / maximum) } as CSSProperties}><span>{DAYS[entry.day]}</span><strong>{formatCurrency(entry.value)}</strong></div>;
            })}
          </div>
        </Card>
      ) : null}

      {kind === "pace" ? (
        <div className="two-column">
          <Card className="projection-hero">
            <div className="card-heading"><div><p className="eyebrow">{month}</p><h2>{pace.status}</h2></div></div>
            <p>Spend at most {formatCurrency(pace.dailyTarget)} each remaining day to stay within the current flexible plan.</p>
            <div className="projection-total"><span>Remaining flexible budget</span><strong>{formatCurrency(pace.remainingBudget)}</strong></div>
          </Card>
          <Card>
            <dl className="summary-list">
              <div><dt>Flexible budget</dt><dd>{formatCurrency(pace.flexibleBudget)}</dd></div>
              <div><dt>Spent to date</dt><dd>{formatCurrency(pace.spent)}</dd></div>
              <div><dt>Days remaining</dt><dd>{pace.daysRemaining}</dd></div>
              <div><dt>Target per day</dt><dd>{formatCurrency(pace.dailyTarget)}</dd></div>
            </dl>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
