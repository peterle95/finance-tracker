"""
finance_tracker/services/asset_tracking_service.py

Service for tracking asset snapshots and calculating net worth.
"""

from datetime import datetime, date
from dateutil.relativedelta import relativedelta

def record_asset_snapshot(state, snapshot_date=None, note=""):
    """Record current asset balances as a snapshot"""
    if snapshot_date is None:
        snapshot_date = date.today().strftime('%Y-%m-%d')
    
    bs = state.budget_settings
    snapshot = {
        'date': snapshot_date,
        'bank_balance': bs.get('bank_account_balance', 0),
        'wallet_balance': bs.get('wallet_balance', 0),
        'savings_balance': bs.get('savings_balance', 0),
        'investment_balance': bs.get('investment_balance', 0),
        'money_lent_balance': bs.get('money_lent_balance', 0),
        'note': note
    }

    # Calculate net worth
    snapshot['net_worth'] = (
        snapshot['bank_balance'] + 
        snapshot['wallet_balance'] + 
        snapshot['savings_balance'] + 
        snapshot['investment_balance'] + 
        snapshot['money_lent_balance']
    )

    if 'asset_snapshots' not in state.budget_settings:
        state.budget_settings['asset_snapshots'] = []

    # Check if snapshot for this date already exists
    existing = [s for s in state.budget_settings['asset_snapshots'] if s['date'] == snapshot_date]
    if existing:
        # Update existing snapshot
        idx = state.budget_settings['asset_snapshots'].index(existing[0])
        state.budget_settings['asset_snapshots'][idx] = snapshot
    else:
        # Add new snapshot
        state.budget_settings['asset_snapshots'].append(snapshot)

    # Sort by date
    state.budget_settings['asset_snapshots'].sort(key=lambda x: x['date'])

    return snapshot

def get_asset_snapshots(state, start_date=None, end_date=None):
    """Get asset snapshots within a date range"""
    snapshots = state.budget_settings.get('asset_snapshots', [])
    
    if not start_date and not end_date:
        return snapshots

    filtered = []
    for snapshot in snapshots:
        snap_date = snapshot['date']
        if start_date and snap_date < start_date:
            continue
        if end_date and snap_date > end_date:
            continue
        filtered.append(snapshot)

    return filtered

def get_current_net_worth(state):
    """Calculate current net worth from current balances"""
    bs = state.budget_settings
    return (
        bs.get('bank_account_balance', 0) +
        bs.get('wallet_balance', 0) +
        bs.get('savings_balance', 0) +
        bs.get('investment_balance', 0) +
        bs.get('money_lent_balance', 0)
    )

def get_net_worth_change(state, period_months=1):
    """Calculate net worth change over a period"""
    snapshots = state.budget_settings.get('asset_snapshots', [])
    
    if not snapshots:
        return None, "No historical data available"

    current_net_worth = get_current_net_worth(state)

    # Get snapshot from period_months ago
    target_date = (date.today() - relativedelta(months=period_months)).strftime('%Y-%m-%d')

    # Find closest snapshot to target date
    past_snapshot = None
    for snapshot in reversed(snapshots):
        if snapshot['date'] <= target_date:
            past_snapshot = snapshot
            break

    if not past_snapshot:
        return None, f"No data from {period_months} month(s) ago"

    change = current_net_worth - past_snapshot['net_worth']
    change_pct = (change / past_snapshot['net_worth'] * 100) if past_snapshot['net_worth'] != 0 else 0

    return {
        'current': current_net_worth,
        'past': past_snapshot['net_worth'],
        'change': change,
        'change_pct': change_pct,
        'past_date': past_snapshot['date']
    }, None

def delete_snapshot(state, snapshot_date):
    """Delete a snapshot by date"""
    snapshots = state.budget_settings.get('asset_snapshots', [])
    state.budget_settings['asset_snapshots'] = [s for s in snapshots if s['date'] != snapshot_date]
    return True

