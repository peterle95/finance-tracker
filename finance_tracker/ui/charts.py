"""
finance_tracker/ui/charts.py

This module handles the generation of Matplotlib figures for the application.
It separates the charting logic from the UI tabs.
"""

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import math
from datetime import datetime
import calendar

def create_budget_depletion_figure(state, month_str: str):
    """
    Generate a budget depletion graph showing:
    - Remaining flexible budget over the month (starts high, decreases with spending)
    - Daily available budget target (recalculated each day)
    """
    from ..services.budget_calculator import (
        get_active_monthly_income, 
        get_active_fixed_costs,
        days_in_month_str
    )
    
    try:
        year, month = map(int, month_str.split("-"))
    except ValueError:
        # Return empty figure for invalid month
        fig = Figure(figsize=(8, 2.5), dpi=100)
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, "Invalid month format", ha='center', va='center', transform=ax.transAxes)
        return fig
    
    # Calculate budget parameters
    base_income = get_active_monthly_income(state, month_str)
    daily_savings_goal = state.budget_settings.get("daily_savings_goal", 0)

    # Prepare daily flexible income lookup (moved from sum to daily map)
    flex_incomes_month = [i for i in state.incomes if i['date'].startswith(month_str)]
    daily_incomes = {}
    for i in flex_incomes_month:
        daily_incomes.setdefault(i['date'], 0)
        daily_incomes[i['date']] += i['amount']
    
    fixed_costs = sum(fc["amount"] for fc in get_active_fixed_costs(state, month_str))
    
    days_in_month = calendar.monthrange(year, month)[1]
    monthly_savings_goal = daily_savings_goal * days_in_month
    # Start balance EXCLUDING flexible income (it is now added day-by-day)
    monthly_flexible_budget = base_income - fixed_costs - monthly_savings_goal
    
    # Get daily expenses
    flex_expenses_month = [e for e in state.expenses if e['date'].startswith(month_str)]
    daily_expenses = {}
    for e in flex_expenses_month:
        daily_expenses.setdefault(e['date'], 0)
        daily_expenses[e['date']] += e['amount']
    
    # Calculate daily data
    today = datetime.now().date()
    dates = []
    remaining_budget = []
    daily_target = []
    
    cumulative_balance = monthly_flexible_budget
    
    for day in range(1, days_in_month + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        if date_obj > today:
            break
        
        # Add flexible income for this specific day (creates the "spike")
        day_income = daily_incomes.get(date_str, 0)
        cumulative_balance += day_income
        
        dates.append(date_obj)
        
        # Calculate daily target for this day
        remaining_days = days_in_month - day + 1
        if cumulative_balance <= 0:
            target = 0
        else:
            target = cumulative_balance / remaining_days if remaining_days > 0 else 0
        
        daily_target.append(target)
        
        # Subtract today's spending
        day_spent = daily_expenses.get(date_str, 0)
        cumulative_balance -= day_spent
        remaining_budget.append(cumulative_balance)
    
    # Create figure
    fig = Figure(figsize=(8, 2.5), dpi=100)
    ax = fig.add_subplot(111)
    
    if not dates:
        ax.text(0.5, 0.5, "No data for this month yet", ha='center', va='center', transform=ax.transAxes)
        return fig
    
    # Plot remaining budget line
    ax.plot(dates, remaining_budget, marker='o', linewidth=2, markersize=4, 
            color='steelblue', label='Remaining Budget')
    
    # Fill area under remaining budget
    ax.fill_between(dates, remaining_budget, 0, 
                    where=[rb >= 0 for rb in remaining_budget],
                    alpha=0.2, color='green', interpolate=True)
    ax.fill_between(dates, remaining_budget, 0,
                    where=[rb < 0 for rb in remaining_budget],
                    alpha=0.2, color='red', interpolate=True)
    
    # Plot daily target line
    ax.plot(dates, daily_target, marker='s', linewidth=2, markersize=4,
            color='orange', linestyle='--', label='Daily Target')
    
    # Add horizontal line at 0
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
    
    ax.set_title(f'Budget Depletion - {calendar.month_name[month]} {year}', fontsize=12, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Amount (€)')
    
    # Format y-axis
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'€{x:,.0f}'))
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates) // 10)))
    
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    
    return fig

def create_net_worth_figure(snapshots):
    """Generate net worth over time line chart"""
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
    
    return fig

def create_allocation_figure(positive_assets, negative_assets, total_positive):
    """Generate current asset allocation pie chart"""
    labels = list(positive_assets.keys())
    sizes = list(positive_assets.values())
    
    fig = Figure(figsize=(8, 6), dpi=100)
    ax = fig.add_subplot(111)
    
    wedges, texts, autotexts = ax.pie(sizes, autopct='%1.1f%%', startangle=140,
                                      textprops=dict(color="w"))
    
    ax.axis('equal')
    
    # Build title with warning if there are negative assets
    title = f'Asset Allocation (Positive Assets Only)\nTotal Positive: €{total_positive:,.2f}'
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
    return fig

