#!/usr/bin/env python3
"""
Quality Momentum Strategy - Complete Pipeline Runner

This script executes the entire Quality Momentum Strategy pipeline in sequence:
1. Universe Collection (S&P 600)
2. Fundamental Data Collection  
3. Sector Scoring Analysis
4. Portfolio Construction
5. Risk Analysis with Fama-French
6. Macro Economic Analysis

Usage: python run_complete_pipeline.py [--skip-data-collection] [--test-mode]
"""

import subprocess
import sys
import os
import time
from datetime import datetime
import argparse

def run_script(script_path, description):
    """Run a Python script and handle errors."""
    print(f"\n{'='*80}")
    print(f"RUNNING: {description}")
    print(f"Script: {script_path}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=False, 
                              text=True, 
                              check=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n✅ {description} completed successfully!")
        print(f"⏱️  Duration: {duration:.1f} seconds")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed!")
        print(f"Error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Run Quality Momentum Strategy Pipeline')
    parser.add_argument('--skip-data-collection', action='store_true', 
                       help='Skip steps 1-2 (universe and data collection)')
    parser.add_argument('--test-mode', action='store_true',
                       help='Run in test mode with limited data')
    
    args = parser.parse_args()
    
    print("🚀 QUALITY MOMENTUM STRATEGY - COMPLETE PIPELINE")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.skip_data_collection:
        print("⚠️  Skipping data collection steps (using existing data)")
    
    if args.test_mode:
        print("🧪 Running in TEST MODE")
    
    # Get script paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    universe_dir = os.path.join(base_dir, 'universe')
    data_collection_dir = os.path.join(base_dir, 'data_collection')
    
    pipeline_steps = []
    
    if not args.skip_data_collection:
        pipeline_steps.extend([
            (os.path.join(universe_dir, '01_universe_collection.py'), 
             "Step 1: S&P 600 Universe Collection"),
            (os.path.join(data_collection_dir, '02_fundamental_data_collection.py'), 
             "Step 2: Fundamental Data Collection")
        ])
    
    pipeline_steps.extend([
        (os.path.join(data_collection_dir, '03_sector_scoring_analysis.py'), 
         "Step 3: Sector Scoring Analysis"),
        (os.path.join(data_collection_dir, '04_portfolio_construction.py'), 
         "Step 4: Portfolio Construction"),
        (os.path.join(data_collection_dir, '05_risk_analysis_with_ff.py'), 
         "Step 5: Risk Analysis with Fama-French"),
        (os.path.join(data_collection_dir, '06_macro_economic_analysis.py'), 
         "Step 6: Macro Economic Analysis")
    ])
    
    # Run pipeline
    successful_steps = 0
    total_start_time = time.time()
    
    for script_path, description in pipeline_steps:
        if os.path.exists(script_path):
            success = run_script(script_path, description)
            if success:
                successful_steps += 1
            else:
                print(f"\n💥 Pipeline failed at: {description}")
                print("❌ Aborting remaining steps")
                break
        else:
            print(f"\n❌ Script not found: {script_path}")
            break
    
    # Summary
    total_duration = time.time() - total_start_time
    
    print(f"\n{'='*80}")
    print("🏁 PIPELINE EXECUTION SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Successful Steps: {successful_steps}/{len(pipeline_steps)}")
    print(f"⏱️  Total Duration: {total_duration/60:.1f} minutes")
    print(f"🏁 End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if successful_steps == len(pipeline_steps):
        print("\n🎉 COMPLETE PIPELINE EXECUTION SUCCESSFUL!")
        print("\n📊 Generated Files:")
        print("  • 01_universe_sp600_companies_YYYY-MM-DD.csv")
        print("  • 02_fundamentals_with_momentum_YYYY-MM-DD.csv") 
        print("  • 03_sector_scored_companies_YYYY-MM-DD.csv")
        print("  • 04_final_portfolio_selection_YYYY-MM-DD.csv")
        print("  • 05_macro_economic_analysis_YYYY-MM-DD.csv")
        print("  • risk_analysis/portfolio_correlations_YYYY-MM-DD.csv")
        print("  • risk_analysis/portfolio_risk_metrics_YYYY-MM-DD.csv")
        
        print(f"\n📈 Your Quality Momentum Strategy portfolio is ready!")
        
        return 0
    else:
        print(f"\n💥 Pipeline incomplete: {successful_steps}/{len(pipeline_steps)} steps completed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 