def generate_net_worth_report(state):
    """Generate a comprehensive net worth report"""
    snapshots = state.budget_settings.get('asset_snapshots', [])
    current_net_worth = get_current_net_worth(state)

    report = f"{'='*80}\n"
    report += f"NET WORTH REPORT\n"
    report += f"{'='*80}\n\n"
    report += f"Generated: {date.today().strftime('%B %d, %Y')}\n\n"

    # Current status
    bs = state.budget_settings
    report += f"CURRENT ASSET BREAKDOWN\n"
    report += f"{'-'*80}\n"
    report += f"Bank Account:        €{bs.get('bank_account_balance', 0):>12,.2f}\n"
    report += f"Wallet:              €{bs.get('wallet_balance', 0):>12,.2f}\n"
    report += f"Savings:             €{bs.get('savings_balance', 0):>12,.2f}\n"
    report += f"Investments:         €{bs.get('investment_balance', 0):>12,.2f}\n"
    report += f"Money Lent:          €{bs.get('money_lent_balance', 0):>12,.2f}\n"
    report += f"{'-'*80}\n"
    report += f"CURRENT NET WORTH:   €{current_net_worth:>12,.2f}\n\n"

    if not snapshots:
        report += "No historical snapshots recorded yet.\n"
        report += "Start tracking by recording your first snapshot!\n"
        return report

    # Historical changes
    report += f"{'='*80}\n"
    report += f"HISTORICAL CHANGES\n"
    report += f"{'='*80}\n\n"

    # Calculate changes for different periods
    periods = [1, 3, 6, 12]
    for months in periods:
        change_data, error = get_net_worth_change(state, months)
        if change_data:
            sign = "+" if change_data['change'] >= 0 else ""
            report += f"Change over {months} month(s) (since {change_data['past_date']}):\n"
            report += f"  {sign}€{change_data['change']:,.2f} ({sign}{change_data['change_pct']:.1f}%)\n"
            report += f"  From: €{change_data['past']:,.2f} → To: €{change_data['current']:,.2f}\n\n"

    # Snapshot history
    report += f"\n{'='*80}\n"
    report += f"SNAPSHOT HISTORY\n"
    report += f"{'='*80}\n\n"
    report += f"{'Date':<12} {'Net Worth':>15} {'Change':>15} {'Note'}\n"
    report += f"{'-'*80}\n"

    for i, snapshot in enumerate(snapshots):
        net_worth = snapshot['net_worth']
        
        # Calculate change from previous snapshot
        if i > 0:
            prev_net_worth = snapshots[i-1]['net_worth']
            change = net_worth - prev_net_worth
            sign = "+" if change >= 0 else ""
            change_str = f"{sign}€{change:,.2f}"
        else:
            change_str = "—"
        
        note = snapshot.get('note', '')[:30]
        report += f"{snapshot['date']:<12} €{net_worth:>13,.2f} {change_str:>15} {note}\n"

    # Latest snapshot info
    if snapshots:
        latest = snapshots[-1]
        report += f"\n{'-'*80}\n"
        report += f"Latest snapshot from: {latest['date']}\n"
        report += f"Latest recorded net worth: €{latest['net_worth']:,.2f}\n"
        
        if latest['date'] != date.today().strftime('%Y-%m-%d'):
            diff = current_net_worth - latest['net_worth']
            sign = "+" if diff >= 0 else ""
            report += f"Change since last snapshot: {sign}€{diff:,.2f}\n"

    return report

def get_asset_allocation_data(state):
    """Get current asset allocation percentages"""
    bs = state.budget_settings

    assets = {
        'Bank Account': bs.get('bank_account_balance', 0),
        'Wallet': bs.get('wallet_balance', 0),
        'Savings': bs.get('savings_balance', 0),
        'Investments': bs.get('investment_balance', 0),
        'Money Lent': bs.get('money_lent_balance', 0)
    }

    total = sum(assets.values())

    if total == 0:
        return {}, 0

    percentages = {k: (v / total * 100) for k, v in assets.items() if v > 0}

    return percentages, total