def create_breakdown_figure(snapshots):
    """Generate asset breakdown over time stacked area chart"""
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
    
    return fig

def create_bar_figure(labels, values, title, breakdown_mode="total", display_mode="value", category_data=None):
    """Render the bar chart based on current breakdown and display modes"""
    fig = Figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(111)

    if breakdown_mode == "total":
        # Show total bars
        ax.bar(labels, values, label="Monthly Totals", color='steelblue')

        if len(values) > 1:
            x = np.arange(len(labels))
            slope, intercept = np.polyfit(x, values, 1)
            trend = slope * x + intercept
            ax.plot(labels, trend, color='red', linestyle='--', label='Trend Line')

        ax.set_title(f"{title} - Total View")
        ax.set_ylabel("Total Amount (€)")
        ax.legend()

    elif breakdown_mode == "flexible":
        # Show grouped bars for flexible income vs costs
        if not category_data:
            return None
        
        x = np.arange(len(labels))
        width = 0.35
        
        income_values = category_data.get("Flexible Income", [0] * len(labels))
        cost_values = category_data.get("Flexible Costs", [0] * len(labels))
        
        if display_mode == "percentage":
            # Convert to percentages (income as 100%, costs as % of income)
            percentage_values = []
            savings_values = []
            for inc, cost in zip(income_values, cost_values):
                if inc > 0:
                    percentage_values.append((cost / inc) * 100)
                    savings_values.append(inc - cost)
                else:
                    percentage_values.append(0 if cost == 0 else 100)
                    savings_values.append(-cost if cost > 0 else 0)
            
            # Color bars based on percentage (green if under 100%, red if over)
            bar_colors = ['#2ecc71' if pct <= 100 else '#e74c3c' for pct in percentage_values]
            bars = ax.bar(labels, percentage_values, color=bar_colors)
            
            # Add descriptive annotations to each bar
            for i, (bar, pct, inc, cost, saving) in enumerate(zip(bars, percentage_values, income_values, cost_values, savings_values)):
                height = bar.get_height()
                # Position text above the bar
                y_pos = height + 2
                
                # Create descriptive text showing costs/income
                desc_text = f"€{cost:.0f}/€{inc:.0f}"
                
                ax.annotate(desc_text,
                           xy=(bar.get_x() + bar.get_width() / 2, y_pos),
                           ha='center', va='bottom',
                           fontsize=8,
                           color='#333333')
            
            # Adjust y-axis to make room for annotations
            max_pct = max(percentage_values) if percentage_values else 100
            ax.set_ylim(0, max(max_pct + 25, 125))
            
            ax.set_title(f"Flexible Costs as % of Flexible Income")
            ax.set_ylabel("Percentage (%)")
        else:
            # Grouped bars showing income and costs side by side
            bars_income = ax.bar(x - width/2, income_values, width, label='Flexible Income', color='#2ecc71')
            bars_costs = ax.bar(x + width/2, cost_values, width, label='Flexible Costs', color='#e74c3c')
            ax.set_xticks(x)
            ax.set_xticklabels(labels)
            ax.set_title(f"Flexible Income vs Flexible Costs")
            ax.set_ylabel("Amount (€)")
            ax.set_ylabel("Amount (€)")
            ax.legend()

    elif breakdown_mode == "over_under":
        # Show grouped bars for Total Income vs Total Expenses
        if not category_data:
            return None
        
        x = np.arange(len(labels))
        width = 0.35
        
        income_values = category_data.get("Total Income", [0] * len(labels))
        expense_values = category_data.get("Total Expenses", [0] * len(labels))
        
        if display_mode == "percentage":
            # Show Net Difference (Income - Expenses)
            diff_values = []
            for inc, exp in zip(income_values, expense_values):
                diff_values.append(inc - exp)
            
            # Color bars based on difference (green if positive, red if negative)
            bar_colors = ['#2ecc71' if d >= 0 else '#e74c3c' for d in diff_values]
            bars = ax.bar(labels, diff_values, color=bar_colors)
            
            # Add horizontal line at 0
            ax.axhline(0, color='black', linewidth=0.8)
            
            # Add descriptive annotations to each bar
            for bar, diff, inc, exp in zip(bars, diff_values, income_values, expense_values):
                height = bar.get_height()
                # Position text above positive bars, below negative bars
                y_pos = height + (max(diff_values) * 0.05 if diff >= 0 else -max(abs(min(diff_values)), 100) * 0.15)
                
                # Format: €{inc} - €{exp} = €{diff}
                sign = "+" if diff >= 0 else ""
                desc_text = f"€{inc:.0f} - €{exp:.0f} = {sign}€{diff:.0f}"
                
                va = 'bottom' if diff >= 0 else 'top'
                
                ax.annotate(desc_text,
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 5 if diff >= 0 else -5),
                           textcoords="offset points",
                           ha='center', va=va,
                           fontsize=8,
                           color='#333333')
            
            # Adjust y-axis to allow room for annotations
            y_max = max(max(diff_values, default=100), 100)
            y_min = min(min(diff_values, default=0), 0)
            range_val = y_max - y_min
            ax.set_ylim(y_min - range_val * 0.2, y_max + range_val * 0.2)
            
            ax.set_title("Net Result (Total Income - Total Expenses)")
            ax.set_ylabel("Net Amount (€)")
        else:
            # Grouped bars showing income and expenses side by side
            bars_income = ax.bar(x - width/2, income_values, width, label='Total Income', color='#2ecc71')
            bars_expenses = ax.bar(x + width/2, expense_values, width, label='Total Expenses', color='#e74c3c')
            ax.set_xticks(x)
            ax.set_xticklabels(labels)
            ax.set_title(f"Total Income vs Total Expenses")
            ax.set_ylabel("Amount (€)")
            ax.legend()

    else:
        # Show stacked bars by category
        if not category_data:
            return None

        categories = list(category_data.keys())
        bottom = np.zeros(len(labels))
        
        # Color palette - use tab20 for more distinct colors
        colors = plt.get_cmap('tab20').colors
        
        for idx, category in enumerate(categories):
            cat_values = category_data[category]
            
            if display_mode == "percentage":
                # Convert to percentages
                total_values = [sum(category_data[cat][i] for cat in categories) for i in range(len(labels))]
                percentages = [cat_values[i] / total_values[i] * 100 if total_values[i] > 0 else 0 
                              for i in range(len(cat_values))]
                ax.bar(labels, percentages, bottom=bottom, label=category, 
                      color=colors[idx % len(colors)])
                bottom += percentages
            else:
                # Show absolute values
                ax.bar(labels, cat_values, bottom=bottom, label=category, 
                      color=colors[idx % len(colors)])
                bottom += cat_values

        if display_mode == "percentage":
            ax.set_title(f"{title} - Category Breakdown (Percentage)")
            ax.set_ylabel("Percentage (%)")
            ax.set_ylim(0, 100)
        else:
            ax.set_title(f"{title} - Category Breakdown (Values)")
            ax.set_ylabel("Amount (€)")
        
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    
    return fig

