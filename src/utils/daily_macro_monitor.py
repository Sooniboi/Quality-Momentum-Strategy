#!/usr/bin/env python3
"""
Daily Macro Economic Monitor - PRE-MARKET EDITION
Runs daily PRE-MARKET to check market regime, recession risk, Fed policy changes.
Results are saved for both intraday monitoring and weekly portfolio reoptimization.

OPTIMAL TIMING: 6:00 AM EST (Pre-Market) - 1 hour before market open
- Captures overnight economic data releases
- Allows defensive positioning before market open
- Reacts to Asian/European market developments
- Prepares for morning economic events (8:30 AM releases)

Usage: python daily_macro_monitor.py
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime, date
import logging
import requests
from functools import lru_cache
import random

# Fix path issues by using absolute paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

# FRED API rate limiting constants
FRED_RATE_LIMIT_PER_MINUTE = 120
FRED_RATE_LIMIT_PER_DAY = 500
FRED_MIN_DELAY = 0.5  # Minimum delay between requests
FRED_MAX_DELAY = 5.0  # Maximum delay for exponential backoff
FRED_CACHE_DURATION = 3600  # Cache duration in seconds (1 hour)

# Global rate limiting state
fred_request_times = []
fred_daily_requests = 0
fred_last_reset = datetime.now()

def setup_logging():
    """Setup logging for daily macro monitoring."""
    log_dir = os.path.join(ROOT_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'daily_macro_monitor.log')),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def manage_fred_rate_limits():
    """Manage FRED API rate limits with exponential backoff."""
    global fred_request_times, fred_daily_requests, fred_last_reset
    logger = logging.getLogger(__name__)
    
    # Reset daily counter if needed
    if (datetime.now() - fred_last_reset).total_seconds() > 86400:  # 24 hours
        fred_daily_requests = 0
        fred_last_reset = datetime.now()
    
    # Check daily limit
    if fred_daily_requests >= FRED_RATE_LIMIT_PER_DAY:
        logger.warning("⚠️ Daily FRED API limit reached. Using cached data.")
        return True
    
    # Clean old request times
    current_time = time.time()
    fred_request_times = [t for t in fred_request_times if current_time - t < 60]
    
    # Check minute limit
    if len(fred_request_times) >= FRED_RATE_LIMIT_PER_MINUTE:
        logger.warning("⚠️ Minute FRED API limit reached. Waiting...")
        time.sleep(FRED_MAX_DELAY)
        return manage_fred_rate_limits()
    
    # Add current request
    fred_request_times.append(current_time)
    fred_daily_requests += 1
    
    # Calculate delay with exponential backoff
    if len(fred_request_times) > FRED_RATE_LIMIT_PER_MINUTE * 0.8:  # 80% of limit
        delay = min(FRED_MAX_DELAY, FRED_MIN_DELAY * (2 ** (len(fred_request_times) / 10)))
        time.sleep(delay)
    
    return False

@lru_cache(maxsize=100)
def cached_fred_request(series_id, timestamp):
    """Cached FRED API request with rate limiting."""
    if manage_fred_rate_limits():
        return None
    
    try:
        # Import FRED API client with correct path
        from src.utils.fred_api import FredAPI
        fred = FredAPI()
        return fred.get_series(series_id)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Error fetching {series_id}: {e}")
        return None

def get_fred_data(series_ids):
    """Get FRED data with proper rate limiting and caching."""
    logger = logging.getLogger(__name__)
    results = {}
    
    # Get current timestamp for cache key
    current_timestamp = int(time.time() / FRED_CACHE_DURATION)
    
    for series_id in series_ids:
        try:
            # Add jitter to prevent thundering herd
            time.sleep(random.uniform(0.1, 0.3))
            
            # Get data with caching
            data = cached_fred_request(series_id, current_timestamp)
            
            if data is not None:
                results[series_id] = data
                logger.info(f"✅ {series_id}: {data} (FRED API)")
            else:
                logger.warning(f"⚠️ Using cached data for {series_id}")
        except Exception as e:
            logger.error(f"❌ Error processing {series_id}: {e}")
    
    return results

def check_economic_calendar():
    """Check economic calendar for upcoming Fed meetings and key events."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("📅 Checking economic calendar for upcoming events...")
        
        # Import economic calendar with correct path
        from src.utils.economic_calendar import EconomicCalendar
        
        calendar = EconomicCalendar()
        
        # Get next Fed meeting
        next_fed = calendar.get_next_fed_meeting()
        
        # Get upcoming key events
        key_events = calendar.get_next_key_events(7)  # Next 7 days
        
        # Check for optimization triggers
        triggers = calendar.get_optimization_triggers()
        
        # ✅ PRE-MARKET ENHANCEMENT: Check for TODAY's high-impact events
        today_events = [e for e in key_events if e['days_until'] == 0]
        morning_releases = [e for e in today_events if 'CPI' in e['name'] or 'NFP' in e['name'] or 'Payrolls' in e['name']]
        
        calendar_info = {
            'next_fed_meeting': next_fed,
            'key_events_next_7_days': key_events,
            'today_events': today_events,
            'morning_high_impact': morning_releases,
            'optimization_triggers': triggers,
            'should_reoptimize': triggers['should_reoptimize'],
            'urgency': triggers['urgency']
        }
        
        # Enhanced pre-market logging
        if next_fed:
            logger.info(f"🏦 Next Fed Meeting: {next_fed['date']} ({next_fed['days_until']} days) - {next_fed['type']}")
            logger.info(f"📊 Rate Expectations: Hold {next_fed.get('rate_hold_prob', 0):.0f}%, Cut {next_fed.get('rate_cut_prob', 0):.0f}%")
        
        # ✅ TODAY'S EVENTS - Critical for pre-market positioning
        if today_events:
            logger.info(f"🚨 TODAY'S HIGH-IMPACT EVENTS ({len(today_events)}):")
            for event in today_events:
                time_str = event.get('time', 'TBD')
                logger.info(f"   📅 {time_str}: {event['name']} - {event['impact']} impact")
        
        # Morning economic releases (8:30 AM typical)
        if morning_releases:
            logger.info(f"🌅 MORNING RELEASES TODAY - Prepare for volatility:")
            for event in morning_releases:
                logger.info(f"   💥 {event.get('time', '8:30 ET')}: {event['name']}")
        
        # High-impact events in next 3 days
        high_impact_soon = [e for e in key_events if e['impact'] in ['Very High', 'Extreme'] and e['days_until'] <= 3]
        if high_impact_soon:
            logger.info(f"⚠️  High-impact events in next 3 days:")
            for event in high_impact_soon:
                logger.info(f"   📅 {event['date']} ({event['days_until']}d): {event['name']}")
        
        # Log optimization triggers
        if triggers['should_reoptimize']:
            logger.info(f"🚨 Optimization triggers detected - Urgency: {triggers['urgency'].upper()}")
            for reason in triggers['trigger_reason']:
                logger.info(f"   • {reason}")
        
        return calendar_info
        
    except Exception as e:
        logger.error(f"❌ Error checking economic calendar: {e}")
        return {
            'next_fed_meeting': None,
            'key_events_next_7_days': [],
            'today_events': [],
            'morning_high_impact': [],
            'optimization_triggers': {'should_reoptimize': False, 'urgency': 'normal'},
            'should_reoptimize': False,
            'urgency': 'normal'
        }

