import { DEFAULT_EXPENSE_CATEGORIES, DEFAULT_INCOME_CATEGORIES } from "./finance";
import type { BankTransaction, CsvImportResult, FinanceDocument, TransactionType } from "./types";

const KEYWORD_CATEGORIES: Array<[string[], string]> = [
  [["paypal", "ebay", "amazon", "klarna"], "Shopping"],
  [["rewe", "edeka", "lidl", "aldi", "netto", "penny", "kaufland", "rossmann"], "Food"],
  [["restaurant", "cafe", "mcdonald", "burger", "pizza", "starbucks"], "Food"],
  [["spotify", "netflix", "hbo", "disney", "prime"], "Entertainment"],
  [["bahn", "mvg", "bvg", "uber", "bolt", "taxi", "flixbus"], "Transportation"],
  [["strom", "gas ", "internet", "telefon", "vodafone", "telekom"], "Utilities"],
  [["krankenkas", "aok", "apotheke", "arzt", "zahnarzt"], "Healthcare"],
  [["miete", "wohnung", "rent"], "Utilities"],
  [["gehalt", "lohn", "salary", "wage"], "Salary"],
  [["zinsen", "dividende", "ertrag"], "Investment"]
];

function splitCsvLine(line: string, separator: string): string[] {
  const values: string[] = [];
  let value = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];
    if (character === "\"") {
      if (quoted && line[index + 1] === "\"") {
        value += "\"";
        index += 1;
      } else {
        quoted = !quoted;
      }
    } else if (character === separator && !quoted) {
      values.push(value.trim());
      value = "";
    } else {
      value += character;
    }
  }
  values.push(value.trim());
  return values;
}

function findColumn(headers: string[], candidates: string[]): number {
  const normalized = headers.map((header) => header.trim().toLocaleLowerCase("de-DE"));
  return candidates
    .map((candidate) => normalized.indexOf(candidate.toLocaleLowerCase("de-DE")))
    .find((index) => index >= 0) ?? -1;
}

export function parseGermanAmount(value: string): number {
  const trimmed = value.replace(/[€\s]/g, "").trim();
  const normalized = trimmed.includes(",")
    ? trimmed.replace(/\./g, "").replace(",", ".")
    : trimmed.replace(/,/g, "");
  return Number(normalized);
}

export function parseBankDate(value: string): string {
  const trimmed = value.trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
    return trimmed;
  }
  const match = trimmed.match(/^(\d{1,2})\.(\d{1,2})\.(\d{2}|\d{4})$/);
  if (!match) {
    return trimmed;
  }
  const year = match[3].length === 2 ? "20" + match[3] : match[3];
  return year + "-" + match[2].padStart(2, "0") + "-" + match[1].padStart(2, "0");
}

export function parseBankCsvText(text: string): CsvImportResult {
  const lines = text.replace(/^\uFEFF/, "").split(/\r?\n/).filter((line) => line.trim().length > 0);
  if (lines.length < 2) {
    return {
      transactions: [],
      meta: { encoding: "detected", separator: ";", totalRows: 0, skippedRows: 0, message: "The CSV is empty." }
    };
  }

  const separators = [";", ",", "\t"];
  const separator = separators
    .sort((first, second) => splitCsvLine(lines[0], second).length - splitCsvLine(lines[0], first).length)[0];
  const headers = splitCsvLine(lines[0], separator);
  const dateColumn = findColumn(headers, ["Buchungstag", "Buchungsdatum", "Date", "Datum"]);
  const amountColumn = findColumn(headers, ["Betrag", "Amount", "Umsatz"]);
  const payeeColumn = findColumn(headers, [
    "Begünstigter/Zahlungspflichtiger",
    "Beguenstigter/Zahlungspflichtiger",
    "Empfänger",
    "Empfaenger",
    "Payee",
    "Auftraggeber/Begünstigter"
  ]);
  const purposeColumn = findColumn(headers, ["Verwendungszweck", "Purpose", "Beschreibung", "Betreff", "Details"]);
  const bookingColumn = findColumn(headers, ["Buchungstext", "Transaktionsart", "Typ"]);
  const currencyColumn = findColumn(headers, ["Währung", "Waehrung", "Currency"]);

  if (dateColumn < 0 || amountColumn < 0) {
    return {
      transactions: [],
      meta: {
        encoding: "detected",
        separator,
        totalRows: lines.length - 1,
        skippedRows: lines.length - 1,
        message: "Required date or amount columns were not found."
      }
    };
  }

  let skippedRows = 0;
  const transactions: BankTransaction[] = lines.slice(1).flatMap((line, index): BankTransaction[] => {
    const row = splitCsvLine(line, separator);
    const amount = parseGermanAmount(row[amountColumn] ?? "");
    const date = parseBankDate(row[dateColumn] ?? "");
    if (!Number.isFinite(amount) || !/^\d{4}-\d{2}-\d{2}$/.test(date)) {
      skippedRows += 1;
      return [];
    }
    const payee = (row[payeeColumn] ?? "").replace(/\s+/g, " ").trim();
    const purpose = (row[purposeColumn] ?? "").replace(/\s+/g, " ").trim();
    const transactionType: TransactionType = amount >= 0 ? "Income" : "Expense";
    return [{
      id: "bank-" + String(index) + "-" + date + "-" + String(Math.abs(amount)),
      date,
      amount,
      payee,
      purpose,
      bookingText: (row[bookingColumn] ?? "").trim(),
      currency: (row[currencyColumn] ?? "EUR").trim() || "EUR",
      transactionType,
      suggestedCategory: "",
      status: "missing" as const
    }];
  });

  return {
    transactions,
    meta: {
      encoding: "detected",
      separator,
      totalRows: lines.length - 1,
      skippedRows
    }
  };
}

