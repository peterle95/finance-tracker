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
      FINANCE_DATA_FILE: dataPath,
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
      const saved = JSON.parse(await readFile(dataPath, "utf8")) as { expenses: unknown[] };
      return saved.expenses.length;
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
