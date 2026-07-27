import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { currentMonth, defaultDocument } from "../../shared/finance";
import { TransactionsScreen } from "./TransactionsScreen";

describe("TransactionsScreen summary", () => {
  it("shows total income minus total costs", () => {
    const document = defaultDocument();
    const month = currentMonth();
    document.budget_settings.monthly_income = 500;
    document.budget_settings.fixed_costs = [{ amount: 50, description: "Rent", start_date: month + "-01", end_date: null }];
    document.incomes = [{ date: month + "-05", amount: 100, category: "Bonus", description: "Bonus" }];
    document.expenses = [{ date: month + "-06", amount: 35, category: "Food", description: "Lunch" }];

    render(<TransactionsScreen document={document} onAdd={vi.fn()} onEdit={vi.fn()} onDelete={vi.fn()} />);

    expect(screen.getAllByText(/Total income/).length).toBeGreaterThan(0);
    expect(screen.getByText(/515,00/)).toBeTruthy();
  });

  it("filters transactions by category", async () => {
    const user = userEvent.setup();
    const document = defaultDocument();
    const month = currentMonth();
    document.expenses = [
      { date: month + "-06", amount: 35, category: "Food", description: "Lunch" },
      { date: month + "-07", amount: 20, category: "Transportation", description: "Bus" }
    ];

    render(<TransactionsScreen document={document} onAdd={vi.fn()} onEdit={vi.fn()} onDelete={vi.fn()} />);

    await user.selectOptions(screen.getByLabelText("Filter by category"), "Food");

    expect(screen.getByText("Lunch")).toBeTruthy();
    expect(screen.queryByText("Bus")).toBeNull();
  });
});
