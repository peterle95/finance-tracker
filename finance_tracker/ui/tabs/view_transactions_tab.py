import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class ViewTransactionsTab:
    def __init__(self, notebook, state, on_data_changed):
        self.state = state
        self.on_data_changed = on_data_changed

        frame = ttk.Frame(notebook, padding="20")
        notebook.add(frame, text="View Transactions")
        self.frame = frame

        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill='x', pady=10)

        ttk.Label(filter_frame, text="Filter by month:").pack(side='left', padx=5)
        self.month_filter = ttk.Entry(filter_frame, width=15)
        self.month_filter.insert(0, datetime.now().strftime("%Y-%m"))
        self.month_filter.pack(side='left', padx=5)
        ttk.Button(filter_frame, text="Refresh", command=self.refresh).pack(side='left', padx=10)

        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill='both', expand=True, pady=10)

        columns = ('ID', 'Date', 'Type', 'Amount', 'Category', 'Description')
        self.transaction_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        for col in columns:
            self.transaction_tree.heading(col, text=col)
            width = 120
            if col == 'Amount': width = 100
            if col == 'Description': width = 250
            if col == 'Type': width = 80
            self.transaction_tree.column(col, width=width, anchor='w')

        self.transaction_tree.column('ID', width=0, stretch=tk.NO)
        self.transaction_tree.tag_configure('expense', foreground='red')
        self.transaction_tree.tag_configure('income', foreground='green')
        self.transaction_tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.transaction_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.transaction_tree.configure(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill='x', pady=5)
        spacer = ttk.Frame(button_frame)
        spacer.pack(side='left', expand=True, fill='x')
        ttk.Button(button_frame, text="Modify Selected", command=self.open_modify_window).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_transaction).pack(side='left')

        self.summary_label = ttk.Label(frame, text="", font=('Arial', 10, 'bold'))
        self.summary_label.pack(pady=10, fill='x')

        self.refresh()

    def refresh(self):
        for item in self.transaction_tree.get_children():
            self.transaction_tree.delete(item)
        filter_month = self.month_filter.get()
        all_transactions = []
        for e in self.state.expenses:
            if e['date'].startswith(filter_month):
                all_transactions.append({**e, 'type': 'Expense'})
        for i in self.state.incomes:
            if i['date'].startswith(filter_month):
                all_transactions.append({**i, 'type': 'Income'})
        all_transactions.sort(key=lambda x: x['date'])

        for trans in all_transactions:
            tag = 'expense' if trans['type'] == 'Expense' else 'income'
            trans_id = trans.get('id', '')
            self.transaction_tree.insert('', 'end', values=(
                trans_id, trans['date'], trans['type'], f"€{trans['amount']:.2f}",
                trans['category'], trans['description']), tags=(tag,))
        self.update_summary()

    def update_summary(self):
        fm = self.month_filter.get()
        base_income = self.state.budget_settings.get('monthly_income', 0)
        total_flex_income = sum(i['amount'] for i in self.state.incomes if i['date'].startswith(fm))
        total_income = base_income + total_flex_income

        total_flex_expenses = sum(e['amount'] for e in self.state.expenses if e['date'].startswith(fm))
        total_fixed_costs = sum(fc['amount'] for fc in self.state.budget_settings.get('fixed_costs', []))
        total_expenses = total_flex_expenses + total_fixed_costs
        net = total_income - total_expenses

        self.summary_label.config(text=(f"Total Income: €{total_income:.2f}  |  "
                                        f"Total Expenses: €{total_expenses:.2f}  |  "
                                        f"Flexible Costs Incurred: €{total_flex_expenses:.2f}  |  "
                                        f"Net: €{net:.2f}"))

    def delete_transaction(self):
        selected = self.transaction_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a transaction to delete.")
            return
        if not messagebox.askyesno("Confirm", "Are you sure you want to delete the selected transaction?"):
            return

        v = self.transaction_tree.item(selected[0])['values']
        trans_id = v[0]
        trans_type = v[2]
        if trans_id:
            ok = self.state.delete_transaction_by_id(trans_type, trans_id)
            if not ok:
                messagebox.showerror("Error", "Could not delete the transaction.")
        else:
            # Legacy no-id fallback
            date_str, _, amount_str, category, desc = v[1:]
            target = self.state.expenses if trans_type == "Expense" else self.state.incomes
            try:
                target.remove({
                    'date': date_str,
                    'amount': float(amount_str.replace('€', '')),
                    'category': category,
                    'description': desc
                })
                self.state.save()
            except ValueError:
                messagebox.showerror("Error", "Could not delete the transaction (fallback failed).")
                return
        self.on_data_changed()

    def open_modify_window(self):
        selected = self.transaction_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a transaction to modify.")
            return
        values = self.transaction_tree.item(selected[0])['values']
        trans_id = values[0]

        original = None
        original_list_name = None
        for t in self.state.expenses:
            if t.get('id') == trans_id:
                original = t
                original_list_name = "Expense"
                break
        if not original:
            for t in self.state.incomes:
                if t.get('id') == trans_id:
                    original = t
                    original_list_name = "Income"
                    break
        if not original:
            messagebox.showerror("Error", "Could not find the selected transaction in the data.")
            return

        win = tk.Toplevel(self.frame)
        win.title("Modify Transaction")
        win.transient(self.frame)
        win.grab_set()
        from ..style import configure_toplevel
        configure_toplevel(win)

        form = ttk.Frame(win, padding="20")
        form.pack(fill='both', expand=True)

        ttk.Label(form, text="Transaction Type:").grid(row=0, column=0, sticky='w', pady=10)
        mod_type_var = tk.StringVar(value=original_list_name)
        type_frame = ttk.Frame(form)
        type_frame.grid(row=0, column=1, sticky='w', pady=5)

        mod_category_var = tk.StringVar(value=original.get('category', ''))
        mod_category_combo = ttk.Combobox(form, textvariable=mod_category_var, width=28, state='readonly')

        def update_mod_cats():
            cats = self.state.categories.get(mod_type_var.get(), [])
            mod_category_combo.config(values=cats)
            if mod_category_var.get() in cats:
                mod_category_combo.set(mod_category_var.get())
            else:
                mod_category_combo.set(cats[0] if cats else "")

        ttk.Radiobutton(type_frame, text="Expense", variable=mod_type_var, value="Expense",
                        command=update_mod_cats).pack(side='left', padx=5)
        ttk.Radiobutton(type_frame, text="Income", variable=mod_type_var, value="Income",
                        command=update_mod_cats).pack(side='left', padx=5)

        ttk.Label(form, text="Date:").grid(row=1, column=0, sticky='w', pady=5)
        mod_date_entry = ttk.Entry(form, width=30)
        mod_date_entry.insert(0, original.get('date', ''))
        mod_date_entry.grid(row=1, column=1, pady=5, sticky='w')

        ttk.Label(form, text="Amount:").grid(row=2, column=0, sticky='w', pady=5)
        mod_amount_entry = ttk.Entry(form, width=30)
        mod_amount_entry.insert(0, original.get('amount', ''))
        mod_amount_entry.grid(row=2, column=1, pady=5, sticky='w')

        ttk.Label(form, text="Category:").grid(row=3, column=0, sticky='w', pady=5)
        mod_category_combo.grid(row=3, column=1, pady=5, sticky='w')
        update_mod_cats()

        ttk.Label(form, text="Description:").grid(row=4, column=0, sticky='w', pady=5)
        mod_desc_entry = ttk.Entry(form, width=30)
        mod_desc_entry.insert(0, original.get('description', ''))
        mod_desc_entry.grid(row=4, column=1, pady=5, sticky='w')

        def save_changes():
            try:
                new_date = mod_date_entry.get()
                datetime.strptime(new_date, "%Y-%m-%d")
                new_amount = float(mod_amount_entry.get())
                new_cat = mod_category_var.get()
                new_desc = mod_desc_entry.get()
                new_type = mod_type_var.get()
                if not new_cat:
                    messagebox.showerror("Error", "Please select a category.", parent=win)
                    return

                # Update existing
                original['date'] = new_date
                original['amount'] = new_amount
                original['category'] = new_cat
                original['description'] = new_desc

                if new_type != original_list_name:
                    source = self.state.expenses if original_list_name == "Expense" else self.state.incomes
                    source.remove(original)
                    (self.state.expenses if new_type == "Expense" else self.state.incomes).append(original)

                self.state.save()
                self.on_data_changed()
                win.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid amount or date format (YYYY-MM-DD).", parent=win)

        ttk.Button(form, text="Save Changes", command=save_changes).grid(row=5, column=1, pady=20, sticky='w')