import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { defaultDocument } from "../../shared/finance";
import { ProjectionScreen } from "./ProjectionScreen";
import { ReportsScreen } from "./ReportsScreen";

describe("ReportsScreen history", () => {
  it("offers Python-compatible history breakdown controls", async () => {
    const user = userEvent.setup();
    const document = defaultDocument();
    document.categories.Expense.push("__proto__");
    document.expenses.push({ date: "2026-07-01", amount: 10, category: "__proto__", description: "Prototype-safe category" });
    render(<ReportsScreen document={document} onExport={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "History" }));
    const breakdown = screen.getByLabelText("History breakdown") as HTMLSelectElement;
    expect(breakdown.value).toBe("total");
    expect(screen.getByText("Include fixed costs")).toBeTruthy();

    await user.selectOptions(breakdown, "categories");
    expect((screen.getByLabelText("History display") as HTMLSelectElement).value).toBe("value");

    await user.selectOptions(breakdown, "flexible");
    await user.selectOptions(screen.getByLabelText("History display"), "percentage");
    expect(screen.getByRole("heading", { name: "Flexible income vs costs" })).toBeTruthy();
  });
});

describe("ProjectionScreen", () => {
  it("renders and exports net worth trend mode", async () => {
    const user = userEvent.setup();
    const exportReport = vi.fn();
    const document = defaultDocument();
    document.budget_settings.asset_snapshots = [
      { date: "2026-05-01", net_worth: 1000, bank_balance: 1000, wallet_balance: 0, savings_balance: 0, investment_balance: 0, money_lent_balance: 0 },
      { date: "2026-06-01", net_worth: 1100, bank_balance: 1100, wallet_balance: 0, savings_balance: 0, investment_balance: 0, money_lent_balance: 0 }
    ];
    render(<ProjectionScreen document={document} onExport={exportReport} />);

    await user.click(screen.getByRole("button", { name: "Net worth trend" }));
    expect(screen.getByRole("heading", { name: "Continue your recorded trajectory" })).toBeTruthy();
    expect(screen.getByText("2026-05-01 → 2026-06-01")).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Export projection" }));
    expect(exportReport).toHaveBeenCalledWith(expect.stringMatching(/^financial_projection_/), expect.stringContaining("NET WORTH TREND PROJECTION"));
  });
});
