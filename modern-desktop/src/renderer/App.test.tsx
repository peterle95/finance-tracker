import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { defaultDocument } from "../shared/finance";
import type { FinanceApi } from "../shared/types";
import { App } from "./App";

describe("App Exploration navigation", () => {
  afterEach(() => cleanup());

  it("prompts before leaving dirty Exploration", async () => {
    const user = userEvent.setup();
    const document = defaultDocument();
    const bridge: FinanceApi = {
      load: vi.fn().mockResolvedValue({ document, connection: { path: "finance_data.json", isConnected: true } }),
      chooseDataFile: vi.fn(),
      createDataFile: vi.fn(),
      saveDocument: vi.fn(),
      chooseBankCsv: vi.fn(),
      exportText: vi.fn()
    };
    window.finance = bridge;
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: () => ({ matches: false, addListener: vi.fn(), removeListener: vi.fn() })
    });
    const leave = vi.spyOn(window, "confirm").mockReturnValue(false);

    render(<App />);
    await waitFor(() => expect(screen.getByRole("heading", { name: "Your money, clearly" })).toBeTruthy());
    await user.click(screen.getByRole("button", { name: "Exploration" }));
    await user.click(screen.getByRole("button", { name: "Open Future Simulator" }));
    await user.type(screen.getByLabelText("Scenario event amount"), "20");
    await user.type(screen.getByLabelText("Scenario event description"), "Test event");
    await user.click(screen.getByRole("button", { name: "Add temporary event" }));
    await user.click(screen.getByRole("button", { name: "Dashboard" }));

    expect(leave).toHaveBeenCalledWith("Exploration has unsaved drafts. Leave without saving?");
    expect(screen.getByRole("heading", { name: "Future Simulator" })).toBeTruthy();
    leave.mockReturnValue(true);
    await user.click(screen.getByRole("button", { name: "Dashboard" }));
    await waitFor(() => expect(screen.getByRole("heading", { name: "Your money, clearly" })).toBeTruthy());
    leave.mockClear();
    await user.click(screen.getByRole("button", { name: "Exploration" }));
    await user.click(screen.getByRole("button", { name: "Dashboard" }));
    expect(leave).not.toHaveBeenCalled();
    leave.mockRestore();
  });

  it("routes confirmed scenario changes through shared save flow", async () => {
    const user = userEvent.setup();
    const document = defaultDocument();
    const saveDocument = vi.fn().mockResolvedValue({ document, connection: { path: "finance_data.json", isConnected: true } });
    const bridge: FinanceApi = {
      load: vi.fn().mockResolvedValue({ document, connection: { path: "finance_data.json", isConnected: true } }),
      chooseDataFile: vi.fn(),
      createDataFile: vi.fn(),
      saveDocument,
      chooseBankCsv: vi.fn(),
      exportText: vi.fn()
    };
    window.finance = bridge;
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: () => ({ matches: false, addListener: vi.fn(), removeListener: vi.fn() })
    });

    render(<App />);
    await waitFor(() => expect(screen.getByRole("heading", { name: "Your money, clearly" })).toBeTruthy());
    await user.click(screen.getByRole("button", { name: "Exploration" }));
    await user.click(screen.getByRole("button", { name: "Open Future Simulator" }));
    await user.type(screen.getByLabelText("Scenario event amount"), "20");
    await user.type(screen.getByLabelText("Scenario event description"), "Confirmed event");
    await user.click(screen.getByRole("button", { name: "Add temporary event" }));
    await user.click(screen.getByRole("button", { name: "Review and confirm" }));
    await user.click(screen.getByRole("button", { name: "Confirm and save" }));

    await waitFor(() => expect(saveDocument).toHaveBeenCalledWith(expect.objectContaining({
      expenses: [expect.objectContaining({ description: "Confirmed event", amount: 20 })]
    })));
  });
});
