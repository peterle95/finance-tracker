import { currentMonth, monthOffset, netWorth, projection, roundCurrency, snapshots } from "./finance";
import type { FinanceDocument } from "./types";

export type JourneyResolution = "daily" | "monthly" | "yearly";
export type JourneySeriesState = "actual" | "projected" | "scenario";
export type JourneyLineStyle = "solid" | "dashed" | "accent";
export type JourneyTurningPointReason = "large_balance_change" | "liability_change" | "trend_shift" | "annotation" | "goal_milestone" | "scenario_event";

export interface JourneyHorizon {
  amount: number;
  unit: "days" | "months" | "years";
}

export const DEFAULT_JOURNEY_HORIZON: JourneyHorizon = { amount: 12, unit: "months" };

export interface JourneyDriverMetadata {
  id: string;
  label: string;
  source: "snapshots" | "transactions" | "projection" | "scenario";
}

export interface JourneyPoint {
  date: string;
  value: number;
  source: "snapshot" | "projection" | "scenario";
  label?: string;
  drivers: Record<string, number>;
}

export interface JourneySeries {
  id: string;
  label: string;
  state: JourneySeriesState;
  style: JourneyLineStyle;
  points: JourneyPoint[];
}

export interface JourneyConfidence {
  level: "high" | "medium" | "low";
  actualPoints: number;
  reason: string;
}

export interface JourneyTurningPoint {
  date: string;
  reason: JourneyTurningPointReason;
  explanation: string;
  source: "snapshot" | "scenario";
}

export interface JourneyDataset {
  horizon: JourneyHorizon;
  resolution: JourneyResolution;
  timeline: string[];
  series: JourneySeries[];
  drivers: JourneyDriverMetadata[];
  confidence: JourneyConfidence;
  assumptions: string[];
  turningPoints: JourneyTurningPoint[];
}

const JOURNEY_DRIVER_METADATA: JourneyDriverMetadata[] = [
  { id: "cash", label: "Cash", source: "snapshots" },
  { id: "assets", label: "Assets", source: "snapshots" },
  { id: "liabilities", label: "Liabilities", source: "snapshots" },
  { id: "income", label: "Income", source: "transactions" },
  { id: "expenses", label: "Expenses", source: "transactions" },
  { id: "savings-target", label: "Savings target", source: "projection" },
  { id: "scenario", label: "Scenario effect", source: "scenario" }
];

function validateHorizon(horizon: JourneyHorizon): JourneyHorizon {
  if (horizon.unit !== "days" && horizon.unit !== "months" && horizon.unit !== "years") {
    throw new RangeError("Journey horizon unit is unsupported.");
  }
  if (!Number.isFinite(horizon.amount) || !Number.isInteger(horizon.amount) || horizon.amount < 1) {
    throw new RangeError("Journey horizon must be a positive whole number.");
  }
  const max = horizon.unit === "days" ? 90 : horizon.unit === "months" ? 12 : 20;
  const min = horizon.unit === "years" ? 5 : 1;
  if (horizon.amount < min || horizon.amount > max) {
    throw new RangeError("Journey horizon is outside supported range.");
  }
  return horizon;
}

export function journeyResolution(horizon: JourneyHorizon): JourneyResolution {
  const unit = validateHorizon(horizon).unit;
  return unit === "days"
    ? "daily"
    : unit === "months"
      ? "monthly"
      : "yearly";
}

function parseDate(value: string): Date {
  const date = new Date(value + "T12:00:00Z");
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || Number.isNaN(date.getTime()) || date.toISOString().slice(0, 10) !== value) {
    throw new RangeError("Journey date must be a valid ISO date.");
  }
  return date;
}

function addDays(value: string, amount: number): string {
  const date = parseDate(value);
  date.setUTCDate(date.getUTCDate() + amount);
  return date.toISOString().slice(0, 10);
}

function addYears(value: string, amount: number): string {
  return String(Number(value.slice(0, 4)) + amount);
}

function bucketDate(value: string, resolution: JourneyResolution): string {
  return resolution === "daily" ? value : resolution === "monthly" ? value.slice(0, 7) : value.slice(0, 4);
}

