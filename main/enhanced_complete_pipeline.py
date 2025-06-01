#!/usr/bin/env python3
"""
Enhanced Complete Pipeline for Quality Momentum Strategy

This is the main entry point for running the complete investment strategy pipeline
with advanced features including backtesting, paper trading, and automation.

Usage:
    python main/enhanced_complete_pipeline.py [options]
    
Options:
    --skip-data-collection    Skip data collection steps
    --skip-backtesting       Skip historical backtesting
    --skip-paper-trading     Skip paper trading setup
    --backtest-years N       Years of backtesting data (default: 3)
    --test-mode             Run in test mode with limited data
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime

# Add src to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, os.path.join(project_root, 'src'))

def print_header():
    """Print pipeline header."""
    print("🚀 ENHANCED QUALITY MOMENTUM STRATEGY PIPELINE")
    print("=" * 80)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Working directory: {project_root}")
    print()

def run_script(script_path, step_name, optional=False):
    """Run a script with error handling."""
    print(f"\n{'='*60}")
    print(f"🚀 STEP: {step_name}")
    print(f"{'='*60}")
    
    full_path = os.path.join(project_root, script_path)
    
    if not os.path.exists(full_path):
        if optional:
            print(f"⚠️ Optional step skipped: {script_path} not found")
            return True
        else:
            print(f"❌ Required file not found: {script_path}")
            return False
    
    try:
        result = subprocess.run([sys.executable, full_path], 
                              cwd=project_root, 
                              capture_output=True, 
                              text=True)
        
        if result.returncode == 0:
            print(f"✅ {step_name} completed successfully")
            return True
        else:
            print(f"❌ {step_name} failed")
            print("Error output:", result.stderr[-1000:])  # Last 1000 chars
            return False
            
    except Exception as e:
        print(f"❌ Error running {step_name}: {str(e)}")
        return False

def main():
    """Execute enhanced complete pipeline."""
    parser = argparse.ArgumentParser(description='Enhanced Quality Momentum Strategy Pipeline')
    parser.add_argument('--skip-data-collection', action='store_true',
                       help='Skip data collection steps (use existing data)')
    parser.add_argument('--skip-backtesting', action='store_true',
                       help='Skip historical backtesting')
    parser.add_argument('--skip-paper-trading', action='store_true',
                       help='Skip paper trading setup')
    parser.add_argument('--backtest-years', type=int, default=3,
                       help='Years of backtesting data (default: 3)')
    parser.add_argument('--test-mode', action='store_true',
                       help='Run in test mode with limited data')
    
    args = parser.parse_args()
    
    print_header()
    
    # Define pipeline steps
    core_steps = [
        ("src/data_collection/01_universe_collection.py", "Universe Collection"),
        ("src/data_collection/02_fundamental_data_collection.py", "Fundamental Data Collection"),
        ("src/analysis/03_sector_scoring_analysis.py", "Sector Scoring Analysis"),
        ("src/analysis/04_macro_economic_analysis.py", "Macro Economic Analysis"),
        ("src/portfolio/05_unified_portfolio_construction.py", "Portfolio Construction"),
        ("src/analysis/06_monte_carlo_simulation.py", "Monte Carlo Simulation"),
    ]
    
    optional_steps = [
        ("trading/backtesting/06_historical_backtesting.py", "Historical Backtesting"),
        ("trading/paper_trading/07_paper_trading_setup.py", "Paper Trading Setup"),
    ]
    
    success_count = 0
    total_steps = len(core_steps)
    
    # Run core pipeline steps
    if not args.skip_data_collection:
        print("📊 RUNNING CORE PIPELINE STEPS")
        print("-" * 40)
        
        for script_path, step_name in core_steps:
            if run_script(script_path, step_name):
                success_count += 1
            else:
                print(f"❌ Core pipeline failed at: {step_name}")
                return 1
    else:
        print("⏭️ SKIPPING DATA COLLECTION - Using existing data")
        success_count = len(core_steps)
    
    # Run optional steps
    if not args.skip_backtesting:
        print("\n📈 RUNNING BACKTESTING")
        print("-" * 40)
        if run_script(optional_steps[0][0], optional_steps[0][1], optional=True):
            total_steps += 1
            success_count += 1
    
    if not args.skip_paper_trading:
        print("\n💼 SETTING UP PAPER TRADING")
        print("-" * 40)
        if run_script(optional_steps[1][0], optional_steps[1][1], optional=True):
            total_steps += 1
            success_count += 1
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"📊 PIPELINE EXECUTION SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Completed steps: {success_count}/{total_steps}")
    print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_count == total_steps:
        print("\n🎉 ENHANCED PIPELINE COMPLETED SUCCESSFULLY!")
        print("\n📁 Generated files locations:")
        print("  📊 Data: data/processed/")
        print("  📈 Reports: reports/")
        print("  💼 Trading: trading/")
        print("\n🔧 Next steps:")
        print("  - Review portfolio in data/processed/portfolios/")
        print("  - Check backtest results in trading/backtesting/")
        print("  - Monitor paper trading in trading/paper_trading/")
        print("  - Consider setting up automation/08_automation_scheduler.py")
        return 0
    else:
        print("\n❌ PIPELINE COMPLETED WITH ERRORS!")
        return 1

if __name__ == "__main__":
    exit(main()) 