from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

def calculate_goal_progress(goal, current_savings):
    """Calculate progress for a single goal"""
    target = goal['target_amount']
    allocated = goal['allocated_amount']
    
    progress_pct = (allocated / target * 100) if target > 0 else 0
    remaining = max(target - allocated, 0)
    
    return {
        'progress_pct': progress_pct,
        'remaining': remaining,
        'is_complete': allocated >= target
    }

def estimate_completion_date(goal, monthly_savings_rate):
    """Estimate when a goal will be completed based on monthly savings rate"""
    remaining = goal['target_amount'] - goal['allocated_amount']
    
    if remaining <= 0:
        return None, "Goal already achieved!"
    
    if monthly_savings_rate <= 0:
        return None, "Set a daily savings goal to estimate completion."
    
    months_needed = remaining / monthly_savings_rate
    
    start_date = date.today()
    completion_date = start_date + relativedelta(months=int(months_needed))
    
    # Add remaining days
    remaining_days = (months_needed - int(months_needed)) * 30
    completion_date += timedelta(days=int(remaining_days))
    
    return completion_date, f"Estimated completion: {completion_date.strftime('%B %Y')}"

def get_total_savings_available(state):
    """Get total savings available for allocation"""
    return state.budget_settings.get('savings_balance', 0)

def get_total_allocated(state):
    """Get total amount already allocated to goals"""
    goals = state.budget_settings.get('savings_goals', [])
    return sum(g.get('allocated_amount', 0) for g in goals)

def get_unallocated_savings(state):
    """Get savings not yet allocated to any goal"""
    total = get_total_savings_available(state)
    allocated = get_total_allocated(state)
    return max(total - allocated, 0)

def validate_allocation(state, goal_index, new_amount):
    """
    Validate if a new allocation amount is valid
    Returns: (is_valid, error_message, available_amount)
    """
    goals = state.budget_settings.get('savings_goals', [])
    
    if goal_index < 0 or goal_index >= len(goals):
        return False, "Invalid goal index", 0
    
    goal = goals[goal_index]
    old_allocation = goal.get('allocated_amount', 0)
    
    # Calculate what would be available if we remove this goal's current allocation
    total_savings = get_total_savings_available(state)
    other_allocations = sum(g.get('allocated_amount', 0) for i, g in enumerate(goals) if i != goal_index)
    available = total_savings - other_allocations
    
    if new_amount < 0:
        return False, "Allocation cannot be negative", available
    
    if new_amount > available:
        return False, f"Insufficient savings. Available: €{available:.2f}", available
    
    return True, "", available

def auto_distribute_savings(state):
    """
    Automatically distribute available savings across goals based on priority and need
    Returns: (success, message)
    """
    goals = state.budget_settings.get('savings_goals', [])
    
    if not goals:
        return False, "No goals to distribute savings to."
    
    total_savings = get_total_savings_available(state)
    
    if total_savings <= 0:
        return False, "No savings available to distribute."
    
    # Reset all allocations first
    for goal in goals:
        goal['allocated_amount'] = 0
    
    # Sort goals by priority and then by how close they are to completion
    priority_order = {'High': 3, 'Medium': 2, 'Low': 1}
    active_goals = [g for g in goals if g.get('allocated_amount', 0) < g['target_amount']]
    
    if not active_goals:
        return False, "All goals are already complete."
    
    # Sort by priority (high first) and then by percentage complete (higher first)
    active_goals.sort(
        key=lambda g: (
            priority_order.get(g.get('priority', 'Medium'), 2),
            g.get('allocated_amount', 0) / g['target_amount'] if g['target_amount'] > 0 else 0
        ),
        reverse=True
    )
    
    remaining_savings = total_savings
    
    # First pass: try to complete goals starting with highest priority
    for goal in active_goals:
        if remaining_savings <= 0:
            break
        
        needed = goal['target_amount'] - goal.get('allocated_amount', 0)
        allocation = min(needed, remaining_savings)
        goal['allocated_amount'] = goal.get('allocated_amount', 0) + allocation
        remaining_savings -= allocation
    
    return True, f"Distributed €{total_savings:.2f} across {len(active_goals)} goal(s)."

