"""
finance_tracker/ui/tabs/reports_tab.py

Tab for generating and viewing various financial reports and charts.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ...services.report_builder import pie_data, history_data
from ...services.budget_calculator import compute_net_available_for_spending
from ..charts import create_bar_figure, create_pie_figure

class ReportsTab:
    def __init__(self, notebook, state):
        self.state = state
        self.canvas = None
        self.bar_breakdown_mode = "total"  # "total" or "categories"
        self.bar_display_mode = "value"  # "value" or "percentage"

        main = ttk.Frame(notebook, padding="10")
        notebook.add(main, text="Charts")
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
        self.value_type_var = tk.StringVar(value="Total")
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

        # Split view for Chart and Info
        self.paned = ttk.PanedWindow(main, orient='horizontal')
        self.paned.grid(row=1, column=0, sticky='nsew', pady=10)
        
        self.chart_frame = ttk.Frame(self.paned)
        self.paned.add(self.chart_frame, weight=4)
        
        self.info_frame = ttk.LabelFrame(self.paned, text="Details", padding=10)
        self.paned.add(self.info_frame, weight=1)
        
        # Info text widget
        self.info_text = tk.Text(self.info_frame, wrap='word', width=30, height=20, state='disabled', 
                               bg='#f0f0f0', relief='flat', font=('Arial', 10))
        self.info_text.pack(fill='both', expand=True)

        self._toggle_controls()

    def _toggle_controls(self):
        s = self.style_var.get()
        self.pie_controls.pack_forget()
        self.bar_controls.pack_forget()
        self.budget_lines_check.pack_forget()
        if s == "Pie Chart":
            self.pie_controls.pack(side='left', padx=(0, 15))
            self.budget_lines_check.pack(side='left', padx=(0, 15))
            self.budget_lines_check.pack(side='left', padx=(0, 15))
            self._update_info_panel([])
        else:
            self.bar_controls.pack(side='left', padx=(0, 15))
            self._update_info_panel(["Click on chart to toggle: Total/Categories view", 
                                   "Right-click to toggle: Value/Percentage display"])

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
            # Reset to defaults when generating new chart
            self.bar_breakdown_mode = "total"
            self.bar_display_mode = "value"
            self._make_bar()

    def _update_info_panel(self, lines, title="Details"):
        self.info_frame.config(text=title)
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', tk.END)
        if lines:
            for line in lines:
                self.info_text.insert(tk.END, line + "\n\n")
        self.info_text.config(state='disabled')

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

        # Store data for interactive updates
        self.bar_chart_data = {
            'labels': labels,
            'values': values,
            'title': title,
            'num_months': n
        }

        self._render_bar_chart()

    def _render_bar_chart(self):
        """Render the bar chart based on current breakdown and display modes"""
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        labels = self.bar_chart_data['labels']
        title = self.bar_chart_data['title']
        values = self.bar_chart_data['values']
        
        category_data = None
        if self.bar_breakdown_mode == "categories":
            category_data = self._get_category_breakdown_data(labels)
            if not category_data:
                messagebox.showinfo("No Data", "No category data available for breakdown.")
                self.bar_breakdown_mode = "total"
                # Fallback to total view
                category_data = None

        fig = create_bar_figure(labels, values, title, 
                              breakdown_mode=self.bar_breakdown_mode,
                              display_mode=self.bar_display_mode,
                              category_data=category_data)
        
        if not fig:
            return

        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Bind click events
        self.canvas.mpl_connect('button_press_event', self._on_bar_click)

    def _get_category_breakdown_data(self, months):
        """Get category-wise data for each month"""
        chart_type = self.chart_type_var.get()
        data_source = self.state.expenses if chart_type == "Expense" else self.state.incomes
        
        # Get all categories
        categories = self.state.categories.get(chart_type, [])
        
        # Initialize data structure
        category_data = {cat: [0.0] * len(months) for cat in categories}
        
        # Populate data
        for month_idx, month in enumerate(months):
            for item in data_source:
                if item['date'].startswith(month):
                    cat = item['category']
                    if cat in category_data:
                        category_data[cat][month_idx] += item['amount']
        
        # Remove categories with no data
        category_data = {cat: values for cat, values in category_data.items() if sum(values) > 0}
        
        # Add fixed costs or base income if needed
        if chart_type == "Expense" and self.include_fixed_var.get():
            fixed_total = sum(fc['amount'] for fc in self.state.budget_settings.get('fixed_costs', []))
            if fixed_total > 0:
                category_data["Fixed Costs"] = [fixed_total] * len(months)
        elif chart_type == "Income" and self.include_base_var.get():
            base_income = self.state.budget_settings.get('monthly_income', 0)
            if base_income > 0:
                category_data["Base Income"] = [base_income] * len(months)
        
        return category_data

    def _on_bar_click(self, event):
        """Handle click events on the bar chart"""
        if event.inaxes is None:
            return
        
        # Left click: toggle breakdown mode
        if event.button == 1:
            if self.bar_breakdown_mode == "total":
                self.bar_breakdown_mode = "categories"
            else:
                self.bar_breakdown_mode = "total"
            self._render_bar_chart()
        
        # Right click: toggle display mode (only in category view)
        elif event.button == 3:
            if self.bar_breakdown_mode == "categories":
                if self.bar_display_mode == "value":
                    self.bar_display_mode = "percentage"
                else:
                    self.bar_display_mode = "value"
                self._render_bar_chart()

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

        budget_info = []
        if self.show_budget_lines_var.get() and self.chart_type_var.get() == "Expense":
            expense_budgets = self.state.budget_settings.get('category_budgets', {}).get('Expense', {})
            nav = compute_net_available_for_spending(self.state, month)
            for cat in labels:
                pct_limit = expense_budgets.get(cat, 0)
                if pct_limit > 0 and nav > 0:
                    actual = totals.get(cat, 0)
                    budget_amount = (pct_limit / 100.0) * nav
                    used_pct = (actual / budget_amount) * 100 if budget_amount > 0 else 0
                    remaining = max(budget_amount - actual, 0)
                    budget_info.append(f"{cat}:\n{used_pct:.0f}% of budget\nLeft: €{remaining:.2f}")

        if budget_info:
            self._update_info_panel(budget_info, title="Budget Status")
        else:
            self._update_info_panel([], title="Details")

        fig = create_pie_figure(labels, sizes, title, 
                              value_type=self.value_type_var.get())
        
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)