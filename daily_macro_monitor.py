#!/usr/bin/env python3
"""
Daily Macro Economic Monitor
Runs daily to check market regime, recession risk, and Fed policy.
Results are saved for weekly portfolio reoptimization to check.

Usage: python daily_macro_monitor.py
"""

import os
import sys
import json
import subprocess
from datetime import datetime, date
import logging

# Add src to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'src'))

def setup_logging():
    """Setup logging for daily macro monitoring."""
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/daily_macro_monitor.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def run_macro_analysis():
    """Run the macro economic analysis and save results."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🔄 Starting daily macro economic analysis...")
        
        # Run the macro analysis script
        result = subprocess.run([
            sys.executable, 
            'src/analysis/04_macro_economic_analysis.py'
        ], capture_output=True, text=True, cwd=current_dir)
        
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
        
        # Import enhanced macro analysis directly
        import importlib.util
        
        analysis_path = os.path.join(current_dir, 'src', 'analysis', '04_macro_economic_analysis.py')
        spec = importlib.util.spec_from_file_location("macro_economic_analysis", analysis_path)
        macro_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(macro_module)
        
        # Get current market conditions
        treasury_rates = macro_module.get_treasury_rates()
        economic_indicators = macro_module.get_economic_indicators()
        yield_curve = macro_module.calculate_yield_curve_metrics(treasury_rates)
        
        # Run enhanced regime classification
        regime_analysis = macro_module.classify_market_regime(economic_indicators, yield_curve)
        current_regime = regime_analysis.get('regime', 'OPTIMISTIC')
        regime_confidence = regime_analysis.get('confidence', 0.5)
        market_conditions = regime_analysis.get('market_conditions', {})
        regime_characteristics = regime_analysis.get('characteristics', {})
        
        # Get recession analysis
        try:
            recession_analysis = macro_module.calculate_recession_probability(
                treasury_rates, {}, economic_indicators
            )
            recession_prob = recession_analysis.get('recession_probability', 0) / 100  # Convert to decimal
        except:
            recession_prob = 0.15  # Default moderate level
            
        # Get Fed policy analysis
        try:
            fred_data = macro_module.get_fred_economic_data()
            fed_analysis = macro_module.analyze_fed_policy_stance(fred_data)
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
        
        logger.info(f"🎯 Final Recommendation: {signals['trading_recommendation']}")
        if reasons:
            logger.info(f"📋 Reasons: {'; '.join(reasons)}")
        
        return signals
        
    except Exception as e:
        logger.error(f"❌ Error in enhanced macro signal extraction: {e}")
        # Return conservative fallback
        return {
            'timestamp': datetime.now().isoformat(),
            'analysis_date': datetime.now().isoformat(),
            'market_regime': {'regime': 'unknown', 'confidence': 0.5},
            'recession_probability': 0.25,  # Conservative default
            'trading_recommendation': 'CAUTION',
            'caution_reason': f'Error in macro analysis: {str(e)}',
            'confidence': 0.3,
            'reasons': ['Fallback due to analysis error']
        }

def save_daily_signals(signals):
    """Save daily macro signals for weekly reoptimization to check."""
    logger = logging.getLogger(__name__)
    
    try:
        # Create directory
        signals_dir = 'data/processed/daily_macro_signals'
        os.makedirs(signals_dir, exist_ok=True)
        
        # Save with today's date
        today = date.today().strftime('%Y-%m-%d')
        signal_file = os.path.join(signals_dir, f'macro_signals_{today}.json')
        
        with open(signal_file, 'w') as f:
            json.dump(signals, f, indent=2)
        
        # Also save as "latest" for easy access
        latest_file = os.path.join(signals_dir, 'latest_macro_signals.json')
        with open(latest_file, 'w') as f:
            json.dump(signals, f, indent=2)
        
        logger.info(f"💾 Saved daily macro signals to {signal_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error saving daily signals: {e}")
        return False

def main():
    """Main daily macro monitoring workflow."""
    logger = setup_logging()
    
    logger.info("🚀 Daily Macro Economic Monitor Started")
    logger.info(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Run macro analysis
        if not run_macro_analysis():
            logger.error("❌ Daily macro monitoring failed - macro analysis error")
            return False
        
        # Step 2: Extract key signals
        signals = extract_macro_signals()
        if signals is None:
            logger.error("❌ Daily macro monitoring failed - signal extraction error")
            return False
        
        # Step 3: Save signals for weekly check
        if not save_daily_signals(signals):
            logger.error("❌ Daily macro monitoring failed - signal saving error")
            return False
        
        # Step 4: Report summary
        logger.info("✅ Daily macro monitoring completed successfully")
        logger.info(f"🎯 Trading Status: {signals['trading_recommendation']}")
        
        if signals['trading_recommendation'] == 'HALT':
            logger.warning(f"⚠️ Trading halted: {signals.get('halt_reason', 'Unknown reason')}")
        elif signals['trading_recommendation'] == 'CAUTION':
            logger.warning(f"⚠️ Trading caution: {signals.get('caution_reason', 'Unknown reason')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Daily macro monitoring failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 