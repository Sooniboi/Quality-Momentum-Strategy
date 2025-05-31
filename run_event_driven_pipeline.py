#!/usr/bin/env python3
"""
Event-Driven Portfolio Optimization Pipeline

This script monitors economic events and automatically triggers portfolio
reoptimization around key market events like Fed meetings, economic releases, etc.
"""

import os
import sys
import time
import argparse
import subprocess
from datetime import datetime, timedelta
import pandas as pd

# Add paths to import local modules
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'data_collection'))

# Import pipeline modules
from data_collection.economic_calendar import (
    EconomicCalendar, 
    apply_fed_proximity_adjustments, 
    generate_reoptimization_report,
    create_event_based_scheduler
)

def run_pipeline_step(step_number: int, test_mode: bool = False) -> bool:
    """Run a specific pipeline step."""
    
    # Get script paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    universe_dir = os.path.join(base_dir, 'universe')
    data_collection_dir = os.path.join(base_dir, 'data_collection')
    
    # Map step numbers to scripts
    step_mapping = {
        1: (os.path.join(universe_dir, '01_universe_collection.py'), 
            "S&P 600 Universe Collection"),
        2: (os.path.join(data_collection_dir, '02_fundamental_data_collection.py'), 
            "Fundamental Data Collection"),
        3: (os.path.join(data_collection_dir, '03_sector_scoring_analysis.py'), 
            "Sector Scoring Analysis"),
        4: (os.path.join(data_collection_dir, '04_portfolio_construction.py'), 
            "Portfolio Construction"),
        5: (os.path.join(data_collection_dir, '05_risk_analysis_with_ff.py'), 
            "Risk Analysis with Fama-French"),
        6: (os.path.join(data_collection_dir, '06_macro_economic_analysis.py'), 
            "Macro Economic Analysis")
    }
    
    if step_number not in step_mapping:
        print(f"❌ Invalid step number: {step_number}")
        return False
    
    script_path, description = step_mapping[step_number]
    
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return False
    
    print(f"\n📈 Running Step {step_number}: {description}")
    start_time = time.time()
    
    try:
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Step {step_number} completed in {duration:.1f}s")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Step {step_number} failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

