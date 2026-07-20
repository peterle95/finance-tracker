import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { defaultDocument } from "../../shared/finance";
import { ExplorationScreen } from "./ExplorationScreen";

describe("ExplorationScreen", () => {
  it("shows workspace context and all three workflow entry panels", () => {
    const document = defaultDocument();
    document.budget_settings.bank_account_balance = 1250;

    render(<ExplorationScreen document={document} />);

    expect(screen.getByRole("heading", { name: "Explore what comes next" })).toBeTruthy();
    expect(screen.getByText("€1,250.00")).toBeTruthy();
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
});