def run_macro_analysis():
    """Run the macro economic analysis and save results."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🔄 Starting daily macro economic analysis...")
        
        # Run the macro analysis script with correct path
        analysis_script = os.path.join(ROOT_DIR, 'src', 'analysis', '04_macro_economic_analysis.py')
        result = subprocess.run([
            sys.executable, 
            analysis_script
        ], capture_output=True, text=True, cwd=ROOT_DIR)
        
        if result.returncode == 0:
            logger.info("✅ Macro analysis completed successfully")
            return True
        else:
            logger.error(f"❌ Macro analysis failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error running macro analysis: {e}")
        return False

def extract_macro_signals():
    """Extract key signals from enhanced 15-regime macro analysis for trading decisions."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🔍 Analyzing market conditions with enhanced 15-regime system...")
        
        # Import enhanced macro analysis directly with correct path
        import importlib.util
        
        analysis_path = os.path.join(ROOT_DIR, 'src', 'analysis', '04_macro_economic_analysis.py')
        spec = importlib.util.spec_from_file_location("macro_economic_analysis", analysis_path)
        macro_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(macro_module)
        
        # Get current market conditions with rate limiting
        treasury_rates = macro_module.get_treasury_rates()
        
        # Get economic indicators with rate limiting
        economic_indicators = get_fred_data([
            'FEDFUNDS', 'DFEDTARU', 'DFEDTARL', 'UNRATE', 'PCEPILFE',
            'PCEPI', 'CPIAUCSL', 'DGS10', 'DGS2', 'DGS3MO', 'DGS30',
            'UMCSENT', 'PAYEMS', 'GDPC1', 'T10Y2Y', 'T10Y3M', 'ICSA',
            'CCSA', 'HOUST', 'INDPRO', 'TCU', 'ISM1MFG', 'VIXCLS',
            'M2SL', 'DFII10', 'DAAA', 'DBAA', 'A939RX0Q048SBEA',
            'PI', 'RSXFS', 'DGORDER', 'BUSINV'
        ])
        
        yield_curve = macro_module.calculate_yield_curve_metrics(treasury_rates)
        
        # Run enhanced regime classification
        regime_analysis = macro_module.classify_market_regime(economic_indicators, yield_curve)
        current_regime = regime_analysis.get('regime', 'OPTIMISTIC')
        regime_confidence = regime_analysis.get('confidence', 0.5)
        market_conditions = regime_analysis.get('market_conditions', {})
        regime_characteristics = regime_analysis.get('characteristics', {})
        
        # Get recession analysis with rate limiting
        try:
            recession_analysis = macro_module.calculate_recession_probability(
                treasury_rates, economic_indicators, {}
            )
            recession_prob = recession_analysis.get('recession_probability', 0) / 100  # Convert to decimal
        except:
            recession_prob = 0.15  # Default moderate level
            
        # Get Fed policy analysis with rate limiting
        try:
            fed_analysis = macro_module.analyze_fed_policy_stance(economic_indicators)
            fed_policy_bias = fed_analysis.get('overall_assessment', {}).get('policy_bias', 'NEUTRAL')
            fed_rate_direction = fed_analysis.get('overall_assessment', {}).get('rate_direction', 'HOLD')
        except:
            fed_policy_bias = 'NEUTRAL'
            fed_rate_direction = 'HOLD'
        
        # Extract key market indicators
        vix = market_conditions.get('vix', 20.0)
        yield_curve_bps = market_conditions.get('yield_curve_bps', 50)
        unemployment = market_conditions.get('unemployment', 4.2)
        inflation = market_conditions.get('inflation', 2.1)
        
        logger.info(f"🎯 Market Regime: {current_regime} (confidence: {regime_confidence:.0%})")
        logger.info(f"📊 Recession Probability: {recession_prob:.1%}")
        logger.info(f"🏦 Fed Policy: {fed_policy_bias} / {fed_rate_direction}")
        logger.info(f"📈 VIX: {vix:.1f} | Curve: {yield_curve_bps:.0f} bps | Unemployment: {unemployment:.1f}%")
        
        # Enhanced trading recommendation logic
        signals = {
            'timestamp': datetime.now().isoformat(),
            'analysis_date': datetime.now().isoformat(),
            'market_regime': {
                'regime': current_regime,
                'confidence': regime_confidence,
                'description': regime_characteristics.get('description', 'Unknown'),
                'risk_level': regime_characteristics.get('risk_level', 'MODERATE')
            },
            'recession_probability': recession_prob,
            'market_conditions': {
                'vix': vix,
                'yield_curve_bps': yield_curve_bps,
                'unemployment': unemployment,
                'inflation': inflation
            },
            'fed_policy': {
                'bias': fed_policy_bias,
                'rate_direction': fed_rate_direction
            },
            'trading_recommendation': 'PROCEED',  # Default, will be updated below
            'confidence': regime_confidence,
            'reasons': []
        }
        
        # Enhanced recommendation logic based on 15-regime system
        reasons = []
        
        # Crisis and high-stress regimes → HALT (defensive rebalancing)
        if current_regime in ['CRISIS_MODE', 'DEFENSIVE']:
            signals['trading_recommendation'] = 'HALT'
            reasons.append(f"Crisis/defensive regime detected: {current_regime}")
        
        # Late cycle with high recession risk → HALT
        elif current_regime == 'LATE_CYCLE' and recession_prob >= 0.35:
            signals['trading_recommendation'] = 'HALT'
            reasons.append(f"Late cycle with high recession risk: {recession_prob:.1%}")
        
        # Extreme volatility → HALT
        elif vix >= 35:
            signals['trading_recommendation'] = 'HALT'
            reasons.append(f"Extreme volatility: VIX {vix:.1f}")
        
        # High volatility regime with elevated VIX → CAUTION
        elif current_regime == 'HIGH_VOLATILITY' and vix >= 25:
            signals['trading_recommendation'] = 'CAUTION'
            reasons.append(f"High volatility regime with elevated VIX: {vix:.1f}")
        
        # High recession probability → CAUTION or HALT
        elif recession_prob >= 0.5:
            signals['trading_recommendation'] = 'HALT'
            reasons.append(f"Very high recession probability: {recession_prob:.1%}")
        elif recession_prob >= 0.3:
            signals['trading_recommendation'] = 'CAUTION'
            reasons.append(f"Elevated recession probability: {recession_prob:.1%}")
        
        # Deep yield curve inversion → CAUTION
        elif yield_curve_bps < -50:
            signals['trading_recommendation'] = 'CAUTION'
            reasons.append(f"Deep yield curve inversion: {yield_curve_bps:.0f} bps")
        
        # Late cycle regime with moderate risk → CAUTION
        elif current_regime == 'LATE_CYCLE':
            signals['trading_recommendation'] = 'CAUTION'
            reasons.append(f"Late cycle regime detected")
        
        # High volatility environments → CAUTION
        elif vix >= 25:
            signals['trading_recommendation'] = 'CAUTION'
            reasons.append(f"Elevated volatility: VIX {vix:.1f}")
        
        # Otherwise proceed based on regime confidence
        else:
            if regime_confidence >= 0.7:
                signals['trading_recommendation'] = 'PROCEED'
                reasons.append(f"Stable {current_regime} regime with high confidence")
            else:
                signals['trading_recommendation'] = 'CAUTION'
                reasons.append(f"Uncertain regime classification: {regime_confidence:.0%} confidence")
        
        # Add specific reason based on recommendation
        if signals['trading_recommendation'] == 'HALT':
            signals['halt_reason'] = '; '.join(reasons)
        elif signals['trading_recommendation'] == 'CAUTION':
            signals['caution_reason'] = '; '.join(reasons)
        else:
            signals['proceed_reason'] = '; '.join(reasons)
        
        signals['reasons'] = reasons
        
        logger.info(f"🎯 Trading Recommendation: {signals['trading_recommendation']}")
        for reason in reasons:
            logger.info(f"   📝 {reason}")
        
        return signals
        
    except Exception as e:
        logger.error(f"❌ Error extracting macro signals: {e}")
        import traceback
        traceback.print_exc()
        
        # Return conservative fallback
        return {
            'timestamp': datetime.now().isoformat(),
            'analysis_date': datetime.now().isoformat(),
            'trading_recommendation': 'CAUTION',
            'confidence': 0.3,
            'reasons': ['Error in analysis - defaulting to caution'],
            'error': str(e)
        }

