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
        """Get Fed meeting dates for current year - UPDATED June 2025."""
        # 2025 Fed Meeting Schedule (8 meetings per year) - Updated from Federal Reserve
        fed_meetings_2025 = [
            {'date': '2025-01-29', 'type': 'FOMC Meeting', 'completed': True},
            {'date': '2025-03-19', 'type': 'FOMC Meeting + SEP', 'completed': True},
            {'date': '2025-05-07', 'type': 'FOMC Meeting', 'completed': True},
            {'date': '2025-06-18', 'type': 'FOMC Meeting + SEP', 'completed': False},  # NEXT MEETING
            {'date': '2025-07-30', 'type': 'FOMC Meeting', 'completed': False},
            {'date': '2025-09-17', 'type': 'FOMC Meeting + SEP', 'completed': False},
            {'date': '2025-10-29', 'type': 'FOMC Meeting', 'completed': False},
            {'date': '2025-12-10', 'type': 'FOMC Meeting + SEP', 'completed': False}
        ]
        
        # Add minutes release dates (3 weeks after meeting)
        for meeting in fed_meetings_2025:
            meeting_date = datetime.strptime(meeting['date'], '%Y-%m-%d')
            minutes_date = meeting_date + timedelta(days=21)  # 3 weeks later
            meeting['minutes_release'] = minutes_date.strftime('%Y-%m-%d')
            
            # Rate decision probabilities (would integrate with CME FedWatch or your scraping)
            if meeting['date'] == '2025-06-18':
                meeting.update({
                    'rate_cut_prob': 15.0,    # Current market expectations
                    'rate_hold_prob': 85.0,   # Based on recent Fed hawkish stance
                    'rate_hike_prob': 0.0,
                    'market_impact': 'Very High',
                    'notes': 'Next meeting - SEP & press conference'
                })
            elif meeting['date'] == '2025-07-30':
                meeting.update({
                    'rate_cut_prob': 35.0,
                    'rate_hold_prob': 60.0,
                    'rate_hike_prob': 5.0,
                    'market_impact': 'High',
                    'notes': 'No SEP, regular meeting'
                })
            else:
                meeting.update({
                    'rate_cut_prob': 25.0,
                    'rate_hold_prob': 70.0,
                    'rate_hike_prob': 5.0,
                    'market_impact': 'High'
                })
            
        return fed_meetings_2025
    
    def get_key_economic_releases(self) -> List[Dict]:
        """Get schedule of key economic data releases - UPDATED June 2025."""
        # Key economic releases for June-July 2025 based on economic calendars
        upcoming_releases = [
            # June 2025
            {'date': '2025-06-04', 'name': 'ADP Employment Change', 'time': '08:15 ET', 'impact': 'Medium', 'forecast': '122.5K'},
            {'date': '2025-06-04', 'name': 'ISM Non-Manufacturing PMI', 'time': '10:00 ET', 'impact': 'High', 'forecast': '52.0'},
            {'date': '2025-06-05', 'name': 'Initial Jobless Claims', 'time': '08:30 ET', 'impact': 'Medium', 'forecast': '235K'},
            {'date': '2025-06-06', 'name': 'Non-Farm Payrolls', 'time': '08:30 ET', 'impact': 'Very High', 'forecast': '142.5K'},
            {'date': '2025-06-06', 'name': 'Unemployment Rate', 'time': '08:30 ET', 'impact': 'Very High', 'forecast': '4.2%'},
            {'date': '2025-06-09', 'name': 'FOMC Minutes Release', 'time': '18:00 ET', 'impact': 'Very High', 'forecast': 'May Meeting'},
            {'date': '2025-06-11', 'name': 'Core CPI (YoY)', 'time': '08:30 ET', 'impact': 'Very High', 'forecast': '2.8%'},
            {'date': '2025-06-11', 'name': 'CPI (YoY)', 'time': '08:30 ET', 'impact': 'Very High', 'forecast': '2.3%'},
            {'date': '2025-06-12', 'name': 'PPI (MoM)', 'time': '08:30 ET', 'impact': 'High', 'forecast': 'TBD'},
            {'date': '2025-06-18', 'name': 'FOMC Rate Decision', 'time': '14:00 ET', 'impact': 'Extreme', 'forecast': 'Hold at 4.25-4.50%'},
            {'date': '2025-06-18', 'name': 'Fed Chair Powell Press Conference', 'time': '14:30 ET', 'impact': 'Extreme', 'forecast': 'Policy guidance'},
            
            # July 2025  
            {'date': '2025-07-02', 'name': 'ADP Employment Change', 'time': '08:15 ET', 'impact': 'Medium', 'forecast': 'TBD'},
            {'date': '2025-07-03', 'name': 'ISM Manufacturing PMI', 'time': '10:00 ET', 'impact': 'High', 'forecast': 'TBD'},
            {'date': '2025-07-04', 'name': 'Independence Day Holiday', 'time': 'All Day', 'impact': 'Market Closed', 'forecast': 'No Trading'},
            {'date': '2025-07-09', 'name': 'FOMC Minutes Release', 'time': '18:00 ET', 'impact': 'Very High', 'forecast': 'June Meeting'},
            {'date': '2025-07-10', 'name': 'Core CPI (YoY)', 'time': '08:30 ET', 'impact': 'Very High', 'forecast': 'TBD'},
            {'date': '2025-07-11', 'name': 'PPI (MoM)', 'time': '08:30 ET', 'impact': 'High', 'forecast': 'TBD'},
            {'date': '2025-07-30', 'name': 'FOMC Rate Decision', 'time': '14:00 ET', 'impact': 'Extreme', 'forecast': 'TBD'},
            {'date': '2025-07-30', 'name': 'Fed Chair Powell Press Conference', 'time': '14:30 ET', 'impact': 'Extreme', 'forecast': 'Policy guidance'},
            
            # August 2025
            {'date': '2025-08-20', 'name': 'FOMC Minutes Release', 'time': '18:00 ET', 'impact': 'Very High', 'forecast': 'July Meeting'}
        ]
        
        return sorted(upcoming_releases, key=lambda x: x['date'])
    
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
            if meeting['completed']:
                continue
            meeting_date = datetime.strptime(meeting['date'], '%Y-%m-%d').date()
            if meeting_date >= today:
                days_until = (meeting_date - today).days
                meeting['days_until'] = days_until
                return meeting
        
        return None
    
    def get_next_key_events(self, days_ahead: int = 14) -> List[Dict]:
        """Get key economic events in next N days."""
        releases = self.get_key_economic_releases()
        today = datetime.now().date()
        cutoff_date = today + timedelta(days=days_ahead)
        
        upcoming_events = []
        for release in releases:
            release_date = datetime.strptime(release['date'], '%Y-%m-%d').date()
            if today <= release_date <= cutoff_date:
                days_until = (release_date - today).days
                release['days_until'] = days_until
                upcoming_events.append(release)
        
        return sorted(upcoming_events, key=lambda x: x['days_until'])
    
    def get_optimization_triggers(self) -> Dict:
        """Determine if reoptimization should be triggered."""
        today = datetime.now().date()
        triggers = {
            'should_reoptimize': False,
            'trigger_reason': [],
            'urgency': 'normal',
            'suggested_focus': [],
            'next_events': []
        }
        
        # Fed meeting proximity
        next_fed = self.get_next_fed_meeting()
        if next_fed:
            days_until = next_fed['days_until']
            
            if days_until <= 1:  # Day of or day before Fed meeting
                triggers['should_reoptimize'] = True
                triggers['trigger_reason'].append(f"Fed meeting {'TODAY' if days_until == 0 else 'TOMORROW'}")
                triggers['urgency'] = 'extreme'
                triggers['suggested_focus'].extend(['defensive_positioning', 'volatility_hedging', 'risk_reduction'])
                
            elif days_until <= 3:  # 2-3 days before Fed meeting
                triggers['should_reoptimize'] = True
                triggers['trigger_reason'].append(f"Fed meeting in {days_until} days")
                triggers['urgency'] = 'high'
                triggers['suggested_focus'].extend(['defensive_positioning', 'rate_sensitivity_analysis'])
            
            elif days_until <= 7:  # 1 week before
                triggers['should_reoptimize'] = True
                triggers['trigger_reason'].append(f"Fed meeting in {days_until} days")
                triggers['urgency'] = 'medium'
                triggers['suggested_focus'].append('volatility_preparation')
        
        # Key economic release proximity
        key_events = self.get_next_key_events(7)  # Next 7 days
        high_impact_soon = []
        
        for event in key_events:
            if event['impact'] in ['Very High', 'Extreme'] and event['days_until'] <= 2:
                high_impact_soon.append(event)
                
        if high_impact_soon:
            triggers['should_reoptimize'] = True
            event_names = [e['name'] for e in high_impact_soon]
            triggers['trigger_reason'].append(f"High-impact releases: {', '.join(event_names)}")
            triggers['urgency'] = 'high' if any(e['impact'] == 'Extreme' for e in high_impact_soon) else 'medium'
            triggers['suggested_focus'].append('earnings_quality_focus')
        
        # Store next events for reference
        triggers['next_events'] = key_events[:5]  # Next 5 events
        
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
    
    else:
        # Normal times - no Fed adjustments
        portfolio_adj['Fed_Adjustment'] = 1.0
    
    return portfolio_adj