function startDate(asOf: string, resolution: JourneyResolution, amount: number): string {
  if (resolution === "daily") {
    return addDays(asOf, -(amount - 1));
  }
  if (resolution === "monthly") {
    return monthOffset(currentMonth(parseDate(asOf)), -(amount - 1));
  }
  return addYears(asOf, -(amount - 1));
}

function transactionDrivers(document: FinanceDocument, date: string, resolution: JourneyResolution, asOf: string): Record<string, number> {
  const matches = [...document.incomes, ...document.expenses].filter((transaction) => {
    const transactionDate = transaction.date;
    return transactionDate <= asOf && (resolution === "daily"
      ? transactionDate === date
      : resolution === "monthly"
        ? transactionDate.startsWith(date)
        : transactionDate.startsWith(date));
  });
  if (!matches.length) {
    return {};
  }
  return {
    income: roundCurrency(document.incomes
      .filter((transaction) => matches.includes(transaction))
      .reduce((total, transaction) => total + transaction.amount, 0)),
    expenses: roundCurrency(document.expenses
      .filter((transaction) => matches.includes(transaction))
      .reduce((total, transaction) => total + transaction.amount, 0))
  };
}

function snapshotDrivers(snapshot: ReturnType<typeof snapshots>[number]): Record<string, number> {
  return {
    cash: roundCurrency(snapshot.bank_balance + snapshot.wallet_balance),
    assets: roundCurrency(snapshot.savings_balance + snapshot.investment_balance + Math.max(snapshot.money_lent_balance, 0)),
    liabilities: roundCurrency(Math.max(-snapshot.money_lent_balance, 0))
  };
}

function actualSeries(document: FinanceDocument, resolution: JourneyResolution, asOf: string, amount: number): JourneySeries {
  const firstDate = startDate(asOf, resolution, amount);
  const lastDate = bucketDate(asOf, resolution);
  const byBucket = new Map<string, ReturnType<typeof snapshots>[number]>();

  snapshots(document).forEach((snapshot) => {
    const date = bucketDate(snapshot.date, resolution);
    if (snapshot.date <= asOf && date >= firstDate && date <= lastDate) {
      byBucket.set(date, snapshot);
    }
  });

  const points = [...byBucket.entries()].sort(([first], [second]) => first.localeCompare(second)).map(([date, snapshot]) => ({
    date,
    value: snapshot.net_worth,
    source: "snapshot" as const,
    label: snapshot.note || undefined,
    drivers: {
      ...snapshotDrivers(snapshot),
      ...transactionDrivers(document, date, resolution, asOf)
    }
  }));

  return { id: "net-worth-actual", label: "Actual net worth", state: "actual", style: "solid", points };
}

function dailyProjection(document: FinanceDocument, asOf: string, amount: number): JourneyPoint[] {
  let balance = netWorth(document);
  const dailyTarget = Number(document.budget_settings.daily_savings_goal ?? 0);
  return Array.from({ length: amount }, (_, index) => {
    const change = roundCurrency(dailyTarget);
    balance = roundCurrency(balance + change);
    return {
      date: addDays(asOf, index + 1),
      value: balance,
      source: "projection" as const,
      label: "Baseline projection",
      drivers: { "savings-target": change }
    };
  });
}

function yearlyProjection(document: FinanceDocument, asOf: string, amount: number): JourneyPoint[] {
  let balance = netWorth(document);
  const dailyTarget = Number(document.budget_settings.daily_savings_goal ?? 0);
  return Array.from({ length: amount }, (_, index) => {
    const year = Number(asOf.slice(0, 4)) + index + 1;
    const daysInYear = new Date(Date.UTC(year, 1, 29)).getUTCDate() === 29 ? 366 : 365;
    const change = roundCurrency(dailyTarget * daysInYear);
    balance = roundCurrency(balance + change);
    return {
      date: String(year),
      value: balance,
      source: "projection" as const,
      label: "Baseline projection",
      drivers: { "savings-target": change }
    };
  });
}