def save_daily_signals(signals, calendar_info):
    """Save daily macro signals and calendar information to JSON files."""
    logger = logging.getLogger(__name__)
    
    try:
        # Ensure output directory exists
        output_dir = os.path.join(ROOT_DIR, 'data', 'daily_signals')
        os.makedirs(output_dir, exist_ok=True)
        
        # Add calendar information to signals
        enhanced_signals = signals.copy()
        enhanced_signals['economic_calendar'] = calendar_info
        
        # Save signals with calendar info
        signals_file = os.path.join(output_dir, 'latest_macro_signals.json')
        with open(signals_file, 'w') as f:
            json.dump(enhanced_signals, f, indent=2, default=str)
        
        # Also save timestamped version for history
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        historical_file = os.path.join(output_dir, f'macro_signals_{timestamp}.json')
        with open(historical_file, 'w') as f:
            json.dump(enhanced_signals, f, indent=2, default=str)
        
        logger.info(f"✅ Daily signals and calendar saved to {signals_file}")
        
        # Create summary for quick access
        summary = {
            'date': datetime.now().isoformat(),
            'trading_recommendation': signals['trading_recommendation'],
            'market_regime': signals.get('market_regime', {}).get('regime', 'Unknown'),
            'regime_confidence': signals.get('market_regime', {}).get('confidence', 0),
            'recession_probability': signals.get('recession_probability', 0),
            'fed_policy_direction': signals.get('fed_policy', {}).get('rate_direction', 'HOLD'),
            'next_fed_meeting_days': calendar_info.get('next_fed_meeting', {}).get('days_until', 999),
            'should_reoptimize': calendar_info.get('should_reoptimize', False),
            'optimization_urgency': calendar_info.get('urgency', 'normal'),
            'main_reasons': signals.get('reasons', [])
        }
        
        summary_file = os.path.join(output_dir, 'daily_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"📊 Daily summary saved: {signals['trading_recommendation']} recommendation")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error saving daily signals: {e}")
        return False

def main():
    """Main function to run daily PRE-MARKET macro monitoring with economic calendar."""
    logger = setup_logging()
    
    logger.info("="*60)
    logger.info("🌅 DAILY PRE-MARKET MACRO MONITOR - Enhanced")
    logger.info("="*60)
    logger.info(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"⏰ Market Opens: 9:30 AM EST (in {9.5 - datetime.now().hour:.1f} hours)")
    
    try:
        # Step 1: Check economic calendar for upcoming events (Enhanced for pre-market)
        logger.info("\n📅 STEP 1: Economic Calendar Check (Pre-Market Focus)")
        calendar_info = check_economic_calendar()
        
        # ✅ PRE-MARKET ALERT: Today's high-impact events
        if calendar_info.get('today_events'):
            logger.info("\n🚨 TODAY'S EVENT ALERT - Position defensively if needed")
            for event in calendar_info['today_events']:
                impact_emoji = {'Very High': '🔴', 'Extreme': '💥', 'High': '🟠', 'Medium': '🟡'}
                logger.info(f"   {impact_emoji.get(event['impact'], '⚪')} {event.get('time', 'TBD')}: {event['name']}")
        
        # Step 2: Run macro economic analysis
        logger.info("\n📊 STEP 2: Macro Economic Analysis")
        analysis_success = run_macro_analysis()
        
        if not analysis_success:
            logger.warning("⚠️ Macro analysis failed, proceeding with signal extraction only")
        
        # Step 3: Extract trading signals
        logger.info("\n🎯 STEP 3: Signal Extraction")
        signals = extract_macro_signals()
        
        # Step 4: Enhanced calendar integration for pre-market
        logger.info("\n🔄 STEP 4: Pre-Market Calendar Integration")
        
        # ✅ TODAY'S EVENTS IMPACT: Adjust recommendation if high-impact events today
        if calendar_info.get('morning_high_impact'):
            logger.info(f"🌅 Morning high-impact releases detected - Increasing caution")
            if signals['trading_recommendation'] == 'PROCEED':
                signals['trading_recommendation'] = 'CAUTION'
                signals['reasons'].append("High-impact morning releases today - defensive positioning")
        
        # Existing calendar urgency logic
        if calendar_info['should_reoptimize']:
            if calendar_info['urgency'] in ['extreme', 'high']:
                logger.info(f"🚨 Calendar urgency override: {calendar_info['urgency']}")
                if signals['trading_recommendation'] == 'PROCEED':
                    signals['trading_recommendation'] = 'CAUTION'
                    signals['reasons'].append("High-impact events approaching - increased caution")
        
        # Step 5: Save results
        logger.info("\n💾 STEP 5: Save Results")
        save_success = save_daily_signals(signals, calendar_info)
        
        # Enhanced pre-market summary
        logger.info("\n" + "="*60)
        logger.info("📋 PRE-MARKET DAILY MONITORING SUMMARY")
        logger.info("="*60)
        logger.info(f"🎯 Trading Recommendation: {signals['trading_recommendation']}")
        logger.info(f"🏦 Market Regime: {signals.get('market_regime', {}).get('regime', 'Unknown')}")
        logger.info(f"📊 Regime Confidence: {signals.get('market_regime', {}).get('confidence', 0):.0%}")
        
        # Pre-market specific alerts
        if calendar_info.get('today_events'):
            logger.info(f"🚨 TODAY'S EVENTS: {len(calendar_info['today_events'])} high-impact releases")
            if calendar_info.get('morning_high_impact'):
                logger.info(f"🌅 MORNING VOLATILITY EXPECTED: {len(calendar_info['morning_high_impact'])} major releases")
        
        if calendar_info['next_fed_meeting']:
            fed_meeting = calendar_info['next_fed_meeting']
            logger.info(f"🗓️  Next Fed Meeting: {fed_meeting['date']} ({fed_meeting['days_until']} days)")
        
        if calendar_info['should_reoptimize']:
            logger.info(f"⚠️  Reoptimization Recommended: {calendar_info['urgency']} urgency")
        
        # Alert for critical conditions with pre-market context
        if signals['trading_recommendation'] == 'HALT':
            logger.warning("🚨 HALT CONDITION - Consider defensive rebalancing BEFORE market open")
        elif signals['trading_recommendation'] == 'CAUTION':
            logger.warning("⚠️ CAUTION CONDITION - Heightened monitoring recommended throughout trading day")
        elif calendar_info.get('today_events'):
            logger.info("✅ PROCEED with awareness of today's high-impact events")
        
        # Pre-market timing advantage summary
        current_hour = datetime.now().hour
        if current_hour < 9:
            hours_to_open = 9.5 - current_hour
            logger.info(f"⏰ TIMING ADVANTAGE: {hours_to_open:.1f} hours to prepare before market open")
            logger.info("💡 Use this time for: Position adjustments, Risk hedging, Volatility preparation")
        
        logger.info("✅ Pre-market macro monitoring completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Daily macro monitoring failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 