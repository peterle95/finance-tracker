import { ChevronLeft, ChevronRight, Download, PieChart as PieChartIcon } from "lucide-react";
import { useMemo, useState, type CSSProperties } from "react";
import {
  Bar,
  Cell,
  ComposedChart,
  LabelList,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { DEFAULT_BEHAVIOR_SETTINGS, type DefaultBehaviorSettings } from "../../shared/behavior-settings";
import {
  categoryTotals,
  currentMonth,
  dayOfWeekHeatmap,
  formatCurrency,
  historicalBreakdown,
  historicalTotals,
  monthOffset,
  monthTransactions,
  spendingPace
} from "../../shared/finance";
import { DEFAULT_RANGE_SETTINGS, type DefaultRangeSettings } from "../../shared/range-settings";
import type { HistoricalBreakdownMode, TransactionDateBasis } from "../../shared/finance";
import type { FinanceDocument, TransactionType } from "../../shared/types";
import { tooltipStyle, tooltipTextStyle } from "./chartStyles";
import { Button, Card, PageHeader } from "./ui";

const COLORS = ["#f5c451", "#2dd4bf", "#7dd3fc", "#8b5cf6", "#fb7185", "#fb923c", "#84cc16"];
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

type ChartKind = "pie" | "history" | "line" | "heatmap" | "pace";
type HistoryMode = "total" | HistoricalBreakdownMode;
type HistoryDisplay = "value" | "percentage";

function setChartValue(row: Record<string, string | number>, key: string, value: number): void {
  Object.defineProperty(row, key, { value, enumerable: true, configurable: true, writable: true });
}

function trendValues(values: number[]): number[] {
  if (values.length < 2) {
    return values;
  }
  const averageX = (values.length - 1) / 2;
  const averageY = values.reduce((total, value) => total + value, 0) / values.length;
  const numerator = values.reduce((total, value, index) => total + (index - averageX) * (value - averageY), 0);
  const denominator = values.reduce((total, _value, index) => total + (index - averageX) ** 2, 0);
  const slope = denominator ? numerator / denominator : 0;
  return values.map((_value, index) => averageY + slope * (index - averageX));
}

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
      setChartValue(row, category, monthTransactions(document, "Expense", month, dateBasis)
        .filter((transaction) => transaction.category === category)
        .reduce((total, transaction) => total + transaction.amount, 0));
    });
    rows.push(row);
    month = monthOffset(month, 1);
  }
  return rows;
}

