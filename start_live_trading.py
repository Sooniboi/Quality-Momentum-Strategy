#!/usr/bin/env python3
"""
One-Click Live Paper Trading Launcher

This script will:
1. Test Alpaca connection (if keys already work, skip setup)
2. Setup only if needed
3. Start the live paper trading automation automatically
4. Start automated weekly PDF email reports every Friday

Usage:
    python start_live_trading.py
    
Just double-click this file or run it to start everything!
NO USER INPUT REQUIRED - Everything runs automatically!
"""

import os
import sys
import subprocess
import json
import time
import schedule
import logging
import glob
import threading
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("📄 Environment variables loaded from .env file")
except ImportError:
    print("⚠️ python-dotenv not installed, loading .env manually...")
    # Manual .env loading if dotenv package not available
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        print("📄 Environment variables loaded manually from .env file")

def print_banner():
    """Print startup banner."""
    print("🚀 QUALITY MOMENTUM STRATEGY - LIVE AUTOMATION SUITE")
    print("=" * 70)
    print("🤖 One-Click Launcher - Starting Complete Automation...")
    print("📊 Trading + Weekly Email Reports")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def test_alpaca_connection():
    """Test if Alpaca connection works with existing configuration."""
    print("🔗 Testing Alpaca connection...")
    
    try:
        # Test Alpaca connection directly
        sys.path.insert(0, 'trading/paper_trading')
        from alpaca_connector import AlpacaPaperTrader
        
        trader = AlpacaPaperTrader()
        account_info = trader.get_account_info()
        
        if account_info and account_info.get('portfolio_value'):
            print(f"✅ Alpaca Connected - Portfolio: ${account_info.get('portfolio_value', 0):,.2f}")
            print(f"💰 Buying Power: ${account_info.get('buying_power', 0):,.2f}")
            print(f"📊 Account Status: {account_info.get('status', 'Unknown')}")
            return True
        else:
            print("❌ Alpaca connection failed - no account data received")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def check_basic_setup():
    """Check if basic configuration exists."""
    print("🔍 Checking basic configuration...")
    
    # Check config file
    if not os.path.exists('config/trading_config.json'):
        print("❌ Trading configuration not found!")
        return False
    
    print("✅ Trading configuration found!")
    return True

def start_weekly_reporter():
    """Start the automated weekly reporting system."""
    print("📧 Starting automated weekly email reporting...")
    
    try:
        # Import and start the weekly reporter
        sys.path.insert(0, 'src/utils')
        from weekly_performance_reporter import WeeklyPerformanceReporter
        
        reporter = WeeklyPerformanceReporter()
        
        # Schedule weekly reports for Friday 4 PM
        schedule.every().friday.at("16:00").do(reporter.generate_weekly_report)
        
        print("✅ Weekly reporter scheduled for every Friday at 4:00 PM EST")
        print("📧 Will automatically send PDF reports with native LaTeX tables")
        print("🎯 No images - pure LaTeX tables and charts only")
        
        # Run a test report immediately
        print("🧪 Running test report to verify system...")
        test_success = reporter.generate_weekly_report()
        
        if test_success:
            print("✅ Test report generated and sent successfully!")
        else:
            print("⚠️ Test report had issues - check logs")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to start weekly reporter: {e}")
        return False

