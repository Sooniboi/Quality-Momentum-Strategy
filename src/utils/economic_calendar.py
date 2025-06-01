#!/usr/bin/env python3
"""
Economic Calendar & Event-Driven Optimization System

This module tracks key economic events and triggers portfolio reoptimization
around market-moving events like Fed meetings, earnings releases, etc.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class EconomicCalendar:
    """Manages economic events and triggers reoptimization."""
    
    def __init__(self):
        self.events = {}
        self.fed_meetings = []
        self.earnings_dates = {}
        self.economic_releases = []
        
    def get_fed_meeting_schedule(self) -> List[Dict]:
        """Get Fed meeting dates for current year."""
        # 2025 Fed Meeting Schedule (8 meetings per year)
        fed_meetings_2025 = [
            {'date': '2025-01-29', 'type': 'FOMC Meeting'},
            {'date': '2025-03-19', 'type': 'FOMC Meeting'},
            {'date': '2025-05-01', 'type': 'FOMC Meeting'},
            {'date': '2025-06-11', 'type': 'FOMC Meeting'},
            {'date': '2025-07-30', 'type': 'FOMC Meeting'},
            {'date': '2025-09-17', 'type': 'FOMC Meeting'},
            {'date': '2025-11-05', 'type': 'FOMC Meeting'},
            {'date': '2025-12-17', 'type': 'FOMC Meeting'}
        ]
        
        # TODO: Integrate with user's Fed rate scrape for real-time probabilities
        for meeting in fed_meetings_2025:
            meeting.update({
                'rate_cut_prob': 0.0,    # From user's scrape
                'rate_hold_prob': 100.0, # From user's scrape  
                'rate_hike_prob': 0.0,   # From user's scrape
                'market_impact': 'High'
            })
            
        return fed_meetings_2025
    
    def get_key_economic_releases(self) -> List[Dict]:
        """Get schedule of key economic data releases."""
        # Monthly releases that impact markets
        releases = [
            {'name': 'NFP', 'frequency': 'First Friday', 'impact': 'High'},
            {'name': 'CPI', 'frequency': 'Mid-month', 'impact': 'High'},
            {'name': 'PPI', 'frequency': 'Mid-month', 'impact': 'Medium'},
            {'name': 'Retail Sales', 'frequency': 'Mid-month', 'impact': 'Medium'},
            {'name': 'GDP', 'frequency': 'Quarterly', 'impact': 'High'},
            {'name': 'PCE', 'frequency': 'End of month', 'impact': 'High'}
        ]
        
        # Generate actual dates for next 3 months
        today = datetime.now()
        future_releases = []
        
        for i in range(3):  # Next 3 months
            month = today + timedelta(days=30*i)
            
            # NFP: First Friday
            first_friday = self._get_first_friday(month.year, month.month)
            future_releases.append({
                'date': first_friday.strftime('%Y-%m-%d'),
                'name': 'Non-Farm Payrolls',
                'impact': 'High',
                'time': '08:30 EST'
            })
            
            # CPI: Around 10th-15th
            cpi_date = month.replace(day=12)
            future_releases.append({
                'date': cpi_date.strftime('%Y-%m-%d'),
                'name': 'Consumer Price Index',
                'impact': 'High', 
                'time': '08:30 EST'
            })
        
        return sorted(future_releases, key=lambda x: x['date'])
    
    def _get_first_friday(self, year: int, month: int) -> datetime:
        """Get first Friday of given month."""
        first_day = datetime(year, month, 1)
        days_to_friday = (4 - first_day.weekday()) % 7
        return first_day + timedelta(days=days_to_friday)
    
    def get_next_fed_meeting(self) -> Optional[Dict]:
        """Get next Fed meeting and days until."""
        meetings = self.get_fed_meeting_schedule()
        today = datetime.now().date()
        
        for meeting in meetings:
            meeting_date = datetime.strptime(meeting['date'], '%Y-%m-%d').date()
            if meeting_date >= today:
                days_until = (meeting_date - today).days
                meeting['days_until'] = days_until
                return meeting
        
        return None
    
    def get_optimization_triggers(self) -> Dict:
        """Determine if reoptimization should be triggered."""
        today = datetime.now().date()
        triggers = {
            'should_reoptimize': False,
            'trigger_reason': [],
            'urgency': 'normal',
            'suggested_focus': []
        }
        
        # Fed meeting proximity
        next_fed = self.get_next_fed_meeting()
        if next_fed:
            days_until = next_fed['days_until']
            
            if days_until <= 2:  # 2 days before Fed meeting
                triggers['should_reoptimize'] = True
                triggers['trigger_reason'].append(f"Fed meeting in {days_until} days")
                triggers['urgency'] = 'high'
                triggers['suggested_focus'].append('defensive_positioning')
                triggers['suggested_focus'].append('rate_sensitivity_analysis')
            
            elif days_until <= 7:  # 1 week before
                triggers['should_reoptimize'] = True
                triggers['trigger_reason'].append(f"Fed meeting in {days_until} days")
                triggers['urgency'] = 'medium'
                triggers['suggested_focus'].append('volatility_preparation')
        
        # Economic release proximity
        releases = self.get_key_economic_releases()
        for release in releases[:3]:  # Next 3 releases
            release_date = datetime.strptime(release['date'], '%Y-%m-%d').date()
            days_until = (release_date - today).days
            
            if days_until <= 1 and release['impact'] == 'High':
                triggers['should_reoptimize'] = True
                triggers['trigger_reason'].append(f"{release['name']} tomorrow")
                triggers['urgency'] = 'medium'
                triggers['suggested_focus'].append('earnings_quality_focus')
        
        # Market stress indicators (VIX spike, etc.)
        # TODO: Add real-time market stress detection
        
        # End of month/quarter rebalancing
        if today.day >= 25:  # Last week of month
            triggers['should_reoptimize'] = True
            triggers['trigger_reason'].append("End of month rebalancing")
            triggers['urgency'] = 'normal'
            triggers['suggested_focus'].append('style_rebalancing')
        
        return triggers

def apply_fed_proximity_adjustments(portfolio_df: pd.DataFrame, days_to_fed: int, 
                                   rate_cut_prob: float) -> pd.DataFrame:
    """Apply tactical adjustments based on Fed meeting proximity."""
    print(f"\nApplying Fed proximity adjustments:")
    print(f"Days to Fed meeting: {days_to_fed}")
    print(f"Rate cut probability: {rate_cut_prob:.1%}")
    
    # Create adjusted weights
    portfolio_adj = portfolio_df.copy()
    
    if days_to_fed <= 7:  # Within 1 week of Fed meeting
        
        if rate_cut_prob > 0.7:  # High probability of rate cut
            print("📈 Rate cut expected - Growth/Tech overweight")
            # Overweight rate-sensitive growth stocks
            tech_mask = portfolio_adj['Sector'] == 'Technology'
            real_estate_mask = portfolio_adj['Sector'] == 'Real Estate'
            portfolio_adj.loc[tech_mask, 'Fed_Adjustment'] = 1.15
            portfolio_adj.loc[real_estate_mask, 'Fed_Adjustment'] = 1.10
            
        elif rate_cut_prob < 0.3:  # Low probability (hold/hike)
            print("📉 Rate hold/hike expected - Defensive positioning")
            # Overweight defensive sectors
            defensive_sectors = ['Consumer Defensive', 'Healthcare', 'Utilities']
            defensive_mask = portfolio_adj['Sector'].isin(defensive_sectors)
            portfolio_adj.loc[defensive_mask, 'Fed_Adjustment'] = 1.10
            
        else:  # Uncertain outcome
            print("❓ Uncertain Fed outcome - Reduce risk")
            # Reduce overall risk, favor quality
            quality_mask = portfolio_adj['Style'] == 'Quality'
            portfolio_adj.loc[quality_mask, 'Fed_Adjustment'] = 1.05
            
        # Reduce position sizes as volatility hedge
        if days_to_fed <= 2:
            portfolio_adj['Fed_Adjustment'] = portfolio_adj.get('Fed_Adjustment', 1.0) * 0.95
            print("⚠️  Fed meeting imminent - reducing position sizes by 5%")
    
    # Apply adjustments
    if 'Fed_Adjustment' in portfolio_adj.columns:
        portfolio_adj['Adjusted_Weight'] = (
            portfolio_adj['Portfolio Weight'] * portfolio_adj['Fed_Adjustment']
        )
        # Renormalize to sum to 1
        portfolio_adj['Adjusted_Weight'] = (
            portfolio_adj['Adjusted_Weight'] / portfolio_adj['Adjusted_Weight'].sum()
        )
    else:
        portfolio_adj['Adjusted_Weight'] = portfolio_adj['Portfolio Weight']
    
    return portfolio_adj

def generate_reoptimization_report(triggers: Dict, portfolio_df: pd.DataFrame) -> None:
    """Generate report explaining reoptimization decisions."""
    print("\n" + "="*80)
    print("EVENT-DRIVEN REOPTIMIZATION ANALYSIS")
    print("="*80)
    
    print(f"\nTrigger Analysis:")
    print(f"Should Reoptimize: {'✅ YES' if triggers['should_reoptimize'] else '❌ NO'}")
    print(f"Urgency Level: {triggers['urgency'].upper()}")
    
    if triggers['trigger_reason']:
        print(f"\nTrigger Reasons:")
        for reason in triggers['trigger_reason']:
            print(f"  • {reason}")
    
    if triggers['suggested_focus']:
        print(f"\nSuggested Focus Areas:")
        for focus in triggers['suggested_focus']:
            print(f"  📊 {focus.replace('_', ' ').title()}")
    
    # Tactical recommendations based on triggers
    if 'defensive_positioning' in triggers['suggested_focus']:
        print(f"\n🛡️  Defensive Positioning Recommended:")
        print(f"  • Increase Quality allocation to 50%+")
        print(f"  • Overweight Healthcare, Consumer Defensive")
        print(f"  • Reduce Technology exposure")
        
    if 'rate_sensitivity_analysis' in triggers['suggested_focus']:
        print(f"\n📈 Rate Sensitivity Analysis:")
        print(f"  • Monitor duration-sensitive sectors")
        print(f"  • Adjust Real Estate allocation")
        print(f"  • Consider Treasury hedge overlay")
        
    if 'volatility_preparation' in triggers['suggested_focus']:
        print(f"\n📊 Volatility Preparation:")
        print(f"  • Reduce position concentrations") 
        print(f"  • Increase cash buffer")
        print(f"  • Monitor VIX levels")

def create_event_based_scheduler() -> Dict:
    """Create dynamic scheduling based on upcoming events."""
    calendar = EconomicCalendar()
    
    schedule = {
        'immediate_runs': [],
        'scheduled_runs': [],
        'monitoring_alerts': []
    }
    
    # Check optimization triggers
    triggers = calendar.get_optimization_triggers()
    
    if triggers['should_reoptimize']:
        if triggers['urgency'] == 'high':
            schedule['immediate_runs'].append({
                'action': 'full_reoptimization',
                'reason': triggers['trigger_reason'],
                'focus': triggers['suggested_focus']
            })
        else:
            schedule['scheduled_runs'].append({
                'action': 'analysis_update',
                'when': 'next_market_open',
                'reason': triggers['trigger_reason']
            })
    
    # Schedule regular monitoring
    next_fed = calendar.get_next_fed_meeting()
    if next_fed and next_fed['days_until'] <= 14:
        schedule['monitoring_alerts'].append({
            'type': 'fed_meeting_watch',
            'date': next_fed['date'],
            'days_until': next_fed['days_until'],
            'frequency': 'daily'
        })
    
    return schedule

def main():
    """Demonstrate event-driven optimization system."""
    print("=== EVENT-DRIVEN OPTIMIZATION SYSTEM ===")
    
    calendar = EconomicCalendar()
    
    # Show upcoming events
    print("\n📅 Upcoming Fed Meetings:")
    meetings = calendar.get_fed_meeting_schedule()
    for meeting in meetings[:3]:
        print(f"  {meeting['date']}: {meeting['type']}")
    
    print("\n📊 Economic Releases:")
    releases = calendar.get_key_economic_releases()
    for release in releases[:5]:
        print(f"  {release['date']}: {release['name']} ({release['impact']} impact)")
    
    # Check current triggers
    triggers = calendar.get_optimization_triggers()
    generate_reoptimization_report(triggers, pd.DataFrame())
    
    # Show dynamic scheduling
    schedule = create_event_based_scheduler()
    print(f"\n🤖 Dynamic Schedule:")
    print(f"  Immediate Actions: {len(schedule['immediate_runs'])}")
    print(f"  Scheduled Actions: {len(schedule['scheduled_runs'])}")
    print(f"  Monitoring Alerts: {len(schedule['monitoring_alerts'])}")

if __name__ == "__main__":
    main() 