def generate_goals_report(state) -> str:
    """Generate a comprehensive goals report"""
    goals = state.budget_settings.get('savings_goals', [])
    
    total_savings = get_total_savings_available(state)
    total_allocated = get_total_allocated(state)
    unallocated = get_unallocated_savings(state)
    
    if not goals:
        report = f"{'='*80}\n"
        report += f"SAVINGS GOALS REPORT\n"
        report += f"{'='*80}\n\n"
        report += f"Total Savings Available: €{total_savings:,.2f}\n"
        report += f"No savings goals set. Create your first goal to start tracking!\n"
        return report
    
    daily_savings = state.budget_settings.get('daily_savings_goal', 0)
    monthly_savings_rate = daily_savings * 30
    
    report = f"{'='*80}\n"
    report += f"SAVINGS GOALS REPORT\n"
    report += f"{'='*80}\n\n"
    report += f"Generated: {date.today().strftime('%B %d, %Y')}\n"
    report += f"Daily Savings Goal: €{daily_savings:.2f} (€{monthly_savings_rate:.2f}/month)\n\n"
    report += f"{'-'*80}\n\n"
    
    total_target = sum(g['target_amount'] for g in goals)
    
    active_goals = [g for g in goals if g.get('allocated_amount', 0) < g['target_amount']]
    completed_goals = [g for g in goals if g.get('allocated_amount', 0) >= g['target_amount']]
    
    report += f"SAVINGS SUMMARY\n"
    report += f"{'-'*80}\n"
    report += f"Total Savings Balance:        €{total_savings:>12,.2f}\n"
    report += f"Amount Allocated to Goals:    €{total_allocated:>12,.2f}\n"
    report += f"Unallocated Savings:          €{unallocated:>12,.2f}\n"
    report += f"\n"
    report += f"Total Goals:                  {len(goals)}\n"
    report += f"Active Goals:                 {len(active_goals)}\n"
    report += f"Completed Goals:              {len(completed_goals)}\n"
    report += f"Total Target Amount:          €{total_target:>12,.2f}\n"
    report += f"Overall Progress:             {(total_allocated/total_target*100) if total_target > 0 else 0:.1f}%\n\n"
    
    if unallocated > 0:
        report += f"⚠️  You have €{unallocated:.2f} in unallocated savings.\n"
        report += f"   Consider allocating this to your goals!\n\n"
    
    if active_goals:
        report += f"{'='*80}\n"
        report += f"ACTIVE GOALS\n"
        report += f"{'='*80}\n\n"
        
        for goal in active_goals:
            progress = calculate_goal_progress(goal, goal.get('allocated_amount', 0))
            completion_date, completion_msg = estimate_completion_date(goal, monthly_savings_rate)
            
            report += f"Goal: {goal['name']}\n"
            if goal.get('description'):
                report += f"Description: {goal['description']}\n"
            report += f"{'-'*40}\n"
            report += f"Target Amount:         €{goal['target_amount']:,.2f}\n"
            report += f"Allocated Savings:     €{goal.get('allocated_amount', 0):,.2f}\n"
            report += f"Still Needed:          €{progress['remaining']:,.2f}\n"
            report += f"Progress:              {progress['progress_pct']:.1f}%\n"
            report += f"Priority:              {goal.get('priority', 'Medium')}\n"
            report += f"Category:              {goal.get('category', 'General')}\n"
            report += f"Completion Estimate:   {completion_msg}\n"
            
            # Progress bar
            bar_length = 40
            filled = int(bar_length * progress['progress_pct'] / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            report += f"[{bar}] {progress['progress_pct']:.1f}%\n"
            report += f"\n"
    
    if completed_goals:
        report += f"{'='*80}\n"
        report += f"COMPLETED GOALS\n"
        report += f"{'='*80}\n\n"
        
        for goal in completed_goals:
            report += f"✓ {goal['name']} - €{goal['target_amount']:,.2f}\n"
            if goal.get('completion_date'):
                report += f"  Completed: {goal['completion_date']}\n"
            report += f"\n"
    
    return report

def calculate_all_goals_summary(state):
    """Calculate summary statistics for all goals"""
    goals = state.budget_settings.get('savings_goals', [])
    
    total_savings = get_total_savings_available(state)
    total_allocated = get_total_allocated(state)
    unallocated = get_unallocated_savings(state)
    
    if not goals:
        return {
            'total_goals': 0,
            'active_goals': 0,
            'completed_goals': 0,
            'total_target': 0,
            'total_allocated': 0,
            'overall_progress': 0,
            'total_savings': total_savings,
            'unallocated': unallocated
        }
    
    total_target = sum(g['target_amount'] for g in goals)
    active = len([g for g in goals if g.get('allocated_amount', 0) < g['target_amount']])
    completed = len([g for g in goals if g.get('allocated_amount', 0) >= g['target_amount']])
    
    return {
        'total_goals': len(goals),
        'active_goals': active,
        'completed_goals': completed,
        'total_target': total_target,
        'total_allocated': total_allocated,
        'overall_progress': (total_allocated / total_target * 100) if total_target > 0 else 0,
        'total_savings': total_savings,
        'unallocated': unallocated
    }