export function suggestBankCategory(
  transaction: BankTransaction,
  document: FinanceDocument
): string {
  const type: TransactionType = transaction.transactionType;
  const categories = document.categories[type] ?? (type === "Expense" ? DEFAULT_EXPENSE_CATEGORIES : DEFAULT_INCOME_CATEGORIES);
  const source = type === "Expense" ? document.expenses : document.incomes;
  const history = new Map<string, number>();
  const normalizedPayee = transaction.payee.toLocaleLowerCase("de-DE").slice(0, 10);
  source.forEach((entry) => {
    const searchable = (entry.description + " " + entry.category).toLocaleLowerCase("de-DE");
    if (normalizedPayee && searchable.includes(normalizedPayee)) {
      history.set(entry.category, (history.get(entry.category) ?? 0) + 1);
    }
  });
  if (history.size > 0) {
    return [...history.entries()].sort((first, second) => second[1] - first[1])[0][0];
  }

  const content = (transaction.payee + " " + transaction.purpose).toLocaleLowerCase("de-DE");
  for (const [keywords, category] of KEYWORD_CATEGORIES) {
    if (keywords.some((keyword) => content.includes(keyword))) {
      const exact = categories.find((entry) => entry.toLocaleLowerCase("de-DE") === category.toLocaleLowerCase("de-DE"));
      if (exact) {
        return exact;
      }
      const prefix = categories.find((entry) => entry.toLocaleLowerCase("de-DE").startsWith(category.toLocaleLowerCase("de-DE").split(":")[0]));
      if (prefix) {
        return prefix;
      }
    }
  }
  return categories.includes("Other") ? "Other" : categories.at(-1) ?? "Other";
}

function datesApart(first: string, second: string): number {
  const firstDate = new Date(first + "T12:00:00");
  const secondDate = new Date(second + "T12:00:00");
  return Math.abs(Math.round((firstDate.getTime() - secondDate.getTime()) / 86400000));
}

export function reconcileBankTransactions(
  transactions: BankTransaction[],
  document: FinanceDocument
): BankTransaction[] {
  const used = new Set<string>();
  return transactions.map((bankTransaction) => {
    const source = bankTransaction.transactionType === "Expense" ? document.expenses : document.incomes;
    const candidates = source
      .filter((manual) => !used.has(manual.id ?? ""))
      .filter((manual) => Math.abs(Math.abs(bankTransaction.amount) - Math.abs(manual.amount)) <= 0.02)
      .map((manual) => ({ manual, difference: datesApart(bankTransaction.date, manual.date) }))
      .filter((candidate) => candidate.difference <= 3)
      .sort((first, second) => first.difference - second.difference);
    const match = candidates[0];
    if (match) {
      const id = match.manual.id ?? "";
      if (id) {
        used.add(id);
      }
      return {
        ...bankTransaction,
        suggestedCategory: match.manual.category,
        status: match.difference === 0 ? "matched" : "possible",
        matchedTransactionId: id || undefined,
        matchConfidence: match.difference === 0 ? "exact" : "fuzzy_date"
      };
    }
    return {
      ...bankTransaction,
      suggestedCategory: suggestBankCategory(bankTransaction, document),
      status: "missing"
    };
  });
}
