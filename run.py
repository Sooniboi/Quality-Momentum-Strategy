#!/usr/bin/env python3
"""
Quality Momentum Strategy - Quick Start

Simple entry point for running the complete quality momentum strategy pipeline.
This script provides an easy way to execute the full analysis and backtesting workflow.

Usage:
    python run.py [options]
    
Examples:
    python run.py                              # Run complete pipeline
    python run.py --skip-data-collection       # Use existing data
    python run.py --skip-backtesting          # Analysis only, no backtesting
"""

import sys
import subprocess
import argparse

def main():
    """Quick start for Quality Momentum Strategy."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Quality Momentum Strategy - Quick Start')
    parser.add_argument('--skip-data-collection', action='store_true',
                       help='Skip data collection, use existing data')
    parser.add_argument('--skip-backtesting', action='store_true',
                       help='Skip historical backtesting')
    parser.add_argument('--test-mode', action='store_true',
                       help='Run in test mode with limited data')
    
    args = parser.parse_args()
    
    print("🚀 Quality Momentum Strategy - Quick Start")
    print("=" * 50)
    print("🔀 Routing to main enhanced pipeline...")
    print()
    
    # Build command for enhanced pipeline
    cmd = [sys.executable, "main/enhanced_complete_pipeline.py"]
    
    # Add arguments
    if args.skip_data_collection:
        cmd.append("--skip-data-collection")
    if args.skip_backtesting:
        cmd.append("--skip-backtesting")
    if args.test_mode:
        cmd.append("--test-mode")
    
    # Execute enhanced pipeline
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⚠️ Pipeline interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error executing pipeline: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 