function projectedSeries(document: FinanceDocument, resolution: JourneyResolution, asOf: string, amount: number): JourneySeries {
  let points: JourneyPoint[];
  if (resolution === "daily") {
    points = dailyProjection(document, asOf, amount);
  } else if (resolution === "monthly") {
    points = projection(document, amount, monthOffset(currentMonth(parseDate(asOf)), 1)).map((row) => ({
      date: row.month,
      value: roundCurrency(row.balance),
      source: "projection" as const,
      label: "Baseline projection",
      drivers: { "savings-target": roundCurrency(row.savingsTarget) }
    }));
  } else {
    points = yearlyProjection(document, asOf, amount);
  }
  return { id: "net-worth-baseline", label: "Baseline projection", state: "projected", style: "dashed", points };
}

function turningPoints(points: JourneyPoint[]): JourneyTurningPoint[] {
  const results: JourneyTurningPoint[] = [];
  // ponytail: fixed 10%/100 threshold; configurable rules if users need personalized markers.
  const add = (point: JourneyPoint, reason: JourneyTurningPointReason, explanation: string) => {
    results.push({ date: point.date, reason, explanation, source: "snapshot" });
  };

  points.forEach((point, index) => {
    const previous = points[index - 1];
    if (point.label) {
      add(point, "annotation", "Snapshot note: " + point.label);
    }
    if (!previous) {
      return;
    }
    const change = roundCurrency(point.value - previous.value);
    if (Math.abs(change) >= Math.max(100, Math.abs(previous.value) * 0.1)) {
      add(point, "large_balance_change", "Net worth changed by " + String(change) + ".");
    }
    if (point.drivers.liabilities !== previous.drivers.liabilities) {
      add(point, "liability_change", "Liabilities changed from " + String(previous.drivers.liabilities ?? 0) + " to " + String(point.drivers.liabilities ?? 0) + ".");
    }
    const previousChange = index > 1 ? points[index - 1].value - points[index - 2].value : 0;
    if (previousChange !== 0 && change !== 0 && Math.sign(previousChange) !== Math.sign(change)) {
      add(point, "trend_shift", "Net-worth trend changed direction.");
    }
  });
  return results;
}

function hasGaps(points: JourneyPoint[], resolution: JourneyResolution): boolean {
  return points.some((point, index) => {
    if (index === 0) {
      return false;
    }
    const previous = points[index - 1].date;
    const expected = resolution === "daily"
      ? addDays(previous, 1)
      : resolution === "monthly"
        ? monthOffset(previous, 1)
        : addYears(previous, 1);
    return point.date !== expected;
  });
}

export function buildJourneyDataset(
  document: FinanceDocument,
  horizon: JourneyHorizon = DEFAULT_JOURNEY_HORIZON,
  asOf = new Date().toISOString().slice(0, 10)
): JourneyDataset {
  const validHorizon = validateHorizon(horizon);
  const resolution = journeyResolution(validHorizon);
  parseDate(asOf);
  const actual = actualSeries(document, resolution, asOf, validHorizon.amount);
  const projected = projectedSeries(document, resolution, asOf, validHorizon.amount);
  const scenario: JourneySeries = {
    id: "net-worth-scenario",
    label: "Active scenario",
    state: "scenario",
    style: "accent",
    points: []
  };
  const timeline = [...new Set([...actual.points, ...projected.points].map((point) => point.date))].sort();
  const hasReliableCoverage = actual.points.length >= 3
    && actual.points.length / validHorizon.amount >= 0.5
    && !hasGaps(actual.points, resolution);
  const confidence = hasReliableCoverage
    ? { level: "high" as const, actualPoints: actual.points.length, reason: "Snapshots cover most selected periods without gaps." }
    : actual.points.length > 0
      ? { level: "medium" as const, actualPoints: actual.points.length, reason: "Sparse snapshot history limits historical confidence." }
      : { level: "low" as const, actualPoints: 0, reason: "No snapshots exist in selected horizon; historical gaps remain empty." };

  return {
    horizon: validHorizon,
    resolution,
    timeline,
    series: [actual, projected, scenario],
    drivers: JOURNEY_DRIVER_METADATA.map((driver) => ({ ...driver })),
    confidence,
    assumptions: ["Baseline projection uses daily_savings_goal and does not fill missing historical snapshots."],
    turningPoints: turningPoints(actual.points)
  };
}
