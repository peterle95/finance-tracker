"""
finance_tracker/ui/tabs/reconciliation_tab.py

Reconciliation tab: finds the "Reconciliation" placeholder expense for a month,
cross-references the bank CSV, and suggests which missing transactions explain
the unaccounted amount so the user can properly categorize them.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from typing import Optional

from ...services.reconciliation_service import (
    STATUS_MATCHED,
    STATUS_MISSING,
    STATUS_POSSIBLE,
    BankTransaction,
    match_transactions,
    parse_bank_csv,
    suggest_category,
)

_TAG_CANDIDATE  = "candidate"   # likely explains part of reconciliation
_TAG_UNLIKELY   = "unlikely"    # unmatched but amount doesn't fit
_TAG_MATCHED    = "matched"
_RECON_CATEGORY = "Reconciliation"


def _find_candidates(
    unmatched: list[BankTransaction],
    target: float,
    tolerance: float = 2.0,
) -> list[tuple[BankTransaction, float]]:
    """
    For each unmatched expense, score how likely it contributes to the
    reconciliation gap.  Returns list of (txn, score) sorted best first.
    Score = 100 if transaction alone equals target, decreasing otherwise.
    """
    results = []
    for t in unmatched:
        if t.tx_type != "Expense":
            continue
        amt = abs(t.amount)
        # Score: 100 if exact match, scaled by closeness, 0 if amt > target + tolerance
        if amt <= target + tolerance:
            # How much of the target does this cover?
            coverage = min(amt / target, 1.0) if target > 0 else 0
            # Bonus if it alone exactly explains the gap
            exact_bonus = 30 if abs(amt - target) <= tolerance else 0
            score = coverage * 70 + exact_bonus
        else:
            score = 0
        results.append((t, round(score, 1)))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


class ReconciliationTab:
    def __init__(self, notebook: ttk.Notebook, state, on_data_changed):
        self.state = state
        self.on_data_changed = on_data_changed

        self._bank_txns: list[BankTransaction] = []
        self._unmatched_month: list[BankTransaction] = []
        self._scored: list[tuple[BankTransaction, float]] = []
        self._recon_entries: list[dict] = []   # existing Reconciliation-category txns

        self.frame = ttk.Frame(notebook, padding="10")
        notebook.add(self.frame, text="Reconciliation")
        self.frame.rowconfigure(1, weight=1)
        self.frame.columnconfigure(0, weight=1)

        # ── TOP BAR ──────────────────────────────────────────────────────
        top = ttk.Frame(self.frame)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        # Month selector
        ttk.Label(top, text="Month (YYYY-MM):").pack(side="left")
        self._month_var = tk.StringVar(value=datetime.now().strftime("%Y-%m"))
        ttk.Entry(top, textvariable=self._month_var, width=10).pack(
            side="left", padx=(5, 15))
        ttk.Button(top, text="Analyse", command=self._analyse).pack(side="left")

        # CSV loader
        ttk.Separator(top, orient="vertical").pack(
            side="left", fill="y", padx=15)
        ttk.Button(top, text="📂  Load Bank CSV",
                   command=self._load_csv).pack(side="left", padx=(0, 8))
        self._file_label = ttk.Label(top, text="No CSV loaded",
                                     foreground="gray",
                                     font=("Arial", 9, "italic"))
        self._file_label.pack(side="left")

        # ── MAIN AREA ─────────────────────────────────────────────────────
        main = ttk.Frame(self.frame)
        main.grid(row=1, column=0, sticky="nsew")
        main.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=2)
        main.columnconfigure(1, weight=1)

        # LEFT: summary + candidate table
        left = ttk.Frame(main)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        # Summary cards
        cards = ttk.Frame(left)
        cards.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for i in range(4):
            cards.columnconfigure(i, weight=1)

        def _card(col, title):
            f = ttk.LabelFrame(cards, text=title, padding="8")
            f.grid(row=0, column=col, sticky="ew", padx=3)
            lbl = ttk.Label(f, text="—", font=("Arial", 13, "bold"), anchor="center")
            lbl.pack(fill="x")
            return lbl

        self._lbl_recon_total  = _card(0, "Reconciliation Placeholder")
        self._lbl_csv_missing  = _card(1, "Unmatched CSV Expenses")
        self._lbl_csv_sum      = _card(2, "Unmatched CSV Total")
        self._lbl_remaining    = _card(3, "Still Unexplained")

        # Candidate table
        tbl_frame = ttk.LabelFrame(
            left,
            text="CSV transactions NOT in tracker  "
                 "(🎯 = likely candidate, sorted by relevance)",
            padding="8",
        )
        tbl_frame.grid(row=1, column=0, sticky="nsew")
        tbl_frame.rowconfigure(0, weight=1)
        tbl_frame.columnconfigure(0, weight=1)

        cols = ("score", "date", "amount", "payee", "purpose", "suggested_cat")
        self._tree = ttk.Treeview(
            tbl_frame, columns=cols, show="headings", selectmode="browse")
        self._tree.heading("score",         text="Fit")
        self._tree.heading("date",          text="Date")
        self._tree.heading("amount",        text="Amount")
        self._tree.heading("payee",         text="Payee")
        self._tree.heading("purpose",       text="Purpose")
        self._tree.heading("suggested_cat", text="Suggested Category")

        self._tree.column("score",         width=55,  anchor="center", stretch=False)
        self._tree.column("date",          width=90,  anchor="center", stretch=False)
        self._tree.column("amount",        width=85,  anchor="e",      stretch=False)
        self._tree.column("payee",         width=170, anchor="w")
        self._tree.column("purpose",       width=200, anchor="w")
        self._tree.column("suggested_cat", width=140, anchor="w")

        self._tree.tag_configure(_TAG_CANDIDATE,
                                 background="#2a3d1a", foreground="#a8e08a")
        self._tree.tag_configure(_TAG_UNLIKELY,
                                 background="#1e2028", foreground="#9098b0")

        vsb = ttk.Scrollbar(tbl_frame, orient="vertical",
                             command=self._tree.yview)
        hsb = ttk.Scrollbar(tbl_frame, orient="horizontal",
                             command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # Table buttons
        tbl_btns = ttk.Frame(left)
        tbl_btns.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(tbl_btns, text="✚  Add Selected with Proper Category",
                   command=self._add_selected).pack(side="left", padx=(0, 8))
        ttk.Button(tbl_btns, text="Add All Candidates",
                   command=self._add_all_candidates).pack(side="left")
        self._lbl_progress = ttk.Label(
            tbl_btns, text="", font=("Arial", 9, "italic"), foreground="gray")
        self._lbl_progress.pack(side="right")

        # RIGHT: explanation + quick-add form
        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        # Explanation text
        explain_frame = ttk.LabelFrame(right, text="What is happening?", padding="8")
        explain_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        explain_frame.rowconfigure(0, weight=1)
        explain_frame.columnconfigure(0, weight=1)

        self._explain_text = tk.Text(
            explain_frame, wrap="word", font=("Arial", 9),
            state="disabled", relief="flat", height=12)
        esb = ttk.Scrollbar(explain_frame, orient="vertical",
                             command=self._explain_text.yview)
        self._explain_text.configure(yscrollcommand=esb.set)
        self._explain_text.grid(row=0, column=0, sticky="nsew")
        esb.grid(row=0, column=1, sticky="ns")

        # Quick-add form
        add_frame = ttk.LabelFrame(right, text="Add as proper transaction", padding="8")
        add_frame.grid(row=1, column=0, sticky="ew")
        add_frame.columnconfigure(1, weight=1)

        def _row(r, label):
            ttk.Label(add_frame, text=label).grid(
                row=r, column=0, sticky="w", pady=2, padx=(0, 6))

        _row(0, "Date:")
        self._add_date_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self._add_date_var, width=12).grid(
            row=0, column=1, sticky="w", pady=2)

        _row(1, "Amount (€):")
        self._add_amount_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self._add_amount_var, width=12).grid(
            row=1, column=1, sticky="w", pady=2)

        _row(2, "Type:")
        self._add_type_var = tk.StringVar(value="Expense")
        tf = ttk.Frame(add_frame)
        tf.grid(row=2, column=1, sticky="w")
        ttk.Radiobutton(tf, text="Expense", variable=self._add_type_var,
                        value="Expense",
                        command=self._refresh_cats).pack(side="left")
        ttk.Radiobutton(tf, text="Income", variable=self._add_type_var,
                        value="Income",
                        command=self._refresh_cats).pack(side="left", padx=5)

        _row(3, "Category:")
        self._add_cat_var = tk.StringVar()
        self._cat_combo = ttk.Combobox(
            add_frame, textvariable=self._add_cat_var,
            width=22, state="readonly")
        self._cat_combo.grid(row=3, column=1, sticky="ew", pady=2)

        _row(4, "Description:")
        self._add_desc_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self._add_desc_var).grid(
            row=4, column=1, sticky="ew", pady=2)

        ttk.Button(
            add_frame,
            text="✚  Add & remove from reconciliation",
            command=self._add_selected,
        ).grid(row=5, column=0, columnspan=2, sticky="e", pady=(10, 0))

        # Existing reconciliation entries
        recon_frame = ttk.LabelFrame(
            right, text=f'Existing "{_RECON_CATEGORY}" entries this month',
            padding="8")
        recon_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        recon_frame.columnconfigure(0, weight=1)

        rcols = ("date", "amount", "desc")
        self._recon_tree = ttk.Treeview(
            recon_frame, columns=rcols, show="headings",
            height=4, selectmode="browse")
        self._recon_tree.heading("date",   text="Date")
        self._recon_tree.heading("amount", text="Amount")
        self._recon_tree.heading("desc",   text="Description")
        self._recon_tree.column("date",   width=80,  anchor="center", stretch=False)
        self._recon_tree.column("amount", width=80,  anchor="e",      stretch=False)
        self._recon_tree.column("desc",   width=150, anchor="w")
        self._recon_tree.grid(row=0, column=0, sticky="ew")

        ttk.Button(recon_frame, text="🗑  Delete selected placeholder",
                   command=self._delete_recon_entry).grid(
            row=1, column=0, sticky="e", pady=(4, 0))

        self._refresh_cats()
        self._set_explanation_initial()

    # ──────────────────────────────────────────────────────────────────────
    # Core analysis
    # ──────────────────────────────────────────────────────────────────────
    def _analyse(self):
        month = self._month_var.get().strip()
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            messagebox.showerror("Invalid", "Use YYYY-MM format.", parent=self.frame)
            return

        # 1. Find Reconciliation category entries for the month
        self._recon_entries = [
            e for e in self.state.expenses
            if e.get("category") == _RECON_CATEGORY
            and e.get("date", "").startswith(month)
        ]
        recon_total = sum(e["amount"] for e in self._recon_entries)

        # 2. Re-match CSV (excluding recon entries from matching target)
        if self._bank_txns:
            match_transactions(self._bank_txns, self.state)
            self._unmatched_month = [
                t for t in self._bank_txns
                if t.date.startswith(month)
                and t.status == STATUS_MISSING
                and t.tx_type == "Expense"
            ]
        else:
            self._unmatched_month = []

        # 3. Score candidates
        self._scored = _find_candidates(self._unmatched_month, recon_total)

        # 4. Compute running totals
        candidate_sum = sum(
            abs(t.amount) for t, s in self._scored if s >= 10)
        remaining = max(recon_total - candidate_sum, 0)

        # 5. Update summary cards
        self._lbl_recon_total.configure(
            text=f"-€{recon_total:.2f}" if recon_total > 0 else "None ✓",
            foreground="red" if recon_total > 0.5 else "green")
        self._lbl_csv_missing.configure(
            text=str(len(self._unmatched_month))
            if self._bank_txns else "Load CSV")
        self._lbl_csv_sum.configure(
            text=f"€{sum(abs(t.amount) for t in self._unmatched_month):.2f}"
            if self._bank_txns else "—")
        self._lbl_remaining.configure(
            text=f"€{remaining:.2f}" if self._bank_txns else "Load CSV",
            foreground="red" if remaining > 0.5 else "green")

        # 6. Render table
        self._render_table()

        # 7. Populate existing recon entries list
        self._recon_tree.delete(*self._recon_tree.get_children())
        for e in self._recon_entries:
            self._recon_tree.insert("", "end",
                                    iid=e.get("id", id(e)),
                                    values=(e["date"],
                                            f"€{e['amount']:.2f}",
                                            e.get("description", "")))

        # 8. Update explanation
        self._update_explanation(month, recon_total, candidate_sum, remaining)

    def _render_table(self):
        self._tree.delete(*self._tree.get_children())
        for idx, (t, score) in enumerate(self._scored):
            is_candidate = score >= 10
            tag = _TAG_CANDIDATE if is_candidate else _TAG_UNLIKELY
            icon = "🎯" if score >= 50 else ("✓" if is_candidate else "·")
            self._tree.insert(
                "", "end", iid=str(idx), tags=(tag,),
                values=(
                    icon,
                    t.date,
                    f"-€{abs(t.amount):.2f}",
                    t.payee[:42],
                    t.purpose[:52],
                    t.suggested_category,
                ),
            )

    # ──────────────────────────────────────────────────────────────────────
    # Explanation text
    # ──────────────────────────────────────────────────────────────────────
    def _set_explanation_initial(self):
        lines = [
            "HOW THIS WORKS\n",
            "1. Select a month and click Analyse.\n\n",
            f'2. The app finds your "{_RECON_CATEGORY}" category '
            "expense for that month — this is the lump sum you entered "
            "when you couldn't identify certain transactions.\n\n",
            "3. Load your bank CSV. The app finds all bank transactions "
            "from that month that are NOT yet in your tracker.\n\n",
            "4. Those unmatched bank rows are sorted by how likely they "
            "are to explain the reconciliation gap (🎯 = strong candidate).\n\n",
            "5. Select a row, assign the correct category, click Add. "
            "The transaction is properly recorded and the reconciliation "
            "placeholder is no longer needed.\n\n",
            "6. Once you've identified all missing transactions, delete "
            'the "Reconciliation" placeholder entry below.',
        ]
        self._explain_text.configure(state="normal")
        self._explain_text.delete("1.0", "end")
        for line in lines:
            self._explain_text.insert("end", line)
        self._explain_text.configure(state="disabled")

    def _update_explanation(self, month: str, recon_total: float,
                            candidate_sum: float, remaining: float):
        self._explain_text.configure(state="normal")
        self._explain_text.delete("1.0", "end")

        if recon_total < 0.01:
            self._explain_text.insert("end",
                f"✅  No Reconciliation entry found for {month}.\n\n"
                "Your books are clean for this month.")
            self._explain_text.configure(state="disabled")
            return

        lines = [f"ANALYSIS FOR {month}\n{'─'*35}\n\n"]

        if not self._bank_txns:
            lines.append(
                f"You have a Reconciliation placeholder of €{recon_total:.2f}.\n\n"
                "Load your bank CSV to identify which specific transactions "
                "this amount represents.")
        else:
            n_cand = sum(1 for _, s in self._scored if s >= 10)
            lines.append(
                f"Reconciliation gap:    €{recon_total:.2f}\n"
                f"CSV candidates found:  {n_cand} transactions\n"
                f"Candidate total:       €{candidate_sum:.2f}\n"
                f"Still unexplained:     €{remaining:.2f}\n\n"
            )
            if remaining < 0.50:
                lines.append(
                    "✅  The candidate transactions fully explain the gap.\n"
                    "Add them with proper categories, then delete the "
                    "Reconciliation placeholder.\n")
            elif candidate_sum > 0:
                lines.append(
                    "⚠  Candidates only partially explain the gap.\n"
                    f"€{remaining:.2f} is still unaccounted for — it may be\n"
                    "a cash transaction or a date outside the CSV range.\n")
            else:
                lines.append(
                    "❌  No CSV candidates found for this month.\n"
                    "The missing transactions may be cash payments,\n"
                    "or from a different bank account not in the CSV.\n")

            lines.append(
                "\nHOW TO USE\n"
                "• 🎯 rows are the most likely candidates.\n"
                "• Click a row → adjust category → click Add.\n"
                "• Added transactions reduce the unexplained amount.\n"
                "• Once done, delete the Reconciliation placeholder.\n")

        self._explain_text.insert("end", "".join(lines))
        self._explain_text.configure(state="disabled")

    # ──────────────────────────────────────────────────────────────────────
    # Adding transactions
    # ──────────────────────────────────────────────────────────────────────
    def _on_select(self, _event=None):
        sel = self._tree.selection()
        if not sel:
            return
        t, _score = self._scored[int(sel[0])]
        self._add_date_var.set(t.date)
        self._add_amount_var.set(f"{abs(t.amount):.2f}")
        self._add_type_var.set(t.tx_type)
        self._refresh_cats()
        self._add_cat_var.set(t.suggested_category)
        desc = t.payee if t.payee else t.purpose
        self._add_desc_var.set(desc[:60])

    def _add_selected(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("No selection",
                                   "Click a row in the table first.",
                                   parent=self.frame)
            return
        t, _ = self._scored[int(sel[0])]
        self._do_add(t)

    def _do_add(self, t: BankTransaction):
        date_str   = self._add_date_var.get().strip()
        amount_str = self._add_amount_var.get().strip()
        cat        = self._add_cat_var.get().strip()
        desc       = self._add_desc_var.get().strip()
        tx_type    = self._add_type_var.get()

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Bad date", "Date must be YYYY-MM-DD.",
                                 parent=self.frame)
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Bad amount", "Amount must be a positive number.",
                                 parent=self.frame)
            return
        if not cat:
            messagebox.showerror("No category", "Pick a category.",
                                 parent=self.frame)
            return
        if cat == _RECON_CATEGORY:
            messagebox.showerror(
                "Wrong category",
                f'Do not add back to "{_RECON_CATEGORY}". '
                "Choose the real category instead.",
                parent=self.frame)
            return

        self.state.add_transaction(tx_type, date_str, amount, cat,
                                   desc or t.payee)
        t.status = STATUS_MATCHED
        t.match_confidence = "reconciled"
        self.on_data_changed()
        self._analyse()   # refresh everything

    def _add_all_candidates(self):
        candidates = [(t, s) for t, s in self._scored if s >= 10]
        if not candidates:
            messagebox.showinfo("Nothing to add",
                                "No strong candidates found.", parent=self.frame)
            return
        if not messagebox.askyesno(
            "Add all candidates",
            f"Add {len(candidates)} candidate transaction(s) with suggested "
            "categories?",
            parent=self.frame,
        ):
            return
        for t, _ in candidates:
            cat  = t.suggested_category
            cats = self.state.categories.get(t.tx_type, ["Other"])
            if cat not in cats:
                cat = cats[-1]
            desc = t.payee if t.payee else t.purpose
            self.state.add_transaction(t.tx_type, t.date, abs(t.amount),
                                       cat, desc[:60])
            t.status = STATUS_MATCHED
        self.on_data_changed()
        self._analyse()
        messagebox.showinfo("Done",
                            f"Added {len(candidates)} transaction(s).",
                            parent=self.frame)

    def _delete_recon_entry(self):
        sel = self._recon_tree.selection()
        if not sel:
            messagebox.showwarning("No selection",
                                   "Select a Reconciliation entry to delete.",
                                   parent=self.frame)
            return
        entry_id = sel[0]
        entry = next(
            (e for e in self._recon_entries
             if str(e.get("id", id(e))) == str(entry_id)),
            None)
        if not entry:
            return
        if not messagebox.askyesno(
            "Delete placeholder",
            f"Delete the Reconciliation entry of €{entry['amount']:.2f} "
            f"on {entry['date']}?\n\n"
            "Only do this after you've properly added all the transactions "
            "it represented.",
            parent=self.frame,
        ):
            return
        self.state.delete_transaction_by_id("Expense", entry.get("id", ""))
        self.on_data_changed()
        self._analyse()

    # ──────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────
    def _refresh_cats(self):
        cats = self.state.categories.get(self._add_type_var.get(), [])
        # Remove Reconciliation from available choices — force proper category
        cats = [c for c in cats if c != _RECON_CATEGORY]
        self._cat_combo.configure(values=cats)
        if self._add_cat_var.get() not in cats:
            self._cat_combo.set(cats[0] if cats else "")

    def _load_csv(self):
        path = filedialog.askopenfilename(
            title="Select bank CSV",
            filetypes=[("CSV files", "*.csv *.CSV"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            txns, meta = parse_bank_csv(path)
        except Exception as exc:
            messagebox.showerror("Import Error", str(exc), parent=self.frame)
            return
        if "error" in meta:
            messagebox.showerror("Import Error", meta["error"], parent=self.frame)
            return
        if not txns:
            messagebox.showinfo("Empty", "No transactions found.", parent=self.frame)
            return

        for t in txns:
            t.suggested_category = suggest_category(
                t.payee, t.purpose, t.tx_type, self.state)

        self._bank_txns = match_transactions(txns, self.state)

        import os
        self._file_label.configure(text=os.path.basename(path), foreground="")

        if self._month_var.get():
            self._analyse()

    def refresh_after_data_change(self):
        if self._bank_txns:
            match_transactions(self._bank_txns, self.state)