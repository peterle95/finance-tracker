import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
from ...services.goals_service import (
    calculate_goal_progress, 
    estimate_completion_date,
    generate_goals_report,
    calculate_all_goals_summary
)

class GoalsTab:
    def __init__(self, notebook, state):
        self.state = state
        
        main = ttk.Frame(notebook, padding="10")
        notebook.add(main, text="Savings Goals")
        main.rowconfigure(1, weight=1)
        main.columnconfigure(0, weight=1)
        
        # Summary section
        summary_frame = ttk.LabelFrame(main, text="Goals Overview", padding="10")
        summary_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        
        self.summary_label = ttk.Label(summary_frame, text="", font=('Arial', 10))
        self.summary_label.pack()
        
        # Main content area
        content = ttk.Frame(main)
        content.grid(row=1, column=0, sticky='nsew')
        content.rowconfigure(0, weight=1)
        content.columnconfigure(0, weight=2)
        content.columnconfigure(1, weight=1)
        
        # Left side - Goals list with progress bars
        left_frame = ttk.LabelFrame(content, text="Your Goals", padding="10")
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        left_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)
        
        # Goals canvas with scrollbar
        goals_canvas_frame = ttk.Frame(left_frame)
        goals_canvas_frame.grid(row=0, column=0, sticky='nsew')
        goals_canvas_frame.rowconfigure(0, weight=1)
        goals_canvas_frame.columnconfigure(0, weight=1)
        
        self.goals_canvas = tk.Canvas(goals_canvas_frame, highlightthickness=0)
        goals_scrollbar = ttk.Scrollbar(goals_canvas_frame, orient='vertical', command=self.goals_canvas.yview)
        self.goals_canvas.configure(yscrollcommand=goals_scrollbar.set)
        
        self.goals_canvas.grid(row=0, column=0, sticky='nsew')
        goals_scrollbar.grid(row=0, column=1, sticky='ns')
        
        self.goals_container = ttk.Frame(self.goals_canvas)
        self.goals_canvas_window = self.goals_canvas.create_window((0, 0), window=self.goals_container, anchor='nw')
        
        self.goals_container.bind('<Configure>', self._on_goals_frame_configure)
        self.goals_canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Buttons below goals list
        goals_buttons = ttk.Frame(left_frame)
        goals_buttons.grid(row=1, column=0, sticky='ew', pady=(10, 0))
        ttk.Button(goals_buttons, text="Refresh", command=self.refresh_goals).pack(side='left', padx=5)
        ttk.Button(goals_buttons, text="Generate Report", command=self.show_report).pack(side='left', padx=5)
        ttk.Button(goals_buttons, text="Export Report", command=self.export_report).pack(side='left', padx=5)
        
        # Right side - Add/Edit goal form
        right_frame = ttk.LabelFrame(content, text="Add/Edit Goal", padding="10")
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 0))
        
        form = ttk.Frame(right_frame)
        form.pack(fill='both', expand=True)
        
        row = 0
        ttk.Label(form, text="Goal Name:").grid(row=row, column=0, sticky='w', pady=5)
        self.goal_name_entry = ttk.Entry(form, width=25)
        self.goal_name_entry.grid(row=row, column=1, pady=5, sticky='ew')
        
        row += 1
        ttk.Label(form, text="Description:").grid(row=row, column=0, sticky='w', pady=5)
        self.goal_desc_entry = ttk.Entry(form, width=25)
        self.goal_desc_entry.grid(row=row, column=1, pady=5, sticky='ew')
        
        row += 1
        ttk.Label(form, text="Target Amount (€):").grid(row=row, column=0, sticky='w', pady=5)
        self.goal_target_entry = ttk.Entry(form, width=25)
        self.goal_target_entry.grid(row=row, column=1, pady=5, sticky='ew')
        
        row += 1
        ttk.Label(form, text="Current Savings (€):").grid(row=row, column=0, sticky='w', pady=5)
        self.goal_current_entry = ttk.Entry(form, width=25)
        self.goal_current_entry.insert(0, "0")
        self.goal_current_entry.grid(row=row, column=1, pady=5, sticky='ew')
        
        row += 1
        ttk.Label(form, text="Monthly Contribution (€):").grid(row=row, column=0, sticky='w', pady=5)
        self.goal_contribution_entry = ttk.Entry(form, width=25)
        self.goal_contribution_entry.insert(0, "0")
        self.goal_contribution_entry.grid(row=row, column=1, pady=5, sticky='ew')
        ttk.Label(form, text="(optional)", foreground="gray", font=('Arial', 8)).grid(row=row, column=2, sticky='w', padx=2)
        
        row += 1
        ttk.Label(form, text="Priority:").grid(row=row, column=0, sticky='w', pady=5)
        self.goal_priority_var = tk.StringVar(value="Medium")
        priority_frame = ttk.Frame(form)
        priority_frame.grid(row=row, column=1, sticky='w', pady=5)
        for priority in ["High", "Medium", "Low"]:
            ttk.Radiobutton(priority_frame, text=priority, variable=self.goal_priority_var, 
                           value=priority).pack(side='left', padx=2)
        
        row += 1
        ttk.Label(form, text="Category:").grid(row=row, column=0, sticky='w', pady=5)
        self.goal_category_var = tk.StringVar(value="General")
        category_combo = ttk.Combobox(form, textvariable=self.goal_category_var, width=23, state='readonly')
        category_combo['values'] = ["Emergency Fund", "Vacation", "Electronics", "Home", "Vehicle", "Education", "Investment", "Other", "General"]
        category_combo.grid(row=row, column=1, pady=5, sticky='ew')
        
        row += 1
        ttk.Separator(form, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky='ew', pady=10)
        
        row += 1
        buttons_frame = ttk.Frame(form)
        buttons_frame.grid(row=row, column=0, columnspan=2, pady=10)
        ttk.Button(buttons_frame, text="Add Goal", command=self.add_goal).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Update Selected", command=self.update_goal).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Clear Form", command=self.clear_form).pack(side='left', padx=5)
        
        # Selected goal tracking
        self.selected_goal_index = None
        
        # Initialize
        self.refresh_goals()
    
    def _on_goals_frame_configure(self, event=None):
        """Update scrollregion when goals container changes"""
        self.goals_canvas.configure(scrollregion=self.goals_canvas.bbox('all'))
    
    def _on_canvas_configure(self, event):
        """Update the width of the canvas window to match the canvas"""
        self.goals_canvas.itemconfig(self.goals_canvas_window, width=event.width)
    
    def refresh_goals(self):
        """Refresh the goals display"""
        # Clear existing widgets
        for widget in self.goals_container.winfo_children():
            widget.destroy()
        
        # Ensure goals list exists
        if 'savings_goals' not in self.state.budget_settings:
            self.state.budget_settings['savings_goals'] = []
        
        goals = self.state.budget_settings['savings_goals']
        
        if not goals:
            ttk.Label(self.goals_container, text="No goals yet. Create your first goal!", 
                     font=('Arial', 10, 'italic')).pack(pady=20)
        else:
            # Sort goals: active first (by priority), then completed
            active_goals = [g for g in goals if g['current_amount'] < g['target_amount']]
            completed_goals = [g for g in goals if g['current_amount'] >= g['target_amount']]
            
            priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
            active_goals.sort(key=lambda g: priority_order.get(g.get('priority', 'Medium'), 1))
            
            sorted_goals = active_goals + completed_goals
            
            for idx, goal in enumerate(sorted_goals):
                self._create_goal_widget(idx, goal)
        
        # Update summary
        self._update_summary()
        
        # Update canvas
        self.goals_canvas.update_idletasks()
        self._on_goals_frame_configure()
    
    def _create_goal_widget(self, index, goal):
        """Create a widget for a single goal"""
        progress = calculate_goal_progress(goal, goal['current_amount'])
        
        # Main goal frame
        goal_frame = ttk.Frame(self.goals_container, relief='solid', borderwidth=1)
        goal_frame.pack(fill='x', padx=5, pady=5)
        
        # Highlight if completed
        if progress['is_complete']:
            goal_frame.configure(style='Complete.TFrame')
        
        # Header
        header = ttk.Frame(goal_frame)
        header.pack(fill='x', padx=10, pady=(10, 5))
        
        # Goal name and category
        name_frame = ttk.Frame(header)
        name_frame.pack(side='left', fill='x', expand=True)
        
        name_label = ttk.Label(name_frame, text=goal['name'], font=('Arial', 11, 'bold'))
        name_label.pack(side='left')
        
        if goal.get('category'):
            category_label = ttk.Label(name_frame, text=f"  [{goal['category']}]", 
                                      font=('Arial', 9), foreground='gray')
            category_label.pack(side='left')
        
        if goal.get('priority'):
            priority_colors = {'High': 'red', 'Medium': 'orange', 'Low': 'green'}
            priority_label = ttk.Label(header, text=goal['priority'], 
                                      foreground=priority_colors.get(goal['priority'], 'black'),
                                      font=('Arial', 9, 'bold'))
            priority_label.pack(side='right', padx=5)
        
        # Description
        if goal.get('description'):
            desc_label = ttk.Label(goal_frame, text=goal['description'], 
                                  font=('Arial', 9), foreground='gray')
            desc_label.pack(anchor='w', padx=10, pady=(0, 5))
        
        # Amounts
        amounts_frame = ttk.Frame(goal_frame)
        amounts_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(amounts_frame, text=f"€{goal['current_amount']:,.2f} / €{goal['target_amount']:,.2f}",
                 font=('Arial', 10, 'bold')).pack(side='left')
        ttk.Label(amounts_frame, text=f"  (€{progress['remaining']:,.2f} remaining)",
                 font=('Arial', 9), foreground='gray').pack(side='left')
        
        # Progress bar
        progress_frame = ttk.Frame(goal_frame)
        progress_frame.pack(fill='x', padx=10, pady=5)
        
        progress_bar = ttk.Progressbar(progress_frame, length=300, mode='determinate', 
                                      value=progress['progress_pct'])
        progress_bar.pack(side='left', fill='x', expand=True)
        
        progress_label = ttk.Label(progress_frame, text=f"{progress['progress_pct']:.1f}%", 
                                  font=('Arial', 9, 'bold'))
        progress_label.pack(side='left', padx=5)
        
        # Completion estimate
        if not progress['is_complete']:
            daily_savings = self.state.budget_settings.get('daily_savings_goal', 0)
            monthly_income = self.state.budget_settings.get('monthly_income', 0)
            fixed_costs = sum(fc['amount'] for fc in self.state.budget_settings.get('fixed_costs', []))
            
            completion_date, completion_msg = estimate_completion_date(
                goal, daily_savings, monthly_income, fixed_costs
            )
            
            estimate_label = ttk.Label(goal_frame, text=completion_msg, 
                                      font=('Arial', 9, 'italic'), foreground='blue')
            estimate_label.pack(anchor='w', padx=10, pady=(0, 5))
            
            if goal.get('monthly_contribution', 0) > 0:
                contrib_label = ttk.Label(goal_frame, 
                                         text=f"Monthly contribution: €{goal['monthly_contribution']:.2f}",
                                         font=('Arial', 8), foreground='gray')
                contrib_label.pack(anchor='w', padx=10, pady=(0, 5))
        else:
            complete_label = ttk.Label(goal_frame, text="✓ Goal Achieved!", 
                                      font=('Arial', 10, 'bold'), foreground='green')
            complete_label.pack(anchor='w', padx=10, pady=(0, 5))
            
            if goal.get('completion_date'):
                comp_date_label = ttk.Label(goal_frame, 
                                           text=f"Completed: {goal['completion_date']}",
                                           font=('Arial', 8), foreground='gray')
                comp_date_label.pack(anchor='w', padx=10, pady=(0, 5))
        
        # Buttons
        button_frame = ttk.Frame(goal_frame)
        button_frame.pack(fill='x', padx=10, pady=(5, 10))
        
        ttk.Button(button_frame, text="Edit", 
                  command=lambda i=index: self.select_goal(i)).pack(side='left', padx=2)
        ttk.Button(button_frame, text="Add Savings", 
                  command=lambda i=index: self.add_savings_to_goal(i)).pack(side='left', padx=2)
        ttk.Button(button_frame, text="Delete", 
                  command=lambda i=index: self.delete_goal(i)).pack(side='left', padx=2)
        
        if progress['is_complete']:
            ttk.Button(button_frame, text="Archive", 
                      command=lambda i=index: self.archive_goal(i)).pack(side='left', padx=2)
    
    def _update_summary(self):
        """Update the summary label"""
        summary = calculate_all_goals_summary(self.state)
        
        text = (f"Total Goals: {summary['total_goals']} | "
                f"Active: {summary['active_goals']} | "
                f"Completed: {summary['completed_goals']} | "
                f"Total Target: €{summary['total_target']:,.2f} | "
                f"Total Saved: €{summary['total_saved']:,.2f} | "
                f"Overall Progress: {summary['overall_progress']:.1f}%")
        
        self.summary_label.config(text=text)
    
    def add_goal(self):
        """Add a new goal"""
        try:
            name = self.goal_name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a goal name.")
                return
            
            target = float(self.goal_target_entry.get())
            if target <= 0:
                messagebox.showerror("Error", "Target amount must be positive.")
                return
            
            current = float(self.goal_current_entry.get() or 0)
            contribution = float(self.goal_contribution_entry.get() or 0)
            
            goal = {
                'name': name,
                'description': self.goal_desc_entry.get().strip(),
                'target_amount': target,
                'current_amount': current,
                'monthly_contribution': contribution,
                'priority': self.goal_priority_var.get(),
                'category': self.goal_category_var.get(),
                'created_date': date.today().strftime('%Y-%m-%d'),
                'completion_date': None
            }
            
            if 'savings_goals' not in self.state.budget_settings:
                self.state.budget_settings['savings_goals'] = []
            
            self.state.budget_settings['savings_goals'].append(goal)
            self.state.save()
            
            self.clear_form()
            self.refresh_goals()
            messagebox.showinfo("Success", f"Goal '{name}' added successfully!")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid number format in amount fields.")
    
    def select_goal(self, index):
        """Load a goal into the form for editing"""
        goals = self.state.budget_settings.get('savings_goals', [])
        if index >= len(goals):
            return
        
        goal = goals[index]
        self.selected_goal_index = index
        
        self.goal_name_entry.delete(0, tk.END)
        self.goal_name_entry.insert(0, goal['name'])
        
        self.goal_desc_entry.delete(0, tk.END)
        self.goal_desc_entry.insert(0, goal.get('description', ''))
        
        self.goal_target_entry.delete(0, tk.END)
        self.goal_target_entry.insert(0, str(goal['target_amount']))
        
        self.goal_current_entry.delete(0, tk.END)
        self.goal_current_entry.insert(0, str(goal['current_amount']))
        
        self.goal_contribution_entry.delete(0, tk.END)
        self.goal_contribution_entry.insert(0, str(goal.get('monthly_contribution', 0)))
        
        self.goal_priority_var.set(goal.get('priority', 'Medium'))
        self.goal_category_var.set(goal.get('category', 'General'))
    
    def update_goal(self):
        """Update the selected goal"""
        if self.selected_goal_index is None:
            messagebox.showwarning("Warning", "Please select a goal to update.")
            return
        
        try:
            name = self.goal_name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a goal name.")
                return
            
            target = float(self.goal_target_entry.get())
            current = float(self.goal_current_entry.get() or 0)
            contribution = float(self.goal_contribution_entry.get() or 0)
            
            goals = self.state.budget_settings['savings_goals']
            goal = goals[self.selected_goal_index]
            
            # Check if goal was just completed
            was_complete = goal['current_amount'] >= goal['target_amount']
            is_complete = current >= target
            
            goal['name'] = name
            goal['description'] = self.goal_desc_entry.get().strip()
            goal['target_amount'] = target
            goal['current_amount'] = current
            goal['monthly_contribution'] = contribution
            goal['priority'] = self.goal_priority_var.get()
            goal['category'] = self.goal_category_var.get()
            
            if is_complete and not was_complete:
                goal['completion_date'] = date.today().strftime('%Y-%m-%d')
            elif not is_complete:
                goal['completion_date'] = None
            
            self.state.save()
            self.clear_form()
            self.refresh_goals()
            messagebox.showinfo("Success", "Goal updated successfully!")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid number format in amount fields.")
    
    def delete_goal(self, index):
        """Delete a goal"""
        goals = self.state.budget_settings.get('savings_goals', [])
        if index >= len(goals):
            return
        
        goal = goals[index]
        if not messagebox.askyesno("Confirm Delete", 
                                   f"Are you sure you want to delete the goal '{goal['name']}'?"):
            return
        
        del goals[index]
        self.state.save()
        self.clear_form()
        self.refresh_goals()
    
    def archive_goal(self, index):
        """Archive a completed goal"""
        goals = self.state.budget_settings.get('savings_goals', [])
        if index >= len(goals):
            return
        
        goal = goals[index]
        
        if not messagebox.askyesno("Archive Goal", 
                                   f"Archive '{goal['name']}'? This will remove it from the active list."):
            return
        
        # Could implement an archived goals list here
        del goals[index]
        self.state.save()
        self.refresh_goals()
        messagebox.showinfo("Archived", f"Goal '{goal['name']}' has been archived.")
    
    def add_savings_to_goal(self, index):
        """Add an amount to a goal's current savings"""
        goals = self.state.budget_settings.get('savings_goals', [])
        if index >= len(goals):
            return
        
        goal = goals[index]
        
        # Create dialog
        dialog = tk.Toplevel(self.goals_container)
        dialog.title(f"Add Savings to {goal['name']}")
        dialog.geometry("350x200")
        dialog.transient(self.goals_container)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"Add savings to: {goal['name']}", 
                 font=('Arial', 10, 'bold')).pack(pady=10)
        ttk.Label(dialog, text=f"Current: €{goal['current_amount']:.2f} / €{goal['target_amount']:.2f}").pack(pady=5)
        
        amount_frame = ttk.Frame(dialog)
        amount_frame.pack(pady=20)
        ttk.Label(amount_frame, text="Amount to add (€):").pack(side='left', padx=5)
        amount_entry = ttk.Entry(amount_frame, width=15)
        amount_entry.pack(side='left', padx=5)
        amount_entry.focus()
        
        def save_addition():
            try:
                amount = float(amount_entry.get())
                if amount <= 0:
                    messagebox.showerror("Error", "Amount must be positive.", parent=dialog)
                    return
                
                old_amount = goal['current_amount']
                goal['current_amount'] += amount
                
                # Check if goal just completed
                if old_amount < goal['target_amount'] and goal['current_amount'] >= goal['target_amount']:
                    goal['completion_date'] = date.today().strftime('%Y-%m-%d')
                    messagebox.showinfo("Goal Achieved!", 
                                      f"Congratulations! You've reached your goal: {goal['name']}!",
                                      parent=dialog)
                
                self.state.save()
                dialog.destroy()
                self.refresh_goals()
                
            except ValueError:
                messagebox.showerror("Error", "Invalid amount.", parent=dialog)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Add", command=save_addition).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side='left', padx=5)
        
        # Bind Enter key
        amount_entry.bind('<Return>', lambda e: save_addition())
    
    def clear_form(self):
        """Clear the form fields"""
        self.goal_name_entry.delete(0, tk.END)
        self.goal_desc_entry.delete(0, tk.END)
        self.goal_target_entry.delete(0, tk.END)
        self.goal_current_entry.delete(0, tk.END)
        self.goal_current_entry.insert(0, "0")
        self.goal_contribution_entry.delete(0, tk.END)
        self.goal_contribution_entry.insert(0, "0")
        self.goal_priority_var.set("Medium")
        self.goal_category_var.set("General")
        self.selected_goal_index = None
    
    def show_report(self):
        """Show goals report in a new window"""
        report_text = generate_goals_report(self.state)
        
        report_win = tk.Toplevel(self.goals_container)
        report_win.title("Savings Goals Report")
        report_win.geometry("900x700")
        
        main_frame = ttk.Frame(report_win, padding=10)
        main_frame.pack(fill='both', expand=True)
        
        text_widget = tk.Text(main_frame, wrap='word', font=('Courier New', 9))
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side='right', fill='y')
        text_widget.pack(side='left', fill='both', expand=True)
        
        text_widget.insert('1.0', report_text)
        text_widget.config(state='disabled')
        
        button_frame = ttk.Frame(report_win, padding=10)
        button_frame.pack(fill='x')
        ttk.Button(button_frame, text="Export", 
                  command=lambda: self.export_report(report_text)).pack(side='right')
        ttk.Button(button_frame, text="Close", 
                  command=report_win.destroy).pack(side='right', padx=5)
    
    def export_report(self, report_text=None):
        """Export goals report to file"""
        if report_text is None:
            report_text = generate_goals_report(self.state)
        
        if not report_text or report_text.startswith("No savings goals"):
            messagebox.showwarning("Warning", "No goals to export.")
            return
        
        today = datetime.now().strftime("%Y-%m-%d")
        default_filename = f"savings_goals_report_{today}.txt"
        
        path = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".txt",
            filetypes=[("Text Documents", "*.txt"), ("All Files", "*.*")]
        )
        
        if not path:
            return
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(report_text)
            messagebox.showinfo("Success", f"Report successfully exported to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export report.\nError: {e}")