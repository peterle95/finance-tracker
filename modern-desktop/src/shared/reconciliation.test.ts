import { describe, expect, it } from "vitest";
import { defaultDocument } from "./finance";
import { parseBankCsvText, reconcileBankTransactions } from "./reconciliation";

describe("bank CSV reconciliation", () => {
  it("parses German amounts and identifies an exact manual match", () => {
    const result = parseBankCsvText(
      "Buchungstag;Betrag;Beguenstigter/Zahlungspflichtiger;Verwendungszweck\n"
      + "20.04.26;-12,50;REWE Markt;Einkauf\n"
    );
    const document = defaultDocument();
    document.expenses.push({
      id: "manual-1",
      date: "2026-04-20",
      amount: 12.5,
      category: "Food",
      description: "REWE groceries"
    });

    const reconciled = reconcileBankTransactions(result.transactions, document);

    expect(result.transactions[0].date).toBe("2026-04-20");
    expect(result.transactions[0].amount).toBe(-12.5);
    expect(reconciled[0]).toMatchObject({
      status: "matched",
      matchedTransactionId: "manual-1",
      suggestedCategory: "Food"
    });
  });

  it("suggests a category for a missing transaction", () => {
    const result = parseBankCsvText(
      "Date,Amount,Payee,Purpose\n"
      + "2026-06-12,-33.20,Netflix,Subscription\n"
    );
    const reconciled = reconcileBankTransactions(result.transactions, defaultDocument());

    expect(reconciled[0].status).toBe("missing");
    expect(reconciled[0].suggestedCategory).toBe("Entertainment");
  });
});
