"""
finance_tracker/ui/tabs/reconciliation_tab.py

Tab for importing bank CSV exports and reconciling them against manually
entered transactions. Highlights what's missing and lets the user add it.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from typing import TYPE_CHECKING

from ...services.reconciliation_service import (
    STATUS_MATCHED,
    STATUS_MISSING,
    STATUS_POSSIBLE,
    BankTransaction,
    get_summary,
    match_transactions,
    parse_bank_csv,
    suggest_category,
)

if TYPE_CHECKING:
    pass

# Row colours (tag names mapped to background colours, set via Treeview tag_configure)
_TAG_MISSING  = "rec_missing"
_TAG_POSSIBLE = "rec_possible"
_TAG_MATCHED  = "rec_matched"

_FILTER_ALL      = "All"
_FILTER_MISSING  = "Missing"
_FILTER_POSSIBLE = "Possible match"
_FILTER_MATCHED  = "Matched"


class ReconciliationTab:
    """Bank CSV import and reconciliation tab."""

    def __init__(self, notebook: ttk.Notebook, state, on_data_changed):
        self.state = state
        self.on_data_changed = on_data_changed

        self._bank_txns: list[BankTransaction] = []
        self._filtered_txns: list[BankTransaction] = []
        self._loaded_file: str = ""

        # ------------------------------------------------------------------ #
        # Root frame
        # ------------------------------------------------------------------ #
        self.frame = ttk.Frame(notebook, padding="10")
        notebook.add(self.frame, text="Reconciliation")
        self.frame.rowconfigure(2, weight=1)
        self.frame.columnconfigure(0, weight=1)

        # ------------------------------------------------------------------ #
        # Row 0 — file loader + summary stats
        # ------------------------------------------------------------------ #
        top = ttk.Frame(self.frame)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        top.columnconfigure(1, weight=1)

        load_frame = ttk.LabelFrame(top, text="Bank CSV Import", padding="10")
        load_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))

        ttk.Button(load_frame, text="📂  Load Bank CSV",
                   command=self._load_csv).pack(side="left", padx=(0, 10))

        self._file_label = ttk.Label(load_frame, text="No file loaded",
                                     foreground="gray", font=("Arial", 9, "italic"))
        self._file_label.pack(side="left")

        ttk.Button(load_frame, text="↻  Re-match",
                   command=self._rematch).pack(side="left", padx=(15, 0))

        # Summary stats panel
        self._stats_frame = ttk.LabelFrame(top, text="CSV Summary", padding="10")
        self._stats_frame.grid(row=0, column=1, sticky="nsew")
        self._stats_label = ttk.Label(self._stats_frame,
                                      text="Load a CSV file to see statistics.",
                                      font=("Arial", 10), justify="left")
        self._stats_label.pack(anchor="w")

        # ------------------------------------------------------------------ #
        # Row 1 — filter bar + action buttons
        # ------------------------------------------------------------------ #
        filter_bar = ttk.Frame(self.frame)
        filter_bar.grid(row=1, column=0, sticky="ew", pady=(0, 5))

        ttk.Label(filter_bar, text="Show:").pack(side="left", padx=(0, 5))
        self._filter_var = tk.StringVar(value=_FILTER_MISSING)
        for label in (_FILTER_ALL, _FILTER_MISSING, _FILTER_POSSIBLE, _FILTER_MATCHED):
            ttk.Radiobutton(
                filter_bar, text=label,
                variable=self._filter_var, value=label,
                command=self._apply_filter,
            ).pack(side="left", padx=4)

        # Action buttons (right-aligned)
        btn_frame = ttk.Frame(filter_bar)
        btn_frame.pack(side="right")
        ttk.Button(btn_frame, text="Add Selected to Tracker",
                   command=self._add_selected).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Add All Missing to Tracker",
                   command=self._add_all_missing).pack(side="left")

        # ------------------------------------------------------------------ #
        # Row 2 — main paned area: treeview (left) + detail panel (right)
        # ------------------------------------------------------------------ #
        paned = ttk.PanedWindow(self.frame, orient="horizontal")
        paned.grid(row=2, column=0, sticky="nsew")

        # Left: transaction table
        tree_outer = ttk.Frame(paned)
        paned.add(tree_outer, weight=4)
        tree_outer.rowconfigure(0, weight=1)
        tree_outer.columnconfigure(0, weight=1)

        cols = ("status", "date", "amount", "type", "payee", "purpose", "category")
        self._tree = ttk.Treeview(tree_outer, columns=cols, show="headings", selectmode="browse")

        self._tree.heading("status",   text="Status")
        self._tree.heading("date",     text="Date",     command=lambda: self._sort("date"))
        self._tree.heading("amount",   text="Amount",   command=lambda: self._sort("amount"))
        self._tree.heading("type",     text="Type",     command=lambda: self._sort("type"))
        self._tree.heading("payee",    text="Payee",    command=lambda: self._sort("payee"))
        self._tree.heading("purpose",  text="Purpose")
        self._tree.heading("category", text="Suggested Category")

        self._tree.column("status",   width=90,  anchor="center", stretch=False)
        self._tree.column("date",     width=95,  anchor="center", stretch=False)
        self._tree.column("amount",   width=90,  anchor="e",      stretch=False)
        self._tree.column("type",     width=70,  anchor="center", stretch=False)
        self._tree.column("payee",    width=180, anchor="w")
        self._tree.column("purpose",  width=220, anchor="w")
        self._tree.column("category", width=140, anchor="w")

        # Colour tags
        self._tree.tag_configure(_TAG_MISSING,  background="#3d1a1a", foreground="#ff8080")
        self._tree.tag_configure(_TAG_POSSIBLE, background="#3d3000", foreground="#ffd080")
        self._tree.tag_configure(_TAG_MATCHED,  background="#1a3a1a", foreground="#80c880")

        vsb = ttk.Scrollbar(tree_outer, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(tree_outer, orient="horizontal",  command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # Right: detail panel
        detail_outer = ttk.LabelFrame(paned, text="Transaction Detail", padding="10")
        paned.add(detail_outer, weight=1)
        detail_outer.columnconfigure(0, weight=1)
        detail_outer.rowconfigure(1, weight=1)

        self._detail_text = tk.Text(
            detail_outer, wrap="word", font=("Courier New", 9),
            height=12, state="disabled", relief="flat",
        )
        self._detail_text.grid(row=0, column=0, sticky="nsew")

        # --- Quick-add form inside detail panel ---
        add_frame = ttk.LabelFrame(detail_outer, text="Add to Tracker", padding="8")
        add_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        add_frame.columnconfigure(1, weight=1)

        ttk.Label(add_frame, text="Date:").grid(row=0, column=0, sticky="w", pady=3)
        self._add_date_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self._add_date_var, width=14).grid(
            row=0, column=1, sticky="w", pady=3)

        ttk.Label(add_frame, text="Amount:").grid(row=1, column=0, sticky="w", pady=3)
        self._add_amount_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self._add_amount_var, width=14).grid(
            row=1, column=1, sticky="w", pady=3)

        ttk.Label(add_frame, text="Type:").grid(row=2, column=0, sticky="w", pady=3)
        self._add_type_var = tk.StringVar(value="Expense")
        type_f = ttk.Frame(add_frame)
        type_f.grid(row=2, column=1, sticky="w")
        ttk.Radiobutton(type_f, text="Expense", variable=self._add_type_var,
                        value="Expense", command=self._refresh_category_combo).pack(side="left")
        ttk.Radiobutton(type_f, text="Income",  variable=self._add_type_var,
                        value="Income",  command=self._refresh_category_combo).pack(side="left", padx=5)

        ttk.Label(add_frame, text="Category:").grid(row=3, column=0, sticky="w", pady=3)
        self._add_cat_var = tk.StringVar()
        self._add_cat_combo = ttk.Combobox(
            add_frame, textvariable=self._add_cat_var, width=20, state="readonly")
        self._add_cat_combo.grid(row=3, column=1, sticky="ew", pady=3)

        ttk.Label(add_frame, text="Description:").grid(row=4, column=0, sticky="w", pady=3)
        self._add_desc_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self._add_desc_var).grid(
            row=4, column=1, sticky="ew", pady=3)

        ttk.Button(add_frame, text="✚  Add This Transaction",
                   command=self._add_selected).grid(
            row=5, column=0, columnspan=2, sticky="e", pady=(8, 0))

        self._refresh_category_combo()
        self._sort_col: str = "date"
        self._sort_rev: bool = False

    # ---------------------------------------------------------------------- #
    # Public helpers
    # ---------------------------------------------------------------------- #
    def refresh_after_data_change(self):
        """Called when the user adds/deletes transactions externally."""
        if self._bank_txns:
            self._rematch()

    # ---------------------------------------------------------------------- #
    # File loading
    # ---------------------------------------------------------------------- #
    def _load_csv(self):
        path = filedialog.askopenfilename(
            title="Select bank CSV export",
            filetypes=[
                ("CSV files", "*.csv *.CSV"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        self._loaded_file = path
        self._do_load_and_match(path)

    def _do_load_and_match(self, path: str):
        try:
            txns, meta = parse_bank_csv(path)
        except Exception as exc:
            messagebox.showerror("Import Error",
                                 f"Could not read the CSV file:\n\n{exc}",
                                 parent=self.frame)
            return

        if "error" in meta:
            messagebox.showerror("Import Error", meta["error"], parent=self.frame)
            return

        if not txns:
            messagebox.showinfo("Empty", "No transactions found in the file.",
                                parent=self.frame)
            return

        # Suggest categories before matching (matching doesn't need them)
        for t in txns:
            t.suggested_category = suggest_category(
                t.payee, t.purpose, t.tx_type, self.state)

        self._bank_txns = match_transactions(txns, self.state)

        # Show file name
        import os
        fname = os.path.basename(path)
        self._file_label.configure(text=fname, foreground="")

        self._update_stats()
        self._apply_filter()

    def _rematch(self):
        if not self._bank_txns:
            return
        for t in self._bank_txns:
            t.status = STATUS_MISSING
            t.matched_tx = None
            t.match_confidence = ""
        match_transactions(self._bank_txns, self.state)
        self._update_stats()
        self._apply_filter()

    # ---------------------------------------------------------------------- #
    # Stats display
    # ---------------------------------------------------------------------- #
    def _update_stats(self):
        s = get_summary(self._bank_txns)
        if not s:
            return

        pct_matched = 0
        if s["total"] > 0:
            pct_matched = (s["matched_count"] + s["possible_count"]) / s["total"] * 100

        text = (
            f"Period: {s['date_from']}  →  {s['date_to']}   |   "
            f"Total: {s['total']} transactions\n"
            f"Income: {s['income_count']} rows  (+€{s['total_income']:,.2f})     "
            f"Expenses: {s['expense_count']} rows  (-€{s['total_expenses']:,.2f})     "
            f"Net: {'+'if s['net']>=0 else ''}€{s['net']:,.2f}\n"
            f"🟢 Matched: {s['matched_count']}   "
            f"🟡 Possible: {s['possible_count']}   "
            f"🔴 Missing: {s['missing_count']}   "
            f"({pct_matched:.0f}% reconciled)"
        )
        self._stats_label.configure(text=text)

    # ---------------------------------------------------------------------- #
    # Filtering + rendering
    # ---------------------------------------------------------------------- #
    def _apply_filter(self, *_):
        filt = self._filter_var.get()
        if filt == _FILTER_ALL:
            self._filtered_txns = list(self._bank_txns)
        elif filt == _FILTER_MISSING:
            self._filtered_txns = [t for t in self._bank_txns if t.status == STATUS_MISSING]
        elif filt == _FILTER_POSSIBLE:
            self._filtered_txns = [t for t in self._bank_txns if t.status == STATUS_POSSIBLE]
        else:
            self._filtered_txns = [t for t in self._bank_txns if t.status == STATUS_MATCHED]

        self._sort_list()
        self._render_tree()

    def _sort(self, col: str):
        if self._sort_col == col:
            self._sort_rev = not self._sort_rev
        else:
            self._sort_col = col
            self._sort_rev = False
        self._sort_list()
        self._render_tree()

    def _sort_list(self):
        col = self._sort_col
        rev = self._sort_rev
        if col == "date":
            self._filtered_txns.sort(key=lambda t: t.date, reverse=rev)
        elif col == "amount":
            self._filtered_txns.sort(key=lambda t: abs(t.amount), reverse=rev)
        elif col == "type":
            self._filtered_txns.sort(key=lambda t: t.tx_type, reverse=rev)
        elif col == "payee":
            self._filtered_txns.sort(key=lambda t: t.payee.lower(), reverse=rev)

    def _render_tree(self):
        self._tree.delete(*self._tree.get_children())
        for idx, t in enumerate(self._filtered_txns):
            if t.status == STATUS_MISSING:
                tag  = _TAG_MISSING
                icon = "🔴 Missing"
            elif t.status == STATUS_POSSIBLE:
                tag  = _TAG_POSSIBLE
                icon = "🟡 Possible"
            else:
                tag  = _TAG_MATCHED
                icon = "🟢 Matched"

            amt_str = f"{'+'if t.amount >= 0 else ''}€{t.amount:,.2f}"
            self._tree.insert(
                "", "end", iid=str(idx), tags=(tag,),
                values=(
                    icon,
                    t.date,
                    amt_str,
                    t.tx_type,
                    t.payee[:50],
                    t.purpose[:60],
                    t.suggested_category,
                ),
            )

    # ---------------------------------------------------------------------- #
    # Selection → detail panel
    # ---------------------------------------------------------------------- #
    def _on_select(self, _event=None):
        sel = self._tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        t   = self._filtered_txns[idx]

        # Fill detail text
        self._detail_text.configure(state="normal")
        self._detail_text.delete("1.0", "end")

        lines = [
            f"{'─'*40}",
            f"  Date          : {t.date}",
            f"  Amount        : {'+'if t.amount>=0 else ''}€{t.amount:,.2f} {t.currency}",
            f"  Type          : {t.tx_type}",
            f"  Booking type  : {t.booking_text}",
            f"  Payee         : {t.payee}",
            f"  Purpose       : {t.purpose}",
            f"{'─'*40}",
            f"  Status        : {t.status.upper()}",
        ]
        if t.matched_tx:
            m = t.matched_tx
            lines += [
                f"  Matched with  : {m.get('description','(no desc)')}",
                f"  Match date    : {m.get('date','')}",
                f"  Match amount  : €{m.get('amount',0):,.2f}",
                f"  Match cat     : {m.get('category','')}",
                f"  Confidence    : {t.match_confidence}",
            ]
        lines.append(f"{'─'*40}")

        self._detail_text.insert("end", "\n".join(lines))
        self._detail_text.configure(state="disabled")

        # Pre-fill the quick-add form
        self._add_date_var.set(t.date)
        self._add_amount_var.set(f"{abs(t.amount):.2f}")
        self._add_type_var.set(t.tx_type)
        self._refresh_category_combo()
        self._add_cat_var.set(t.suggested_category)

        # Pre-fill description: prefer payee, fallback to purpose
        desc = t.payee if t.payee else t.purpose
        self._add_desc_var.set(desc[:60])

    # ---------------------------------------------------------------------- #
    # Category combo helper
    # ---------------------------------------------------------------------- #
    def _refresh_category_combo(self):
        tx_type = self._add_type_var.get()
        cats = self.state.categories.get(tx_type, [])
        self._add_cat_combo.configure(values=cats)
        current = self._add_cat_var.get()
        if current not in cats:
            self._add_cat_combo.set(cats[0] if cats else "")

    # ---------------------------------------------------------------------- #
    # Adding transactions
    # ---------------------------------------------------------------------- #
    def _get_selected_btx(self) -> BankTransaction | None:
        sel = self._tree.selection()
        if not sel:
            return None
        return self._filtered_txns[int(sel[0])]

    def _add_selected(self):
        btx = self._get_selected_btx()
        if btx is None:
            messagebox.showwarning("No selection",
                                   "Please select a transaction in the table first.",
                                   parent=self.frame)
            return
        if btx.status == STATUS_MATCHED:
            if not messagebox.askyesno(
                "Already matched",
                "This transaction appears to already be in your tracker.\n"
                "Add it anyway?",
                parent=self.frame,
            ):
                return
        self._do_add_one(btx)

    def _do_add_one(self, btx: BankTransaction):
        """Read the quick-add form and add the transaction to state."""
        date_str = self._add_date_var.get().strip()
        amount_str = self._add_amount_var.get().strip()
        cat = self._add_cat_var.get().strip()
        desc = self._add_desc_var.get().strip()
        tx_type = self._add_type_var.get()

        # Validate
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid date",
                                 "Date must be in YYYY-MM-DD format.",
                                 parent=self.frame)
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid amount",
                                 "Amount must be a positive number.",
                                 parent=self.frame)
            return
        if not cat:
            messagebox.showerror("No category",
                                 "Please select a category.",
                                 parent=self.frame)
            return

        self.state.add_transaction(tx_type, date_str, amount, cat, desc or btx.payee)
        self.on_data_changed()

        # Mark as matched in our local list so the display updates
        btx.status = STATUS_MATCHED
        btx.match_confidence = "manual"

        self._update_stats()
        self._apply_filter()

        messagebox.showinfo("Added",
                            f"{tx_type} of €{amount:.2f} on {date_str} added.",
                            parent=self.frame)

    def _add_all_missing(self):
        missing = [t for t in self._bank_txns if t.status == STATUS_MISSING]
        if not missing:
            messagebox.showinfo("Nothing to add",
                                "No missing transactions found.",
                                parent=self.frame)
            return

        answer = messagebox.askyesno(
            "Add all missing",
            f"This will add {len(missing)} missing transaction(s) using the "
            f"suggested categories and the payee name as description.\n\n"
            f"Continue?",
            parent=self.frame,
        )
        if not answer:
            return

        added = 0
        for t in missing:
            cat = t.suggested_category
            if not cat or cat not in self.state.categories.get(t.tx_type, []):
                cats = self.state.categories.get(t.tx_type, ["Other"])
                cat = cats[-1]
            desc = t.payee if t.payee else t.purpose
            self.state.add_transaction(
                t.tx_type, t.date, abs(t.amount), cat, desc[:60])
            t.status = STATUS_MATCHED
            t.match_confidence = "bulk_import"
            added += 1

        self.on_data_changed()
        self._update_stats()
        self._apply_filter()
        messagebox.showinfo("Done",
                            f"Added {added} transaction(s) to the tracker.",
                            parent=self.frame)