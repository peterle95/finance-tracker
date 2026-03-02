"""Tab for importing CSV transactions and reconciling them with tracked transactions."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from ...services.import_reconcile_service import load_csv, map_csv_rows, reconcile_rows, likely_duplicate


class ImportReconcileTab:
    def __init__(self, notebook, state, on_data_changed):
        self.state = state
        self.on_data_changed = on_data_changed
        self.csv_headers = []
        self.csv_rows = []
        self.mapped_rows = []
        self.diff_rows = []

        self.frame = ttk.Frame(notebook, padding="10")
        notebook.add(self.frame, text="Import & Reconcile")

        top = ttk.Frame(self.frame)
        top.pack(fill="x", pady=(0, 8))
        ttk.Button(top, text="Import CSV", command=self.load_csv_file).pack(side="left")
        ttk.Button(top, text="Apply Mapping", command=self.apply_mapping).pack(side="left", padx=5)
        ttk.Button(top, text="Select All Untracked", command=self.select_all_untracked).pack(side="left", padx=5)
        ttk.Button(top, text="Import Selected", command=self.import_selected).pack(side="left", padx=5)

        self.summary_var = tk.StringVar(value="Load a CSV file to begin reconciliation.")
        ttk.Label(self.frame, textvariable=self.summary_var, font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 8))

        map_frame = ttk.LabelFrame(self.frame, text="Column Mapping", padding="8")
        map_frame.pack(fill="x", pady=(0, 8))

        self.map_vars = {k: tk.StringVar(value="") for k in ("date", "amount", "description", "category")}
        for idx, key in enumerate(("date", "amount", "description", "category")):
            ttk.Label(map_frame, text=f"{key.title()} column:").grid(row=0, column=idx * 2, padx=(0, 3), sticky="w")
            combo = ttk.Combobox(map_frame, textvariable=self.map_vars[key], state="readonly", width=16)
            combo.grid(row=0, column=idx * 2 + 1, padx=(0, 10), sticky="w")
            setattr(self, f"{key}_combo", combo)

        opts = ttk.Frame(self.frame)
        opts.pack(fill="x", pady=(0, 8))
        ttk.Label(opts, text="Default category for imported rows:").pack(side="left")
        self.default_category_var = tk.StringVar(value="Other")
        self.default_category_combo = ttk.Combobox(opts, textvariable=self.default_category_var, state="readonly", width=20)
        self.default_category_combo.pack(side="left", padx=5)
        self.default_category_combo["values"] = self.state.categories.get("Expense", ["Other"])

        self.mark_float_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts, text="Mark selected imports as Float", variable=self.mark_float_var).pack(side="left", padx=(15, 5))
        ttk.Label(opts, text="Expected from:").pack(side="left")
        self.expected_from_entry = ttk.Entry(opts, width=20)
        self.expected_from_entry.pack(side="left", padx=5)

        columns = ("select", "state", "date", "amount", "description", "category", "tracked")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings", height=16)
        self.tree.pack(fill="both", expand=True)
        for col, title, width in [
            ("select", "Import", 70), ("state", "Status", 100), ("date", "Date", 100),
            ("amount", "Amount", 90), ("description", "Description", 250),
            ("category", "Category", 120), ("tracked", "Tracked Match", 260),
        ]:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="w")

        self.tree.tag_configure("matched", background="#e8f8e8")
        self.tree.tag_configure("untracked", background="#fff4d6")
        self.tree.tag_configure("orphaned", background="#ffd9d9")
        self.tree.bind("<Double-1>", self.toggle_selected)

    def load_csv_file(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if not path:
            return
        try:
            self.csv_rows = load_csv(path)
        except Exception as exc:
            messagebox.showerror("CSV Error", f"Failed to load CSV: {exc}")
            return
        if not self.csv_rows:
            messagebox.showinfo("No Rows", "CSV file is empty.")
            return

        self.csv_headers = list(self.csv_rows[0].keys())
        for key in self.map_vars:
            combo = getattr(self, f"{key}_combo")
            combo["values"] = [""] + self.csv_headers
            guessed = self._guess_column(key)
            self.map_vars[key].set(guessed)
        self.summary_var.set(f"Loaded {len(self.csv_rows)} CSV rows. Verify mapping and click Apply Mapping.")

    def _guess_column(self, field):
        aliases = {
            "date": ["date", "booking date", "transaction date"],
            "amount": ["amount", "value", "total"],
            "description": ["description", "memo", "name", "details"],
            "category": ["category", "type"],
        }
        for header in self.csv_headers:
            normalized = header.strip().lower()
            if normalized in aliases[field]:
                return header
        return ""

    def apply_mapping(self):
        if not self.csv_rows:
            messagebox.showwarning("No CSV", "Load a CSV first.")
            return

        mapping = {k: v.get() for k, v in self.map_vars.items()}
        if not mapping["date"] or not mapping["amount"] or not mapping["description"]:
            messagebox.showerror("Mapping", "Date, amount and description mappings are required.")
            return

        try:
            self.mapped_rows = map_csv_rows(self.csv_rows, mapping, self.default_category_var.get())
        except Exception as exc:
            messagebox.showerror("Mapping Error", f"Could not map CSV rows: {exc}")
            return

        results = reconcile_rows(self.mapped_rows, self.state)
        self._build_diff_rows(results)
        self.render_diff_rows()

    def _build_diff_rows(self, results):
        self.diff_rows = []
        for item in results["matched"]:
            csv_row = item["csv"]
            tracked = item["tracked"]
            self.diff_rows.append({
                "selected": False,
                "status": "Matched",
                "tag": "matched",
                "csv": csv_row,
                "tracked": tracked,
            })

        for item in results["untracked"]:
            self.diff_rows.append({
                "selected": True,
                "status": "Untracked",
                "tag": "untracked",
                "csv": item["csv"],
                "tracked": None,
            })

        for tracked in results["orphaned"]:
            self.diff_rows.append({
                "selected": False,
                "status": "Orphaned",
                "tag": "orphaned",
                "csv": None,
                "tracked": tracked,
            })

        s = results["summary"]
        self.summary_var.set(
            f"Matched: {s['matched']}  |  Untracked: {s['untracked']}  |  Orphaned manual: {s['orphaned']}"
        )

    def render_diff_rows(self):
        self.tree.delete(*self.tree.get_children())
        for idx, row in enumerate(self.diff_rows):
            if row["csv"]:
                csv_row = row["csv"]
                tracked_text = ""
                if row["tracked"]:
                    t = row["tracked"]
                    tracked_text = f"{t.get('type')} | {t.get('date')} | €{float(t.get('amount', 0)):.2f} | {t.get('description', '')}"
                values = (
                    "☑" if row["selected"] else "☐",
                    row["status"],
                    csv_row.get("date", ""),
                    f"€{float(csv_row.get('amount', 0)):.2f}",
                    csv_row.get("description", ""),
                    csv_row.get("category", ""),
                    tracked_text,
                )
            else:
                t = row["tracked"]
                values = ("☐", row["status"], t.get("date", ""), f"€{float(t.get('amount', 0)):.2f}", t.get("description", ""), t.get("category", ""), "Missing from CSV")
            self.tree.insert("", "end", iid=str(idx), values=values, tags=(row["tag"],))

    def toggle_selected(self, event):
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item or col != "#1":
            return
        row = self.diff_rows[int(item)]
        if row["status"] == "Orphaned":
            return
        row["selected"] = not row["selected"]
        self.render_diff_rows()

    def select_all_untracked(self):
        for row in self.diff_rows:
            if row["status"] == "Untracked":
                row["selected"] = True
        self.render_diff_rows()

    def import_selected(self):
        selected_rows = [r for r in self.diff_rows if r["selected"] and r["csv"]]
        if not selected_rows:
            messagebox.showinfo("Nothing selected", "Select rows to import first.")
            return

        duplicate_warnings = []
        for row in selected_rows:
            duplicate = likely_duplicate(row["csv"], self.state)
            if duplicate:
                duplicate_warnings.append(
                    f"{row['csv']['date']} €{row['csv']['amount']:.2f} {row['csv']['description']}"
                )

        if duplicate_warnings:
            warning_text = "Likely duplicates detected:\n\n" + "\n".join(duplicate_warnings[:8])
            if len(duplicate_warnings) > 8:
                warning_text += f"\n...and {len(duplicate_warnings)-8} more"
            warning_text += "\n\nContinue import?"
            if not messagebox.askyesno("Duplicate warning", warning_text):
                return

        is_float = self.mark_float_var.get()
        expected_from = self.expected_from_entry.get().strip() or None

        for row in selected_rows:
            csv_row = row["csv"]
            category = csv_row.get("category") or self.default_category_var.get()
            float_meta = {}
            if is_float:
                category = "Float"
                float_meta = {
                    "is_float": True,
                    "expected_from": expected_from,
                    "reimbursement_status": "pending",
                    "linked_transaction_id": None,
                }
            self.state.add_transaction(
                "Expense",
                csv_row["date"],
                float(csv_row["amount"]),
                category,
                csv_row.get("description", ""),
                **float_meta,
            )

        messagebox.showinfo("Import Complete", f"Imported {len(selected_rows)} transactions.")
        self.on_data_changed()
        self.apply_mapping()
