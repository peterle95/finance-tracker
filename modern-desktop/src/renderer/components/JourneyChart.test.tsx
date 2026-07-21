import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { currentMonth, defaultDocument, monthOffset } from "../../shared/finance";
import { JourneyChart } from "./JourneyChart";

describe("JourneyChart", () => {
  it("switches horizons, scrubs the timeline, and exposes drivers and markers", async () => {
    const user = userEvent.setup();
    const document = defaultDocument();
    const month = currentMonth();
    document.budget_settings.asset_snapshots = [
      { date: monthOffset(month, -1) + "-01", net_worth: 1000, bank_balance: 1000, wallet_balance: 0, savings_balance: 0, investment_balance: 0, money_lent_balance: 0 },
      { date: month + "-01", net_worth: 1250, bank_balance: 1300, wallet_balance: 0, savings_balance: 0, investment_balance: 0, money_lent_balance: -50, note: "Debt added" }
    ];

    render(<JourneyChart document={document} />);

    const horizon = screen.getByLabelText("Journey horizon") as HTMLSelectElement;
    expect(horizon.value).toBe("12-months");
    expect(screen.getByText(/monthly ·/i)).toBeTruthy();
    expect(screen.getByText(/Source: snapshot/)).toBeTruthy();
    expect(screen.getByText("Cash")).toBeTruthy();

    const markers = screen.getAllByRole("button", { name: /Turning point/ });
    expect(markers.length).toBeGreaterThan(0);
    await user.click(markers[0]);
    expect(screen.getByRole("status").textContent).toContain("Selected");

    await user.selectOptions(horizon, "90-days");
    expect(horizon.value).toBe("90-days");
    expect(screen.getByText(/daily ·/i)).toBeTruthy();
    const scrubber = screen.getByRole("slider", { name: "Journey timeline scrubber" });
    await user.click(scrubber);
    const beforeKeyboardMove = screen.getByRole("status").textContent;
    fireEvent.keyDown(scrubber, { key: "End" });
    expect(screen.getByRole("status").textContent).not.toBe(beforeKeyboardMove);

    await user.selectOptions(horizon, "20-years");
    expect(horizon.value).toBe("20-years");
    expect(screen.getByText(/yearly ·/i)).toBeTruthy();
  });
});
