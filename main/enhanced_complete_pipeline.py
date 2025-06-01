#!/usr/bin/env python3
"""
Enhanced Complete Pipeline for Quality Momentum Strategy

This is the main entry point for running the complete investment strategy pipeline
with advanced features including backtesting and comprehensive analysis.

Usage:
    python main/enhanced_complete_pipeline.py [options]
    
Options:
    --skip-data-collection    Skip data collection steps
    --skip-backtesting       Skip historical backtesting
    --backtest-years N       Years of backtesting data (default: 3)
    --test-mode             Run in test mode with limited data
"""

import os
import sys
import subprocess
import argparse
import time
from datetime import datetime

# Add src to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, os.path.join(project_root, 'src'))

def print_header():
    """Print pipeline header."""
    print("🚀 QUALITY MOMENTUM STRATEGY - COMPLETE ANALYSIS PIPELINE")
    print("=" * 80)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Working directory: {project_root}")
    print("🎯 Focus: Data Analysis + Portfolio Construction + Backtesting")
    print()

def print_progress(current_step, total_steps, step_name, status="RUNNING"):
    """Print progress indicator."""
    progress = int((current_step / total_steps) * 20)
    bar = "█" * progress + "░" * (20 - progress)
    percentage = int((current_step / total_steps) * 100)
    
    if status == "RUNNING":
        emoji = "🔄"
    elif status == "COMPLETED":
        emoji = "✅"
    elif status == "FAILED":
        emoji = "❌"
    else:
        emoji = "📊"
    
    print(f"\n{emoji} STEP {current_step}/{total_steps}: {step_name}")
    print(f"Progress: [{bar}] {percentage}%")
    print(f"{'='*60}")

def run_script(script_path, step_name, current_step, total_steps, optional=False):
    """Run a script with enhanced progress tracking."""
    print_progress(current_step, total_steps, step_name, "RUNNING")
    
    full_path = os.path.join(project_root, script_path)
    
    if not os.path.exists(full_path):
        if optional:
            print(f"⚠️ Optional step skipped: {script_path} not found")
            return True
        else:
            print(f"❌ Required file not found: {script_path}")
            return False
    
    start_time = time.time()
    
    try:
        # Run with real-time output
        process = subprocess.Popen([sys.executable, full_path], 
                                 cwd=project_root, 
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 text=True,
                                 bufsize=1,
                                 universal_newlines=True)
        
        # Print output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"  📝 {output.strip()}")
        
        rc = process.poll()
        elapsed_time = time.time() - start_time
        
        if rc == 0:
            print_progress(current_step, total_steps, step_name, "COMPLETED")
            print(f"⏱️ Completed in {elapsed_time:.1f} seconds")
            return True
        else:
            print_progress(current_step, total_steps, step_name, "FAILED")
            print(f"❌ {step_name} failed after {elapsed_time:.1f} seconds")
            return False
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ Error running {step_name} after {elapsed_time:.1f} seconds: {str(e)}")
        return False

def main():
    """Execute enhanced complete pipeline."""
    parser = argparse.ArgumentParser(description='Quality Momentum Strategy Analysis Pipeline')
    parser.add_argument('--skip-data-collection', action='store_true',
                       help='Skip data collection steps (use existing data)')
    parser.add_argument('--skip-backtesting', action='store_true',
                       help='Skip historical backtesting')
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
        ("src/analysis/06_monte_carlo_simulation.py", "Monte Carlo Risk Analysis"),
    ]
    
    backtesting_step = ("trading/backtesting/06_historical_backtesting.py", "Historical Backtesting")
    
    success_count = 0
    total_steps = len(core_steps)
    if not args.skip_backtesting:
        total_steps += 1
    
    pipeline_start_time = time.time()
    
    # Run core pipeline steps
    if not args.skip_data_collection:
        current_step = 0
        
        for script_path, step_name in core_steps:
            current_step += 1
            if run_script(script_path, step_name, current_step, total_steps):
                success_count += 1
            else:
                print(f"❌ Core pipeline failed at: {step_name}")
                return 1
    else:
        print("⏭️ SKIPPING DATA COLLECTION - Using existing data")
        success_count = len(core_steps)
        current_step = len(core_steps)
    
    # Run backtesting
    if not args.skip_backtesting:
        current_step += 1
        if run_script(backtesting_step[0], backtesting_step[1], current_step, total_steps, optional=True):
            success_count += 1
    
    # Final summary
    total_elapsed = time.time() - pipeline_start_time
    
    print(f"\n{'='*80}")
    print(f"🏁 PIPELINE EXECUTION COMPLETE")
    print(f"{'='*80}")
    print(f"✅ Completed steps: {success_count}/{total_steps}")
    print(f"⏱️ Total execution time: {total_elapsed/60:.1f} minutes")
    print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_count == total_steps:
        print("\n🎉 ANALYSIS PIPELINE COMPLETED SUCCESSFULLY!")
        print("\n📁 Generated files locations:")
        print("  📊 Raw Data: data/raw/")
        print("  📈 Processed Data: data/processed/")
        print("  🎯 Portfolio: data/processed/portfolios/")
        print("  📊 Backtest Results: trading/backtesting/")
        print("  📄 Reports: reports/")
        
        print("\n🎯 Key Outputs:")
        print("  📊 Final Portfolio: 04_unified_portfolio_selection_*.csv")
        print("  📈 Backtest Report: 06_backtest_report_*.html")
        print("  📊 Performance Charts: 06_performance_charts_*.png")
        
        print("\n🔧 Next steps:")
        print("  - Review portfolio performance in backtest results")
        print("  - Analyze risk metrics in Monte Carlo reports")
        print("  - Consider implementing live trading (if desired)")
        return 0
    else:
        print("\n❌ PIPELINE COMPLETED WITH ERRORS!")
        return 1

if __name__ == "__main__":
    exit(main()) 