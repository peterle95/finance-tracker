import { describe, expect, it } from "vitest";
import {
  assetAllocation,
  createSnapshot,
  defaultDocument,
  getActiveFixedCosts,
  getActiveMonthlyIncome,
  historicalBreakdown,
  historicalTotals,
  makeTransaction,
  mergeDocuments,
  monthTransactions,
  netWorthTrendProjection,
  negativeCarryover,
  normalizeDocument
} from "./finance";

describe("shared finance compatibility", () => {
  it("preserves unknown root and budget fields during a save merge", () => {
    const current = defaultDocument();
    current.desktop_only = { retain: true };
    current.budget_settings.legacy_widget = { enabled: true };
    const requested = structuredClone(current);
    requested.budget_settings.savings_balance = 4200;

    const merged = mergeDocuments(current, requested);

    expect(merged.desktop_only).toEqual({ retain: true });
    expect(merged.budget_settings.legacy_widget).toEqual({ enabled: true });
    expect(merged.budget_settings.savings_balance).toBe(4200);
  });

  it("books BNPL expenses next month while retaining their behavior date", () => {
    const transaction = makeTransaction("Expense", {
      date: "2026-06-16",
      amount: 25.5,
      category: "Shopping",
      description: "Klarna purchase"
    }, true);

    expect(transaction.date).toBe("2026-07-01");
    expect(transaction.behavior_date).toBe("2026-06-16");
  });

  it("filters reports by transaction date or spend-date metadata", () => {
    const document = defaultDocument();
    document.expenses.push({
      date: "2026-07-01",
      behavior_date: "2026-06-16",
      amount: 25.5,
      category: "Shopping",
      description: "Klarna purchase"
    });

    expect(monthTransactions(document, "Expense", "2026-06")).toHaveLength(0);
    expect(monthTransactions(document, "Expense", "2026-06", "behavior")).toHaveLength(1);
    expect(monthTransactions(document, "Expense", "2026-07", "behavior")).toHaveLength(0);
  });

  it("projects net worth from the average recent snapshot change", () => {
    const document = defaultDocument();
    document.budget_settings.asset_snapshots = [
      { date: "2026-01-01", net_worth: 1000, bank_balance: 1000, wallet_balance: 0, savings_balance: 0, investment_balance: 0, money_lent_balance: 0 },
      { date: "2026-02-01", net_worth: 1200, bank_balance: 1200, wallet_balance: 0, savings_balance: 0, investment_balance: 0, money_lent_balance: 0 },
      { date: "2026-03-01", net_worth: 900, bank_balance: 900, wallet_balance: 0, savings_balance: 0, investment_balance: 0, money_lent_balance: 0 }
    ];

    const result = netWorthTrendProjection(document, 2, 6, "2026-07");

    expect(result?.averageMonthlyChange).toBe(-50);
    expect(result?.intervals).toHaveLength(2);
    expect(result?.rows).toEqual([
      { month: "2026-07", change: -50, balance: 850 },
      { month: "2026-08", change: -50, balance: 800 }
    ]);
  });

  it("builds complete historical category and over-under series", () => {
    const document = defaultDocument();
    document.budget_settings.monthly_income = 1000;
    document.budget_settings.fixed_costs = [{ amount: 100, description: "Rent", start_date: "2026-01-01", end_date: null }];
    document.incomes.push({ date: "2026-06-05", amount: 50, category: "Bonus", description: "Bonus" });
    document.expenses.push(
      { date: "2026-06-10", amount: 10, category: "Food", description: "Lunch" },
      { date: "2026-07-01", behavior_date: "2026-06-16", amount: 25, category: "Shopping", description: "BNPL" }
    );

    expect(historicalBreakdown(document, "Expense", ["2026-06", "2026-07"], "categories", true, "behavior")).toEqual([
      { name: "Food", values: [10, 0] },
      { name: "Shopping", values: [25, 0] },
      { name: "Fixed Costs", values: [100, 100] }
    ]);
    expect(historicalBreakdown(document, "Expense", ["2026-06"], "over-under", false, "behavior")).toEqual([
      { name: "Total Income", values: [1050] },
      { name: "Total Expenses", values: [135] }
    ]);
    expect(historicalBreakdown(document, "Expense", ["2026-06"], "flexible", false, "behavior")).toEqual([
      { name: "Flexible Income", values: [50] },
      { name: "Flexible Costs", values: [35] }
    ]);
    expect(historicalTotals(document, "Expense", 1, "2026-06", "behavior", false)[0].value).toBe(35);
    expect(historicalTotals(document, "Expense", 1, "2026-06", "behavior", true)[0].value).toBe(135);
  });

  it("requires snapshot history and finite projection inputs", () => {
    const document = defaultDocument();

    expect(netWorthTrendProjection(document, 12, 6)).toBeNull();
    expect(netWorthTrendProjection(document, Number.NaN, 6)).toBeNull();
    expect(historicalTotals(document, "Expense", Number.NaN)).toEqual([]);
  });

  it("uses active date windows for income and fixed costs", () => {
    const document = defaultDocument();
    document.budget_settings.monthly_income = [
      { amount: 2500, description: "Salary", start_date: "2026-01-01", end_date: null },
      { amount: 300, description: "Old role", start_date: "2025-01-01", end_date: "2025-12-31" }
    ];
    document.budget_settings.fixed_costs = [
      { amount: 900, description: "Rent", start_date: "2026-01-01", end_date: null },
      { amount: 60, description: "Old plan", start_date: "2025-01-01", end_date: "2025-12-31" }
    ];

    expect(getActiveMonthlyIncome(document, "2026-06")).toBe(2500);
    expect(getActiveFixedCosts(document, "2026-06")).toHaveLength(1);
  });

  it("carries only a negative previous month into the next budget", () => {
    const document = defaultDocument();
    document.budget_settings.monthly_income = 100;
    document.budget_settings.fixed_costs = [];
    document.expenses.push({
      id: "overspend",
      date: "2026-05-02",
      amount: 125,
      category: "Food",
      description: "Groceries"
    });

    expect(negativeCarryover(document, "2026-06")).toBe(-25);
  });

  it("records snapshots from the current balance fields", () => {
    const document = defaultDocument();
    document.budget_settings.bank_account_balance = 1000;
    document.budget_settings.wallet_balance = 50;
    document.budget_settings.savings_balance = 5000;

    const snapshot = createSnapshot(document, "2026-06-30", "Month end");

    expect(snapshot.net_worth).toBe(6050);
    expect(snapshot.note).toBe("Month end");
  });

  it("rounds signed loan balances and excludes liabilities from asset allocation", () => {
    const document = defaultDocument();
    document.budget_settings.bank_account_balance = 2305.77;
    document.budget_settings.loans = [{
      id: "loan-1",
      borrower: "Friend",
      amount: -4347.039999999995,
      description: "Amount owed",
      date: "2026-07-10"
    }];
    document.budget_settings.money_lent_balance = -4347.039999999995;

    const normalized = normalizeDocument(document);
    const allocation = assetAllocation(normalized);

    expect(normalized.budget_settings.money_lent_balance).toBe(-4347.04);
    expect(allocation.assets).toEqual([{ name: "Bank", value: 2305.77 }]);
    expect(allocation.liabilities).toEqual([{ name: "Money owed", value: -4347.04 }]);
  });
});
