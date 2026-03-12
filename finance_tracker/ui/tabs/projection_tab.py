"""
finance_tracker/ui/tabs/projection_tab.py

Tab for projecting future financial state based on current trends.
"""

import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from ...services.projection_service import projection_text


class ProjectionTab:
    def __init__(self, notebook, state):
        self.state = state

        main = ttk.Frame(notebook, padding="10")
        notebook.add(main, text="Projection")
        main.rowconfigure(1, weight=1)
        main.columnconfigure(0, weight=1)

        controls = ttk.LabelFrame(main, text="Projection Options", padding="10")
        controls.grid(row=0, column=0, sticky="ew", pady=5)

        ttk.Label(controls, text="Number of months to project:").pack(side="left", padx=5)
        self.months_entry = ttk.Entry(controls, width=8)
        self.months_entry.insert(0, "12")
        self.months_entry.pack(side="left", padx=5)

        self.projection_mode = tk.StringVar(value="target_savings")
        ttk.Label(controls, text="Projection mode:").pack(side="left", padx=(15, 5))
        ttk.Radiobutton(
            controls,
            text="Target savings",
            value="target_savings",
            variable=self.projection_mode,
            command=self._update_mode_controls,
        ).pack(side="left", padx=2)
        ttk.Radiobutton(
            controls,
            text="Net worth month-by-month trend",
            value="net_worth_change",
            variable=self.projection_mode,
            command=self._update_mode_controls,
        ).pack(side="left", padx=2)

        self.analysis_months_label = ttk.Label(controls, text="Months to analyze:")
        self.analysis_months_label.pack(side="left", padx=(15, 5))
        self.analysis_months_entry = ttk.Entry(controls, width=6)
        self.analysis_months_entry.insert(0, "6")
        self.analysis_months_entry.pack(side="left", padx=5)

        ttk.Button(controls, text="Generate Projection", command=self.generate).pack(side="left", padx=20)
        ttk.Button(controls, text="Export Projection", command=self.export).pack(side="left", padx=5)

        self.text = tk.Text(main, height=20, width=90, font=("Courier New", 9))
        self.text.grid(row=1, column=0, sticky="nsew", pady=10)

        self._update_mode_controls()

    def _update_mode_controls(self):
        state = "normal" if self.projection_mode.get() == "net_worth_change" else "disabled"
        self.analysis_months_entry.configure(state=state)

    def generate(self):
        try:
            months = int(self.months_entry.get())
            if months <= 0:
                messagebox.showerror("Error", "Number of months must be positive.")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid number of months.")
            return

        try:
            analysis_months = int(self.analysis_months_entry.get())
            if analysis_months <= 0:
                messagebox.showerror("Error", "Months to analyze must be positive.")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid number of months to analyze.")
            return

        report = projection_text(
            self.state,
            months,
            mode=self.projection_mode.get(),
            history_months=analysis_months,
        )
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", report)

    def export(self):
        content = self.text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Warning", "Please generate a projection before exporting.")
            return

        today = datetime.now().strftime("%Y-%m-%d")
        default_filename = f"bank_projection_{today}.txt"
        path = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".txt",
            filetypes=[("Text Documents", "*.txt"), ("All Files", "*.*")],
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Success", f"Projection successfully exported to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export projection.\nError: {e}")
