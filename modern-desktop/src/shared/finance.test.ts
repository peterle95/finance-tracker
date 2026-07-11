import { describe, expect, it } from "vitest";
import {
  assetAllocation,
  createSnapshot,
  defaultDocument,
  getActiveFixedCosts,
  getActiveMonthlyIncome,
  makeTransaction,
  mergeDocuments,
  monthTransactions,
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
