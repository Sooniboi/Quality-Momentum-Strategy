#!/usr/bin/env python3
"""
Start Log Monitoring System
This script starts the log monitoring system in the background
"""

import subprocess
import sys
import os
from pathlib import Path

def start_monitor():
    """Start the log monitoring system."""
    # Get the directory of this script
    script_dir = Path(__file__).parent
    
    # Path to the monitor script
    monitor_script = script_dir / 'src' / 'utils' / 'log_monitor.py'
    
    # Check if script exists
    if not monitor_script.exists():
        print("❌ Error: Monitor script not found!")
        sys.exit(1)
    
    # Start the monitor in the background
    try:
        # Use nohup to keep it running after terminal closes
        cmd = f"nohup python3 {monitor_script} > logs/log_monitor.out 2>&1 &"
        subprocess.run(cmd, shell=True, check=True)
        
        print("✅ Log monitoring system started successfully!")
        print("📝 Logs will be written to logs/log_monitor.log")
        print("📧 Alerts will be sent to your configured email")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting monitor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_monitor() 