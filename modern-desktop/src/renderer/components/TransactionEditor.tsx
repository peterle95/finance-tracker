import * as Dialog from "@radix-ui/react-dialog";
import { CalendarDays, X } from "lucide-react";
import { useEffect, useState } from "react";
import { isoToday, makeTransaction } from "../../shared/finance";
import type { FinanceDocument, FinanceTransaction, TransactionType } from "../../shared/types";
import { Button } from "./ui";

interface TransactionEditorProps {
  open: boolean;
  document: FinanceDocument;
  type: TransactionType;
  transaction?: FinanceTransaction;
  onOpenChange(open: boolean): void;
  onSubmit(type: TransactionType, transaction: FinanceTransaction, original?: FinanceTransaction): void;
}

export function TransactionEditor({
  open,
  document,
  type,
  transaction,
  onOpenChange,
  onSubmit
}: TransactionEditorProps) {
  const originalDate = transaction?.behavior_date ?? transaction?.date ?? isoToday();
  const [date, setDate] = useState(originalDate);
  const [amount, setAmount] = useState(String(transaction?.amount ?? ""));
  const [category, setCategory] = useState(transaction?.category ?? document.categories[type][0] ?? "Other");
  const [description, setDescription] = useState(transaction?.description ?? "");
  const [bnpl, setBnpl] = useState(type === "Expense" && !transaction ? true : Boolean(transaction?.behavior_date));

  useEffect(() => {
    if (open) {
      const nextDate = transaction?.behavior_date ?? transaction?.date ?? isoToday();
      setDate(nextDate);
      setAmount(transaction?.amount ? String(transaction.amount) : "");
      setCategory(transaction?.category ?? document.categories[type][0] ?? "Other");
      setDescription(transaction?.description ?? "");
      setBnpl(type === "Expense" && !transaction ? true : Boolean(transaction?.behavior_date));
    }
  }, [open, transaction, type, document.categories]);

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const numericAmount = Number(amount);
    if (!Number.isFinite(numericAmount) || numericAmount <= 0 || !date || !category) {
      return;
    }
    const values = {
      date,
      amount: numericAmount,
      category,
      description
    };
    const saved = transaction
      ? {
        ...transaction,
        ...values,
        date: bnpl ? makeTransaction(type, values, true).date : date,
        behavior_date: bnpl ? date : undefined
      }
      : makeTransaction(type, values, bnpl);
    if (transaction) {
      onSubmit(type, saved, transaction);
    } else {
      onSubmit(type, saved);
    }
    onOpenChange(false);
  }

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog-content" aria-describedby="transaction-editor-description">
          <div className="dialog-heading">
            <div>
              <p className="eyebrow">{transaction ? "Edit entry" : "New entry"}</p>
              <Dialog.Title>{type === "Expense" ? "Expense" : "Income"} transaction</Dialog.Title>
              <Dialog.Description id="transaction-editor-description">
                Add a precise record to the shared finance file.
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button className="icon-button" aria-label="Close transaction editor">
                <X size={18} />
              </button>
            </Dialog.Close>
          </div>
          <form className="form-grid" onSubmit={submit}>
            <label>
              <span>Date</span>
              <input
                aria-label="Date"
                type="date"
                value={date}
                onChange={(event) => setDate(event.target.value)}
                required
              />
            </label>
            <label>
              <span>Amount</span>
              <input
                aria-label="Amount"
                type="number"
                min="0.01"
                step="0.01"
                inputMode="decimal"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
                placeholder="0.00"
                required
              />
            </label>
            <label className="span-two">
              <span>Category</span>
              <select aria-label="Category" value={category} onChange={(event) => setCategory(event.target.value)}>
                {document.categories[type].map((entry) => (
                  <option key={entry} value={entry}>{entry}</option>
                ))}
              </select>
            </label>
            <label className="span-two">
              <span>Description</span>
              <input
                aria-label="Description"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="What was this for?"
              />
            </label>
            {type === "Expense" ? (
              <label className="check-row span-two">
                <input
                  type="checkbox"
                  checked={bnpl}
                  onChange={(event) => setBnpl(event.target.checked)}
                />
                <span>
                  <CalendarDays size={16} />
                  Pay next month (book on the first, keep this as the spend date)
                </span>
              </label>
            ) : null}
            <div className="dialog-actions span-two">
              <Dialog.Close asChild>
                <Button type="button" variant="ghost">Cancel</Button>
              </Dialog.Close>
              <Button type="submit">{transaction ? "Save changes" : "Add transaction"}</Button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