class EventDrivenOptimizer:
    """Main class for event-driven portfolio optimization."""
    
    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self.calendar = EconomicCalendar()
        self.last_optimization = None
        
    def check_optimization_triggers(self) -> dict:
        """Check if optimization should be triggered based on events."""
        print("\n🔍 Checking for optimization triggers...")
        
        triggers = self.calendar.get_optimization_triggers()
        next_fed = self.calendar.get_next_fed_meeting()
        
        # Additional trigger logic
        self._add_custom_triggers(triggers, next_fed)
        
        return triggers
    
    def _add_custom_triggers(self, triggers: dict, next_fed: dict) -> None:
        """Add custom trigger logic."""
        today = datetime.now().date()
        
        # Market hours check (only trade during market hours)
        current_hour = datetime.now().hour
        if current_hour < 9 or current_hour > 16:  # Outside market hours
            if triggers['urgency'] != 'high':
                triggers['should_reoptimize'] = False
                triggers['trigger_reason'].append("Outside market hours - delaying")
        
        # Frequency limiter (don't reoptimize too often)
        if self.last_optimization:
            days_since_last = (today - self.last_optimization).days
            if days_since_last < 1 and triggers['urgency'] != 'high':
                triggers['should_reoptimize'] = False
                triggers['trigger_reason'].append("Recent optimization - skipping")
        
        # Weekend check
        if today.weekday() >= 5:  # Saturday/Sunday
            triggers['should_reoptimize'] = False
            triggers['trigger_reason'].append("Weekend - market closed")
    
    def run_event_triggered_optimization(self, triggers: dict) -> bool:
        """Run optimization based on event triggers."""
        print(f"\n🚀 Running event-triggered optimization...")
        print(f"Trigger reasons: {', '.join(triggers['trigger_reason'])}")
        print(f"Urgency: {triggers['urgency']}")
        
        success = True
        
        try:
            if triggers['urgency'] == 'high':
                # Full reoptimization for high urgency
                print("🔥 HIGH URGENCY - Running full pipeline...")
                success = self._run_full_optimization(triggers)
                
            elif triggers['urgency'] == 'medium':
                # Analysis-only update for medium urgency
                print("📊 MEDIUM URGENCY - Running analysis update...")
                success = self._run_analysis_only(triggers)
                
            else:
                # Light refresh for normal urgency
                print("🔄 NORMAL URGENCY - Running light refresh...")
                success = self._run_light_refresh(triggers)
                
            if success:
                self.last_optimization = datetime.now().date()
                self._apply_tactical_adjustments(triggers)
                
        except Exception as e:
            print(f"❌ Optimization failed: {e}")
            success = False
            
        return success
    
    def _run_full_optimization(self, triggers: dict) -> bool:
        """Run complete pipeline for high urgency events."""
        steps_to_run = [1, 2, 3, 4, 5, 6]  # All steps
        
        for step in steps_to_run:
            print(f"\n📈 Running step {step}...")
            if not run_pipeline_step(step, test_mode=self.test_mode):
                print(f"❌ Step {step} failed")
                return False
                
        print("✅ Full optimization completed")
        return True
    
    def _run_analysis_only(self, triggers: dict) -> bool:
        """Run analysis steps only (skip data collection)."""
        analysis_steps = [3, 4, 5]  # Scoring, portfolio, risk analysis
        
        for step in analysis_steps:
            print(f"\n📊 Running analysis step {step}...")
            if not run_pipeline_step(step, test_mode=self.test_mode):
                print(f"❌ Step {step} failed")
                return False
                
        print("✅ Analysis update completed")
        return True
        
    def _run_light_refresh(self, triggers: dict) -> bool:
        """Run light refresh (portfolio construction only)."""
        refresh_steps = [4, 5]  # Portfolio construction and risk analysis
        
        for step in refresh_steps:
            print(f"\n🔄 Running refresh step {step}...")
            if not run_pipeline_step(step, test_mode=self.test_mode):
                print(f"❌ Step {step} failed")
                return False
                
        print("✅ Light refresh completed")
        return True
    
    def _apply_tactical_adjustments(self, triggers: dict) -> None:
        """Apply tactical adjustments based on event proximity."""
        try:
            # Load latest portfolio
            portfolio_files = [f for f in os.listdir('.') 
                             if f.startswith('04_final_portfolio_selection_')]
            if not portfolio_files:
                print("⚠️  No portfolio file found for tactical adjustments")
                return
                
            latest_portfolio = sorted(portfolio_files)[-1]
            portfolio_df = pd.read_csv(latest_portfolio)
            
            # Apply Fed meeting proximity adjustments
            next_fed = self.calendar.get_next_fed_meeting()
            if next_fed and next_fed['days_until'] <= 7:
                adjusted_portfolio = apply_fed_proximity_adjustments(
                    portfolio_df, 
                    next_fed['days_until'],
                    next_fed.get('rate_cut_prob', 0.0)
                )
                
                # Save tactical adjustment
                timestamp = datetime.now().strftime('%Y-%m-%d')
                tactical_file = f"04_tactical_adjusted_portfolio_{timestamp}.csv"
                adjusted_portfolio.to_csv(tactical_file, index=False)
                print(f"💾 Tactical adjustments saved to {tactical_file}")
                
        except Exception as e:
            print(f"⚠️  Tactical adjustments failed: {e}")
    
    def monitor_events(self, check_interval_minutes: int = 60) -> None:
        """Continuously monitor for events and trigger optimization."""
        print(f"🤖 Starting event monitoring (checking every {check_interval_minutes} minutes)")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                triggers = self.check_optimization_triggers()
                generate_reoptimization_report(triggers, pd.DataFrame())
                
                if triggers['should_reoptimize']:
                    print(f"\n🎯 OPTIMIZATION TRIGGERED!")
                    success = self.run_event_triggered_optimization(triggers)
                    
                    if success:
                        print("✅ Event-driven optimization completed successfully")
                    else:
                        print("❌ Event-driven optimization failed")
                        
                    # Send notification (email, Slack, etc.)
                    self._send_notification(triggers, success)
                
                else:
                    print("😴 No optimization triggers - continuing monitoring...")
                
                # Wait for next check
                print(f"\n⏰ Next check in {check_interval_minutes} minutes...")
                time.sleep(check_interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n👋 Event monitoring stopped by user")
    
    def _send_notification(self, triggers: dict, success: bool) -> None:
        """Send notification about optimization results."""
        # TODO: Implement email/Slack notifications
        status = "✅ SUCCESS" if success else "❌ FAILED"
        message = f"Portfolio Optimization {status}\n"
        message += f"Triggers: {', '.join(triggers['trigger_reason'])}\n"
        message += f"Urgency: {triggers['urgency']}\n"
        message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        print(f"\n📧 Notification: {message}")
        
    def run_immediate_check(self) -> None:
        """Run immediate optimization check (for manual triggers)."""
        print("🔍 Running immediate optimization check...")
        
        triggers = self.check_optimization_triggers()
        generate_reoptimization_report(triggers, pd.DataFrame())
        
        if triggers['should_reoptimize']:
            user_input = input("\n❓ Optimization recommended. Proceed? (y/n): ")
            if user_input.lower() in ['y', 'yes']:
                success = self.run_event_triggered_optimization(triggers)
                if success:
                    print("✅ Optimization completed")
                else:
                    print("❌ Optimization failed")
            else:
                print("⏭️  Optimization skipped by user")
        else:
            print("😴 No optimization needed at this time")

def create_sample_events_config() -> None:
    """Create sample events configuration file."""
    config = {
        "monitoring_settings": {
            "check_interval_minutes": 60,
            "market_hours_only": True,
            "weekend_monitoring": False
        },
        "trigger_thresholds": {
            "fed_meeting_days": 7,
            "high_impact_release_days": 1,
            "market_stress_threshold": 25.0
        },
        "notification_settings": {
            "email_enabled": False,
            "slack_enabled": False,
            "webhook_url": ""
        }
    }
    
    import json
    with open('event_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("📝 Sample configuration created: event_config.json")

def main():
    parser = argparse.ArgumentParser(description='Event-Driven Portfolio Optimization')
    parser.add_argument('--mode', choices=['check', 'monitor', 'config'], 
                       default='check', help='Operation mode')
    parser.add_argument('--test-mode', action='store_true', 
                       help='Run in test mode')
    parser.add_argument('--interval', type=int, default=60,
                       help='Monitoring interval in minutes')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("EVENT-DRIVEN PORTFOLIO OPTIMIZATION SYSTEM")
    print("=" * 80)
    
    if args.mode == 'config':
        create_sample_events_config()
        return
    
    optimizer = EventDrivenOptimizer(test_mode=args.test_mode)
    
    if args.mode == 'check':
        optimizer.run_immediate_check()
    elif args.mode == 'monitor':
        optimizer.monitor_events(args.interval)

if __name__ == "__main__":
    main() 