export function ReportsScreen({
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
  const [kind, setKind] = useState<ChartKind>(defaultBehaviors.reportView);
  const [type, setType] = useState<TransactionType>(defaultBehaviors.reportType);
  const [dateFilterMode, setDateFilterMode] = useState<"month" | "range">("month");
  const [month, setMonth] = useState(currentMonth());
  const [startMonth, setStartMonth] = useState(monthOffset(currentMonth(), -(defaultRanges.reportLineMonths - 1)));
  const [endMonth, setEndMonth] = useState(currentMonth());
  const [selectedCategories, setSelectedCategories] = useState<string[]>(document.categories[defaultBehaviors.reportType].slice(0, 3));
  const rangeStart = dateFilterMode === "month" ? month : startMonth;
  const rangeEnd = dateFilterMode === "month" ? month : endMonth;
  const historyMonths = dateFilterMode === "month" ? 1 : Math.max(1, (Number(rangeEnd.slice(0, 4)) - Number(rangeStart.slice(0, 4))) * 12 + Number(rangeEnd.slice(5)) - Number(rangeStart.slice(5)) + 1);
  const [dateBasis, setDateBasis] = useState<TransactionDateBasis>(defaultBehaviors.reportDateBasis);
  const [historyMode, setHistoryMode] = useState<HistoryMode>(defaultBehaviors.reportHistoryMode);
  const [historyDisplay, setHistoryDisplay] = useState<HistoryDisplay>(defaultBehaviors.reportHistoryDisplay);
  const [includeRecurring, setIncludeRecurring] = useState(defaultBehaviors.reportIncludeRecurring);
  const [showHistoryLabels, setShowHistoryLabels] = useState(defaultBehaviors.reportShowHistoryLabels);
  const pieData = categoryTotals(document, type, rangeStart, rangeEnd, includeRecurring, dateBasis);
  const historyData = historicalTotals(document, type, historyMonths, rangeEnd, dateBasis, includeRecurring);
  const historyMonthLabels = historyData.map((entry) => entry.month);
  const rawHistorySeries = historyMode === "total"
    ? [{ name: type === "Expense" ? "Expenses" : "Income", values: historyData.map((entry) => entry.value) }]
    : historicalBreakdown(document, type, historyMonthLabels, historyMode, includeRecurring, dateBasis);
  const historySeries = historyDisplay === "percentage" && historyMode === "categories"
    ? rawHistorySeries.map((series) => ({
      ...series,
      values: series.values.map((value, index) => {
        const total = rawHistorySeries.reduce((sum, entry) => sum + entry.values[index], 0);
        return total ? value / total * 100 : 0;
      })
    }))
    : historyDisplay === "percentage" && historyMode === "flexible"
      ? [{
        name: "Flexible Costs % of Income",
        values: rawHistorySeries[1]?.values.map((cost, index) => {
          const income = rawHistorySeries[0]?.values[index] ?? 0;
          return income > 0 ? cost / income * 100 : cost > 0 ? 100 : 0;
        }) ?? []
      }]
      : historyDisplay === "percentage" && historyMode === "over-under"
        ? [{
          name: "Net Result",
          values: rawHistorySeries[0]?.values.map((income, index) => income - (rawHistorySeries[1]?.values[index] ?? 0)) ?? []
        }]
        : rawHistorySeries;
  const historyChartData = historyMonthLabels.map((historyMonth, index) => {
    const row: Record<string, string | number> = { month: historyMonth };
    historySeries.forEach((series) => {
      setChartValue(row, series.name, series.values[index] ?? 0);
    });
    if (historyMode === "total") {
      row.Trend = trendValues(historyData.map((entry) => entry.value))[index] ?? 0;
    }
    return row;
  });
  const historyUsesPercent = historyDisplay === "percentage" && (historyMode === "categories" || historyMode === "flexible");
  const categoryLine = useMemo(
    () => lineRows(document, rangeStart, rangeEnd, selectedCategories, dateBasis),
    [document, rangeStart, rangeEnd, selectedCategories, dateBasis]
  );
  const heatmap = dayOfWeekHeatmap(document, historyMonths, rangeEnd, dateBasis);
  const pace = spendingPace(document, month, dateBasis);
  const reportPeriod = kind === "history"
    ? "Last " + historyMonths + " months"
    : kind === "pie" ? rangeStart + " to " + rangeEnd : kind === "pace" ? month : rangeStart + " to " + rangeEnd;
  const reportValues = kind === "history"
    ? historyChartData.map((row) => row.month + ": " + historySeries
      .map((series) => series.name + " " + (historyUsesPercent ? Number(row[series.name]).toFixed(1) + "%" : formatCurrency(Number(row[series.name]))))
      .join(", "))
    : pieData.map((entry) => entry.name + ": " + formatCurrency(entry.value));
  const report = [
    "FINANCE REPORT",
    "",
    "View: " + kind,
    "Date basis: " + (dateBasis === "behavior" ? "Spend date (metadata)" : "Transaction date"),
    ...(kind === "history" ? ["History mode: " + historyMode, "Display: " + historyDisplay] : []),
    "Period: " + reportPeriod,
    "",
    ...reportValues
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
          <div className="segmented-control" aria-label="Report date filter">
            <button className={dateFilterMode === "month" ? "selected" : ""} onClick={() => setDateFilterMode("month")}>Month</button>
            <button className={dateFilterMode === "range" ? "selected" : ""} onClick={() => setDateFilterMode("range")}>Range</button>
          </div>
          {dateFilterMode === "month" ? <div className="budget-month-navigation" aria-label="Report month navigation">
            <Button type="button" variant="ghost" aria-label="Previous report month" onClick={() => setMonth(monthOffset(month, -1))}><ChevronLeft size={17} /></Button>
            <input aria-label="Report month" type="month" value={month} onChange={(event) => event.target.value && setMonth(event.target.value)} />
            <Button type="button" variant="ghost" aria-label="Next report month" onClick={() => setMonth(monthOffset(month, 1))}><ChevronRight size={17} /></Button>
          </div> : <>
            <input aria-label="Report from month" type="month" value={startMonth} onChange={(event) => setStartMonth(event.target.value)} />
            <input aria-label="Report to month" type="month" value={endMonth} onChange={(event) => setEndMonth(event.target.value)} />
          </>}
          {(kind === "pie" || kind === "history") ? (
            <select value={type} onChange={(event) => setType(event.target.value as TransactionType)}>
              <option value="Expense">Expenses</option>
              <option value="Income">Income</option>
            </select>
          ) : null}
          {kind === "history" ? (
            <>
              <select aria-label="History breakdown" value={historyMode} onChange={(event) => setHistoryMode(event.target.value as HistoryMode)}>
                <option value="total">Monthly totals</option>
                <option value="categories">Categories</option>
                <option value="flexible">Flexible income vs costs</option>
                <option value="over-under">Total income vs expenses</option>
              </select>
              {historyMode !== "total" ? (
                <select aria-label="History display" value={historyDisplay} onChange={(event) => setHistoryDisplay(event.target.value as HistoryDisplay)}>
                  <option value="value">Values</option>
                  <option value="percentage">{historyMode === "over-under" ? "Net result" : "Percentage"}</option>
                </select>
              ) : null}
              {historyMode === "total" || historyMode === "categories" ? (
                <label className="check-row toolbar-check">
                  <input type="checkbox" checked={includeRecurring} onChange={(event) => setIncludeRecurring(event.target.checked)} />
                  <span>{type === "Expense" ? "Include fixed costs" : "Include base income"}</span>
                </label>
              ) : null}
              <label className="check-row toolbar-check">
                <input type="checkbox" checked={showHistoryLabels} onChange={(event) => setShowHistoryLabels(event.target.checked)} />
                <span>Show labels</span>
              </label>
            </>
          ) : null}
          {kind === "line" ? (
            <>
            </>
          ) : null}
          {kind === "pie" ? (
            <label className="check-row toolbar-check">
              <input type="checkbox" checked={includeRecurring} onChange={(event) => setIncludeRecurring(event.target.checked)} />
              <span>{type === "Expense" ? "Include fixed costs" : "Include base income"}</span>
            </label>
          ) : null}
        </div>
      </Card>

      {kind === "pie" ? (
        <Card className="chart-card report-chart">
          <div className="card-heading"><div><p className="eyebrow">{rangeStart} to {rangeEnd}</p><h2>{type} by category</h2></div><PieChartIcon size={22} /></div>
          {pieData.length ? (
            <ResponsiveContainer width="100%" height={420}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={145} innerRadius={75} paddingAngle={3}>
                  {pieData.map((_entry, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} labelStyle={tooltipTextStyle} itemStyle={tooltipTextStyle} formatter={(value) => formatCurrency(Number(value))} />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="muted-copy">No data for this range.</p>}
          <div className="legend-list">{pieData.map((entry, index) => <span key={entry.name}><i style={{ backgroundColor: COLORS[index % COLORS.length] }} />{entry.name}<strong>{formatCurrency(entry.value)}</strong></span>)}</div>
        </Card>
      ) : null}

      {kind === "history" ? (
        <Card className="chart-card report-chart">
          <div className="card-heading"><div><p className="eyebrow">Last {historyMonths} months</p><h2>{historyMode === "total" ? type + " history" : historyMode === "categories" ? type + " category history" : historyMode === "flexible" ? "Flexible income vs costs" : historyDisplay === "percentage" ? "Monthly net result" : "Total income vs expenses"}</h2></div></div>
          {historySeries.length ? (
            <ResponsiveContainer width="100%" height={420}>
              <ComposedChart data={historyChartData}>
                <XAxis dataKey="month" tickLine={false} axisLine={false} />
                <YAxis tickFormatter={(value) => historyUsesPercent ? Math.round(value) + "%" : "€" + Math.round(value)} tickLine={false} axisLine={false} width={70} />
                <Tooltip contentStyle={tooltipStyle} labelStyle={tooltipTextStyle} itemStyle={tooltipTextStyle} formatter={(value) => historyUsesPercent ? Number(value).toFixed(1) + "%" : formatCurrency(Number(value))} />
                {historyMode !== "total" ? <Legend /> : null}
                {historyDisplay === "percentage" && historyMode === "over-under" ? <ReferenceLine y={0} stroke="#94a3b8" /> : null}
                {historySeries.map((series, index) => (
                  <Bar
                    key={series.name}
                    dataKey={series.name}
                    stackId={historyMode === "categories" ? "categories" : undefined}
                    radius={historyMode === "categories" ? 0 : [8, 8, 0, 0]}
                    fill={historyMode === "total" ? type === "Expense" ? "#fb7185" : "#2dd4bf" : COLORS[index % COLORS.length]}
                  >
                    {historyDisplay === "percentage" && (historyMode === "flexible" || historyMode === "over-under")
                      ? historyChartData.map((row) => {
                        const value = Number(row[series.name]);
                        const positive = historyMode === "flexible" ? value <= 100 : value >= 0;
                        return <Cell key={String(row.month)} fill={positive ? "#2dd4bf" : "#fb7185"} />;
                      })
                      : null}
                    {showHistoryLabels ? <LabelList dataKey={series.name} position="top" formatter={(value) => historyUsesPercent ? Math.round(Number(value)) + "%" : "€" + Math.round(Number(value))} /> : null}
                  </Bar>
                ))}
                {historyMode === "total" ? <Line type="monotone" dataKey="Trend" stroke="#f5c451" strokeWidth={2} strokeDasharray="7 5" dot={false} /> : null}
              </ComposedChart>
            </ResponsiveContainer>
          ) : <p className="muted-copy">No history data for this view.</p>}
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
              <Tooltip contentStyle={tooltipStyle} labelStyle={tooltipTextStyle} itemStyle={tooltipTextStyle} formatter={(value) => formatCurrency(Number(value))} />
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
