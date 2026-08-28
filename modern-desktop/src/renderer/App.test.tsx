import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { defaultDocument } from "../shared/finance";
import type { FinanceApi, FinanceDocument } from "../shared/types";
import { App } from "./App";

describe("App navigation", () => {
  afterEach(() => cleanup());

  function installBridge(document = defaultDocument()) {
    window.finance = {
      load: vi.fn().mockResolvedValue({ document, connection: { path: "finance_data.json", isConnected: true } }),
      chooseDataFile: vi.fn(),
      createDataFile: vi.fn(),
      saveDocument: vi.fn(),
      chooseBankCsv: vi.fn(),
      exportText: vi.fn()
    };
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: () => ({ matches: false, addListener: vi.fn(), removeListener: vi.fn() })
    });
    vi.spyOn(window.document, "hasFocus").mockReturnValue(true);
  }

  it("navigates across screens with hints, regions, scrolling, feedback, and exit", async () => {
    const user = userEvent.setup();
    installBridge();
    render(<App />);
    await screen.findByRole("heading", { name: "Your money, clearly" });
    const scrollBy = vi.fn();
    Object.defineProperty(HTMLElement.prototype, "scrollBy", { configurable: true, value: scrollBy });

    await user.keyboard(" ");
    expect(screen.getByRole("status").textContent).toContain("Keyboard mode · main");
    expect(document.querySelectorAll("[data-keyboard-hint]").length).toBeGreaterThan(0);
    await user.keyboard("?");
    expect(screen.getByLabelText("Keyboard navigation help")).toBeTruthy();
    await user.keyboard("h");
    expect(screen.getByRole("status").textContent).toContain("Keyboard mode · header");
    await user.keyboard("j");
    expect(scrollBy).toHaveBeenCalledWith({ top: 360, behavior: "smooth" });
  });

  it("keeps dialog editing and ordinary interactions native", async () => {
    const user = userEvent.setup();
    installBridge();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Transactions" }));
    const open = screen.getByRole("button", { name: "Expense" });
    await user.click(open);
    const dialog = await screen.findByRole("dialog");
    const description = within(dialog).getByLabelText("Description");
    await user.type(description, " lunch");
    expect((description as HTMLInputElement).value).toContain(" lunch");
    await user.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(document.activeElement).toBe(open);
  });

  it("falls back from invalid persisted keyboard settings and persists reset", async () => {
    const user = userEvent.setup();
    installBridge();
    localStorage.setItem("finance-tracker-keyboard-navigation", JSON.stringify({ activationKey: " ", hintAlphabet: "a", activationMode: "bad" }));
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Settings" }));
    expect((screen.getByLabelText("Activation key") as HTMLInputElement).value).toBe(" ");
    await user.click(screen.getByRole("button", { name: "Reset keyboard defaults" }));
    expect(JSON.parse(localStorage.getItem("finance-tracker-keyboard-navigation") ?? "{}")).toEqual({ activationKey: " ", hintAlphabet: "asdfjkl", activationMode: "select" });
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
    const saveDocument = vi.fn(async (_previous: FinanceDocument, next: FinanceDocument) => ({ document: next, connection: { path: "finance_data.json", isConnected: true } }));
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

    await waitFor(() => expect(saveDocument).toHaveBeenCalledWith(expect.anything(), expect.objectContaining({
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
    const saveDocument = vi.fn(async (_previous: FinanceDocument, next: FinanceDocument) => ({ document: next, connection: { path: "finance_data.json", isConnected: true } }));
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

    await waitFor(() => expect(saveDocument).toHaveBeenCalledWith(expect.anything(), expect.objectContaining({
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

  it("replaces an edited legacy transaction without an id", async () => {
    const user = userEvent.setup();
    const document = defaultDocument();
    document.categories.Expense = ["Travel", "Flights/Trains"];
    document.expenses = [{
      date: new Date().toISOString().slice(0, 10),
      amount: 447.26,
      category: "Travel",
      description: "BKK-BLN"
    }];
    const saveDocument = vi.fn(async (_previous: FinanceDocument, next: FinanceDocument) => ({ document: next, connection: { path: "finance_data.json", isConnected: true } }));
    window.finance = {
      load: vi.fn().mockResolvedValue({ document, connection: { path: "finance_data.json", isConnected: true } }),
      chooseDataFile: vi.fn(),
      createDataFile: vi.fn(),
      saveDocument,
      chooseBankCsv: vi.fn(),
      exportText: vi.fn()
    };
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: () => ({ matches: false, addListener: vi.fn(), removeListener: vi.fn() })
    });

    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Transactions" }));
    await user.click(screen.getByRole("button", { name: "Edit transaction" }));
    await user.selectOptions(screen.getByLabelText("Category"), "Flights/Trains");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() => expect(saveDocument).toHaveBeenCalledWith(expect.anything(), expect.objectContaining({
      expenses: [{
        date: document.expenses[0].date,
        amount: 447.26,
        category: "Flights/Trains",
        description: "BKK-BLN",
        behavior_date: undefined
      }]
    })));
  });

  it("shows category deletion errors and restores the category", async () => {
    const user = userEvent.setup();
    const document = defaultDocument();
    window.finance = {
      load: vi.fn().mockResolvedValue({ document, connection: { path: "data", isConnected: true } }),
      chooseDataFile: vi.fn(),
      createDataFile: vi.fn(),
      saveDocument: vi.fn().mockRejectedValue(new Error("Cannot delete category \"Food\" because it has transactions.")),
      chooseBankCsv: vi.fn(),
      exportText: vi.fn()
    };
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: () => ({ matches: false, addListener: vi.fn(), removeListener: vi.fn() })
    });

    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Category limits" }));
    await user.click(screen.getByRole("button", { name: "Remove Food" }));

    expect((await screen.findByRole("status")).textContent).toContain("Cannot delete category");
    expect(screen.getByText("Food")).toBeTruthy();
  });
});
