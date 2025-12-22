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
from datetime import datetime

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
                
                # Create descriptive text showing costs/income and savings/overspent
                if saving >= 0:
                    desc_text = f"€{cost:.0f}/€{inc:.0f}\nSaved: €{saving:.0f}"
                else:
                    desc_text = f"€{cost:.0f}/€{inc:.0f}\nOver: €{abs(saving):.0f}"
                
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

    if value_type == "Percentage":
        autopct = '%1.1f%%'
    else:
        def absolute_value(val):
            a = (val / 100.0) * sum(sizes)
            return f'€{a:.2f}'
        autopct = absolute_value

    wedges, texts, autotexts = ax.pie(sizes, autopct=autopct, startangle=140, textprops=dict(color="w"))
    ax.axis('equal')
    ax.set_title(title)
    
    # Improved legend placement
    ax.legend(wedges, labels, title="Categories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

    plt.setp(autotexts, size=8, weight="bold")

    fig.tight_layout()
    return fig
