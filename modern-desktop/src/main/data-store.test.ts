// @vitest-environment node

import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cloneDocument } from "../shared/finance";
import * as fileUtils from "./file-utils";

vi.mock("electron", () => ({ dialog: {} }));

import { DataStore } from "./data-store";

async function json(path: string): Promise<any> {
  return JSON.parse(await readFile(path, "utf8"));
}

describe.sequential("DataStore", () => {
  let directory: string;
  let previousDataDirectory: string | undefined;

  beforeEach(async () => {
    directory = await mkdtemp(join(tmpdir(), "finance-store-"));
    previousDataDirectory = process.env.FINANCE_DATA_DIR;
    process.env.FINANCE_DATA_DIR = directory;
  });

  afterEach(async () => {
    vi.restoreAllMocks();
    if (previousDataDirectory === undefined) delete process.env.FINANCE_DATA_DIR;
    else process.env.FINANCE_DATA_DIR = previousDataDirectory;
    await rm(directory, { recursive: true, force: true });
  });

  function store() {
    return new DataStore(join(directory, "config", "settings.json"), null);
  }

  it("migrates legacy data, adds transaction IDs, and leaves the legacy file untouched", async () => {
    const legacy = {
      expenses: [
        { date: "2026-08-01", amount: 12, category: "Food", description: "Lunch", receipt: "kept" },
        { date: "2026-08-02", amount: 8, category: "Travel", description: "Bus" }
      ],
      incomes: [],
      categories: { Expense: ["Food"], Income: ["Salary"] },
      budget_settings: { monthly_income: 1000, custom_setting: "kept" },
      custom_root: { kept: true }
    };
    const legacyText = JSON.stringify(legacy);
    await writeFile(join(directory, "finance_data.json"), legacyText, "utf8");

    const result = await store().load();

    expect(result.connection.message).toBeUndefined();
    expect(result.document?.expenses[0]).toMatchObject({ category: "Food", receipt: "kept" });
    expect(result.document?.expenses[0].id).toMatch(/^[0-9a-f-]{36}$/);
    expect(result.document?.budget_settings.custom_setting).toBe("kept");
    expect(result.document?.custom_root).toEqual({ kept: true });
    expect(await readFile(join(directory, "finance_data.json"), "utf8")).toBe(legacyText);
    expect(await json(join(directory, "categories.json"))).toEqual({
      Expense: [{ name: "Food", file_key: "food" }, { name: "Travel", file_key: "travel" }],
      Income: [{ name: "Salary", file_key: "salary" }]
    });
    expect(await json(join(directory, "transactions_expense_travel.json"))).toEqual([
      expect.objectContaining({ category: "Travel", description: "Bus" })
    ]);
    expect((await json(join(directory, "preferences.json")))._extra).toEqual({
      legacy_budget_settings: { custom_setting: "kept" },
      legacy_root: { custom_root: { kept: true } }
    });
  });

  it("reads temporary aliases and unwraps owner extras", async () => {
    await writeFile(join(directory, "finance_data.json"), JSON.stringify({
      expenses: [], incomes: [], categories: { Expense: ["Food"], Income: ["Salary"] }, budget_settings: {}
    }), "utf8");
    const dataStore = store();
    await dataStore.load();
    await writeFile(join(directory, "budget.json"), JSON.stringify({
      monthly_income: 10, owner_budget: "kept", _extra: { hidden_budget: true }
    }), "utf8");
    await writeFile(join(directory, "net_worth.json"), JSON.stringify({
      bank_account_balance: 20, owner_net_worth: "kept", _extra: { hidden_net_worth: true }
    }), "utf8");
    await writeFile(join(directory, "preferences.json"), JSON.stringify({
      _extra: {
        budget_settings: { alias_setting: "kept" },
        document: { alias_root: "kept" }
      }
    }), "utf8");

    const result = await dataStore.load();

    expect(result.document?.budget_settings).toMatchObject({
      owner_budget: "kept", hidden_budget: true,
      owner_net_worth: "kept", hidden_net_worth: true,
      alias_setting: "kept"
    });
    expect(result.document?.budget_settings).not.toHaveProperty("_extra");
    expect(result.document?.alias_root).toBe("kept");
  });

  it("creates and loads missing registered transaction files", async () => {
    await writeFile(join(directory, "finance_data.json"), JSON.stringify({
      expenses: [], incomes: [], categories: { Expense: ["Food"], Income: ["Salary"] }, budget_settings: {}
    }), "utf8");
    const dataStore = store();
    await dataStore.load();
    const path = join(directory, "transactions_expense_food.json");
    await rm(path);

    const result = await dataStore.load();

    expect(result.document?.expenses).toEqual([]);
    expect(await json(path)).toEqual([]);
  });

  it("does not initialize over split files when the category registry is missing", async () => {
    const path = join(directory, "net_worth.json");
    const original = '{"wallet_balance":321}';
    await writeFile(path, original, "utf8");

    const result = await store().load();

    expect(result.document).toBeNull();
    expect(result.connection.message).toContain("categories.json is missing");
    expect(await readFile(path, "utf8")).toBe(original);
  });

  it("redirects a remembered repository root to its shared dataset", async () => {
    const shared = join(directory, "shared");
    await mkdir(shared);
    process.env.FINANCE_DATA_DIR = shared;
    await new DataStore(join(directory, "first-config.json"), null).load();
    process.env.FINANCE_DATA_DIR = directory;

    const result = await new DataStore(join(directory, "second-config.json"), null).load();

    expect(result.connection.path).toBe(shared);
    await expect(readFile(join(directory, "categories.json"), "utf8")).rejects.toThrow();
  });

  it("rejects unsafe file keys and malformed transaction rows", async () => {
    await writeFile(join(directory, "finance_data.json"), JSON.stringify({
      expenses: [], incomes: [], categories: { Expense: ["Food"], Income: ["Salary"] }, budget_settings: {}
    }), "utf8");
    const dataStore = store();
    await dataStore.load();
    const categories = await json(join(directory, "categories.json"));
    categories.Expense[0].file_key = "../../escape";
    await writeFile(join(directory, "categories.json"), JSON.stringify(categories), "utf8");
    expect((await dataStore.load()).connection.message).toContain("invalid name or file_key");

    categories.Expense[0].file_key = "food";
    await writeFile(join(directory, "categories.json"), JSON.stringify(categories), "utf8");
    await writeFile(join(directory, "transactions_expense_food.json"), '["junk"]', "utf8");
    expect((await dataStore.load()).connection.message).toContain("must contain transaction objects");
  });

  it("changes only requested feature fields and preserves latest unrelated data", async () => {
    await writeFile(join(directory, "finance_data.json"), JSON.stringify({
      expenses: [], incomes: [], categories: { Expense: ["Food"], Income: ["Salary"] },
      budget_settings: { daily_savings_goal: 1, bank_account_balance: 10 }
    }), "utf8");
    const dataStore = store();
    const loaded = await dataStore.load();
    const previous = loaded.document!;
    const next = cloneDocument(previous);
    next.budget_settings.daily_savings_goal = 5;
    const netWorthPath = join(directory, "net_worth.json");
    const netWorth = await json(netWorthPath);
    await writeFile(netWorthPath, JSON.stringify({ ...netWorth, bank_account_balance: 999, external: "kept" }), "utf8");
    const budgetPath = join(directory, "budget.json");
    const budget = await json(budgetPath);
    await writeFile(budgetPath, JSON.stringify({ ...budget, external: "kept" }), "utf8");

    await writeFile(join(directory, "budget.sync-conflict-save.json"), "{}", "utf8");
    const result = await dataStore.saveDocument(previous, next);

    expect(await json(netWorthPath)).toMatchObject({ bank_account_balance: 999, external: "kept" });
    expect(await json(budgetPath)).toMatchObject({ daily_savings_goal: 5, external: "kept" });
    expect(result.document?.budget_settings).toMatchObject({ bank_account_balance: 999, external: "kept" });
    expect(result.warnings).toContain("Ignored conflict file: budget.sync-conflict-save.json");
  });

  it("creates collision-safe files, retains keys on rename, and enforces category deletion", async () => {
    await writeFile(join(directory, "finance_data.json"), JSON.stringify({
      expenses: [{ id: "tx-1", date: "2026-08-01", amount: 3, category: "Food", description: "Snack", extra: true }],
      incomes: [], categories: { Expense: ["Food"], Income: ["Salary"] }, budget_settings: {}
    }), "utf8");
    const dataStore = store();
    const loaded = await dataStore.load();
    const original = loaded.document!;
    const added = cloneDocument(original);
    added.categories.Expense.push("Fóód");
    await dataStore.saveDocument(original, added);
    expect(await json(join(directory, "transactions_expense_food-2.json"))).toEqual([]);

    const removed = cloneDocument(added);
    removed.categories.Expense = ["Food"];
    await dataStore.saveDocument(added, removed);
    await expect(readFile(join(directory, "transactions_expense_food-2.json"), "utf8")).rejects.toThrow();

    const renamed = cloneDocument(removed);
    renamed.categories.Expense = ["Dining"];
    renamed.expenses[0].category = "Dining";
    await dataStore.saveDocument(removed, renamed);
    expect((await json(join(directory, "categories.json"))).Expense).toEqual([{ name: "Dining", file_key: "food" }]);
    expect(await json(join(directory, "transactions_expense_food.json"))).toEqual([
      expect.objectContaining({ id: "tx-1", category: "Dining", extra: true })
    ]);

    const deleted = cloneDocument(renamed);
    deleted.categories.Expense = [];
    await expect(dataStore.saveDocument(renamed, deleted)).rejects.toThrow("Cannot delete category \"Dining\" because it has transactions.");
  });

  it("ignores conflict files and warns about conflicts and orphan transaction files", async () => {
    await writeFile(join(directory, "finance_data.json"), JSON.stringify({
      expenses: [], incomes: [], categories: { Expense: ["Food"], Income: ["Salary"] }, budget_settings: {}
    }), "utf8");
    const dataStore = store();
    await dataStore.load();
    await writeFile(join(directory, "budget.sync-conflict-20260810.json"), "{}", "utf8");
    await writeFile(join(directory, "transactions_expense_orphan.json"), "[]", "utf8");

    const result = await dataStore.load();

    expect(result.warnings).toEqual(expect.arrayContaining([
      "Ignored conflict file: budget.sync-conflict-20260810.json",
      "Orphan transaction file: transactions_expense_orphan.json"
    ]));
    expect(result.conflicts).toEqual([{ fileName: "budget.sync-conflict-20260810.json", originalFileName: "budget.json" }]);
    expect(await readFile(join(directory, "transactions_expense_orphan.json"), "utf8")).toBe("[]");
  });

  it("moves a transaction using only its source and destination files", async () => {
    await writeFile(join(directory, "finance_data.json"), JSON.stringify({
      expenses: [{ id: "move", date: "2026-08-01", amount: 3, category: "Food", description: "Snack", extra: "kept" }],
      incomes: [], categories: { Expense: ["Food", "Travel"], Income: ["Salary"] }, budget_settings: {}
    }), "utf8");
    const dataStore = store();
    const loaded = await dataStore.load();
    const previous = loaded.document!;
    const next = cloneDocument(previous);
    next.expenses[0].category = "Travel";
    const foodPath = join(directory, "transactions_expense_food.json");
    const food = await json(foodPath);
    food.push({ id: "external", date: "2026-08-02", amount: 4, category: "Food", description: "External" });
    await writeFile(foodPath, JSON.stringify(food), "utf8");
    const categoriesBefore = await readFile(join(directory, "categories.json"), "utf8");

    await dataStore.saveDocument(previous, next);

    expect(await json(foodPath)).toEqual([expect.objectContaining({ id: "external" })]);
    expect(await json(join(directory, "transactions_expense_travel.json"))).toEqual([
      expect.objectContaining({ id: "move", category: "Travel", extra: "kept" })
    ]);
    expect(await readFile(join(directory, "categories.json"), "utf8")).toBe(categoriesBefore);
  });

  it("does not treat a moved delete-plus-add as a populated category rename", async () => {
    await writeFile(join(directory, "finance_data.json"), JSON.stringify({
      expenses: [{ id: "food", date: "2026-08-01", amount: 3, category: "Food", description: "Snack" }],
      incomes: [], categories: { Expense: ["Food", "Travel"], Income: ["Salary"] }, budget_settings: {}
    }), "utf8");
    const dataStore = store();
    const loaded = await dataStore.load();
    const next = cloneDocument(loaded.document!);
    next.categories.Expense = ["Travel", "Cafe"];

    await expect(dataStore.saveDocument(loaded.document!, next)).rejects.toThrow("Cannot delete category");
    expect(await json(join(directory, "transactions_expense_food.json"))).toHaveLength(1);
  });

  it("does not overwrite malformed rows introduced after load", async () => {
    await writeFile(join(directory, "finance_data.json"), JSON.stringify({
      expenses: [{ id: "food", date: "2026-08-01", amount: 3, category: "Food", description: "Snack" }],
      incomes: [], categories: { Expense: ["Food"], Income: ["Salary"] }, budget_settings: {}
    }), "utf8");
    const dataStore = store();
    const loaded = await dataStore.load();
    const next = cloneDocument(loaded.document!);
    next.expenses[0].amount = 4;
    const path = join(directory, "transactions_expense_food.json");
    await writeFile(path, '[{"id":"food","date":"2026-08-01","amount":3,"category":"Food","description":"Snack"},"junk"]', "utf8");

    await expect(dataStore.saveDocument(loaded.document!, next)).rejects.toThrow("must contain transaction objects");
    expect(await json(path)).toHaveLength(2);
  });

  it("keeps the current bytes and removes only the reviewed conflict copy", async () => {
    const dataStore = store();
    await dataStore.load();
    const originalText = "[ ]\n";
    const fileName = "loans.sync-conflict-20261007-181259-IHHEE5V.json";
    const otherName = "loans.sync-conflict-20261008-181259-OTHER.json";
    await writeFile(join(directory, "loans.json"), originalText, "utf8");
    await writeFile(join(directory, fileName), "[]", "utf8");
    await writeFile(join(directory, otherName), "[]", "utf8");
    const netWorthText = await readFile(join(directory, "net_worth.json"), "utf8");

    const preview = await dataStore.readConflict(fileName);
    expect(preview.differences).toEqual([]);
    const result = await dataStore.resolveConflict(preview, { source: "current" });

    expect(await readFile(join(directory, "loans.json"), "utf8")).toBe(originalText);
    await expect(readFile(join(directory, fileName))).rejects.toThrow();
    expect(await readFile(join(directory, otherName), "utf8")).toBe("[]");
    expect(await readFile(join(directory, "net_worth.json"), "utf8")).toBe(netWorthText);
    expect(result.conflicts).toEqual([{ fileName: otherName, originalFileName: "loans.json" }]);
    expect(result.warnings).not.toContain(`Ignored conflict file: ${fileName}`);
  });

  it.each(["loans.json", "transactions_expense_food.json"])("merges %s by stable IDs with explicit additions, deletions, and changed records", async (owner) => {
    const dataStore = store();
    await dataStore.load();
    const first = { id: "first", date: "2026-10-01", amount: 10, description: "Tickets", custom: "kept",
      ...(owner === "loans.json" ? { borrower: "Alex" } : { category: "Food", behavior_date: "2026-09-12" }) };
    const retained = { ...first, id: "retained", amount: 20 };
    const removed = { ...first, id: "removed", amount: 5 };
    const added = { ...first, id: "added", amount: -7 };
    const updated = { ...first, amount: 40 };
    const fileName = owner.replace(".json", ".sync-conflict-20261007-181259-IHHEE5V.json");
    await writeFile(join(directory, owner), JSON.stringify([first, retained, removed]), "utf8");
    await writeFile(join(directory, fileName), JSON.stringify([added, updated]), "utf8");
    const preview = await dataStore.readConflict(fileName);

    expect(preview.canMerge).toBe(true);
    expect(preview.differences.map((item) => item.key)).toEqual(["first", "retained", "removed", "added"]);
    await expect(dataStore.resolveConflict(preview, { source: "merge", choices: { first: "conflict" } })).rejects.toThrow("every difference");
    expect(await json(join(directory, owner))).toEqual([first, retained, removed]);
    const result = await dataStore.resolveConflict(preview, { source: "merge", choices: {
      first: "conflict", retained: "current", removed: "conflict", added: "conflict"
    } });

    expect(await json(join(directory, owner))).toEqual([updated, retained, added]);
    expect(result.connection.isConnected).toBe(true);
    expect(result.conflicts).toEqual([]);
    await expect(readFile(join(directory, fileName))).rejects.toThrow();
  });

  it("merges object settings while preserving selected extensions and ignoring JSON key order", async () => {
    const dataStore = store();
    await dataStore.load();
    const current = { daily_savings_goal: 5, monthly_income: 100, _extra: { first: 1, second: 2 }, custom: "keep" };
    const fileName = "budget.sync-conflict-20261007-181259-IHHEE5V.json";
    await writeFile(join(directory, "budget.json"), JSON.stringify(current), "utf8");
    await writeFile(join(directory, fileName), JSON.stringify({ monthly_income: 200, daily_savings_goal: 8, _extra: { second: 2, first: 1 } }), "utf8");
    const preview = await dataStore.readConflict(fileName);

    expect(preview.differences.map((item) => item.key)).toEqual(["daily_savings_goal", "monthly_income", "custom"]);
    await dataStore.resolveConflict(preview, { source: "merge", choices: {
      daily_savings_goal: "conflict", monthly_income: "current", custom: "current"
    } });

    expect(await json(join(directory, "budget.json"))).toEqual({ ...current, daily_savings_goal: 8 });
  });

  it("requires an explicit merge choice for record IDs that shadow prototype properties", async () => {
    const dataStore = store();
    await dataStore.load();
    const loan = { id: "constructor", borrower: "Alex", amount: 10, date: "2026-10-01" };
    const fileName = "loans.sync-conflict-20261007-181259-IHHEE5V.json";
    await writeFile(join(directory, "loans.json"), JSON.stringify([loan]), "utf8");
    await writeFile(join(directory, fileName), JSON.stringify([{ ...loan, amount: 20 }]), "utf8");
    const preview = await dataStore.readConflict(fileName);

    expect(preview.differences.map((item) => item.key)).toEqual(["constructor"]);
    await expect(dataStore.resolveConflict(preview, { source: "merge", choices: {} })).rejects.toThrow("every difference");
    await dataStore.resolveConflict(preview, { source: "merge", choices: { ["constructor"]: "conflict" as const } });
    expect(await json(join(directory, "loans.json"))).toEqual([{ ...loan, amount: 20 }]);
  });

  it("matches goals by name and offers whole-file choices for arrays without stable IDs", async () => {
    const dataStore = store();
    await dataStore.load();
    const goal = { name: "Emergency", target_amount: 1000, allocated_amount: 50, extension: true };
    const goalName = "savings_goals.sync-conflict-goals.json";
    await writeFile(join(directory, "savings_goals.json"), JSON.stringify([goal]), "utf8");
    await writeFile(join(directory, goalName), JSON.stringify([{ ...goal, allocated_amount: 100 }]), "utf8");
    const preview = await dataStore.readConflict(goalName);
    expect(preview.differences[0].key).toBe("Emergency");
    await dataStore.resolveConflict(preview, { source: "merge", choices: { Emergency: "conflict" } });
    expect(await json(join(directory, "savings_goals.json"))).toEqual([{ ...goal, allocated_amount: 100 }]);

    const loan = { borrower: "Alex", amount: 1, date: "2026-10-01" };
    const fileName = "loans.sync-conflict-legacy.json";
    await writeFile(join(directory, "loans.json"), JSON.stringify([loan]), "utf8");
    await writeFile(join(directory, fileName), JSON.stringify([{ ...loan, amount: 2 }]), "utf8");
    const legacyPreview = await dataStore.readConflict(fileName);
    expect(legacyPreview.canMerge).toBe(false);
    await dataStore.resolveConflict(legacyPreview, { source: "conflict" });
    expect(await json(join(directory, "loans.json"))).toEqual([{ ...loan, amount: 2 }]);
  });

  it.each(["loans.json", "loans.sync-conflict-stale.json"])("refuses a stale preview when %s changes", async (changedFile) => {
    const dataStore = store();
    await dataStore.load();
    const fileName = "loans.sync-conflict-stale.json";
    await writeFile(join(directory, fileName), "[]", "utf8");
    const preview = await dataStore.readConflict(fileName);
    await writeFile(join(directory, changedFile), "[ ]\n", "utf8");
    const currentText = await readFile(join(directory, "loans.json"), "utf8");
    const conflictText = await readFile(join(directory, fileName), "utf8");

    await expect(dataStore.resolveConflict(preview, { source: "conflict" })).rejects.toThrow("changed");
    expect(await readFile(join(directory, "loans.json"), "utf8")).toBe(currentText);
    expect(await readFile(join(directory, fileName), "utf8")).toBe(conflictText);
  });

  it("rejects path traversal, non-files, and previews from another directory", async () => {
    const dataStore = store();
    await dataStore.load();
    await expect(dataStore.readConflict("../loans.sync-conflict-outside.json")).rejects.toThrow("supported");
    await expect(dataStore.readConflict("..\\loans.sync-conflict-outside.json")).rejects.toThrow("supported");
    await expect(dataStore.readConflict("settings.sync-conflict-unrelated.json")).rejects.toThrow("supported");
    await mkdir(join(directory, "loans.sync-conflict-directory.json"));
    await expect(dataStore.readConflict("loans.sync-conflict-directory.json")).rejects.toThrow("regular file");
    const fileName = "loans.sync-conflict-path.json";
    await writeFile(join(directory, fileName), "[]", "utf8");
    const preview = await dataStore.readConflict(fileName);
    await expect(dataStore.resolveConflict({ ...preview, directory: join(directory, "other") }, { source: "current" })).rejects.toThrow("directory");
    expect(await readFile(join(directory, fileName), "utf8")).toBe("[]");
  });

  it.each(["{", "{}", '[{"id":"bad","borrower":"Alex","amount":"invalid","date":"2026-10-01"}]'])("retains both files when the chosen copy is invalid: %s", async (invalidText) => {
    const dataStore = store();
    await dataStore.load();
    const currentText = await readFile(join(directory, "loans.json"), "utf8");
    const fileName = "loans.sync-conflict-invalid.json";
    await writeFile(join(directory, fileName), invalidText, "utf8");
    const preview = await dataStore.readConflict(fileName);

    await expect(dataStore.resolveConflict(preview, { source: "conflict" })).rejects.toThrow();
    expect(await readFile(join(directory, "loans.json"), "utf8")).toBe(currentText);
    expect(await readFile(join(directory, fileName), "utf8")).toBe(invalidText);
    await dataStore.resolveConflict(preview, { source: "current" });
    await expect(readFile(join(directory, fileName))).rejects.toThrow();
  });

  it("exposes conflicts when loading fails and restores a missing current file", async () => {
    const dataStore = store();
    await dataStore.load();
    const fileName = "loans.sync-conflict-recovery.json";
    const loan = { id: "recovered", borrower: "Alex", amount: -10, date: "2026-10-01", custom: "kept" };
    await writeFile(join(directory, fileName), JSON.stringify([loan]), "utf8");
    await rm(join(directory, "loans.json"));
    const failedLoad = await dataStore.load();
    expect(failedLoad.document).toBeNull();
    expect(failedLoad.conflicts).toEqual([{ fileName, originalFileName: "loans.json" }]);
    const preview = await dataStore.readConflict(fileName);
    expect(preview.currentError).toContain("missing");
    await expect(dataStore.resolveConflict(preview, { source: "current" })).rejects.toThrow("missing");
    const result = await dataStore.resolveConflict(preview, { source: "conflict" });
    expect(result.document?.budget_settings.loans).toEqual([expect.objectContaining(loan)]);
    expect(await json(join(directory, "loans.json"))).toEqual([loan]);
  });

  it("keeps the conflict copy if writing fails or it changes during the write", async () => {
    const dataStore = store();
    await dataStore.load();
    const fileName = "loans.sync-conflict-write.json";
    const loan = { id: "new", borrower: "Alex", amount: 10, date: "2026-10-01" };
    const conflictText = JSON.stringify([loan]);
    await writeFile(join(directory, fileName), conflictText, "utf8");
    const preview = await dataStore.readConflict(fileName);
    const atomicWrite = fileUtils.writeJsonAtomically;
    const spy = vi.spyOn(fileUtils, "writeJsonAtomically").mockRejectedValueOnce(new Error("Disk full"));
    await expect(dataStore.resolveConflict(preview, { source: "conflict" })).rejects.toThrow("Disk full");
    expect(await json(join(directory, "loans.json"))).toEqual([]);
    expect(await readFile(join(directory, fileName), "utf8")).toBe(conflictText);

    spy.mockImplementationOnce(async (path, value) => {
      await atomicWrite(path, value);
      await writeFile(join(directory, fileName), "[]", "utf8");
    });
    await expect(dataStore.resolveConflict(preview, { source: "conflict" })).rejects.toThrow("changed");
    expect(await json(join(directory, "loans.json"))).toEqual([loan]);
    expect(await readFile(join(directory, fileName), "utf8")).toBe("[]");
  });

  it("does not replace the category registry with a version that hides populated transaction files", async () => {
    const dataStore = store();
    await dataStore.load();
    const categoriesText = await readFile(join(directory, "categories.json"), "utf8");
    await writeFile(join(directory, "transactions_expense_food.json"), JSON.stringify([
      { id: "kept", date: "2026-10-01", amount: 10, category: "Food", description: "Lunch" }
    ]), "utf8");
    const fileName = "categories.sync-conflict-deleted.json";
    await writeFile(join(directory, fileName), JSON.stringify({ Expense: [], Income: [] }), "utf8");
    const preview = await dataStore.readConflict(fileName);
    await expect(dataStore.resolveConflict(preview, { source: "conflict" })).rejects.toThrow("hide transactions");
    expect(await readFile(join(directory, "categories.json"), "utf8")).toBe(categoriesText);
    expect(await readFile(join(directory, fileName), "utf8")).toContain("Expense");
  });
});
