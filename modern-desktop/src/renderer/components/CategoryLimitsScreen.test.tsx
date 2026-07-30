import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { defaultDocument } from "../../shared/finance";
import { CategoryLimitsScreen } from "./CategoryLimitsScreen";

describe("CategoryLimitsScreen", () => {
  it("inserts added categories alphabetically", async () => {
    const user = userEvent.setup();
    const document = defaultDocument();
    document.categories.Expense = ["Sparkasse", "Travel"];
    const onSave = vi.fn();

    render(<CategoryLimitsScreen document={document} onSave={onSave} />);
    await user.type(screen.getByPlaceholderText("New expense category"), "Sweets");
    await user.click(screen.getByRole("button", { name: "Add category" }));

    expect(onSave).toHaveBeenCalledWith(expect.objectContaining({
      categories: expect.objectContaining({ Expense: ["Sparkasse", "Sweets", "Travel"] })
    }));
  });
});
