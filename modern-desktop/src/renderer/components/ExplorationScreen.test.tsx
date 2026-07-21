import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { defaultDocument, formatCurrency } from "../../shared/finance";
import { ExplorationScreen } from "./ExplorationScreen";

describe("ExplorationScreen", () => {
  it("shows workspace context and all three workflow entry panels", () => {
    const document = defaultDocument();
    document.budget_settings.bank_account_balance = 1250;

    render(<ExplorationScreen document={document} />);

    expect(screen.getByRole("heading", { name: "Explore what comes next" })).toBeTruthy();
    expect(screen.getByText("Current net worth").parentElement?.textContent).toContain(formatCurrency(1250));
    expect(screen.getByRole("button", { name: "Open Future Simulator" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Open Net-Worth Journey" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Open Budget Balancer" })).toBeTruthy();
  });

  it("opens focused workflows and returns to landing", async () => {
    const user = userEvent.setup();
    render(<ExplorationScreen document={defaultDocument()} />);

    await user.click(screen.getByRole("button", { name: "Open Net-Worth Journey" }));
    expect(screen.getByRole("heading", { name: "Net-Worth Journey" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Open Budget Balancer" })).toBeNull();

    await user.click(screen.getByRole("button", { name: "Back to Exploration" }));
    expect(screen.getByRole("heading", { name: "Explore what comes next" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Open Budget Balancer" })).toBeTruthy();
  });

  it("preserves scenario and budget drafts across focused views", async () => {
    const user = userEvent.setup();
    const document = defaultDocument();
    const save = vi.fn();
    render(<ExplorationScreen document={document} onConfirm={save} />);

    await user.click(screen.getByRole("button", { name: "Open Future Simulator" }));
    await user.type(screen.getByLabelText("Scenario event amount"), "300");
    await user.type(screen.getByLabelText("Scenario event description"), "Trip");
    await user.click(screen.getByRole("button", { name: "Add temporary event" }));
    expect(document.expenses).toHaveLength(0);
    expect(document.budget_settings.category_budgets?.Expense?.Food).toBeUndefined();
    await user.click(screen.getByRole("button", { name: "Back to Exploration" }));
    await user.click(screen.getByRole("button", { name: "Open Budget Balancer" }));

    const budget = screen.getByLabelText("Draft budget percentage for Food");
    await user.clear(budget);
    await user.type(budget, "25");
    await user.click(screen.getByRole("button", { name: "Back to Exploration" }));
    expect(screen.getByText("Draft changes")).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Open Future Simulator" }));
    expect(screen.getByText("Trip · " + new Date().toISOString().slice(0, 10))).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Back to Exploration" }));
    await user.click(screen.getByRole("button", { name: "Open Budget Balancer" }));
    expect((screen.getByLabelText("Draft budget percentage for Food") as HTMLInputElement).value).toBe("25");
    expect(save).not.toHaveBeenCalled();
  });

  it("does not save drafts until explicit confirmation and can reset them", async () => {
    const user = userEvent.setup();
    const save = vi.fn();
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<ExplorationScreen document={defaultDocument()} onConfirm={save} />);

    await user.click(screen.getByRole("button", { name: "Open Future Simulator" }));
    await user.type(screen.getByLabelText("Scenario event amount"), "40");
    await user.type(screen.getByLabelText("Scenario event description"), "Cinema");
    await user.click(screen.getByRole("button", { name: "Add temporary event" }));
    expect(save).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Review and confirm" }));
    expect(save).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Confirm and save" }));
    expect(save).toHaveBeenCalledWith(expect.objectContaining({
      expenses: [expect.objectContaining({ description: "Cinema", amount: 40 })]
    }));

    await user.click(screen.getByRole("button", { name: "Reset drafts" }));
    expect(confirm).toHaveBeenCalledWith("Reset all temporary Exploration drafts?");
    expect(screen.getByRole("status").textContent).toContain("reset to saved baseline");
    confirm.mockRestore();
  });

  it("cancels drafts and returns to the saved baseline", async () => {
    const user = userEvent.setup();
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<ExplorationScreen document={defaultDocument()} />);

    await user.click(screen.getByRole("button", { name: "Open Future Simulator" }));
    await user.type(screen.getByLabelText("Scenario event amount"), "15");
    await user.type(screen.getByLabelText("Scenario event description"), "Cancelled");
    await user.click(screen.getByRole("button", { name: "Add temporary event" }));
    await user.click(screen.getByRole("button", { name: "Cancel drafts" }));

    expect(screen.getByRole("heading", { name: "Explore what comes next" })).toBeTruthy();
    expect(screen.queryByText("Cancelled")).toBeNull();
    confirm.mockRestore();
  });

  it("edits, removes, and undoes hypothetical events without changing the baseline", async () => {
    const user = userEvent.setup();
    const document = defaultDocument();
    render(<ExplorationScreen document={document} />);

    await user.click(screen.getByRole("button", { name: "Open Future Simulator" }));
    await user.type(screen.getByLabelText("Scenario event amount"), "50");
    await user.type(screen.getByLabelText("Scenario event description"), "Trip");
    await user.click(screen.getByRole("button", { name: "Add temporary event" }));

    await user.click(screen.getByRole("button", { name: "Edit temporary event Trip" }));
    await user.clear(screen.getByLabelText("Scenario event amount"));
    await user.type(screen.getByLabelText("Scenario event amount"), "75");
    await user.clear(screen.getByLabelText("Scenario event description"));
    await user.type(screen.getByLabelText("Scenario event description"), "Updated trip");
    await user.click(screen.getByRole("button", { name: "Save event changes" }));
    expect(screen.getByText("Updated trip · " + new Date().toISOString().slice(0, 10))).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Remove temporary event Updated trip" }));
    expect(screen.queryByText("Updated trip · " + new Date().toISOString().slice(0, 10))).toBeNull();
    expect(document.expenses).toHaveLength(0);

    await user.type(screen.getByLabelText("Scenario event amount"), "20");
    await user.type(screen.getByLabelText("Scenario event description"), "Undo me");
    await user.click(screen.getByRole("button", { name: "Add temporary event" }));
    await user.click(screen.getByRole("button", { name: "Undo last edit" }));
    expect(screen.queryByText("Undo me · " + new Date().toISOString().slice(0, 10))).toBeNull();
  });

  it("rejects zero, malformed, and past-dated hypothetical events", async () => {
    const user = userEvent.setup();
    render(<ExplorationScreen document={defaultDocument()} />);

    await user.click(screen.getByRole("button", { name: "Open Future Simulator" }));
    await user.type(screen.getByLabelText("Scenario event description"), "Invalid");
    await user.click(screen.getByRole("button", { name: "Add temporary event" }));
    expect(screen.getByRole("status").textContent).toContain("positive amount");
  });

  it("rejects past-dated hypothetical events", async () => {
    const user = userEvent.setup();
    render(<ExplorationScreen document={defaultDocument()} />);

    await user.click(screen.getByRole("button", { name: "Open Future Simulator" }));
    fireEvent.change(screen.getByLabelText("Scenario event amount"), { target: { value: "10" } });
    fireEvent.change(screen.getByLabelText("Scenario event description"), { target: { value: "Invalid" } });
    fireEvent.change(screen.getByLabelText("Scenario event date"), { target: { value: "2000-01-01" } });
    await user.click(screen.getByRole("button", { name: "Add temporary event" }));
    expect(screen.getByRole("status").textContent).toContain("today or a future date");
    expect(screen.queryByText(/Invalid ·/)).toBeNull();
  });
});
