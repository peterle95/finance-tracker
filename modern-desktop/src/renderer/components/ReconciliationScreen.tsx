import { CheckCircle2, FileUp, Plus, RefreshCw, Sparkles } from "lucide-react";
import { useState } from "react";
import { cloneDocument, makeTransaction } from "../../shared/finance";
import { reconcileBankTransactions } from "../../shared/reconciliation";
import type { BankTransaction, CsvImportResult, FinanceDocument } from "../../shared/types";
import { Button, Card, EmptyState, PageHeader } from "./ui";

export function ReconciliationScreen({
  document,
  onSave
}: {
  document: FinanceDocument;
  onSave(document: FinanceDocument): void;
}) {
  const [importResult, setImportResult] = useState<CsvImportResult | null>(null);
  const [rows, setRows] = useState<BankTransaction[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [message, setMessage] = useState("");

  async function chooseCsv() {
    const result = await window.finance.chooseBankCsv();
    if (!result) {
      return;
    }
    const reconciled = reconcileBankTransactions(result.transactions, document);
    setImportResult(result);
    setRows(reconciled);
    setSelected(new Set(reconciled.filter((entry) => entry.status === "missing").map((entry) => entry.id)));
    setMessage(result.meta.message ?? "");
  }

  function updateCategory(id: string, category: string) {
    setRows((current) => current.map((entry) => entry.id === id ? { ...entry, suggestedCategory: category } : entry));
  }

  function addRows(targets: BankTransaction[]) {
    if (!targets.length) {
      return;
    }
    const next = cloneDocument(document);
    targets.forEach((bank) => {
      const transaction = makeTransaction(bank.transactionType, {
        date: bank.date,
        amount: Math.abs(bank.amount),
        category: bank.suggestedCategory || next.categories[bank.transactionType][0] || "Other",
        description: bank.payee || bank.purpose || "Imported bank transaction"
      });
      if (bank.transactionType === "Expense") {
        next.expenses.push(transaction);
      } else {
        next.incomes.push(transaction);
      }
    });
    onSave(next);
    setRows((current) => reconcileBankTransactions(current, next));
    setSelected(new Set());
    setMessage(targets.length + " transaction(s) added to the shared finance file.");
  }

  const missing = rows.filter((entry) => entry.status === "missing");
  const matched = rows.filter((entry) => entry.status === "matched").length;
  const possible = rows.filter((entry) => entry.status === "possible").length;

  return (
    <div className="page">
      <PageHeader
        eyebrow="Bank imports"
        title="Reconciliation"
        description="Compare a German bank CSV export to your manual ledger, then add only the entries you need."
        action={<Button onClick={() => void chooseCsv()}><FileUp size={16} /> Import CSV</Button>}
      />

      {importResult ? (
        <>
          <div className="metric-grid">
            <Card className="metric"><p>Imported rows</p><strong>{importResult.meta.totalRows}</strong><span>{importResult.meta.separator === "\t" ? "Tab" : importResult.meta.separator} separated</span></Card>
            <Card className="metric metric-positive"><p>Matched</p><strong>{matched}</strong><span>Exact date and amount</span></Card>
            <Card className="metric"><p>Possible matches</p><strong>{possible}</strong><span>Within three days</span></Card>
            <Card className="metric metric-warning"><p>Missing</p><strong>{missing.length}</strong><span>Ready to add</span></Card>
          </div>

          <Card className="toolbar-card">
            <div className="toolbar">
              <Button variant="secondary" onClick={() => setRows((current) => reconcileBankTransactions(current, document))}><RefreshCw size={16} /> Re-check matches</Button>
              <Button variant="secondary" onClick={() => addRows(rows.filter((entry) => selected.has(entry.id) && entry.status !== "matched"))}><Plus size={16} /> Add selected</Button>
              <Button onClick={() => addRows(missing)}><Sparkles size={16} /> Add all missing</Button>
              {message ? <span className="status-message">{message}</span> : null}
            </div>
          </Card>

          <Card className="table-card">
            <div className="table-scroll">
              <table>
                <thead><tr><th><input aria-label="Select all missing transactions" type="checkbox" checked={missing.length > 0 && missing.every((entry) => selected.has(entry.id))} onChange={(event) => setSelected(event.target.checked ? new Set(missing.map((entry) => entry.id)) : new Set())} /></th><th>Date</th><th>Payee</th><th>Type</th><th>Suggested category</th><th className="number">Amount</th><th>Status</th></tr></thead>
                <tbody>
                  {rows.map((entry) => (
                    <tr key={entry.id}>
                      <td><input aria-label={"Select " + entry.payee} type="checkbox" disabled={entry.status === "matched"} checked={selected.has(entry.id)} onChange={(event) => setSelected((current) => { const next = new Set(current); event.target.checked ? next.add(entry.id) : next.delete(entry.id); return next; })} /></td>
                      <td>{entry.date}</td>
                      <td><strong>{entry.payee || "—"}</strong><span className="subtle-line">{entry.purpose}</span></td>
                      <td>{entry.transactionType}</td>
                      <td><select value={entry.suggestedCategory} disabled={entry.status === "matched"} onChange={(event) => updateCategory(entry.id, event.target.value)}>{document.categories[entry.transactionType].map((category) => <option key={category}>{category}</option>)}</select></td>
                      <td className="number">{entry.amount.toLocaleString("de-DE", { style: "currency", currency: entry.currency || "EUR" })}</td>
                      <td><span className={"status-pill " + entry.status}>{entry.status === "matched" ? <CheckCircle2 size={14} /> : null}{entry.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      ) : (
        <EmptyState title="Import a bank CSV when you are ready" detail="Sparkasse, DKB, N26-style date and amount columns are detected automatically. Nothing is saved until you choose entries to add." action={<Button onClick={() => void chooseCsv()}><FileUp size={16} /> Choose CSV</Button>} />
      )}
    </div>
  );
}
