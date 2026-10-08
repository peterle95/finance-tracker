import { _electron as electron, expect, test } from "@playwright/test";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

test("opens the shared data file and saves an expense", async () => {
  const directory = await mkdtemp(join(tmpdir(), "finance-modern-e2e-"));
  const dataPath = join(directory, "finance_data.json");
  const userDataPath = join(directory, "user-data");
  await writeFile(dataPath, JSON.stringify({
    expenses: [],
    incomes: [],
    budget_settings: {
      bank_account_balance: 1000,
      money_lent_balance: -34.149999999,
      loans: [{
        id: "signed-loan",
        borrower: "Friend",
        amount: -34.149999999,
        description: "Amount owed",
        date: "2026-07-10"
      }]
    },
    categories: {
      Expense: ["Food", "Other"],
      Income: ["Salary", "Other"]
    }
  }), "utf8");

  const app = await electron.launch({
    args: [join(process.cwd(), "out", "main", "index.js")],
    env: {
      ...process.env,
      FINANCE_DATA_DIR: directory,
      FINANCE_TRACKER_USER_DATA: userDataPath
    }
  });

  try {
    const window = await app.firstWindow();
    await expect(window.getByRole("heading", { name: "Your money, clearly" })).toBeVisible();
    await window.getByRole("button", { name: "Add expense" }).click();
    await window.getByLabel("Amount").fill("12.50");
    await window.getByLabel("Description").fill("E2E lunch");
    await window.getByRole("button", { name: "Add transaction" }).click();
    await expect.poll(async () => {
      const categories = JSON.parse(await readFile(join(directory, "categories.json"), "utf8")) as {
        Expense: Array<{ name: string; file_key: string }>;
      };
      const key = categories.Expense.find((category) => category.name === "Food")?.file_key;
      const saved = JSON.parse(await readFile(join(directory, `transactions_expense_${key}.json`), "utf8")) as unknown[];
      return saved.length;
    }).toBe(1);
    await window.getByRole("button", { name: "Net worth" }).click();
    await expect(window.getByText("Money owed").first()).toBeVisible();
    await expect(window.locator(".recharts-sector").first()).toBeVisible();
    await window.getByRole("button", { name: "Category limits" }).click();
    await expect(window.getByRole("heading", { name: "Category limits" })).toBeVisible();
  } finally {
    await app.close();
    await rm(directory, { recursive: true, force: true });
  }
});

test("reviews and resolves a Syncthing loan conflict through the desktop bridge", async () => {
  const directory = await mkdtemp(join(tmpdir(), "finance-conflict-e2e-"));
  const fileName = "loans.sync-conflict-20261007-181259-IHHEE5V.json";
  const current = { id: "loan-1", borrower: "Alex", amount: 40, description: "Tickets", notes: "", date: "2026-10-01", custom: "kept" };
  const retained = { ...current, id: "loan-2", borrower: "Taylor", amount: -5 };
  const updated = { ...current, amount: 55 };
  const added = { ...current, id: "loan-3", borrower: "Sam", amount: 10 };
  const conflictText = JSON.stringify([added, updated]);
  await writeFile(join(directory, "finance_data.json"), JSON.stringify({
    expenses: [], incomes: [], categories: { Expense: ["Food"], Income: ["Salary"] },
    budget_settings: { loans: [current, retained] }
  }), "utf8");
  await writeFile(join(directory, fileName), conflictText, "utf8");
  const app = await electron.launch({
    args: [join(process.cwd(), "out", "main", "index.js")],
    env: { ...process.env, FINANCE_DATA_DIR: directory, FINANCE_TRACKER_USER_DATA: join(directory, "user-data") }
  });
  try {
    const window = await app.firstWindow();
    await window.getByRole("button", { name: "Resolve sync conflicts" }).click();
    const resolver = window.getByRole("dialog", { name: "Resolve sync conflict" });
    await expect(resolver.getByText(join(directory, "loans.json"), { exact: true })).toBeVisible();
    await expect(resolver.getByText(join(directory, fileName), { exact: true })).toBeVisible();
    await resolver.getByRole("button", { name: "Keep current file" }).click();
    await resolver.getByRole("button", { name: "Cancel" }).click();
    expect(JSON.parse(await readFile(join(directory, "loans.json"), "utf8"))).toEqual([current, retained]);
    expect(await readFile(join(directory, fileName), "utf8")).toBe(conflictText);

    await window.getByRole("button", { name: "Resolve sync conflicts" }).click();
    await resolver.getByRole("button", { name: "Use conflict copy" }).click();
    expect(await readFile(join(directory, fileName), "utf8")).toBe(conflictText);
    await resolver.getByRole("button", { name: "Confirm resolution" }).click();
    await expect(resolver).not.toBeVisible();
    await expect(window.getByRole("status")).toContainText("Sync conflict resolved.");
    expect(JSON.parse(await readFile(join(directory, "loans.json"), "utf8"))).toEqual([added, updated]);
    await expect(readFile(join(directory, fileName))).rejects.toThrow();
    await expect(window.getByRole("button", { name: "Resolve sync conflicts" })).toHaveCount(0);
  } finally {
    await app.close();
    await rm(directory, { recursive: true, force: true });
  }
});
