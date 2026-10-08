import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { defaultDocument } from "../shared/finance";
import type { ConflictPreview, FinanceApi, FinanceDocument } from "../shared/types";
import { App } from "./App";

describe("App navigation", () => {
  afterEach(() => cleanup());

  function installBridge(document = defaultDocument()) {
    window.finance = {
      load: vi.fn().mockResolvedValue({ document, connection: { path: "finance_data.json", isConnected: true } }),
      chooseDataFile: vi.fn(),
      createDataFile: vi.fn(),
      saveDocument: vi.fn(),
      readConflict: vi.fn(),
      resolveConflict: vi.fn(),
      chooseBankCsv: vi.fn(),
      exportText: vi.fn()
    };
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: () => ({ matches: false, addListener: vi.fn(), removeListener: vi.fn() })
    });
    vi.spyOn(window.document, "hasFocus").mockReturnValue(true);
  }

  function installConflicts() {
    const document = defaultDocument();
    installBridge(document);
    const fileName = "loans.sync-conflict-20261007-181259-IHHEE5V.json";
    const otherName = "preferences.sync-conflict-20261008-181259-OTHER.json";
    const current = { id: "loan-1", borrower: "Alex", amount: 40, date: "2026-10-01", description: "Tickets" };
    const updated = { ...current, amount: 55 };
    const added = { ...current, id: "loan-2", borrower: "Sam", amount: 10 };
    const preview: ConflictPreview = {
      directory: "/finance", fileName, originalFileName: "loans.json", canMerge: true,
      currentText: JSON.stringify([current]), conflictText: JSON.stringify([updated, added]),
      differences: [
        { key: "loan-1", label: "Alex (loan-1)", currentText: JSON.stringify(current), conflictText: JSON.stringify(updated) },
        { key: "loan-2", label: "Sam (loan-2)", currentText: "Not present", conflictText: JSON.stringify(added) }
      ]
    };
    const conflicts = [{ fileName, originalFileName: "loans.json" }, { fileName: otherName, originalFileName: "preferences.json" }];
    vi.mocked(window.finance.load).mockResolvedValue({ document, connection: { path: "/finance", isConnected: true }, conflicts,
      warnings: conflicts.map((conflict) => `Ignored conflict file: ${conflict.fileName}`) });
    vi.mocked(window.finance.readConflict).mockResolvedValue(preview);
    vi.mocked(window.finance.resolveConflict).mockResolvedValue({ document: { ...document, budget_settings: { ...document.budget_settings, loans: [updated, added] } },
      connection: { path: "/finance", isConnected: true }, conflicts: [conflicts[1]] });
    return { preview, conflicts };
  }

  it("shows one hint set for header and page actions", async () => {
    const user = userEvent.setup();
    installBridge();
    render(<App />);
    await screen.findByRole("heading", { name: "Your money, clearly" });

    await user.keyboard(" ");
    expect(screen.getByRole("status").textContent).toContain("Keyboard mode");
    expect(screen.getByRole("button", { name: "Toggle theme" }).getAttribute("data-keyboard-hint")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Add expense" }).getAttribute("data-keyboard-hint")).toBeTruthy();
    await user.keyboard("?");
    expect(screen.getByLabelText("Keyboard navigation help")).toBeTruthy();
    expect(screen.getByLabelText("Keyboard navigation help").textContent).toContain("Type a hint to activate it.");
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
    localStorage.setItem("finance-tracker-keyboard-navigation", JSON.stringify({ activationKey: " ", hintAlphabet: "a" }));
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Settings" }));
    expect((screen.getByLabelText("Activation key") as HTMLInputElement).value).toBe(" ");
    await user.click(screen.getByRole("button", { name: "Reset keyboard defaults" }));
    expect(JSON.parse(localStorage.getItem("finance-tracker-keyboard-navigation") ?? "{}")).toEqual({ activationKey: " ", hintAlphabet: "asdfjkl" });
  });

  it("persists reduced-motion preference and applies it to the document", async () => {
    const user = userEvent.setup();
    const document = defaultDocument();
    const bridge: FinanceApi = {
      load: vi.fn().mockResolvedValue({ document, connection: { path: "finance_data.json", isConnected: true } }),
      chooseDataFile: vi.fn(),
      createDataFile: vi.fn(),
      saveDocument: vi.fn(),
      readConflict: vi.fn(),
      resolveConflict: vi.fn(),
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
      readConflict: vi.fn(),
      resolveConflict: vi.fn(),
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
      readConflict: vi.fn(),
      resolveConflict: vi.fn(),
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
      readConflict: vi.fn(),
      resolveConflict: vi.fn(),
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
      readConflict: vi.fn(),
      resolveConflict: vi.fn(),
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

  it("opens the conflict notice, reviews differences, and requires confirmation before cleanup", async () => {
    const user = userEvent.setup();
    const { preview } = installConflicts();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Resolve sync conflicts" }));
    const dialog = await screen.findByRole("dialog", { name: "Resolve sync conflict" });
    await within(dialog).findByText("/finance/loans.json");
    expect(within(dialog).getByText(`/finance/${preview.fileName}`)).toBeTruthy();
    expect(within(dialog).queryByRole("columnheader", { name: "Keep" })).toBeNull();
    await user.click(within(dialog).getByRole("button", { name: "Use conflict copy" }));
    expect(window.finance.resolveConflict).not.toHaveBeenCalled();
    expect(within(dialog).getByLabelText("Confirm conflict resolution").textContent).toContain(preview.fileName);
    await user.click(within(dialog).getByRole("button", { name: "Back to review" }));
    expect(window.finance.resolveConflict).not.toHaveBeenCalled();
    await user.click(within(dialog).getByRole("button", { name: "Use conflict copy" }));
    await user.click(within(dialog).getByRole("button", { name: "Confirm resolution" }));

    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(window.finance.resolveConflict).toHaveBeenCalledWith(preview, { source: "conflict" });
    expect(screen.getByRole("status").textContent).toContain("Sync conflict resolved.");
    expect(screen.getByRole("button", { name: "Resolve sync conflicts" }).textContent).toContain("preferences.sync-conflict");
  });

  it("keeps failed resolutions open for refresh and cancels without resolving", async () => {
    const user = userEvent.setup();
    installConflicts();
    vi.mocked(window.finance.resolveConflict).mockRejectedValue(new Error("A conflict version changed. Refresh the preview."));
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Resolve sync conflicts" }));
    await user.click(await screen.findByRole("button", { name: "Keep current file" }));
    await user.click(screen.getByRole("button", { name: "Confirm resolution" }));
    expect((await screen.findByRole("alert")).textContent).toContain("changed");
    expect(screen.getByRole("dialog")).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Refresh preview" }));
    await within(screen.getByRole("dialog")).findByText("Alex (loan-1)");
    expect(window.finance.readConflict).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole("alert")).toBeNull();
    await user.click(screen.getByRole("button", { name: "Use conflict copy" }));
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(window.finance.resolveConflict).toHaveBeenCalledTimes(1);
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Resolve sync conflicts" }));
  });

  it("resolves record IDs that also name object prototype properties as whole files", async () => {
    const user = userEvent.setup();
    const { preview } = installConflicts();
    const loan = { id: "constructor", borrower: "Alex", amount: 10, date: "2026-10-01" };
    vi.mocked(window.finance.readConflict).mockResolvedValue({ ...preview,
      currentText: JSON.stringify([loan]), conflictText: JSON.stringify([{ ...loan, amount: 20 }]),
      differences: [{ key: "constructor", label: "Alex (constructor)", currentText: JSON.stringify(loan), conflictText: JSON.stringify({ ...loan, amount: 20 }) }]
    });
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Resolve sync conflicts" }));
    await screen.findByText("Alex (constructor)");
    await user.click(screen.getByRole("button", { name: "Use conflict copy" }));
    await user.click(screen.getByRole("button", { name: "Confirm resolution" }));
    expect(window.finance.resolveConflict).toHaveBeenCalledWith(expect.objectContaining({ originalFileName: "loans.json" }), { source: "conflict" });
  });

  it("preserves the clickable conflict notice after saving unrelated settings", async () => {
    const user = userEvent.setup();
    const { conflicts } = installConflicts();
    vi.mocked(window.finance.saveDocument).mockImplementation(async (_previous, document) => ({ document,
      connection: { path: "/finance", isConnected: true }, conflicts }));
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Settings" }));
    await user.click(screen.getByRole("button", { name: "Change default ranges" }));
    await user.clear(screen.getByLabelText("Projection months"));
    await user.type(screen.getByLabelText("Projection months"), "18");
    await user.click(screen.getByRole("button", { name: "Save ranges" }));
    await waitFor(() => expect(screen.getByRole("status").textContent).toContain("Saved to the shared"));
    await user.click(screen.getByRole("button", { name: "Resolve sync conflicts" }));
    await screen.findByRole("dialog", { name: "Resolve sync conflict" });
    expect(window.finance.readConflict).toHaveBeenCalledWith(conflicts[0].fileName);
  });

  it("makes the resolver accessible even when a conflicted current file prevents loading", async () => {
    const user = userEvent.setup();
    const { preview, conflicts } = installConflicts();
    vi.mocked(window.finance.load).mockResolvedValue({ document: null, connection: { path: "/finance", isConnected: false, message: "loans.json is missing." }, conflicts });
    vi.mocked(window.finance.readConflict).mockResolvedValue({ ...preview, currentText: null, currentError: "The current file is missing.", canMerge: false });
    render(<App />);
    await screen.findByRole("heading", { name: "Connect your shared finance directory" });
    await user.click(screen.getByRole("button", { name: "Resolve sync conflicts" }));
    const current = await screen.findByRole("button", { name: "Keep current file" }) as HTMLButtonElement;
    expect(current.disabled).toBe(true);
    await user.click(screen.getByRole("button", { name: "Use conflict copy" }));
    await user.click(screen.getByRole("button", { name: "Confirm resolution" }));
    await screen.findByRole("heading", { name: "Your money, clearly" });
  });
});
