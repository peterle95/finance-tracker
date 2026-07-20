import { describe, expect, it } from "vitest";
import { defaultDocument } from "./finance";
import { buildJourneyDataset, journeyResolution } from "./journey";

describe("journey adapters", () => {
  it("maps supported horizons to daily, monthly, and yearly resolutions", () => {
    expect(journeyResolution({ amount: 90, unit: "days" })).toBe("daily");
    expect(journeyResolution({ amount: 12, unit: "months" })).toBe("monthly");
    expect(journeyResolution({ amount: 5, unit: "years" })).toBe("yearly");
    expect(journeyResolution({ amount: 20, unit: "years" })).toBe("yearly");
  });

  it("preserves sparse actual history and exposes projection metadata", () => {
    const document = defaultDocument();
    document.budget_settings.daily_savings_goal = 10;
    document.budget_settings.asset_snapshots = [
      { date: "2026-05-01", net_worth: 1000, bank_balance: 1000, wallet_balance: 0, savings_balance: 0, investment_balance: 0, money_lent_balance: 0 },
      { date: "2026-07-01", net_worth: 1200, bank_balance: 1250, wallet_balance: 0, savings_balance: 0, investment_balance: 0, money_lent_balance: -50, note: "Debt added" }
    ];
    document.expenses.push({ date: "2026-07-01", amount: 25, category: "Food", description: "Lunch" });
    document.expenses.push({ date: "2026-07-25", amount: 100, category: "Food", description: "Future lunch" });

    const dataset = buildJourneyDataset(document, { amount: 12, unit: "months" }, "2026-07-20");
    const actual = dataset.series.find((series) => series.state === "actual")!;
    const projected = dataset.series.find((series) => series.state === "projected")!;

    expect(dataset.resolution).toBe("monthly");
    expect(dataset.series.map((series) => series.state)).toEqual(["actual", "projected", "scenario"]);
    expect(actual.points.map((point) => point.date)).toEqual(["2026-05", "2026-07"]);
    expect(actual.points[1].drivers).toMatchObject({ cash: 1250, liabilities: 50, expenses: 25 });
    expect(projected.points).toHaveLength(12);
    expect(projected.points[0]).toMatchObject({ date: "2026-08", source: "projection", drivers: { "savings-target": 310 } });
    expect(dataset.timeline).toContain("2026-05");
    expect(dataset.timeline).not.toContain("2026-06");
    expect(dataset.confidence.level).toBe("medium");
    expect(dataset.assumptions[0]).toContain("does not fill missing historical snapshots");
  });

  it("emits deterministic reasons for annotations, debt changes, and trend shifts", () => {
    const document = defaultDocument();
    document.budget_settings.asset_snapshots = [
      { date: "2026-05-01", net_worth: 1000, bank_balance: 1000, wallet_balance: 0, savings_balance: 0, investment_balance: 0, money_lent_balance: 0 },
      { date: "2026-06-01", net_worth: 1200, bank_balance: 1250, wallet_balance: 0, savings_balance: 0, investment_balance: 0, money_lent_balance: -50, note: "Debt added" },
      { date: "2026-07-01", net_worth: 900, bank_balance: 950, wallet_balance: 0, savings_balance: 0, investment_balance: 0, money_lent_balance: 0 }
    ];

    const reasons = buildJourneyDataset(document, { amount: 12, unit: "months" }, "2026-07-20").turningPoints.map((point) => point.reason);

    expect(reasons).toContain("annotation");
    expect(reasons).toContain("large_balance_change");
    expect(reasons).toContain("liability_change");
    expect(reasons).toContain("trend_shift");
  });

  it("marks empty history as low confidence without inventing actual points", () => {
    const dataset = buildJourneyDataset(defaultDocument(), { amount: 90, unit: "days" }, "2026-07-20");

    expect(dataset.resolution).toBe("daily");
    expect(dataset.series.find((series) => series.state === "actual")?.points).toEqual([]);
    expect(dataset.series.find((series) => series.state === "projected")?.points).toHaveLength(90);
    expect(dataset.confidence).toMatchObject({ level: "low", actualPoints: 0 });
  });

  it("rejects invalid dates and unsupported horizons", () => {
    expect(() => buildJourneyDataset(defaultDocument(), { amount: 12, unit: "months" }, "2026-02-30")).toThrow();
    expect(() => journeyResolution({ amount: 4, unit: "years" })).toThrow();
  });
});
