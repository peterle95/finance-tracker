import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { defaultDocument } from "../../shared/finance";
import { TransactionEditor } from "./TransactionEditor";

describe("TransactionEditor", () => {
  it("submits a new expense through the typed form", async () => {
    const user = userEvent.setup();
    const submit = vi.fn();
    render(
      <TransactionEditor
        open
        document={defaultDocument()}
        type="Expense"
        onOpenChange={vi.fn()}
        onSubmit={submit}
      />
    );

    await user.type(screen.getByLabelText("Amount"), "27.5");
    await user.type(screen.getByLabelText("Description"), "Lunch with a friend");
    await user.click(screen.getByRole("button", { name: "Add transaction" }));

    expect(submit).toHaveBeenCalledWith("Expense", expect.objectContaining({
      amount: 27.5,
      category: "Food",
      description: "Lunch with a friend"
    }));
  });
});
