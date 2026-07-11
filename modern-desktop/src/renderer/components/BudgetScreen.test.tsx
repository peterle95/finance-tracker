import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { defaultDocument } from "../../shared/finance";
import { BudgetScreen } from "./BudgetScreen";

describe("BudgetScreen lending", () => {
  it("loads a clicked loan into the form and saves edits", async () => {
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
    render(<BudgetScreen document={document} onSave={save} onOpenCategoryLimits={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Edit loan for Alex" }));

    const form = screen.getByRole("button", { name: /Save changes/ }).closest("form")!;
    expect((within(form).getByPlaceholderText("Borrower") as HTMLInputElement).value).toBe("Alex");
    expect((within(form).getByPlaceholderText("Amount (negative if owed)") as HTMLInputElement).value).toBe("125");
    expect((within(form).getByPlaceholderText("Description") as HTMLInputElement).value).toBe("Concert tickets");

    const amount = within(form).getByPlaceholderText("Amount (negative if owed)");
    await user.clear(amount);
    await user.type(amount, "175");
    await user.click(screen.getByRole("button", { name: /Save changes/ }));

    expect(save).toHaveBeenCalledWith(expect.objectContaining({
      budget_settings: expect.objectContaining({
        money_lent_balance: 175,
        loans: [expect.objectContaining({ id: "loan-1", amount: 175 })]
      })
    }));
  });
});
