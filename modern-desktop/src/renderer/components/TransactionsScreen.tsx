import { ArrowDownRight, ArrowUpRight, Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { currentMonth, formatCurrency, getActiveMonthlyIncome, sumFixedCosts } from "../../shared/finance";
import type { FinanceDocument, FinanceTransaction, TransactionType } from "../../shared/types";
import { Button, Card, EmptyState, PageHeader } from "./ui";

interface TransactionsScreenProps {
  document: FinanceDocument;
  onAdd(type: TransactionType): void;
  onEdit(type: TransactionType, transaction: FinanceTransaction): void;
  onDelete(type: TransactionType, transaction: FinanceTransaction): void;
}

export function TransactionsScreen({
  document,
  onAdd,
  onEdit,
  onDelete
}: TransactionsScreenProps) {
  const [type, setType] = useState<"All" | TransactionType>("All");
  const [category, setCategory] = useState("All");
  const [query, setQuery] = useState("");
  const [month, setMonth] = useState(currentMonth);
  const [sortKey, setSortKey] = useState<"date" | "amount" | "category">("date");
  const [descending, setDescending] = useState(true);
  const categories = useMemo(() => Array.from(new Set([
    ...document.categories.Expense,
    ...document.categories.Income,
    ...document.expenses.map((transaction) => transaction.category),
    ...document.incomes.map((transaction) => transaction.category)
  ])).sort((first, second) => first.localeCompare(second)), [document]);

  const transactions = useMemo(() => {
    const source: Array<{ type: TransactionType; transaction: FinanceTransaction }> = [
      ...document.expenses.map((transaction) => ({ type: "Expense" as const, transaction })),
      ...document.incomes.map((transaction) => ({ type: "Income" as const, transaction }))
    ];
    return source
      .filter((entry) => type === "All" || entry.type === type)
      .filter((entry) => category === "All" || entry.transaction.category === category)
      .filter((entry) => !month || entry.transaction.date.startsWith(month))
      .filter((entry) => {
        const value = [
          entry.transaction.description,
          entry.transaction.category,
          entry.transaction.date,
          entry.transaction.behavior_date ?? ""
        ].join(" ").toLocaleLowerCase();
        return value.includes(query.toLocaleLowerCase());
      })
      .sort((first, second) => {
        const firstValue = first.transaction[sortKey];
        const secondValue = second.transaction[sortKey];
        const compared = typeof firstValue === "number" && typeof secondValue === "number"
          ? firstValue - secondValue
          : String(firstValue).localeCompare(String(secondValue));
        return descending ? -compared : compared;
      });
  }, [document, type, category, query, month, sortKey, descending]);

  const flexibleCosts = transactions
    .filter((entry) => entry.type === "Expense")
    .reduce((total, entry) => total + entry.transaction.amount, 0);
  const flexibleIncome = transactions
    .filter((entry) => entry.type === "Income")
    .reduce((total, entry) => total + entry.transaction.amount, 0);
  const totalIncome = (month ? getActiveMonthlyIncome(document, month) : 0) + flexibleIncome;
  const totalCosts = flexibleCosts + (month ? sumFixedCosts(document, month) : 0);
  const totalIncomeDifference = totalIncome - totalCosts;

  function toggleSort(next: typeof sortKey) {
    if (next === sortKey) {
      setDescending((value) => !value);
    } else {
      setSortKey(next);
      setDescending(true);
    }
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="Shared ledger"
        title="Transactions"
        description="Search, refine, and correct every income and expense without losing its original data."
        action={
          <div className="button-group">
            <Button variant="secondary" onClick={() => onAdd("Income")}><ArrowUpRight size={16} /> Income</Button>
            <Button onClick={() => onAdd("Expense")}><Plus size={16} /> Expense</Button>
          </div>
        }
      />

      <Card className="toolbar-card">
        <div className="toolbar transactions-toolbar">
          <label className="search-field">
            <Search size={17} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search description, category, or date" />
          </label>
          <select value={type} onChange={(event) => setType(event.target.value as "All" | TransactionType)}>
            <option value="All">All types</option>
            <option value="Expense">Expenses</option>
            <option value="Income">Income</option>
          </select>
          <select aria-label="Filter by category" value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="All">All categories</option>
            {categories.map((entry) => <option key={entry} value={entry}>{entry}</option>)}
          </select>
          <input aria-label="Filter by booking month" type="month" value={month} onChange={(event) => setMonth(event.target.value)} />
          <Button variant="ghost" onClick={() => { setQuery(""); setType("All"); setCategory("All"); setMonth(currentMonth()); }}>Clear filters</Button>
        </div>
      </Card>

      <Card className="transactions-summary">
        <div>
          <p className="eyebrow">Flexible costs</p>
          <strong>{formatCurrency(flexibleCosts)}</strong>
          <span>{query || type !== "All" ? "Matching filters" : month ? "In " + month : "Matching transactions"}</span>
        </div>
        <div>
          <p className="eyebrow">Total income − total costs</p>
          <strong className={totalIncomeDifference < 0 ? "amount-expense" : "amount-income"}>
            {formatCurrency(totalIncomeDifference)}
          </strong>
          <span>Total income minus total costs</span>
        </div>
      </Card>

      {transactions.length ? (
        <Card className="table-card">
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th><button onClick={() => toggleSort("date")}>Date</button></th>
                  <th><button onClick={() => toggleSort("category")}>Category</button></th>
                  <th>Description</th>
                  <th className="number"><button onClick={() => toggleSort("amount")}>Amount</button></th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {transactions.map(({ type: transactionType, transaction }, index) => (
                  <tr key={transaction.id ?? transaction.date + index}>
                    <td>
                      <span className={"type-pill " + (transactionType === "Expense" ? "expense" : "income")}>
                        {transactionType === "Expense" ? <ArrowDownRight size={14} /> : <ArrowUpRight size={14} />}
                        {transactionType}
                      </span>
                    </td>
                    <td>{transaction.date}{transaction.behavior_date ? <span className="subtle-line">Spent {transaction.behavior_date}</span> : null}</td>
                    <td>{transaction.category}</td>
                    <td>{transaction.description || "—"}</td>
                    <td className={"number " + (transactionType === "Expense" ? "amount-expense" : "amount-income")}>
                      {transactionType === "Expense" ? "−" : "+"}{formatCurrency(transaction.amount)}
                    </td>
                    <td>
                      <div className="row-actions">
                        <button className="icon-button" onClick={() => onEdit(transactionType, transaction)} aria-label="Edit transaction">
                          <Pencil size={16} />
                        </button>
                        <button className="icon-button danger-icon" onClick={() => onDelete(transactionType, transaction)} aria-label="Delete transaction">
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        <EmptyState
          title="No transactions match these filters"
          detail="Try a different month or add a new income or expense."
          action={<Button onClick={() => onAdd("Expense")}>Add a transaction</Button>}
        />
      )}
    </div>
  );
}
