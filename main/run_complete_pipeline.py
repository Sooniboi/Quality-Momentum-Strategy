#!/usr/bin/env python3
"""
Quality Momentum Strategy - Complete Pipeline Runner
====================================================

Main execution script for the complete investment strategy pipeline.
Runs all steps from universe collection to portfolio construction.

Usage:
    python main/run_complete_pipeline.py [--skip-existing]
"""

import os
import sys
import subprocess
import pandas as pd
from datetime import datetime

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_step(script_path, step_name, skip_existing=False):
    """Run a pipeline step with error handling."""
    print(f"\n{'='*60}")
    print(f"🚀 RUNNING: {step_name}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__) + "/..")
        
        if result.returncode == 0:
            print(f"✅ {step_name} completed successfully")
            if result.stdout:
                print("Output:", result.stdout[-500:])  # Last 500 chars
            return True
        else:
            print(f"❌ {step_name} failed")
            print("Error:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running {step_name}: {str(e)}")
        return False

def main():
    """Execute complete pipeline."""
    print("🎯 QUALITY MOMENTUM STRATEGY - COMPLETE PIPELINE")
    print("=" * 70)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Define pipeline steps
    steps = [
        ("src/data_collection/01_universe_collection.py", "Universe Collection"),
        ("src/data_collection/02_fundamental_data_collection.py", "Fundamental Data"),
        ("src/analysis/03_sector_scoring_analysis.py", "Sector Scoring"),
        ("src/analysis/04_macro_economic_analysis.py", "Macro Analysis"),
        ("src/portfolio/05_unified_portfolio_construction.py", "Portfolio Construction"),
        ("src/analysis/06_monte_carlo_simulation.py", "Monte Carlo Simulation"),
    ]
    
    success_count = 0
    
    for script_path, step_name in steps:
        if run_step(script_path, step_name):
            success_count += 1
        else:
            print(f"❌ Pipeline failed at step: {step_name}")
            break
    
    # Summary
    print(f"\n{'='*70}")
    print(f"📊 PIPELINE SUMMARY")
    print(f"{'='*70}")
    print(f"✅ Completed steps: {success_count}/{len(steps)}")
    print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_count == len(steps):
        print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        print("\n📁 Check data/results/ for output files")
        print("📊 Run trading/backtesting/run_backtest.py for historical analysis")
        return 0
    else:
        print("❌ PIPELINE FAILED!")
        return 1

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run Quality Momentum Strategy Pipeline')
    parser.add_argument('--skip-existing', action='store_true', 
                       help='Skip steps with existing output files')
    args = parser.parse_args()
    
    exit(main()) 