from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

def calculate_goal_progress(goal, current_savings):
    """Calculate progress for a single goal"""
    target = goal['target_amount']
    saved = goal['current_amount']
    
    progress_pct = (saved / target * 100) if target > 0 else 0
    remaining = max(target - saved, 0)
    
    return {
        'progress_pct': progress_pct,
        'remaining': remaining,
        'is_complete': saved >= target
    }

def estimate_completion_date(goal, daily_savings_goal, monthly_income, fixed_costs):
    """Estimate when a goal will be completed"""
    remaining = goal['target_amount'] - goal['current_amount']
    
    if remaining <= 0:
        return None, "Goal already achieved!"
    
    # Use the goal's custom contribution if set, otherwise use daily savings goal
    if goal.get('monthly_contribution', 0) > 0:
        monthly_contribution = goal['monthly_contribution']
    else:
        # Fallback to daily savings goal * 30
        monthly_contribution = daily_savings_goal * 30
    
    if monthly_contribution <= 0:
        return None, "Set a monthly contribution or daily savings goal to estimate completion."
    
    months_needed = remaining / monthly_contribution
    
    start_date = date.today()
    completion_date = start_date + relativedelta(months=int(months_needed))
    
    # Add remaining days
    remaining_days = (months_needed - int(months_needed)) * 30
    completion_date += timedelta(days=int(remaining_days))
    
    return completion_date, f"Estimated: {completion_date.strftime('%B %Y')}"

def generate_goals_report(state) -> str:
    """Generate a comprehensive goals report"""
    goals = state.budget_settings.get('savings_goals', [])
    
    if not goals:
        return "No savings goals set. Create your first goal to start tracking!"
    
    daily_savings = state.budget_settings.get('daily_savings_goal', 0)
    monthly_income = state.budget_settings.get('monthly_income', 0)
    fixed_costs = sum(fc['amount'] for fc in state.budget_settings.get('fixed_costs', []))
    
    report = f"{'='*80}\n"
    report += f"SAVINGS GOALS REPORT\n"
    report += f"{'='*80}\n\n"
    report += f"Generated: {date.today().strftime('%B %d, %Y')}\n"
    report += f"Daily Savings Goal: €{daily_savings:.2f}\n\n"
    report += f"{'-'*80}\n\n"
    
    total_target = sum(g['target_amount'] for g in goals)
    total_saved = sum(g['current_amount'] for g in goals)
    total_remaining = total_target - total_saved
    
    active_goals = [g for g in goals if g['current_amount'] < g['target_amount']]
    completed_goals = [g for g in goals if g['current_amount'] >= g['target_amount']]
    
    report += f"SUMMARY\n"
    report += f"{'-'*80}\n"
    report += f"Total Goals:           {len(goals)}\n"
    report += f"Active Goals:          {len(active_goals)}\n"
    report += f"Completed Goals:       {len(completed_goals)}\n"
    report += f"Total Target Amount:   €{total_target:,.2f}\n"
    report += f"Total Saved:           €{total_saved:,.2f}\n"
    report += f"Total Remaining:       €{total_remaining:,.2f}\n"
    report += f"Overall Progress:      {(total_saved/total_target*100) if total_target > 0 else 0:.1f}%\n\n"
    
    if active_goals:
        report += f"{'='*80}\n"
        report += f"ACTIVE GOALS\n"
        report += f"{'='*80}\n\n"
        
        for goal in active_goals:
            progress = calculate_goal_progress(goal, goal['current_amount'])
            completion_date, completion_msg = estimate_completion_date(
                goal, daily_savings, monthly_income, fixed_costs
            )
            
            report += f"Goal: {goal['name']}\n"
            if goal.get('description'):
                report += f"Description: {goal['description']}\n"
            report += f"{'-'*40}\n"
            report += f"Target Amount:         €{goal['target_amount']:,.2f}\n"
            report += f"Current Savings:       €{goal['current_amount']:,.2f}\n"
            report += f"Remaining:             €{progress['remaining']:,.2f}\n"
            report += f"Progress:              {progress['progress_pct']:.1f}%\n"
            
            if goal.get('monthly_contribution', 0) > 0:
                report += f"Monthly Contribution:  €{goal['monthly_contribution']:.2f}\n"
            
            report += f"Priority:              {goal.get('priority', 'Medium')}\n"
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
    
    # Monthly allocation suggestion
    if active_goals:
        report += f"{'='*80}\n"
        report += f"SUGGESTED MONTHLY ALLOCATION\n"
        report += f"{'='*80}\n\n"
        
        total_monthly_needed = sum(g.get('monthly_contribution', 0) for g in active_goals)
        
        if total_monthly_needed > 0:
            report += f"Total Monthly Contributions Needed: €{total_monthly_needed:.2f}\n\n"
            
            for goal in sorted(active_goals, key=lambda g: g.get('priority', 'Medium'), reverse=True):
                if goal.get('monthly_contribution', 0) > 0:
                    pct = (goal['monthly_contribution'] / total_monthly_needed * 100)
                    report += f"  {goal['name']:<30} €{goal['monthly_contribution']:>8.2f} ({pct:.1f}%)\n"
        else:
            report += f"Set monthly contributions for your goals to see allocation suggestions.\n"
        
        report += f"\n"
    
    return report

def calculate_all_goals_summary(state):
    """Calculate summary statistics for all goals"""
    goals = state.budget_settings.get('savings_goals', [])
    
    if not goals:
        return {
            'total_goals': 0,
            'active_goals': 0,
            'completed_goals': 0,
            'total_target': 0,
            'total_saved': 0,
            'overall_progress': 0
        }
    
    total_target = sum(g['target_amount'] for g in goals)
    total_saved = sum(g['current_amount'] for g in goals)
    active = len([g for g in goals if g['current_amount'] < g['target_amount']])
    completed = len([g for g in goals if g['current_amount'] >= g['target_amount']])
    
    return {
        'total_goals': len(goals),
        'active_goals': active,
        'completed_goals': completed,
        'total_target': total_target,
        'total_saved': total_saved,
        'overall_progress': (total_saved / total_target * 100) if total_target > 0 else 0
    }