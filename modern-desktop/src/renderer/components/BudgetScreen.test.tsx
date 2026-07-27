import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { currentMonth, defaultDocument, monthOffset } from "../../shared/finance";
import { BudgetScreen } from "./BudgetScreen";

describe("BudgetScreen lending", () => {
  it("navigates between budget months", async () => {
    const user = userEvent.setup();
    render(<BudgetScreen document={defaultDocument()} onSave={vi.fn()} />);

    const month = screen.getByLabelText("Budget month") as HTMLInputElement;
    expect(month.value).toBe(currentMonth());
    const carryoverMonths = screen.getByLabelText("Carryover months") as HTMLInputElement;
    expect(carryoverMonths.value).toBe("3");
    fireEvent.change(carryoverMonths, { target: { value: "5" } });
    expect(carryoverMonths.value).toBe("5");
    await user.click(screen.getByRole("button", { name: "Previous month" }));
    expect(month.value).toBe(monthOffset(currentMonth(), -1));
    await user.click(screen.getByRole("button", { name: "Next month" }));
    expect(month.value).toBe(currentMonth());
  });

  it("opens a loan modifier and confirms amount changes", async () => {
    const user = userEvent.setup();
    const save = vi.fn();
    const document = defaultDocument();
    document.budget_settings.loans = [{
      id: "loan-1",
      borrower: "Alex",
      amount: 125,
      description: "Concert tickets",
      date: "2026-06-10"
    }];
    document.budget_settings.money_lent_balance = 125;
    render(<BudgetScreen document={document} onSave={save} />);

    await user.click(screen.getByRole("button", { name: "Modify loan for Alex" }));

    const dialog = screen.getByRole("dialog");
    expect((within(dialog).getByLabelText("Borrower") as HTMLInputElement).value).toBe("Alex");
    expect((within(dialog).getByLabelText("Amount") as HTMLInputElement).value).toBe("125");
    expect((within(dialog).getByLabelText("Description") as HTMLInputElement).value).toBe("Concert tickets");

    const amount = within(dialog).getByLabelText("Amount");
    await user.clear(amount);
    await user.type(amount, "175");
    await user.type(within(dialog).getByLabelText("Notes"), "Repay after payday");
    await user.click(within(dialog).getByRole("button", { name: "Done" }));

    expect(screen.getByText(/Difference: \+50,00/)).toBeTruthy();
    expect(save).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Confirm and save" }));

    expect(save).toHaveBeenCalledWith(expect.objectContaining({
      budget_settings: expect.objectContaining({
        money_lent_balance: 175,
        loans: [expect.objectContaining({ id: "loan-1", amount: 175, notes: "Repay after payday" })]
      })
    }));
  });

  it("opens and closes fixed income and fixed cost views from balances", async () => {
    const user = userEvent.setup();
    render(<BudgetScreen document={defaultDocument()} onSave={vi.fn()} />);

    expect(screen.queryByRole("heading", { name: "Income sources" })).toBeNull();
    await user.click(screen.getByRole("button", { name: "Fixed income" }));
    expect(screen.getByRole("heading", { name: "Income sources" })).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Close fixed income" }));
    expect(screen.queryByRole("heading", { name: "Income sources" })).toBeNull();

    await user.click(screen.getByRole("button", { name: "Fixed costs" }));
    expect(screen.getByRole("heading", { name: "Recurring costs" })).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Close fixed costs" }));
    expect(screen.queryByRole("heading", { name: "Recurring costs" })).toBeNull();
  });
});
