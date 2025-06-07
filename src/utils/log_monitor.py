#!/usr/bin/env python3
"""
Log Monitoring System for Quality Momentum Strategy
Monitors all important logs and provides real-time alerts
"""

import os
import time
import logging
from datetime import datetime
from pathlib import Path
import subprocess
from typing import Dict, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class LogMonitor:
    """Monitors all system logs and provides real-time alerts."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.logs_dir = self.base_dir / 'logs'
        self.reports_dir = self.base_dir / 'reports' / 'weekly' / 'generated'
        
        # Setup monitoring log
        self.setup_monitoring_log()
        
        # Log files to monitor
        self.log_files = {
            'weekly_reporter': self.logs_dir / 'weekly_reporter.log',
            'live_trading': self.logs_dir / 'live_trading_automation.log',
            'alpaca_trading': self.logs_dir / 'alpaca_trading.log',
            'macro_monitor': self.logs_dir / 'macro_monitor.log'
        }
        
        # Load email config
        self.load_email_config()
        
        # Track last positions
        self.last_positions = {}
        
    def setup_monitoring_log(self):
        """Setup the monitoring system's own log file."""
        self.logger = logging.getLogger('log_monitor')
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        self.logs_dir.mkdir(exist_ok=True)
        
        # Add file handler
        fh = logging.FileHandler(self.logs_dir / 'log_monitor.log')
        fh.setLevel(logging.INFO)
        
        # Add console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
    
    def load_email_config(self):
        """Load email configuration from .env file."""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            self.email_config = {
                'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                'smtp_port': int(os.getenv('SMTP_PORT', 587)),
                'sender_email': os.getenv('SENDER_EMAIL'),
                'sender_password': os.getenv('SENDER_PASSWORD'),
                'recipient_email': os.getenv('RECIPIENT_EMAIL')
            }
            
            if not all([self.email_config['sender_email'], 
                       self.email_config['sender_password'], 
                       self.email_config['recipient_email']]):
                self.logger.warning("⚠️ Email configuration incomplete")
                
        except Exception as e:
            self.logger.error(f"❌ Error loading email config: {e}")
            self.email_config = None
    
    def send_alert(self, subject: str, message: str, is_critical: bool = False):
        """Send email alert."""
        if not self.email_config:
            self.logger.warning("⚠️ Cannot send alert - email config missing")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['recipient_email']
            msg['Subject'] = f"{'🚨 CRITICAL: ' if is_critical else '⚠️ '}{subject}"
            
            body = f"""
🔍 Quality Momentum Strategy - System Alert

{message}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
System: Automated Log Monitor
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['sender_email'], self.email_config['sender_password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['sender_email'], self.email_config['recipient_email'], text)
            server.quit()
            
            self.logger.info(f"✅ Alert sent: {subject}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send alert: {e}")
    
    def check_weekly_report(self):
        """Check if weekly report was generated and sent."""
        try:
            # Check if report was generated today
            today = datetime.now().strftime('%Y_%m_%d')
            report_files = list(self.reports_dir.glob(f'*{today}*.pdf'))
            
            if not report_files:
                self.send_alert(
                    "Weekly Report Not Generated",
                    "No weekly report was generated today. Please check the system.",
                    is_critical=True
                )
                return False
            
            # Check log for successful email
            with open(self.log_files['weekly_reporter'], 'r') as f:
                log_content = f.read()
                if "✅ Enhanced email sent successfully!" not in log_content:
                    self.send_alert(
                        "Weekly Report Email Failed",
                        "Report was generated but email sending failed. Please check the logs.",
                        is_critical=True
                    )
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error checking weekly report: {e}")
            return False
    
    def check_trading_status(self):
        """Check if trading system is running properly."""
        try:
            with open(self.log_files['live_trading'], 'r') as f:
                log_content = f.read()
                
                # Check for errors
                if "❌" in log_content or "ERROR" in log_content:
                    self.send_alert(
                        "Trading System Error",
                        "Errors detected in trading system. Please check the logs.",
                        is_critical=True
                    )
                    return False
                
                # Check for successful trades
                if "✅ Trade executed" not in log_content:
                    self.logger.warning("⚠️ No successful trades found in recent logs")
                
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error checking trading status: {e}")
            return False
    
    def check_macro_monitor(self):
        """Check if macro monitoring is working."""
        try:
            with open(self.log_files['macro_monitor'], 'r') as f:
                log_content = f.read()
                
                # Check for errors
                if "❌" in log_content or "ERROR" in log_content:
                    self.send_alert(
                        "Macro Monitor Error",
                        "Errors detected in macro monitoring system. Please check the logs.",
                        is_critical=True
                    )
                    return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error checking macro monitor: {e}")
            return False
    
    def monitor_logs(self):
        """Main monitoring loop."""
        self.logger.info("🚀 Starting log monitoring system...")
        
        while True:
            try:
                # Check weekly report
                if datetime.now().hour >= 16 and datetime.now().weekday() == 4:  # Friday after 4 PM
                    self.check_weekly_report()
                
                # Check trading status
                self.check_trading_status()
                
                # Check macro monitor
                self.check_macro_monitor()
                
                # Sleep for 5 minutes
                time.sleep(300)
                
            except KeyboardInterrupt:
                self.logger.info("👋 Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                time.sleep(60)  # Sleep for 1 minute on error

def main():
    """Main entry point."""
    monitor = LogMonitor()
    monitor.monitor_logs()

if __name__ == "__main__":
    main() 