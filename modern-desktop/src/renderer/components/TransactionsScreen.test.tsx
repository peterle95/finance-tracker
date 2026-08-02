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

  it("clears the default month filter", async () => {
    const user = userEvent.setup();
    const document = defaultDocument();
    const month = currentMonth();
    document.expenses = [
      { date: month + "-06", amount: 35, category: "Food", description: "This month" },
      { date: "2020-01-06", amount: 20, category: "Food", description: "Older transaction" }
    ];

    render(<TransactionsScreen document={document} onAdd={vi.fn()} onEdit={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.queryByText("Older transaction")).toBeNull();

    await user.click(screen.getByRole("button", { name: "Clear filters" }));

    expect(screen.getByText("Older transaction")).toBeTruthy();
    expect((screen.getByLabelText("Filter from booking month") as HTMLInputElement).value).toBe("");
    expect((screen.getByLabelText("Filter to booking month") as HTMLInputElement).value).toBe("");
  });

  it("filters transactions by an inclusive month range", async () => {
    const user = userEvent.setup();
    const document = defaultDocument();
    document.expenses = [
      { date: "2020-01-06", amount: 20, category: "Food", description: "Before range" },
      { date: "2020-02-06", amount: 30, category: "Food", description: "Start month" },
      { date: "2020-03-06", amount: 40, category: "Food", description: "End month" },
      { date: "2020-04-06", amount: 50, category: "Food", description: "After range" }
    ];

    render(<TransactionsScreen document={document} onAdd={vi.fn()} onEdit={vi.fn()} onDelete={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: "Clear filters" }));
    await user.type(screen.getByLabelText("Filter from booking month"), "2020-02");
    await user.type(screen.getByLabelText("Filter to booking month"), "2020-03");

    expect(screen.queryByText("Before range")).toBeNull();
    expect(screen.getByText("Start month")).toBeTruthy();
    expect(screen.getByText("End month")).toBeTruthy();
    expect(screen.queryByText("After range")).toBeNull();
  });
});