def generate_reoptimization_report(triggers: Dict, portfolio_df: pd.DataFrame) -> None:
    """Generate report on reoptimization triggers and recommendations."""
    print(f"\n{'='*60}")
    print(f"📅 EVENT-DRIVEN OPTIMIZATION ANALYSIS")
    print(f"{'='*60}")
    
    if triggers['should_reoptimize']:
        urgency_emoji = {'normal': '🟢', 'medium': '🟡', 'high': '🟠', 'extreme': '🔴'}
        print(f"🚨 REOPTIMIZATION TRIGGERED {urgency_emoji.get(triggers['urgency'], '⚪')}")
        print(f"📊 Urgency Level: {triggers['urgency'].upper()}")
        print(f"📝 Reasons:")
        for reason in triggers['trigger_reason']:
            print(f"   • {reason}")
        
        if triggers['suggested_focus']:
            print(f"🎯 Suggested Focus Areas:")
            for focus in triggers['suggested_focus']:
                print(f"   • {focus.replace('_', ' ').title()}")
        
        # Show next events
        if triggers.get('next_events'):
            print(f"\n📅 UPCOMING KEY EVENTS:")
            for event in triggers['next_events']:
                impact_emoji = {'Low': '🟢', 'Medium': '🟡', 'High': '🟠', 'Very High': '🔴', 'Extreme': '💥'}
                print(f"   {impact_emoji.get(event['impact'], '⚪')} {event['date']} ({event['days_until']}d): {event['name']}")
    else:
        print("✅ No immediate reoptimization triggers detected")
        print("📊 Current schedule: Normal monitoring mode")
        
        # Still show next events for awareness
        if triggers.get('next_events'):
            print(f"\n📅 MONITORING - NEXT KEY EVENTS:")
            for event in triggers['next_events'][:3]:
                print(f"   📆 {event['date']} ({event['days_until']}d): {event['name']}")

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
        if triggers['urgency'] in ['extreme', 'high']:
            schedule['immediate_runs'].append({
                'action': 'full_reoptimization',
                'reason': triggers['trigger_reason'],
                'focus': triggers['suggested_focus'],
                'urgency': triggers['urgency']
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
            'frequency': 'daily' if next_fed['days_until'] <= 7 else 'weekly'
        })
    
    # Monitor key events
    key_events = calendar.get_next_key_events(14)
    for event in key_events:
        if event['impact'] in ['Very High', 'Extreme']:
            schedule['monitoring_alerts'].append({
                'type': 'economic_release_watch',
                'event': event['name'],
                'date': event['date'],
                'days_until': event['days_until'],
                'impact': event['impact']
            })
    
    return schedule

