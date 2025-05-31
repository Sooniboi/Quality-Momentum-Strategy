#!/usr/bin/env python3
"""
Operational Scheduler for Quality Momentum Strategy

This module handles all regular operational tasks beyond event-driven triggers:
- Daily monitoring and data updates
- Weekly rebalancing and performance reviews
- Monthly deep analysis and risk reviews
- Quarterly strategy reviews and universe updates
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional
import calendar
import os
import time

class OperationalScheduler:
    """Manages regular operational tasks and schedules."""
    
    def __init__(self):
        self.last_daily_run = None
        self.last_weekly_run = None
        self.last_monthly_run = None
        self.last_quarterly_run = None
    
    def get_daily_tasks(self) -> Dict:
        """Define daily operational tasks."""
        today = datetime.now().date()
        current_hour = datetime.now().hour
        
        daily_tasks = {
            'should_run_daily': False,
            'tasks': [],
            'priority': 'low',
            'estimated_duration_minutes': 5
        }
        
        # Only run during market hours (9 AM - 4 PM ET)
        if current_hour < 9 or current_hour > 16:
            daily_tasks['skip_reason'] = 'Outside market hours'
            return daily_tasks
            
        # Skip weekends
        if today.weekday() >= 5:
            daily_tasks['skip_reason'] = 'Weekend'
            return daily_tasks
        
        # Check if daily tasks already completed today
        if self.last_daily_run == today:
            daily_tasks['skip_reason'] = 'Daily tasks already completed'
            return daily_tasks
        
        daily_tasks['should_run_daily'] = True
        daily_tasks['tasks'] = [
            {
                'name': 'portfolio_health_check',
                'description': 'Quick portfolio health and performance check',
                'estimated_minutes': 2,
                'critical': True
            },
            {
                'name': 'market_data_refresh',
                'description': 'Update key market indicators (VIX, rates, sectors)',
                'estimated_minutes': 1,
                'critical': True
            },
            {
                'name': 'risk_monitoring',
                'description': 'Check for risk limit breaches or concentration issues',
                'estimated_minutes': 1,
                'critical': True
            },
            {
                'name': 'news_sentiment_scan',
                'description': 'Scan for major market-moving news or events',
                'estimated_minutes': 1,
                'critical': False
            }
        ]
        
        # Increase priority if market stress detected
        if self._detect_market_stress():
            daily_tasks['priority'] = 'high'
            daily_tasks['tasks'].append({
                'name': 'stress_analysis',
                'description': 'Enhanced risk analysis due to market stress',
                'estimated_minutes': 3,
                'critical': True
            })
        
        return daily_tasks
    
    def get_weekly_tasks(self) -> Dict:
        """Define weekly operational tasks (typically Monday mornings)."""
        today = datetime.now().date()
        
        weekly_tasks = {
            'should_run_weekly': False,
            'tasks': [],
            'priority': 'medium',
            'estimated_duration_minutes': 30
        }
        
        # Run weekly tasks on Mondays (or Tuesday if Monday is holiday)
        if today.weekday() not in [0, 1]:  # Monday = 0, Tuesday = 1
            weekly_tasks['skip_reason'] = 'Not Monday/Tuesday'
            return weekly_tasks
        
        # Check if weekly tasks already completed this week
        if self.last_weekly_run and (today - self.last_weekly_run).days < 7:
            weekly_tasks['skip_reason'] = 'Weekly tasks already completed this week'
            return weekly_tasks
        
        weekly_tasks['should_run_weekly'] = True
        weekly_tasks['tasks'] = [
            {
                'name': 'performance_review',
                'description': 'Weekly portfolio performance vs benchmarks',
                'estimated_minutes': 8,
                'critical': True
            },
            {
                'name': 'sector_momentum_update',
                'description': 'Refresh sector scoring and momentum analysis',
                'estimated_minutes': 10,
                'critical': True
            },
            {
                'name': 'risk_metrics_review',
                'description': 'Review portfolio correlations and risk metrics',
                'estimated_minutes': 5,
                'critical': True
            },
            {
                'name': 'tactical_rebalancing',
                'description': 'Apply tactical adjustments based on momentum shifts',
                'estimated_minutes': 5,
                'critical': False
            },
            {
                'name': 'universe_screening',
                'description': 'Check for new additions/deletions to S&P 600',
                'estimated_minutes': 2,
                'critical': False
            }
        ]
        
        return weekly_tasks
    
    def get_monthly_tasks(self) -> Dict:
        """Define monthly operational tasks (first business day of month)."""
        today = datetime.now().date()
        
        monthly_tasks = {
            'should_run_monthly': False,
            'tasks': [],
            'priority': 'high',
            'estimated_duration_minutes': 90
        }
        
        # Check if this is first business day of month
        if not self._is_first_business_day_of_month(today):
            monthly_tasks['skip_reason'] = 'Not first business day of month'
            return monthly_tasks
        
        # Check if monthly tasks already completed this month
        if (self.last_monthly_run and 
            self.last_monthly_run.month == today.month and 
            self.last_monthly_run.year == today.year):
            monthly_tasks['skip_reason'] = 'Monthly tasks already completed'
            return monthly_tasks
        
        monthly_tasks['should_run_monthly'] = True
        monthly_tasks['tasks'] = [
            {
                'name': 'full_pipeline_refresh',
                'description': 'Complete data collection and portfolio reconstruction',
                'estimated_minutes': 60,
                'critical': True
            },
            {
                'name': 'comprehensive_risk_analysis',
                'description': 'Deep dive risk analysis with stress testing',
                'estimated_minutes': 15,
                'critical': True
            },
            {
                'name': 'performance_attribution',
                'description': 'Detailed performance attribution analysis',
                'estimated_minutes': 10,
                'critical': True
            },
            {
                'name': 'strategy_drift_analysis',
                'description': 'Check for strategy drift and style consistency',
                'estimated_minutes': 5,
                'critical': True
            }
        ]
        
        return monthly_tasks
    
    def get_quarterly_tasks(self) -> Dict:
        """Define quarterly operational tasks (first business day of quarter)."""
        today = datetime.now().date()
        
        quarterly_tasks = {
            'should_run_quarterly': False,
            'tasks': [],
            'priority': 'critical',
            'estimated_duration_minutes': 180
        }
        
        # Check if this is first business day of quarter
        if not self._is_first_business_day_of_quarter(today):
            quarterly_tasks['skip_reason'] = 'Not first business day of quarter'
            return quarterly_tasks
        
        # Check if quarterly tasks already completed this quarter
        if (self.last_quarterly_run and 
            self._get_quarter(self.last_quarterly_run) == self._get_quarter(today)):
            quarterly_tasks['skip_reason'] = 'Quarterly tasks already completed'
            return quarterly_tasks
        
        quarterly_tasks['should_run_quarterly'] = True
        quarterly_tasks['tasks'] = [
            {
                'name': 'universe_refresh',
                'description': 'Complete S&P 600 universe update and validation',
                'estimated_minutes': 30,
                'critical': True
            },
            {
                'name': 'strategy_review',
                'description': 'Comprehensive strategy performance review',
                'estimated_minutes': 45,
                'critical': True
            },
            {
                'name': 'factor_analysis',
                'description': 'Deep factor exposure and Fama-French analysis',
                'estimated_minutes': 30,
                'critical': True
            },
            {
                'name': 'benchmark_analysis',
                'description': 'Compare against relevant benchmarks and peers',
                'estimated_minutes': 20,
                'critical': True
            },
            {
                'name': 'model_calibration',
                'description': 'Recalibrate scoring models and parameters',
                'estimated_minutes': 45,
                'critical': False
            },
            {
                'name': 'documentation_update',
                'description': 'Update strategy documentation and methodology',
                'estimated_minutes': 10,
                'critical': False
            }
        ]
        
        return quarterly_tasks
    
    def get_special_tasks(self) -> Dict:
        """Define special circumstance tasks."""
        special_tasks = {
            'should_run_special': False,
            'tasks': [],
            'triggers': []
        }
        
        # Market stress response
        if self._detect_market_stress():
            special_tasks['should_run_special'] = True
            special_tasks['triggers'].append('market_stress')
            special_tasks['tasks'].append({
                'name': 'crisis_portfolio_review',
                'description': 'Emergency portfolio review due to market stress',
                'estimated_minutes': 30,
                'critical': True
            })
        
        # Large portfolio movements
        if self._detect_large_portfolio_moves():
            special_tasks['should_run_special'] = True
            special_tasks['triggers'].append('large_moves')
            special_tasks['tasks'].append({
                'name': 'movement_analysis',
                'description': 'Analyze large portfolio movements and causes',
                'estimated_minutes': 15,
                'critical': True
            })
        
        # Earnings season adjustments
        if self._is_earnings_season():
            special_tasks['should_run_special'] = True
            special_tasks['triggers'].append('earnings_season')
            special_tasks['tasks'].append({
                'name': 'earnings_positioning',
                'description': 'Adjust positioning for earnings season volatility',
                'estimated_minutes': 20,
                'critical': False
            })
        
        return special_tasks
    
    def get_comprehensive_schedule(self) -> Dict:
        """Get complete operational schedule for current conditions."""
        print("🔍 Checking operational schedule...")
        
        schedule = {
            'timestamp': datetime.now().isoformat(),
            'daily': self.get_daily_tasks(),
            'weekly': self.get_weekly_tasks(),
            'monthly': self.get_monthly_tasks(),
            'quarterly': self.get_quarterly_tasks(),
            'special': self.get_special_tasks(),
            'summary': {
                'total_tasks': 0,
                'critical_tasks': 0,
                'estimated_total_minutes': 0,
                'highest_priority': 'none'
            }
        }
        
        # Calculate summary
        all_task_lists = [
            schedule['daily']['tasks'],
            schedule['weekly']['tasks'],
            schedule['monthly']['tasks'],
            schedule['quarterly']['tasks'],
            schedule['special']['tasks']
        ]
        
        priorities = []
        
        for task_list in all_task_lists:
            for task in task_list:
                schedule['summary']['total_tasks'] += 1
                if task.get('critical', False):
                    schedule['summary']['critical_tasks'] += 1
                schedule['summary']['estimated_total_minutes'] += task.get('estimated_minutes', 0)
        
        # Determine highest priority
        if schedule['quarterly']['should_run_quarterly']:
            priorities.append('critical')
        if schedule['monthly']['should_run_monthly']:
            priorities.append('high')
        if schedule['weekly']['should_run_weekly']:
            priorities.append('medium')
        if schedule['daily']['should_run_daily']:
            priorities.append('low')
        if schedule['special']['should_run_special']:
            priorities.append('urgent')
        
        if priorities:
            priority_order = ['urgent', 'critical', 'high', 'medium', 'low']
            schedule['summary']['highest_priority'] = next(
                (p for p in priority_order if p in priorities), 'none'
            )
        
        return schedule
    
    def _detect_market_stress(self) -> bool:
        """Detect if market is in stress condition."""
        try:
            # Simple VIX check - in production would be more sophisticated
            # For now, return False to avoid false positives
            return False
        except:
            return False
    
    def _detect_large_portfolio_moves(self) -> bool:
        """Detect if portfolio has large unexpected movements."""
        try:
            # In production, would check portfolio performance vs expected
            return False
        except:
            return False
    
    def _is_earnings_season(self) -> bool:
        """Check if currently in earnings season."""
        today = datetime.now().date()
        month = today.month
        
        # Earnings seasons: Jan/Feb, Apr/May, Jul/Aug, Oct/Nov
        earnings_months = [1, 2, 4, 5, 7, 8, 10, 11]
        return month in earnings_months
    
    def _is_first_business_day_of_month(self, check_date: date) -> bool:
        """Check if date is first business day of month."""
        # Get first day of month
        first_day = check_date.replace(day=1)
        
        # Find first business day
        while first_day.weekday() >= 5:  # Saturday = 5, Sunday = 6
            first_day += timedelta(days=1)
        
        return check_date == first_day
    
    def _is_first_business_day_of_quarter(self, check_date: date) -> bool:
        """Check if date is first business day of quarter."""
        quarter_start_months = [1, 4, 7, 10]
        
        if check_date.month not in quarter_start_months:
            return False
        
        return self._is_first_business_day_of_month(check_date)
    
    def _get_quarter(self, check_date: date) -> int:
        """Get quarter number (1-4) for given date."""
        return (check_date.month - 1) // 3 + 1

def generate_operational_report(schedule: Dict) -> None:
    """Generate comprehensive operational schedule report."""
    print("\n" + "="*80)
    print("OPERATIONAL SCHEDULE ANALYSIS")
    print("="*80)
    
    print(f"\nSchedule Generated: {schedule['timestamp']}")
    print(f"Total Tasks: {schedule['summary']['total_tasks']}")
    print(f"Critical Tasks: {schedule['summary']['critical_tasks']}")
    print(f"Estimated Duration: {schedule['summary']['estimated_total_minutes']} minutes")
    print(f"Highest Priority: {schedule['summary']['highest_priority'].upper()}")
    
    # Daily Tasks
    daily = schedule['daily']
    print(f"\n📅 DAILY TASKS:")
    if daily['should_run_daily']:
        print(f"✅ {len(daily['tasks'])} daily tasks scheduled")
        print(f"   Priority: {daily['priority']} | Duration: {daily['estimated_duration_minutes']} min")
        for task in daily['tasks']:
            critical = "🔴" if task.get('critical') else "🟡"
            print(f"   {critical} {task['name']}: {task['description']}")
    else:
        print(f"⏭️  Daily tasks skipped: {daily.get('skip_reason', 'Unknown')}")
    
    # Weekly Tasks
    weekly = schedule['weekly']
    print(f"\n📊 WEEKLY TASKS:")
    if weekly['should_run_weekly']:
        print(f"✅ {len(weekly['tasks'])} weekly tasks scheduled")
        print(f"   Priority: {weekly['priority']} | Duration: {weekly['estimated_duration_minutes']} min")
        for task in weekly['tasks']:
            critical = "🔴" if task.get('critical') else "🟡"
            print(f"   {critical} {task['name']}: {task['description']}")
    else:
        print(f"⏭️  Weekly tasks skipped: {weekly.get('skip_reason', 'Unknown')}")
    
    # Monthly Tasks
    monthly = schedule['monthly']
    print(f"\n📈 MONTHLY TASKS:")
    if monthly['should_run_monthly']:
        print(f"✅ {len(monthly['tasks'])} monthly tasks scheduled")
        print(f"   Priority: {monthly['priority']} | Duration: {monthly['estimated_duration_minutes']} min")
        for task in monthly['tasks']:
            critical = "🔴" if task.get('critical') else "🟡"
            print(f"   {critical} {task['name']}: {task['description']}")
    else:
        print(f"⏭️  Monthly tasks skipped: {monthly.get('skip_reason', 'Unknown')}")
    
    # Quarterly Tasks
    quarterly = schedule['quarterly']
    print(f"\n🏛️  QUARTERLY TASKS:")
    if quarterly['should_run_quarterly']:
        print(f"✅ {len(quarterly['tasks'])} quarterly tasks scheduled")
        print(f"   Priority: {quarterly['priority']} | Duration: {quarterly['estimated_duration_minutes']} min")
        for task in quarterly['tasks']:
            critical = "🔴" if task.get('critical') else "🟡"
            print(f"   {critical} {task['name']}: {task['description']}")
    else:
        print(f"⏭️  Quarterly tasks skipped: {quarterly.get('skip_reason', 'Unknown')}")
    
    # Special Tasks
    special = schedule['special']
    print(f"\n🚨 SPECIAL TASKS:")
    if special['should_run_special']:
        print(f"✅ {len(special['tasks'])} special tasks triggered")
        print(f"   Triggers: {', '.join(special['triggers'])}")
        for task in special['tasks']:
            critical = "🔴" if task.get('critical') else "🟡"
            print(f"   {critical} {task['name']}: {task['description']}")
    else:
        print(f"😴 No special tasks triggered")
    
    # Execution recommendations
    print(f"\n💡 EXECUTION RECOMMENDATIONS:")
    
    if schedule['summary']['highest_priority'] == 'urgent':
        print("🚨 URGENT: Execute special tasks immediately")
    elif schedule['summary']['highest_priority'] == 'critical':
        print("🔥 CRITICAL: Execute quarterly tasks today")
    elif schedule['summary']['highest_priority'] == 'high':
        print("📊 HIGH: Execute monthly tasks within business hours")
    elif schedule['summary']['highest_priority'] == 'medium':
        print("⚡ MEDIUM: Execute weekly tasks Monday morning")
    elif schedule['summary']['highest_priority'] == 'low':
        print("📅 LOW: Execute daily tasks during market hours")
    else:
        print("😴 No operational tasks required at this time")
    
    print(f"\n🤖 AUTOMATION SUGGESTIONS:")
    print(f"  • Schedule daily tasks: 10:00 AM ET (5 min)")
    print(f"  • Schedule weekly tasks: Monday 9:30 AM ET (30 min)")
    print(f"  • Schedule monthly tasks: 1st business day 9:00 AM ET (90 min)")
    print(f"  • Schedule quarterly tasks: 1st business day of quarter (3 hours)")

def main():
    """Demonstrate operational scheduler."""
    print("=== OPERATIONAL SCHEDULER SYSTEM ===")
    
    scheduler = OperationalScheduler()
    schedule = scheduler.get_comprehensive_schedule()
    generate_operational_report(schedule)

if __name__ == "__main__":
    main() 