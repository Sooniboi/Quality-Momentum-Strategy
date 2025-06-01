#!/usr/bin/env python3
"""
Quality Momentum Strategy - Quick Start Runner

Simple entry point for running the complete system.
This script automatically routes to the main pipeline.

Usage:
    python run.py [options]
    
All command line options are passed through to the main pipeline.
"""

import os
import sys
import subprocess

def main():
    """Route to main enhanced pipeline."""
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, 'main', 'enhanced_complete_pipeline.py')
    
    # Check if main script exists
    if not os.path.exists(main_script):
        print("❌ Main pipeline script not found!")
        print(f"Expected: {main_script}")
        return 1
    
    # Pass all arguments through to main script
    cmd = [sys.executable, main_script] + sys.argv[1:]
    
    print("🚀 Quality Momentum Strategy - Quick Start")
    print("=" * 50)
    print("🔀 Routing to main enhanced pipeline...")
    print()
    
    # Execute main pipeline
    try:
        result = subprocess.run(cmd, cwd=script_dir)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⏹️ Execution interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error executing pipeline: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main()) 