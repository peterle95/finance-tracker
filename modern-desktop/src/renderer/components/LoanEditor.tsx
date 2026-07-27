import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { formatCurrency, isoToday, roundCurrency } from "../../shared/finance";
import type { Loan } from "../../shared/types";
import { Button } from "./ui";

interface LoanEditorProps {
  open: boolean;
  loan: Loan | null;
  onOpenChange(open: boolean): void;
  onSave(loan: Loan): void;
}

interface LoanDraft {
  borrower: string;
  amount: string;
  description: string;
  notes: string;
  date: string;
}

function draftFromLoan(loan: Loan | null): LoanDraft {
  return {
    borrower: loan?.borrower ?? "",
    amount: loan ? String(loan.amount) : "",
    description: loan?.description ?? "",
    notes: loan?.notes ?? "",
    date: loan?.date ?? isoToday()
  };
}

function signedCurrency(value: number): string {
  return (value >= 0 ? "+" : "−") + formatCurrency(Math.abs(value));
}

export function LoanEditor({ open, loan, onOpenChange, onSave }: LoanEditorProps) {
  const [draft, setDraft] = useState<LoanDraft>(() => draftFromLoan(loan));
  const [pendingLoan, setPendingLoan] = useState<Loan | null>(null);

  useEffect(() => {
    if (open) {
      setDraft(draftFromLoan(loan));
      setPendingLoan(null);
    }
  }, [open, loan]);

  function updateDraft(update: Partial<LoanDraft>) {
    setDraft((current) => ({ ...current, ...update }));
  }

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!loan || !draft.borrower.trim() || !draft.date) {
      return;
    }
    const amount = roundCurrency(Number(draft.amount));
    if (!Number.isFinite(amount) || amount === 0) {
      return;
    }
    const nextLoan: Loan = {
      ...loan,
      borrower: draft.borrower.trim(),
      amount,
      description: draft.description.trim(),
      notes: draft.notes.trim(),
      date: draft.date
    };
    if (amount !== roundCurrency(loan.amount)) {
      setPendingLoan(nextLoan);
      return;
    }
    onSave(nextLoan);
    onOpenChange(false);
  }

  function confirmSave() {
    if (!pendingLoan) {
      return;
    }
    onSave(pendingLoan);
    onOpenChange(false);
  }

  const amountDifference = pendingLoan && loan ? pendingLoan.amount - loan.amount : 0;

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog-content" aria-describedby="loan-editor-description">
          <div className="dialog-heading">
            <div>
              <p className="eyebrow">Lending</p>
              <Dialog.Title>Modify loan</Dialog.Title>
              <Dialog.Description id="loan-editor-description">
                Update every loan detail, including notes.
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button className="icon-button" aria-label="Close loan editor">
                <X size={18} />
              </button>
            </Dialog.Close>
          </div>

          {pendingLoan && loan ? (
            <div className="loan-change-confirmation">
              <p className="eyebrow">Amount change</p>
              <h2>Confirm the new amount</h2>
              <p>
                The amount changes from {formatCurrency(loan.amount)} to {formatCurrency(pendingLoan.amount)}.
              </p>
              <strong>Difference: {signedCurrency(amountDifference)}</strong>
              <div className="dialog-actions">
                <Button type="button" variant="ghost" onClick={() => setPendingLoan(null)}>Back</Button>
                <Button type="button" onClick={confirmSave}>Confirm and save</Button>
              </div>
            </div>
          ) : (
            <form className="form-grid" onSubmit={submit}>
              <label>
                <span>Borrower</span>
                <input aria-label="Borrower" value={draft.borrower} onChange={(event) => updateDraft({ borrower: event.target.value })} required />
              </label>
              <label>
                <span>Amount</span>
                <input aria-label="Amount" type="number" step="0.01" inputMode="decimal" value={draft.amount} onChange={(event) => updateDraft({ amount: event.target.value })} required />
              </label>
              <label>
                <span>Date</span>
                <input aria-label="Date" type="date" value={draft.date} onChange={(event) => updateDraft({ date: event.target.value })} required />
              </label>
              <label>
                <span>Description</span>
                <input aria-label="Description" value={draft.description} onChange={(event) => updateDraft({ description: event.target.value })} />
              </label>
              <label className="span-two">
                <span>Notes</span>
                <textarea aria-label="Notes" rows={6} value={draft.notes} onChange={(event) => updateDraft({ notes: event.target.value })} placeholder="Add context, repayment details, or reminders" />
              </label>
              <div className="dialog-actions span-two">
                <Dialog.Close asChild>
                  <Button type="button" variant="ghost">Cancel</Button>
                </Dialog.Close>
                <Button type="submit">Done</Button>
              </div>
            </form>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