def create_pie_figure(labels, sizes, title, value_type="Total"):
    """Generate pie chart"""
    fig = Figure(figsize=(8, 6), dpi=100)
    ax = fig.add_subplot(111)

    total = sum(sizes) if sizes else 0
    wedges, _ = ax.pie(sizes, startangle=140, labels=None)

    # Value callouts (leader lines) with collision avoidance
    label_items = []
    for i, w in enumerate(wedges):
        angle = (w.theta2 + w.theta1) / 2.0
        x = math.cos(math.radians(angle))
        y = math.sin(math.radians(angle))
        side = 1 if x >= 0 else -1

        if value_type == "Percentage":
            pct = (sizes[i] / total) * 100 if total else 0
            label = f"{pct:.1f}%"
        else:
            label = f"€{sizes[i]:.2f}"

        label_items.append({
            'label': label,
            'side': side,
            'xy': (x * 0.72, y * 0.72),
            'y': y,
        })

    def _spread(items):
        if not items:
            return
        items.sort(key=lambda it: it['y'])
        min_sep = 0.085
        y_min, y_max = -1.15, 1.15

        # Forward pass
        cur = max(items[0]['y'], y_min)
        items[0]['y_adj'] = cur
        for it in items[1:]:
            cur = max(it['y'], cur + min_sep)
            it['y_adj'] = cur

        # If we overflow the top, shift down
        overflow = items[-1]['y_adj'] - y_max
        if overflow > 0:
            for it in items:
                it['y_adj'] -= overflow

        # Backward pass (to maintain spacing after shift)
        cur = min(items[-1]['y_adj'], y_max)
        items[-1]['y_adj'] = cur
        for it in reversed(items[:-1]):
            cur = min(it['y_adj'], cur - min_sep)
            it['y_adj'] = max(cur, y_min)

    left = [it for it in label_items if it['side'] == -1]
    right = [it for it in label_items if it['side'] == 1]
    _spread(left)
    _spread(right)

    x_text = 1.35
    for it in left + right:
        xt = x_text * it['side']
        yt = it.get('y_adj', it['y'])
        ax.annotate(
            it['label'],
            xy=it['xy'],
            xytext=(xt, yt),
            ha='left' if it['side'] == 1 else 'right',
            va='center',
            arrowprops=dict(arrowstyle='-', connectionstyle='angle3', color='black', lw=0.8),
            fontsize=8,
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor='none', alpha=0.9),
        )

    ax.axis('equal')
    ax.set_title(title)
    
    # Improved legend placement
    ax.legend(wedges, labels, title="Categories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

    fig.tight_layout()
    return fig
 
