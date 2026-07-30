import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { defaultDocument } from "../shared/finance";
import type { FinanceApi, FinanceDocument } from "../shared/types";
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

  it("routes reviewed budget changes through shared save flow", async () => {
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
    await user.click(screen.getByRole("button", { name: "Open Budget Balancer" }));
    await user.clear(screen.getByLabelText("Draft budget percentage for Food"));
    await user.type(screen.getByLabelText("Draft budget percentage for Food"), "20");
    await user.click(screen.getByRole("button", { name: "Review and confirm" }));
    expect((screen.getByRole("button", { name: "Confirm and save" }) as HTMLButtonElement).disabled).toBe(true);
    await user.click(screen.getByLabelText("I reviewed each changed category before saving."));
    await user.click(screen.getByRole("button", { name: "Confirm and save" }));

    await waitFor(() => expect(saveDocument).toHaveBeenCalledWith(expect.objectContaining({
      budget_settings: expect.objectContaining({ category_budgets: expect.objectContaining({ Expense: expect.objectContaining({ Food: 20 }) }) })
    })));
  });

  it("persists reduced-motion preference and applies it to the document", async () => {
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
    localStorage.removeItem("finance-tracker-reduced-motion");

    render(<App />);
    await waitFor(() => expect(screen.getByRole("heading", { name: "Your money, clearly" })).toBeTruthy());
    await user.click(screen.getByRole("button", { name: "Settings" }));
    const preference = screen.getByRole("checkbox", { name: "Reduce nonessential motion" }) as HTMLInputElement;
    expect(preference.checked).toBe(false);
    await user.click(preference);

    expect(preference.checked).toBe(true);
    expect(localStorage.getItem("finance-tracker-reduced-motion")).toBe("true");
    expect(window.document.documentElement.dataset.reducedMotion).toBe("true");
  });

  it("saves default ranges and applies them to feature screens", async () => {
    const user = userEvent.setup();
    const document = defaultDocument();
    const saveDocument = vi.fn(async (next: FinanceDocument) => ({ document: next, connection: { path: "finance_data.json", isConnected: true } }));
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
    await user.click(screen.getByRole("button", { name: "Settings" }));
    await user.click(screen.getByRole("button", { name: "Change default ranges" }));
    await user.clear(screen.getByLabelText("Projection months"));
    await user.type(screen.getByLabelText("Projection months"), "18");
    await user.clear(screen.getByLabelText("Budget carryover months"));
    await user.type(screen.getByLabelText("Budget carryover months"), "7");
    await user.click(screen.getByRole("button", { name: "Save ranges" }));

    await waitFor(() => expect(saveDocument).toHaveBeenCalledWith(expect.objectContaining({
      budget_settings: expect.objectContaining({
        default_ranges: expect.objectContaining({ projectionMonths: 18, carryoverMonths: 7 })
      })
    })));
    await user.click(screen.getByRole("button", { name: "Budget" }));
    expect((screen.getByLabelText("Carryover months") as HTMLInputElement).value).toBe("7");
    await user.click(screen.getByRole("button", { name: "Projection" }));
    expect((screen.getByRole("slider") as HTMLInputElement).value).toBe("18");
  });

  it("saves default behaviors and applies them to feature screens", async () => {
    const user = userEvent.setup();
    const document = defaultDocument();
    const saveDocument = vi.fn(async (next: FinanceDocument) => ({ document: next, connection: { path: "finance_data.json", isConnected: true } }));
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
    await user.click(screen.getByRole("button", { name: "Settings" }));
    await user.click(screen.getByRole("button", { name: "Change default behaviors" }));
    await user.click(screen.getByLabelText("Include negative carryover by default in Budget"));
    await user.selectOptions(screen.getByLabelText("Default projection mode"), "net-worth");
    await user.selectOptions(screen.getByLabelText("Report date basis"), "behavior");
    await user.selectOptions(screen.getByLabelText("Default report view"), "history");
    await user.click(screen.getByRole("button", { name: "Save behaviors" }));

    await waitFor(() => expect(saveDocument).toHaveBeenCalledWith(expect.objectContaining({
      budget_settings: expect.objectContaining({
        default_behaviors: expect.objectContaining({
          includeNegativeCarryover: false,
          projectionMode: "net-worth",
          reportDateBasis: "behavior",
          reportView: "history"
        })
      })
    })));
    await user.click(screen.getByRole("button", { name: "Budget" }));
    expect((screen.getByLabelText("Include previous deficits") as HTMLInputElement).checked).toBe(false);
    await user.click(screen.getByRole("button", { name: "Projection" }));
    expect(screen.getByRole("button", { name: "Net worth trend" }).className).toContain("selected");
    await user.click(screen.getByRole("button", { name: "Reports" }));
    expect(screen.getByRole("button", { name: "History" }).className).toContain("selected");
    expect((screen.getByLabelText("Report date basis") as HTMLSelectElement).value).toBe("behavior");
  });
});
