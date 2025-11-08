import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
from ...services.goals_service import (
    calculate_goal_progress, 
    estimate_completion_date,
    generate_goals_report,
    calculate_all_goals_summary,
    get_total_savings_available,
    get_total_allocated,
    get_unallocated_savings,
    validate_allocation,
    auto_distribute_savings
)

class GoalsTab:
    def __init__(self, notebook, state):
        self.state = state
        
        main = ttk.Frame(notebook, padding="10")
        notebook.add(main, text="Savings Goals")
        main.rowconfigure(2, weight=1)
        main.columnconfigure(0, weight=1)
        
        # Savings overview section
        savings_frame = ttk.LabelFrame(main, text="Savings Overview", padding="10")
        savings_frame.grid(row=0, column=0, sticky='ew', pady=(0, 5))
        
        self.savings_overview_label = ttk.Label(savings_frame, text="", font=('Arial', 11, 'bold'))
        self.savings_overview_label.pack()
        
        info_label = ttk.Label(savings_frame, 
                              text="Note: Savings balance is managed in the Budget Report tab. Here you allocate existing savings to goals.",
                              font=('Arial', 8, 'italic'), foreground='gray')
        info_label.pack(pady=(5, 0))
        
        # Summary section
        summary_frame = ttk.LabelFrame(main, text="Goals Summary", padding="10")
        summary_frame.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        
        self.summary_label = ttk.Label(summary_frame, text="", font=('Arial', 10))
        self.summary_label.pack()
        
        # Main content area
        content = ttk.Frame(main)
        content.grid(row=2, column=0, sticky='nsew')
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

        # Mouse wheel scrolling
        self.goals_canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)
        self.goals_canvas.bind_all("<Button-4>", self._on_mouse_wheel)
        self.goals_canvas.bind_all("<Button-5>", self._on_mouse_wheel)
        
        # Buttons below goals list
        goals_buttons = ttk.Frame(left_frame)
        goals_buttons.grid(row=1, column=0, sticky='ew', pady=(10, 0))
        ttk.Button(goals_buttons, text="Refresh", command=self.refresh_goals).pack(side='left', padx=5)
        ttk.Button(goals_buttons, text="Auto-Distribute", command=self.auto_distribute).pack(side='left', padx=5)
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
        ttk.Separator(form, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        
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
    
    def _on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling"""
        # For Windows and MacOS
        if event.num == 5 or event.delta == -120:
            self.goals_canvas.yview_scroll(1, "units")
        if event.num == 4 or event.delta == 120:
            self.goals_canvas.yview_scroll(-1, "units")

    def _on_goals_frame_configure(self, event=None):
        """Update scrollregion when goals container changes"""
        self.goals_canvas.configure(scrollregion=self.goals_canvas.bbox('all'))
    
    def _on_canvas_configure(self, event):
        """Update the width of the canvas window to match the canvas"""
        self.goals_canvas.itemconfig(self.goals_canvas_window, width=event.width)
    
    def _bind_mouse_wheel(self, widget):
        """Recursively bind mouse wheel event to all children"""
        widget.bind("<MouseWheel>", self._on_mouse_wheel)
        widget.bind("<Button-4>", self._on_mouse_wheel)
        widget.bind("<Button-5>", self._on_mouse_wheel)
        for child in widget.winfo_children():
            self._bind_mouse_wheel(child)

    def refresh_goals(self):
        """Refresh the goals display"""
        # Clear existing widgets
        for widget in self.goals_container.winfo_children():
            widget.destroy()
        
        # Ensure goals list exists
        if 'savings_goals' not in self.state.budget_settings:
            self.state.budget_settings['savings_goals'] = []
        
        # Migrate old goals to new format if needed
        goals = self.state.budget_settings['savings_goals']
        for goal in goals:
            if 'allocated_amount' not in goal:
                # Migrate from old 'current_amount' to new 'allocated_amount'
                goal['allocated_amount'] = goal.get('current_amount', 0)
                if 'current_amount' in goal:
                    del goal['current_amount']
        
        if not goals:
            ttk.Label(self.goals_container, text="No goals yet. Create your first goal!", 
                     font=('Arial', 10, 'italic')).pack(pady=20)
        else:
            # Sort goals: active first (by priority), then completed
            active_goals = [g for g in goals if g.get('allocated_amount', 0) < g['target_amount']]
            completed_goals = [g for g in goals if g.get('allocated_amount', 0) >= g['target_amount']]
            
            priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
            active_goals.sort(key=lambda g: priority_order.get(g.get('priority', 'Medium'), 1))
            
            sorted_goals = active_goals + completed_goals
            
            for goal in sorted_goals:
                original_index = goals.index(goal)
                self._create_goal_widget(original_index, goal)
        
        # Update summaries
        self._update_savings_overview()
        self._update_summary()
        
        # Update canvas
        self.goals_canvas.update_idletasks()
        self._on_goals_frame_configure()
    
    def _update_savings_overview(self):
        """Update the savings overview display"""
        total_savings = get_total_savings_available(self.state)
        total_allocated = get_total_allocated(self.state)
        unallocated = get_unallocated_savings(self.state)
        
        text = f"Total Savings: €{total_savings:,.2f}  |  Allocated: €{total_allocated:,.2f}  |  Unallocated: €{unallocated:,.2f}"
        
        self.savings_overview_label.config(text=text)
        
        if unallocated > 0:
            self.savings_overview_label.config(foreground='green')
        elif unallocated < 0:
            self.savings_overview_label.config(foreground='orange')
        else:
            self.savings_overview_label.config(foreground='red')
    
    def _create_goal_widget(self, index, goal):
        """Create a widget for a single goal"""
        progress = calculate_goal_progress(goal, goal.get('allocated_amount', 0))
        
        # Main goal frame
        goal_frame = ttk.Frame(self.goals_container, relief='solid', borderwidth=1)
        goal_frame.pack(fill='x', padx=5, pady=5)
        
        # Bind mouse wheel for scrolling
        self._bind_mouse_wheel(goal_frame)
        
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
        
        allocated = goal.get('allocated_amount', 0)
        ttk.Label(amounts_frame, text=f"€{allocated:,.2f} / €{goal['target_amount']:,.2f}",
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
            monthly_savings = daily_savings * 30
            
            completion_date, completion_msg = estimate_completion_date(goal, monthly_savings)
            
            estimate_label = ttk.Label(goal_frame, text=completion_msg, 
                                      font=('Arial', 9, 'italic'), foreground='blue')
            estimate_label.pack(anchor='w', padx=10, pady=(0, 5))
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
        ttk.Button(button_frame, text="Allocate Savings", 
                  command=lambda i=index: self.allocate_to_goal(i)).pack(side='left', padx=2)
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
            
            goal = {
                'name': name,
                'description': self.goal_desc_entry.get().strip(),
                'target_amount': target,
                'allocated_amount': 0.0,  # Start with 0 allocation
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
            messagebox.showinfo("Success", f"Goal '{name}' added successfully!\nNow allocate savings to this goal.")
            
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
            if target <= 0:
                messagebox.showerror("Error", "Target amount must be positive.")
                return
            
            goals = self.state.budget_settings['savings_goals']
            goal = goals[self.selected_goal_index]
            
            # Check if goal was just completed
            was_complete = goal.get('allocated_amount', 0) >= goal['target_amount']
            is_complete = goal.get('allocated_amount', 0) >= target
            
            goal['name'] = name
            goal['description'] = self.goal_desc_entry.get().strip()
            goal['target_amount'] = target
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
        allocated = goal.get('allocated_amount', 0)
        
        msg = f"Are you sure you want to delete the goal '{goal['name']}'?"
        if allocated > 0:
            msg += f"\n\n€{allocated:.2f} is currently allocated to this goal."
            msg += "\nThis amount will be returned to your unallocated savings."
        
        if not messagebox.askyesno("Confirm Delete", msg):
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
        
        msg = f"Archive '{goal['name']}'?\n\n"
        msg += f"This will remove it from the active list.\n"
        msg += f"The €{goal.get('allocated_amount', 0):.2f} allocated to this goal will remain in your savings."
        
        if not messagebox.askyesno("Archive Goal", msg):
            return
        
        # Could implement an archived goals list here
        del goals[index]
        self.state.save()
        self.refresh_goals()
        messagebox.showinfo("Archived", f"Goal '{goal['name']}' has been archived.")
    
    def allocate_to_goal(self, index):
        """Allocate savings to a specific goal"""
        goals = self.state.budget_settings.get('savings_goals', [])
        if index >= len(goals):
            return
        
        goal = goals[index]
        current_allocation = goal.get('allocated_amount', 0)
        
        # Create dialog
        dialog = tk.Toplevel(self.goals_container)
        dialog.title(f"Allocate Savings to {goal['name']}")
        dialog.geometry("450x450")
        dialog.transient(self.goals_container)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"Allocate savings to: {goal['name']}", 
                 font=('Arial', 11, 'bold')).pack(pady=10)
        
        # Current status
        info_frame = ttk.LabelFrame(dialog, text="Current Status", padding=10)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(info_frame, text=f"Target Amount: €{goal['target_amount']:,.2f}").pack(anchor='w')
        ttk.Label(info_frame, text=f"Currently Allocated: €{current_allocation:,.2f}").pack(anchor='w')
        ttk.Label(info_frame, text=f"Still Needed: €{goal['target_amount'] - current_allocation:,.2f}").pack(anchor='w')
        
        ttk.Separator(info_frame, orient='horizontal').pack(fill='x', pady=5)
        
        total_savings = get_total_savings_available(self.state)
        unallocated = get_unallocated_savings(self.state)
        
        ttk.Label(info_frame, text=f"Total Savings Balance: €{total_savings:,.2f}").pack(anchor='w')
        ttk.Label(info_frame, text=f"Unallocated Savings: €{unallocated:,.2f}", 
                 foreground='blue' if unallocated > 0 else 'red').pack(anchor='w')
        
        # Allocation input
        allocation_frame = ttk.Frame(dialog)
        allocation_frame.pack(pady=20)
        
        ttk.Label(allocation_frame, text="New Total Allocation (€):").grid(row=0, column=0, padx=5, pady=5)
        allocation_entry = ttk.Entry(allocation_frame, width=15)
        allocation_entry.insert(0, str(current_allocation))
        allocation_entry.grid(row=0, column=1, padx=5, pady=5)
        allocation_entry.focus()
        allocation_entry.select_range(0, tk.END)
        
        # Quick allocation buttons
        quick_frame = ttk.LabelFrame(dialog, text="Quick Allocate", padding=5)
        quick_frame.pack(fill='x', padx=20, pady=5)
        
        def set_allocation(amount):
            allocation_entry.delete(0, tk.END)
            allocation_entry.insert(0, f"{amount:.2f}")
        
        button_row = ttk.Frame(quick_frame)
        button_row.pack()
        
        ttk.Button(button_row, text="Max Available", 
                  command=lambda: set_allocation(current_allocation + unallocated)).pack(side='left', padx=2)
        ttk.Button(button_row, text="Complete Goal", 
                  command=lambda: set_allocation(goal['target_amount'])).pack(side='left', padx=2)
        ttk.Button(button_row, text="Clear (€0)", 
                  command=lambda: set_allocation(0)).pack(side='left', padx=2)
        
        status_label = ttk.Label(dialog, text="", foreground='red')
        status_label.pack(pady=5)
        
        def validate_and_save():
            try:
                new_allocation = float(allocation_entry.get())
                
                is_valid, error_msg, available = validate_allocation(self.state, index, new_allocation)
                
                if not is_valid:
                    status_label.config(text=error_msg)
                    return
                
                old_allocation = goal.get('allocated_amount', 0)
                goal['allocated_amount'] = new_allocation
                
                # Check if goal just completed
                was_complete = old_allocation >= goal['target_amount']
                is_complete = new_allocation >= goal['target_amount']
                
                if is_complete and not was_complete:
                    goal['completion_date'] = date.today().strftime('%Y-%m-%d')
                    messagebox.showinfo("Goal Achieved!", 
                                      f"Congratulations! You've reached your goal: {goal['name']}!",
                                      parent=dialog)
                elif not is_complete and was_complete:
                    goal['completion_date'] = None
                
                self.state.save()
                dialog.destroy()
                self.refresh_goals()
                
            except ValueError:
                status_label.config(text="Invalid amount.")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Save", command=validate_and_save).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side='left', padx=5)
        
        # Bind Enter key
        allocation_entry.bind('<Return>', lambda e: validate_and_save())
    
    def auto_distribute(self):
        """Automatically distribute unallocated savings across goals"""
        unallocated = get_unallocated_savings(self.state)
        
        if unallocated <= 0:
            messagebox.showinfo("Info", "No unallocated savings to distribute.")
            return
        
        if not messagebox.askyesno("Auto-Distribute", 
                                   f"Automatically distribute €{unallocated:.2f} across your goals?\n\n"
                                   "This will prioritize high-priority goals and try to complete goals in order."):
            return
        
        success, message = auto_distribute_savings(self.state)
        
        if success:
            self.state.save()
            self.refresh_goals()
            messagebox.showinfo("Success", message)
        else:
            messagebox.showwarning("Cannot Distribute", message)
    
    def clear_form(self):
        """Clear the form fields"""
        self.goal_name_entry.delete(0, tk.END)
        self.goal_desc_entry.delete(0, tk.END)
        self.goal_target_entry.delete(0, tk.END)
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