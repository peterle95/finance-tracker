import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from ...services.asset_tracking_service import (
    record_asset_snapshot, 
    get_asset_snapshots, 
    get_current_net_worth, 
    get_net_worth_change, 
    delete_snapshot, 
    generate_net_worth_report,
    get_asset_allocation_data
)

class NetWorthTab:
    def __init__(self, notebook, state):
        self.state = state
        self.canvas = None
        self.chart_type = "net_worth"  # "net_worth" or "allocation"

        main = ttk.Frame(notebook, padding="10")
        notebook.add(main, text="Net Worth")
        main.rowconfigure(2, weight=1)
        main.columnconfigure(0, weight=1)
        
        # Current status section
        status_frame = ttk.LabelFrame(main, text="Current Net Worth", padding="10")
        status_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="", font=('Arial', 12, 'bold'))
        self.status_label.pack()
        
        self.change_label = ttk.Label(status_frame, text="", font=('Arial', 10))
        self.change_label.pack(pady=(5, 0))
        
        # Controls section
        controls = ttk.Frame(main)
        controls.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        
        # Left side - snapshot recording
        left_controls = ttk.LabelFrame(controls, text="Record Snapshot", padding="10")
        left_controls.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        snapshot_form = ttk.Frame(left_controls)
        snapshot_form.pack(fill='x')
        
        ttk.Label(snapshot_form, text="Date:").pack(side='left', padx=(0, 5))
        self.snapshot_date_entry = ttk.Entry(snapshot_form, width=12)
        self.snapshot_date_entry.insert(0, date.today().strftime('%Y-%m-%d'))
        self.snapshot_date_entry.pack(side='left', padx=(0, 5))
        
        ttk.Label(snapshot_form, text="Note:").pack(side='left', padx=(10, 5))
        self.snapshot_note_entry = ttk.Entry(snapshot_form, width=20)
        self.snapshot_note_entry.pack(side='left', padx=(0, 5))
        
        ttk.Button(snapshot_form, text="Record Snapshot", 
                  command=self.record_snapshot).pack(side='left', padx=(10, 0))
        
        # Right side - chart controls
        right_controls = ttk.LabelFrame(controls, text="Visualization", padding="10")
        right_controls.pack(side='right', fill='x', expand=True, padx=(5, 0))
        
        chart_form = ttk.Frame(right_controls)
        chart_form.pack(fill='x')
        
        ttk.Label(chart_form, text="Chart Type:").pack(side='left', padx=(0, 5))
        
        self.chart_type_var = tk.StringVar(value="net_worth")
        ttk.Radiobutton(chart_form, text="Net Worth Over Time", 
                       variable=self.chart_type_var, value="net_worth",
                       command=self.generate_chart).pack(side='left', padx=5)
        ttk.Radiobutton(chart_form, text="Asset Allocation", 
                       variable=self.chart_type_var, value="allocation",
                       command=self.generate_chart).pack(side='left', padx=5)
        ttk.Radiobutton(chart_form, text="Asset Breakdown", 
                       variable=self.chart_type_var, value="breakdown",
                       command=self.generate_chart).pack(side='left', padx=5)
        
        ttk.Button(chart_form, text="Refresh", 
                  command=self.generate_chart).pack(side='left', padx=(10, 0))
        
        # Main content area
        content = ttk.Frame(main)
        content.grid(row=2, column=0, sticky='nsew')
        content.rowconfigure(0, weight=1)
        content.columnconfigure(0, weight=2)
        content.columnconfigure(1, weight=1)
        
        # Left - Chart
        chart_frame = ttk.LabelFrame(content, text="Visualization", padding="10")
        chart_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        chart_frame.rowconfigure(0, weight=1)
        chart_frame.columnconfigure(0, weight=1)
        
        self.chart_container = ttk.Frame(chart_frame)
        self.chart_container.grid(row=0, column=0, sticky='nsew')
        
        # Right - Snapshots list
        right_frame = ttk.LabelFrame(content, text="Snapshot History", padding="10")
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 0))
        right_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)
        
        # Snapshots tree
        tree_frame = ttk.Frame(right_frame)
        tree_frame.grid(row=0, column=0, sticky='nsew')
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        
        columns = ('Date', 'Net Worth', 'Change')
        self.snapshots_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=10)
        self.snapshots_tree.heading('Date', text='Date')
        self.snapshots_tree.heading('Net Worth', text='Net Worth')
        self.snapshots_tree.heading('Change', text='Change')
        
        self.snapshots_tree.column('Date', width=100)
        self.snapshots_tree.column('Net Worth', width=120, anchor='e')
        self.snapshots_tree.column('Change', width=100, anchor='e')
        
        self.snapshots_tree.grid(row=0, column=0, sticky='nsew')
        
        scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.snapshots_tree.yview)
        scroll.grid(row=0, column=1, sticky='ns')
        self.snapshots_tree.configure(yscrollcommand=scroll.set)
        
        # Buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=1, column=0, sticky='ew', pady=(10, 0))
        
        ttk.Button(button_frame, text="Delete Selected", 
                  command=self.delete_selected_snapshot).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Generate Report", 
                  command=self.show_report).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Export Report", 
                  command=self.export_report).pack(side='left', padx=5)
        
        # Initialize
        self.refresh()

    def refresh(self):
        """Refresh all data and displays"""
        self.update_status()
        self.refresh_snapshots_tree()
        self.generate_chart()

    def update_status(self):
        """Update the current net worth display"""
        current = get_current_net_worth(self.state)
        
        # Color code based on positive/negative
        color = 'green' if current >= 0 else 'red'
        self.status_label.config(text=f"€{current:,.2f}", foreground=color)
        
        # Show 1-month change
        change_data, error = get_net_worth_change(self.state, 1)
        if change_data:
            change = change_data['change']
            change_pct = change_data['change_pct']
            sign = "+" if change >= 0 else ""
            color = 'green' if change >= 0 else 'red'
            
            text = f"1-month change: {sign}€{change:,.2f} ({sign}{change_pct:.1f}%)"
            self.change_label.config(text=text, foreground=color)
        else:
            self.change_label.config(text="No historical data for comparison", foreground='gray')

    def refresh_snapshots_tree(self):
        """Refresh the snapshots tree view"""
        for item in self.snapshots_tree.get_children():
            self.snapshots_tree.delete(item)
        
        snapshots = get_asset_snapshots(self.state)
        
        for i, snapshot in enumerate(snapshots):
            net_worth = snapshot['net_worth']
            
            # Calculate change from previous
            if i > 0:
                prev_net_worth = snapshots[i-1]['net_worth']
                change = net_worth - prev_net_worth
                sign = "+" if change >= 0 else ""
                change_str = f"{sign}€{change:,.2f}"
            else:
                change_str = "—"
            
            self.snapshots_tree.insert('', 'end', values=(
                snapshot['date'],
                f"€{net_worth:,.2f}",
                change_str
            ))

    def record_snapshot(self):
        """Record a new asset snapshot"""
        try:
            snapshot_date = self.snapshot_date_entry.get()
            datetime.strptime(snapshot_date, '%Y-%m-%d')
            
            note = self.snapshot_note_entry.get().strip()
            
            snapshot = record_asset_snapshot(self.state, snapshot_date, note)
            self.state.save()
            
            messagebox.showinfo("Success", 
                              f"Snapshot recorded for {snapshot_date}\n"
                              f"Net Worth: €{snapshot['net_worth']:,.2f}")
            
            self.snapshot_note_entry.delete(0, tk.END)
            self.snapshot_date_entry.delete(0, tk.END)
            self.snapshot_date_entry.insert(0, date.today().strftime('%Y-%m-%d'))
            
            self.refresh()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")

    def delete_selected_snapshot(self):
        """Delete the selected snapshot"""
        selected = self.snapshots_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a snapshot to delete.")
            return
        
        values = self.snapshots_tree.item(selected[0])['values']
        snapshot_date = values[0]
        
        if not messagebox.askyesno("Confirm Delete", 
                                 f"Delete snapshot from {snapshot_date}?"):
            return
        
        delete_snapshot(self.state, snapshot_date)
        self.state.save()
        self.refresh()

    def generate_chart(self):
        """Generate the selected chart type"""
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        
        chart_type = self.chart_type_var.get()
        
        if chart_type == "net_worth":
            self._generate_net_worth_chart()
        elif chart_type == "allocation":
            self._generate_allocation_chart()
        elif chart_type == "breakdown":
            self._generate_breakdown_chart()

    def _generate_net_worth_chart(self):
        """Generate net worth over time line chart"""
        snapshots = get_asset_snapshots(self.state)
        
        if not snapshots:
            # Show message
            label = ttk.Label(self.chart_container, 
                            text="No snapshots recorded yet.\nRecord your first snapshot to see the chart!",
                            font=('Arial', 11), foreground='gray')
            label.pack(expand=True)
            return
        
        # Add current as the latest point if not today
        current_date = date.today().strftime('%Y-%m-%d')
        if not snapshots or snapshots[-1]['date'] != current_date:
            current_snapshot = {
                'date': current_date,
                'net_worth': get_current_net_worth(self.state),
                'note': 'Current'
            }
            snapshots = snapshots + [current_snapshot]
        
        dates = [datetime.strptime(s['date'], '%Y-%m-%d') for s in snapshots]
        net_worths = [s['net_worth'] for s in snapshots]
        
        fig = Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        # Plot line
        ax.plot(dates, net_worths, marker='o', linewidth=2, markersize=6, color='steelblue')
        
        # Fill area - handle positive and negative separately
        ax.fill_between(dates, net_worths, 0, where=[nw >= 0 for nw in net_worths], 
                       alpha=0.3, color='green', interpolate=True)
        ax.fill_between(dates, net_worths, 0, where=[nw < 0 for nw in net_worths], 
                       alpha=0.3, color='red', interpolate=True)
        
        # Add horizontal line at 0
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
        
        ax.set_title('Net Worth Over Time', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Net Worth (€)')
        
        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'€{x:,.0f}'))
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate(rotation=45)
        
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

    def _generate_allocation_chart(self):
        """Generate current asset allocation pie chart"""
        bs = self.state.budget_settings
        
        # Get all assets (including negative ones)
        assets = {
            'Bank Account': bs.get('bank_account_balance', 0),
            'Wallet': bs.get('wallet_balance', 0),
            'Savings': bs.get('savings_balance', 0),
            'Investments': bs.get('investment_balance', 0),
            'Money Lent': bs.get('money_lent_balance', 0)
        }
        
        total = sum(assets.values())
        
        # Filter to only positive assets for pie chart
        positive_assets = {k: v for k, v in assets.items() if v > 0}
        negative_assets = {k: v for k, v in assets.items() if v < 0}
        
        if not positive_assets:
            label = ttk.Label(self.chart_container, 
                            text="No positive assets to display.\n\n"
                                 "Pie charts can only show positive values.\n"
                                 "Add some positive balances in Budget Report tab!",
                            font=('Arial', 11), foreground='gray')
            label.pack(expand=True)
            return
        
        labels = list(positive_assets.keys())
        sizes = list(positive_assets.values())
        
        fig = Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        wedges, texts, autotexts = ax.pie(sizes, autopct='%1.1f%%', startangle=140,
                                          textprops=dict(color="w"))
        
        ax.axis('equal')
        
        # Build title with warning if there are negative assets
        title = f'Asset Allocation (Positive Assets Only)\nTotal Positive: €{sum(sizes):,.2f}'
        if negative_assets:
            total_negative = sum(negative_assets.values())
            title += f'\n⚠️ Negative Assets: €{total_negative:,.2f} (not shown in chart)'
        
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.legend(wedges, labels, title="Assets", loc="center left", 
                 bbox_to_anchor=(1, 0, 0.5, 1))
        
        plt.setp(autotexts, size=9, weight="bold")
        
        # Add text box showing negative assets if any
        if negative_assets:
            negative_text = "Negative Assets:\n" + "\n".join(
                [f"{k}: €{v:,.2f}" for k, v in negative_assets.items()]
            )
            ax.text(0.02, 0.02, negative_text, transform=ax.transAxes,
                   fontsize=9, verticalalignment='bottom',
                   bbox=dict(boxstyle='round', facecolor='#ffcccc', alpha=0.8))
        
        fig.tight_layout()
        
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

    def _generate_breakdown_chart(self):
        """Generate asset breakdown over time stacked area chart"""
        snapshots = get_asset_snapshots(self.state)
        
        if not snapshots:
            label = ttk.Label(self.chart_container, 
                            text="No snapshots recorded yet.\nRecord your first snapshot to see the chart!",
                            font=('Arial', 11), foreground='gray')
            label.pack(expand=True)
            return
        
        dates = [datetime.strptime(s['date'], '%Y-%m-%d') for s in snapshots]
        
        # Extract each asset type
        bank = [s['bank_balance'] for s in snapshots]
        wallet = [s['wallet_balance'] for s in snapshots]
        savings = [s['savings_balance'] for s in snapshots]
        investments = [s['investment_balance'] for s in snapshots]
        money_lent = [s['money_lent_balance'] for s in snapshots]
        
        fig = Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        # For stacked area chart, we need to handle negative values differently
        # We'll plot each asset as a separate line instead when there are negatives
        has_negatives = any(
            any(val < 0 for val in asset_list) 
            for asset_list in [bank, wallet, savings, investments, money_lent]
        )
        
        if has_negatives:
            # Plot as lines instead of stacked area
            ax.plot(dates, bank, label='Bank', marker='o', markersize=4, linewidth=2)
            ax.plot(dates, wallet, label='Wallet', marker='s', markersize=4, linewidth=2)
            ax.plot(dates, savings, label='Savings', marker='^', markersize=4, linewidth=2)
            ax.plot(dates, investments, label='Investments', marker='d', markersize=4, linewidth=2)
            ax.plot(dates, money_lent, label='Money Lent', marker='*', markersize=4, linewidth=2)
            
            # Add horizontal line at 0
            ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
            
            ax.set_title('Asset Breakdown Over Time\n(Line chart used due to negative values)', 
                        fontsize=12, fontweight='bold')
        else:
            # Original stacked area chart for all positive values
            ax.stackplot(dates, bank, wallet, savings, investments, money_lent,
                        labels=['Bank', 'Wallet', 'Savings', 'Investments', 'Money Lent'],
                        alpha=0.8)
            ax.set_title('Asset Breakdown Over Time', fontsize=14, fontweight='bold')
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Amount (€)')
        
        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'€{x:,.0f}'))
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate(rotation=45)
        
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

    def show_report(self):
        """Show the net worth report in a dialog"""
        report = generate_net_worth_report(self.state)
        
        report_win = tk.Toplevel()
        report_win.title("Net Worth Report")
        report_win.geometry("700x600")
        
        # Text widget for report
        text_frame = ttk.Frame(report_win)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        text = tk.Text(text_frame, wrap='word', font=('Courier New', 10))
        text.insert('1.0', report)
        text.config(state='disabled')
        
        scroll = ttk.Scrollbar(text_frame, orient='vertical', command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        
        scroll.pack(side='right', fill='y')
        text.pack(side='left', fill='both', expand=True)
        
        # Buttons
        button_frame = ttk.Frame(report_win)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Close", 
                  command=report_win.destroy).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Export to File", 
                  command=lambda: self.export_report(report)).pack(side='right', padx=5)
    
    def export_report(self, report_text=None):
        """Export the net worth report to a text file"""
        if report_text is None:
            report_text = generate_net_worth_report(self.state)
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Net Worth Report As"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(report_text)
                messagebox.showinfo("Success", f"Report saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save report: {str(e)}")
