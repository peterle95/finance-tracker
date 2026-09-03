import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { defaultDocument } from "../../shared/finance";
import { NetWorthScreen } from "./NetWorthScreen";

describe("NetWorthScreen snapshot changes", () => {
  it("defaults to month-by-month changes and supports changes from the beginning", async () => {
    const user = userEvent.setup();
    const financeDocument = defaultDocument();
    financeDocument.budget_settings.asset_snapshots = [
      { date: "2026-05-01", net_worth: 1000, bank_balance: 1000, wallet_balance: 0, savings_balance: 0, investment_balance: 0, money_lent_balance: 0 },
      { date: "2026-06-01", net_worth: 1200, bank_balance: 1200, wallet_balance: 0, savings_balance: 0, investment_balance: 0, money_lent_balance: 0 }
    ];

    render(<NetWorthScreen document={financeDocument} onSave={vi.fn()} onExport={vi.fn()} />);

    expect(screen.queryByRole("heading", { name: "Changes over time" })).toBeNull();
    expect(screen.getByText("Record and review snapshots")).toBeTruthy();
    expect(screen.queryByPlaceholderText("Month end or milestone")).toBeNull();
    expect(document.querySelector(".snapshot-history-list")).toBeTruthy();

    const monthByMonth = screen.getByRole("button", { name: "Month-by-month" });
    const fromBeginning = screen.getByRole("button", { name: "Since beginning" });
    expect(monthByMonth.getAttribute("aria-pressed")).toBe("true");
    expect(fromBeginning.getAttribute("aria-pressed")).toBe("false");
    expect(screen.getByText(/Since previous: \+200,00/)).toBeTruthy();

    await user.click(fromBeginning);

    expect(monthByMonth.getAttribute("aria-pressed")).toBe("false");
    expect(fromBeginning.getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByText(/Since beginning: \+200,00/)).toBeTruthy();

    const sinceMonth = screen.getByRole("button", { name: "Since: 2026-05" });
    await user.click(sinceMonth);
    expect(sinceMonth.getAttribute("aria-pressed")).toBe("true");
  });
});