def main():
    """Demonstrate event-driven optimization system - UPDATED June 2025."""
    print("=== EVENT-DRIVEN OPTIMIZATION SYSTEM ===")
    print("🗓️  Updated: June 2025 with current Fed schedule")
    
    calendar = EconomicCalendar()
    
    # Show upcoming Fed meetings
    print("\n📅 2025 FOMC MEETINGS:")
    meetings = calendar.get_fed_meeting_schedule()
    for meeting in meetings:
        status = "✅ COMPLETED" if meeting['completed'] else "📅 UPCOMING"
        sep_indicator = " + SEP" if "SEP" in meeting['type'] else ""
        print(f"  {status} {meeting['date']}: {meeting['type']}")
        if not meeting['completed'] and 'days_until' in meeting:
            print(f"    📊 {meeting['days_until']} days until | Market Impact: {meeting.get('market_impact', 'High')}")
    
    # Show next Fed meeting details
    next_fed = calendar.get_next_fed_meeting()
    if next_fed:
        print(f"\n🎯 NEXT FED MEETING:")
        print(f"  📅 Date: {next_fed['date']} ({next_fed['days_until']} days)")
        print(f"  📊 Type: {next_fed['type']}")
        print(f"  📈 Market Expectations:")
        print(f"    • Rate Cut: {next_fed.get('rate_cut_prob', 0):.1f}%")
        print(f"    • Rate Hold: {next_fed.get('rate_hold_prob', 0):.1f}%")
        print(f"    • Rate Hike: {next_fed.get('rate_hike_prob', 0):.1f}%")
        if 'notes' in next_fed:
            print(f"  📝 Notes: {next_fed['notes']}")
    
    # Show upcoming economic releases
    print(f"\n📊 KEY ECONOMIC RELEASES (Next 14 Days):")
    releases = calendar.get_next_key_events(14)
    for release in releases[:8]:  # Show top 8
        impact_emoji = {'Low': '🟢', 'Medium': '🟡', 'High': '🟠', 'Very High': '🔴', 'Extreme': '💥'}
        print(f"  {impact_emoji.get(release['impact'], '⚪')} {release['date']} ({release['days_until']}d): {release['name']}")
        if 'forecast' in release and release['forecast'] != 'TBD':
            print(f"    📈 Forecast: {release['forecast']}")
    
    # Check current triggers
    triggers = calendar.get_optimization_triggers()
    generate_reoptimization_report(triggers, pd.DataFrame())
    
    # Show dynamic scheduling
    schedule = create_event_based_scheduler()
    print(f"\n🤖 DYNAMIC SCHEDULE:")
    print(f"  🚨 Immediate Actions: {len(schedule['immediate_runs'])}")
    print(f"  📅 Scheduled Actions: {len(schedule['scheduled_runs'])}")
    print(f"  👁️  Monitoring Alerts: {len(schedule['monitoring_alerts'])}")
    
    if schedule['immediate_runs']:
        for action in schedule['immediate_runs']:
            print(f"    🚨 {action['action']} - Urgency: {action['urgency']}")
    
    if schedule['monitoring_alerts']:
        print(f"  📋 Active Monitoring:")
        for alert in schedule['monitoring_alerts'][:3]:
            if alert['type'] == 'fed_meeting_watch':
                print(f"    📅 Fed Meeting: {alert['date']} ({alert['days_until']}d)")
            else:
                print(f"    📊 {alert['event']}: {alert['date']} ({alert['days_until']}d)")

if __name__ == "__main__":
    main() 