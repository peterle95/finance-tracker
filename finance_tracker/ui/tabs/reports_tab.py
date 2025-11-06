import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from ...services.report_builder import pie_data, history_data
from ...services.budget_calculator import compute_net_available_for_spending

class ReportsTab:
    def __init__(self, notebook, state):
        self.state = state
        self.canvas = None

        main = ttk.Frame(notebook, padding="10")
        notebook.add(main, text="Reports")
        main.rowconfigure(1, weight=1)
        main.columnconfigure(0, weight=1)

        controls = ttk.LabelFrame(main, text="Chart Options", padding="10")
        controls.grid(row=0, column=0, sticky='ew', pady=5)

        top = ttk.Frame(controls)
        top.pack(fill='x', expand=True, pady=(0, 10))

        # Chart style
        style_frame = ttk.Frame(top)
        style_frame.pack(side='left', padx=(0, 20))
        ttk.Label(style_frame, text="Chart Style:").pack(side='left')
        self.style_var = tk.StringVar(value="Pie Chart")
        ttk.Radiobutton(style_frame, text="Pie Chart", variable=self.style_var, value="Pie Chart",
                        command=self._toggle_controls).pack(anchor='w')
        ttk.Radiobutton(style_frame, text="Historical Bar Chart", variable=self.style_var, value="Bar Chart",
                        command=self._toggle_controls).pack(anchor='w')

        # Data type
        type_frame = ttk.Frame(top)
        type_frame.pack(side='left', padx=(0, 20))
        ttk.Label(type_frame, text="Data Type:").pack(side='left')
        self.chart_type_var = tk.StringVar(value="Expense")
        ttk.Radiobutton(type_frame, text="Expenses", variable=self.chart_type_var, value="Expense",
                        command=self._toggle_fixed_controls).pack(side='left')
        ttk.Radiobutton(type_frame, text="Incomes", variable=self.chart_type_var, value="Income",
                        command=self._toggle_fixed_controls).pack(side='left', padx=5)

        # Pie controls
        self.pie_controls = ttk.Frame(top)
        self.pie_controls.pack(side='left', padx=(0, 15))
        ttk.Label(self.pie_controls, text="Select Month:").pack(side='left')
        self.month_entry = ttk.Entry(self.pie_controls, width=15)
        from datetime import datetime
        self.month_entry.insert(0, datetime.now().strftime("%Y-%m"))
        self.month_entry.pack(side='left', padx=5)
        ttk.Label(self.pie_controls, text="Display As:").pack(side='left', padx=(10, 0))
        self.value_type_var = tk.StringVar(value="Percentage")
        ttk.Radiobutton(self.pie_controls, text="%", variable=self.value_type_var, value="Percentage").pack(side='left')
        ttk.Radiobutton(self.pie_controls, text="€", variable=self.value_type_var, value="Total").pack(side='left', padx=5)

        # Bar controls
        self.bar_controls = ttk.Frame(top)
        ttk.Label(self.bar_controls, text="Number of Months:").pack(side='left')
        self.months_entry = ttk.Entry(self.bar_controls, width=10)
        self.months_entry.insert(0, "6")
        self.months_entry.pack(side='left', padx=5)

        bottom = ttk.Frame(controls)
        bottom.pack(fill='x', expand=True)

        self.fixed_frame = ttk.Frame(bottom)
        self.fixed_frame.pack(side='left', padx=(0, 15))
        self.include_fixed_var = tk.BooleanVar(value=False)
        self.fixed_check = ttk.Checkbutton(self.fixed_frame, text="Include Fixed Costs", variable=self.include_fixed_var)
        self.include_base_var = tk.BooleanVar(value=False)
        self.base_check = ttk.Checkbutton(self.fixed_frame, text="Include Base Income", variable=self.include_base_var)
        self._toggle_fixed_controls()

        self.show_budget_lines_var = tk.BooleanVar(value=False)
        self.budget_lines_check = ttk.Checkbutton(bottom, text="Show Budget Limits", variable=self.show_budget_lines_var)
        self.budget_lines_check.pack(side='left', padx=(0, 15))

        ttk.Button(bottom, text="Generate Chart", command=self.generate).pack(side='right')

        self.chart_frame = ttk.Frame(main)
        self.chart_frame.grid(row=1, column=0, sticky='nsew', pady=10)

        self._toggle_controls()

    def _toggle_controls(self):
        s = self.style_var.get()
        self.pie_controls.pack_forget()
        self.bar_controls.pack_forget()
        self.budget_lines_check.pack_forget()
        if s == "Pie Chart":
            self.pie_controls.pack(side='left', padx=(0, 15))
            self.budget_lines_check.pack(side='left', padx=(0, 15))
        else:
            self.bar_controls.pack(side='left', padx=(0, 15))

    def _toggle_fixed_controls(self):
        self.fixed_check.pack_forget()
        self.base_check.pack_forget()
        if self.chart_type_var.get() == "Expense":
            self.fixed_check.pack()
        else:
            self.base_check.pack()

    def generate(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        style = self.style_var.get()
        if style == "Pie Chart":
            self._make_pie()
        else:
            self._make_bar()

    def _make_bar(self):
        try:
            n = int(self.months_entry.get())
            if n <= 1:
                messagebox.showerror("Error", "Number of months must be greater than 1.")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid number of months.")
            return

        title, labels, values = history_data(
            self.state, n, self.chart_type_var.get(),
            include_fixed=self.include_fixed_var.get(),
            include_base_income=self.include_base_var.get()
        )
        if not any(values):
            messagebox.showinfo("No Data", "No data to display for the selected period.")
            return

        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        ax.bar(labels, values, label="Monthly Totals")

        if len(values) > 1:
            x = np.arange(len(labels))
            slope, intercept = np.polyfit(x, values, 1)
            trend = slope * x + intercept
            ax.plot(labels, trend, color='red', linestyle='--', label='Trend Line')

        ax.set_title(title)
        ax.set_ylabel("Total Amount (€)")
        ax.legend()
        fig.autofmt_xdate(rotation=45)
        fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

    def _make_pie(self):
        month = self.month_entry.get()
        title, totals = pie_data(
            self.state, month, self.chart_type_var.get(),
            include_fixed=self.include_fixed_var.get(),
            include_base_income=self.include_base_var.get()
        )
        if not totals:
            from tkinter import messagebox
            messagebox.showinfo("No Data", f"No data to display for {month}.")
            return
        labels = list(totals.keys())
        sizes = list(totals.values())

        fig = Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)

        if self.value_type_var.get() == "Percentage":
            autopct = '%1.1f%%'
        else:
            def absolute_value(val):
                a = (val / 100.0) * sum(sizes)
                return f'€{a:.2f}'
            autopct = absolute_value

        wedges, texts, autotexts = ax.pie(sizes, autopct=autopct, startangle=140, textprops=dict(color="w"))
        ax.axis('equal')
        ax.set_title(title)
        ax.legend(wedges, labels, title="Categories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

        from matplotlib import pyplot as plt
        plt.setp(autotexts, size=8, weight="bold")

        if self.show_budget_lines_var.get() and self.chart_type_var.get() == "Expense":
            expense_budgets = self.state.budget_settings.get('category_budgets', {}).get('Expense', {})
            budget_info = []
            nav = compute_net_available_for_spending(self.state, month)
            for cat in labels:
                pct_limit = expense_budgets.get(cat, 0)
                if pct_limit > 0 and nav > 0:
                    actual = totals.get(cat, 0)
                    budget_amount = (pct_limit / 100.0) * nav
                    used_pct = (actual / budget_amount) * 100 if budget_amount > 0 else 0
                    remaining = max(budget_amount - actual, 0)
                    budget_info.append(f"{cat}: {used_pct:.0f}% of budget, left: €{remaining:.2f}")

            if budget_info:
                ax.text(1.5, 0.5, "Budget Status:\n" + "\n".join(budget_info),
                        transform=ax.transAxes, fontsize=9, va='center',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)