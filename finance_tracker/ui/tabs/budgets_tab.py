import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from ...services.budget_calculator import compute_net_available_for_spending, auto_assign_percentages

class BudgetsTab:
    def __init__(self, notebook, state):
        self.state = state
        self.budget_sliders = {}
        self._slider_lock = False

        main = ttk.Frame(notebook, padding="10")
        notebook.add(main, text="Budgets")
        main.rowconfigure(1, weight=1)
        main.columnconfigure(0, weight=1)

        toolbar = ttk.Frame(main)
        toolbar.grid(row=0, column=0, sticky='ew', pady=(0, 5))
        ttk.Label(toolbar, text="Budget Month (YYYY-MM):").pack(side='left', padx=(0, 5))
        self.month_var = tk.StringVar(value=datetime.now().strftime("%Y-%m"))
        ttk.Entry(toolbar, textvariable=self.month_var, width=10).pack(side='left')
        ttk.Button(toolbar, text="Refresh Amounts", command=self._update_monetary_labels).pack(side='left', padx=10)

        group = ttk.LabelFrame(main, text="Category Budget Limits", padding="10")
        group.grid(row=1, column=0, sticky='nsew')

        self._create_widgets(group)

    def _create_widgets(self, parent):
        parent.rowconfigure(3, weight=1)
        parent.columnconfigure(0, weight=1)

        self.cat_type_var = tk.StringVar(value="Expense")
        type_frame = ttk.Frame(parent)
        type_frame.grid(row=0, column=0, sticky='ew', pady=2)
        ttk.Label(type_frame, text="Type:").pack(side='left')
        ttk.Radiobutton(type_frame, text="Expense", variable=self.cat_type_var, value="Expense",
                        command=self._create_budget_sliders).pack(side='left', padx=5)
        ttk.Radiobutton(type_frame, text="Income", variable=self.cat_type_var, value="Income",
                        command=self._create_budget_sliders).pack(side='left', padx=5)

        manage = ttk.Frame(parent)
        manage.grid(row=1, column=0, sticky='ew', pady=5)
        ttk.Label(manage, text="New Category:").pack(side='left', padx=(0, 5))
        self.new_cat_entry = ttk.Entry(manage, width=20)
        self.new_cat_entry.pack(side='left')
        ttk.Button(manage, text="Add", command=self.add_category).pack(side='left', padx=5)

        ttk.Label(manage, text="Remove Category:").pack(side='left', padx=(10, 5))
        self.remove_cat_combo = ttk.Combobox(manage, width=20, state='readonly')
        self.remove_cat_combo.pack(side='left')
        ttk.Button(manage, text="Remove", command=self.remove_category).pack(side='left', padx=5)

        self.sliders_frame = ttk.Frame(parent)
        self.sliders_frame.grid(row=2, column=0, sticky='nsew', pady=5)

        btns = ttk.Frame(parent)
        btns.grid(row=3, column=0, sticky='ew', pady=5)
        ttk.Button(btns, text="Auto-Assign From Expenses", command=self.auto_assign).pack(side='left', padx=(0, 5))
        ttk.Button(btns, text="Normalize to 100%", command=lambda: (self._normalize_sliders(), self._update_total_percentage_label())).pack(side='left', padx=(0, 10))
        spacer = ttk.Frame(btns)
        spacer.pack(side='left', expand=True, fill='x')
        self.total_pct_label = ttk.Label(btns, text="Total: 0.0%")
        self.total_pct_label.pack(side='left', padx=(0, 10))
        ttk.Button(btns, text="Save Budgets", command=self.save_budgets).pack(side='left', padx=5)

        self._create_budget_sliders()

    def _create_budget_sliders(self):
        for w in self.sliders_frame.winfo_children():
            w.destroy()
        self.budget_sliders = {}

        cat_type = self.cat_type_var.get()
        categories = self.state.categories.get(cat_type, [])
        saved = self.state.budget_settings.get('category_budgets', {}).get(cat_type, {}).copy()

        if not saved:
            if categories:
                even = 100.0 / len(categories)
                for c in categories:
                    saved[c] = even
        else:
            for c in categories:
                if c not in saved:
                    saved[c] = 0.0

        self.remove_cat_combo['values'] = categories

        for c in categories:
            frame = ttk.Frame(self.sliders_frame)
            frame.pack(fill='x', pady=2)

            ttk.Label(frame, text=c, width=15).pack(side='left')
            var = tk.DoubleVar(value=float(saved.get(c, 0)))
            slider = ttk.Scale(frame, from_=0, to=100, orient='horizontal', variable=var,
                               command=lambda v, cat=c: self._on_slider_change(cat, float(v)))
            slider.pack(side='left', fill='x', expand=True, padx=5)
            label = ttk.Label(frame, text=f"{var.get():.1f}%", width=7)
            label.pack(side='left')
            amount_label = ttk.Label(frame, text="€0.00", width=12)
            amount_label.pack(side='left')

            self.budget_sliders[c] = {'var': var, 'slider': slider, 'label': label, 'amount_label': amount_label}

        self._update_monetary_labels()
        self._update_total_percentage_label()

    def _on_slider_change(self, changed_category, new_value):
        if self._slider_lock:
            return
        self._slider_lock = True
        old_value = self.budget_sliders[changed_category]['var'].get()
        self.budget_sliders[changed_category]['var'].set(new_value)
        self.budget_sliders[changed_category]['label'].config(text=f"{new_value:.1f}%")
        self._adjust_other_sliders(changed_category, new_value, old_value)
        self._slider_lock = False
        self._update_monetary_labels()
        self._update_total_percentage_label()

    def _adjust_other_sliders(self, changed_category, new_value, old_value):
        delta = new_value - old_value
        others = {k: v for k, v in self.budget_sliders.items() if k != changed_category}
        other_total = sum(s['var'].get() for s in others.values())
        if other_total > 0:
            for cat, info in others.items():
                cur = info['var'].get()
                adj = delta * (cur / other_total)
                val = max(0, min(100, cur - adj))
                info['var'].set(val)
                info['label'].config(text=f"{val:.1f}%")
        else:
            if len(others) > 0:
                per = delta / len(others)
                for info in others.values():
                    val = max(0, min(100, info['var'].get() - per))
                    info['var'].set(val)
                    info['label'].config(text=f"{val:.1f}%")

    def _normalize_sliders(self):
        total = sum(s['var'].get() for s in self.budget_sliders.values())
        if total == 0:
            return
        if abs(total - 100.0) > 0.01:
            for info in self.budget_sliders.values():
                cur = info['var'].get()
                norm = (cur / total) * 100.0
                info['var'].set(norm)
                info['label'].config(text=f"{norm:.1f}%")
        self._update_monetary_labels()

    def _update_monetary_labels(self):
        month = self.month_var.get()
        nav = compute_net_available_for_spending(self.state, month)
        for _, info in self.budget_sliders.items():
            pct = info['var'].get()
            amount = (pct / 100.0) * nav
            info['amount_label'].config(text=f"€{amount:.2f}")

    def _update_total_percentage_label(self):
        total = sum(s['var'].get() for s in self.budget_sliders.values())
        self.total_pct_label.config(text=f"Total: {total:.1f}%")

    def add_category(self):
        cat_type = self.cat_type_var.get()
        new_cat = self.new_cat_entry.get().strip()
        if not new_cat:
            messagebox.showerror("Error", "Category name cannot be empty.")
            return
        if new_cat.lower() in [c.lower() for c in self.state.categories[cat_type]]:
            messagebox.showwarning("Warning", "This category already exists.")
            return
        self.state.categories[cat_type].append(new_cat)
        self.state.categories[cat_type].sort()
        self.state.save()
        self._create_budget_sliders()
        self.new_cat_entry.delete(0, tk.END)

    def remove_category(self):
        cat_type = self.cat_type_var.get()
        cat = self.remove_cat_combo.get()
        if not cat:
            messagebox.showwarning("Warning", "Please select a category to delete.")
            return
        if cat.lower() == "other":
            messagebox.showerror("Error", "Cannot delete the 'Other' category.")
            return
        if not messagebox.askyesno("Confirm", f"Delete '{cat}'? Existing transactions won't be changed."):
            return
        self.state.categories[cat_type].remove(cat)
        budgets = self.state.budget_settings['category_budgets'].get(cat_type, {})
        if cat in budgets:
            del budgets[cat]
        self.state.save()
        self._create_budget_sliders()

    def save_budgets(self):
        cat_type = self.cat_type_var.get()
        if cat_type not in self.state.budget_settings['category_budgets']:
            self.state.budget_settings['category_budgets'][cat_type] = {}
        for cat, info in self.budget_sliders.items():
            self.state.budget_settings['category_budgets'][cat_type][cat] = float(info['var'].get())
        self.state.save()
        self._create_budget_sliders()
        messagebox.showinfo("Success", "Category budgets have been saved.")

    def auto_assign(self):
        cat_type = self.cat_type_var.get()
        categories = list(self.budget_sliders.keys())
        month = self.month_var.get()
        percentages, msg, overspent = auto_assign_percentages(self.state, month, cat_type, categories)
        if not percentages:
            if msg:
                messagebox.showinfo("Info", msg)
            return
        for cat, pct in percentages.items():
            if cat in self.budget_sliders:
                self.budget_sliders[cat]['var'].set(pct)
                self.budget_sliders[cat]['label'].config(text=f"{pct:.1f}%")
        self._update_monetary_labels()
        self._update_total_percentage_label()
        if overspent:
            messagebox.showwarning("Overspent", msg)
        else:
            messagebox.showinfo("Remaining Budget", msg)