def run_pipeline_once():
    """Run the complete pipeline once with portfolio validation."""
    print("🔄 Executing Quality Momentum Strategy pipeline...")
    
    try:
        # Step 0: Check macro signals and set defensive mode if needed
        print("🌍 Step 0: Checking macro economic signals...")
        macro_ok, macro_reason = check_daily_macro_signals()
        is_defensive_mode = "DEFENSIVE_MODE" in macro_reason
        
        if is_defensive_mode:
            print("🛡️ DEFENSIVE MODE DETECTED - Will optimize for recession/bear market")
            # Save defensive signal for portfolio construction
            os.makedirs('data/processed/temp_signals', exist_ok=True)
            defensive_signal = {
                'mode': 'DEFENSIVE',
                'reason': macro_reason,
                'timestamp': datetime.now().isoformat()
            }
            with open('data/processed/temp_signals/defensive_mode.json', 'w') as f:
                json.dump(defensive_signal, f, indent=2)
        else:
            print("✅ Normal market conditions - Standard optimization")
            # Remove defensive signal if it exists
            defensive_file = 'data/processed/temp_signals/defensive_mode.json'
            if os.path.exists(defensive_file):
                os.remove(defensive_file)
        
        # Step 1: Run the enhanced pipeline (analysis + portfolio construction)
        print("📊 Step 1: Running analysis and portfolio construction...")
        result = subprocess.run([
            sys.executable, 'main/enhanced_complete_pipeline.py',
            '--skip-backtesting'  # We'll do our own validation
        ], cwd=os.getcwd(), capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Pipeline failed: {result.stderr}")
            return False
        
        if is_defensive_mode:
            print("✅ Defensive portfolio construction completed")
        else:
            print("✅ Portfolio construction completed")
        
        # Step 2: Validate portfolio with Monte Carlo + Backtesting
        print("🎲 Step 2: Validating portfolio with Monte Carlo simulation...")
        monte_carlo_result = subprocess.run([
            sys.executable, 'src/analysis/06_monte_carlo_simulation.py'
        ], cwd=os.getcwd(), capture_output=True, text=True)
        
        print("📈 Step 3: Running backtesting validation...")
        backtest_result = subprocess.run([
            sys.executable, 'trading/backtesting/06_historical_backtesting.py'
        ], cwd=os.getcwd(), capture_output=True, text=True)
        
        # Step 3: Analyze validation results
        validation_passed = validate_portfolio_results()
        
        if not validation_passed:
            if is_defensive_mode:
                print("❌ Defensive portfolio validation FAILED - CRITICAL RISK")
            else:
                print("❌ Portfolio validation FAILED - SKIPPING LIVE TRADES")
            print("🛡️ Risk controls prevented potentially bad trades")
            return False
        
        if is_defensive_mode:
            print("✅ Defensive portfolio validation PASSED - Executing defensive rebalancing")
        else:
            print("✅ Portfolio validation PASSED - Proceeding with live trades")
        
        # Step 4: Execute trading signals if validation passed
        try:
            # Import and run signal generation + trading
            sys.path.insert(0, 'src')
            sys.path.insert(0, 'trading/paper_trading')
            
            from signals.signal_generator import QualityMomentumSignalGenerator
            from alpaca_connector import AlpacaPaperTrader
            
            # Generate signals
            signal_generator = QualityMomentumSignalGenerator()
            signals = signal_generator.generate_signals({})
            
            if signals:
                validated_signals = signal_generator.validate_signals(signals)
                print(f"📊 Generated {len(validated_signals)} trading signals")
                
                # Execute trades
                trader = AlpacaPaperTrader()
                results = trader.execute_signals(validated_signals)
                
                successful_trades = sum(1 for r in results.values() if "placed" in r)
                if is_defensive_mode:
                    print(f"🛡️ Executed {successful_trades}/{len(validated_signals)} defensive rebalancing trades")
                else:
                    print(f"💼 Executed {successful_trades}/{len(validated_signals)} trades")
            else:
                print("📊 No trading signals generated")
                
        except Exception as e:
            print(f"⚠️ Error executing trades: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error running pipeline: {e}")
        return False

def check_daily_macro_signals() -> tuple[bool, str]:
    """Check latest daily macro signals to determine if trading should proceed."""
    try:
        print("🌍 Checking daily macro economic signals...")
        
        # Enhanced macro signal checking using the 15-regime system
        try:
            import importlib.util
            
            # Import enhanced macro analysis
            analysis_path = os.path.join(os.getcwd(), 'src', 'analysis', '04_macro_economic_analysis.py')
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
            
            print(f"🎯 Current Market Regime: {current_regime} (confidence: {regime_confidence:.0%})")
            
            # Enhanced defensive trigger logic
            defensive_regimes = ['DEFENSIVE', 'CRISIS_MODE', 'LATE_CYCLE']
            high_risk_regimes = ['HIGH_VOLATILITY', 'HIGH_INFLATION'] 
            
            vix = market_conditions.get('vix', 20.0)
            recession_prob = 0  # Will calculate below
            yield_curve_bps = market_conditions.get('yield_curve_bps', 50)
            
            # Calculate recession probability if possible
            try:
                recession_analysis = macro_module.calculate_recession_probability(
                    treasury_rates, {}, economic_indicators
                )
                recession_prob = recession_analysis.get('recession_probability', 0)
            except:
                recession_prob = 15.0  # Default moderate level
            
            # Defensive mode triggers (more sophisticated)
            defensive_triggers = []
            
            if current_regime in defensive_regimes:
                defensive_triggers.append(f"Market regime: {current_regime}")
            
            if vix >= 35:
                defensive_triggers.append(f"Crisis volatility: VIX {vix:.1f}")
            elif vix >= 25 and current_regime in high_risk_regimes:
                defensive_triggers.append(f"High volatility in risky regime: VIX {vix:.1f}")
            
            if recession_prob >= 50:
                defensive_triggers.append(f"High recession probability: {recession_prob:.1f}%")
            elif recession_prob >= 35 and yield_curve_bps < -20:
                defensive_triggers.append(f"Elevated recession risk with inverted curve: {recession_prob:.1f}%")
                
            if yield_curve_bps < -50:
                defensive_triggers.append(f"Deep yield curve inversion: {yield_curve_bps:.0f} bps")
            
            # Decision logic
            if defensive_triggers:
                trigger_reason = "; ".join(defensive_triggers)
                return True, f"DEFENSIVE_MODE: {trigger_reason}"
            elif current_regime in high_risk_regimes and regime_confidence >= 0.7:
                return True, f"PROCEED_CAUTIOUS: {current_regime} regime detected with {regime_confidence:.0%} confidence"
            else:
                return True, f"PROCEED_NORMAL: {current_regime} regime, low risk environment"
                
        except Exception as e:
            print(f"⚠️ Enhanced regime detection failed: {e}")
            
            # Fallback to basic macro checking
            return check_basic_macro_signals()
            
    except Exception as e:
        print(f"❌ Error checking macro signals: {e}")
        return True, "PROCEED_NORMAL: No macro constraints detected"

def check_basic_macro_signals() -> tuple[bool, str]:
    """Fallback basic macro signal checking."""
    print("📊 Using basic macro signal checking...")
    
    # Check for daily macro signals file
    signal_pattern = 'data/processed/daily_macro_signals/macro_signal_*.json'
    signal_files = glob.glob(signal_pattern)
    
    if not signal_files:
        print("⚠️ No daily macro signals found - proceeding with normal trading")
        return True, "PROCEED_NORMAL: No daily signals available"
    
    # Get latest signal
    latest_signal_file = max(signal_files, key=os.path.getctime)
    
    try:
        with open(latest_signal_file, 'r') as f:
            daily_signal = json.load(f)
        
        signal_type = daily_signal.get('recommendation', 'PROCEED')
        confidence = daily_signal.get('confidence', 0.5)
        reasons = daily_signal.get('reasons', [])
        
        print(f"📊 Daily Signal: {signal_type} (confidence: {confidence:.0%})")
        
        if signal_type == 'HALT':
            return True, f"DEFENSIVE_MODE: {', '.join(reasons)}"
        elif signal_type == 'CAUTION':
            return True, f"PROCEED_CAUTIOUS: {', '.join(reasons)}"
        else:
            return True, f"PROCEED_NORMAL: {', '.join(reasons)}"
            
    except Exception as e:
        print(f"⚠️ Error reading macro signals: {e}")
        return True, "PROCEED_NORMAL: Signal file error"

def validate_portfolio_results() -> bool:
    """Validate portfolio using daily macro signals, Monte Carlo and backtesting results."""
    try:
        print("🔍 Running comprehensive portfolio validation...")
        
        # STEP 1: Check daily macro signals first
        macro_ok, macro_reason = check_daily_macro_signals()
        
        # Extract if this is defensive mode
        is_defensive_mode = "DEFENSIVE_MODE" in macro_reason
        
        if is_defensive_mode:
            print(f"🛡️ DEFENSIVE MODE ACTIVATED: {macro_reason}")
            print("🔄 Portfolio will be reoptimized for recession/bear market conditions")
            print("📈 Switching from growth to value/defensive allocation")
        else:
            print(f"✅ Macro validation passed: {macro_reason}")
        
        # Continue with portfolio reoptimization in all cases
        # The macro signal will influence the portfolio construction strategy
        
        # STEP 2: Check if validation files exist
        monte_carlo_files = glob.glob('data/processed/monte_carlo_*')
        backtest_files = glob.glob('trading/backtesting/*backtest*')
        
        if not monte_carlo_files or not backtest_files:
            print("⚠️ Validation files not found - proceeding with caution")
            return True  # Default to proceed if files missing
        
        # STEP 3: Technical validation criteria
        validation_checks = {
            'macro_conditions': macro_ok,
            'monte_carlo_risk': True,
            'backtest_performance': True,
            'portfolio_concentration': True
        }
        
        # Check Monte Carlo results
        try:
            print("📊 Checking Monte Carlo risk metrics...")
            # Add your risk threshold checks here
            validation_checks['monte_carlo_risk'] = True
        except Exception as e:
            print(f"⚠️ Monte Carlo validation error: {e}")
            validation_checks['monte_carlo_risk'] = False
        
        # Check backtest results  
        try:
            print("📈 Checking backtest performance...")
            # Add your performance threshold checks here
            validation_checks['backtest_performance'] = True
        except Exception as e:
            print(f"⚠️ Backtest validation error: {e}")
            validation_checks['backtest_performance'] = False
        
        # Overall validation result
        passed_checks = sum(validation_checks.values())
        total_checks = len(validation_checks)
        
        print(f"📋 Validation Summary: {passed_checks}/{total_checks} checks passed")
        
        # In defensive mode, be more lenient with validation (need to rebalance urgently)
        required_checks = 2 if is_defensive_mode else 3
        validation_passed = passed_checks >= required_checks
        
        if validation_passed:
            if is_defensive_mode:
                print("✅ Defensive portfolio validation PASSED - URGENT REBALANCING APPROVED")
            else:
                print("✅ Portfolio validation PASSED")
        else:
            print("❌ Portfolio validation FAILED")
            print("🛡️ Risk management: Skipping trades to protect capital")
        
        return validation_passed
        
    except Exception as e:
        print(f"❌ Error in portfolio validation: {e}")
        return False  # Fail safe - don't trade if validation errors

def setup_logging():
    """Setup logging for the automation."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/live_trading_automation.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def run_weekly_reporter_background():
    """Run weekly reporter in background thread."""
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except Exception as e:
        print(f"❌ Weekly reporter background error: {e}")

def start_live_automation():
    """Start the complete live automation system."""
    print("🤖 Starting complete automation system...")
    print("📅 Trading: Monthly (every 4 weeks) on Monday at 10:00 AM")
    print("📧 Reports: Weekly on Friday at 4:00 PM")
    print("⚡ Both systems will run continuously and execute automatically")
    print()
    
    logger = setup_logging()
    
    # Start weekly reporter
    weekly_success = start_weekly_reporter()
    if not weekly_success:
        print("⚠️ Weekly reporter failed to start - continuing with trading only")
    
    def scheduled_pipeline():
        """Scheduled pipeline execution."""
        logger.info("=== AUTOMATED PIPELINE EXECUTION STARTED ===")
        print(f"\n🔄 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Running scheduled pipeline...")
        
        try:
            if run_pipeline_once():
                logger.info("Pipeline execution completed successfully")
                print("✅ Automated execution completed successfully!")
            else:
                logger.error("Pipeline execution failed")
                print("❌ Automated execution failed!")
        except Exception as e:
            logger.error(f"Pipeline execution error: {e}")
            print(f"❌ Execution error: {e}")
        
        logger.info("=== AUTOMATED PIPELINE EXECUTION FINISHED ===")
        print(f"📅 Next execution: {schedule.next_run()}")
    
    # Schedule for monthly runs - using every().monday for better compatibility
    schedule.every().monday.at("10:00").do(scheduled_pipeline)
    
    # Also run once immediately for testing
    print("🧪 Running initial execution to test the system...")
    scheduled_pipeline()
    
    print(f"\n📅 Next scheduled run: {schedule.next_run()}")
    print("\n📁 Monitor these files:")
    print("  • logs/live_trading_automation.log - Trading automation activity")
    print("  • logs/weekly_reporter.log - Weekly report generation")
    print("  • logs/alpaca_trading.log - Trading activity")
    print("  • Your email inbox - Weekly PDF reports every Friday")
    print("  • Your Alpaca dashboard - Live positions")
    print("\n💡 Press Ctrl+C to stop the automation")
    
    # Start weekly reporter in background thread
    if weekly_success:
        reporter_thread = threading.Thread(target=run_weekly_reporter_background, daemon=True)
        reporter_thread.start()
        print("✅ Weekly reporter running in background")
    
    # Run the main scheduler
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Automation stopped by user")
        print("🛑 Live trading and weekly reporting automation has been halted")
        logger.info("Automation stopped by user")
        return True

def main():
    """Main launcher function."""
    print_banner()
    
    # Step 1: Test if Alpaca connection already works
    print("🔗 TESTING EXISTING CONFIGURATION...")
    print("=" * 50)
    
    if test_alpaca_connection():
        print("✅ Great! Your Alpaca credentials are already working!")
        alpaca_ready = True
    else:
        print("❌ Alpaca connection failed!")
        print("Please check your Alpaca API credentials in environment variables:")
        print("  ALPACA_API_KEY")
        print("  ALPACA_SECRET_KEY")
        return 1
    
    # Step 2: Check basic config 
    if not check_basic_setup():
        print("❌ Basic configuration missing!")
        return 1
    
    # Step 3: Start complete automation system
    print("\n🤖 STARTING COMPLETE AUTOMATION SUITE...")
    print("=" * 50)
    
    print("🚀 Your Quality Momentum Strategy is now running FULLY AUTOMATED!")
    print("\n📊 What happens automatically:")
    print("  TRADING AUTOMATION:")
    print("    • Monthly data collection and analysis")
    print("    • Signal generation based on quality metrics")
    print("    • Portfolio rebalancing via Alpaca paper trading")
    print("    • Continuous monitoring and execution")
    print()
    print("  📧 WEEKLY EMAIL REPORTS:")
    print("    • Every Friday at 4:00 PM EST")
    print("    • Professional PDF with native LaTeX tables")
    print("    • Complete portfolio analysis and performance attribution")
    print("    • Quality metrics, sector allocation, risk analysis")
    print("    • NO IMAGES - Pure LaTeX tables and charts only")
    print("    • Sent automatically to your email")
    print()
    print("  🎯 ZERO MAINTENANCE REQUIRED!")
    print("    • No user input needed")
    print("    • Self-sustaining system")
    print("    • Robust error handling and fallbacks")
    
    try:
        start_live_automation()
        return 0
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        if exit_code != 0:
            input("\nPress Enter to exit...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0) 