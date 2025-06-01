#!/usr/bin/env python3
"""
Automation Scheduler for Quality Momentum Strategy

This module sets up automated scheduling for the complete pipeline:
- Configures cron jobs for regular execution
- Handles error notifications and logging
- Manages different execution schedules (daily, weekly, monthly)
- Provides monitoring and status checking

Supports multiple scheduling options:
- Linux/Mac: cron jobs
- Windows: Task Scheduler integration
- Python-based: APScheduler for cross-platform
"""

import os
import sys
import subprocess
import platform
import json
from datetime import datetime, timedelta
import schedule
import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

class AutomationScheduler:
    def __init__(self):
        """Initialize the automation scheduler."""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.base_dir, '08_scheduler_config.json')
        self.platform = platform.system().lower()
        self.load_config()
    
    def load_config(self):
        """Load or create scheduler configuration."""
        default_config = {
            "schedule_type": "monthly",  # daily, weekly, monthly
            "schedule_time": "09:00",    # HH:MM format
            "schedule_day": "first_monday",  # for monthly: first_monday, 1-31
            "email_notifications": False,
            "email_config": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "email": "your_email@gmail.com",
                "password": "your_app_password"
            },
            "pipeline_options": {
                "skip_data_collection": False,
                "skip_backtesting": False,
                "skip_paper_trading": False,
                "test_mode": False
            },
            "retry_attempts": 3,
            "retry_delay_minutes": 30,
            "last_run": None,
            "next_run": None,
            "enabled": True
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def create_cron_job(self):
        """Create cron job for Unix-like systems."""
        if self.platform not in ['linux', 'darwin']:  # darwin = macOS
            print(f"❌ Cron jobs not supported on {self.platform}")
            return False
        
        script_path = os.path.join(self.base_dir, 'enhanced_complete_pipeline.py')
        python_path = sys.executable
        
        # Build command
        cmd_parts = [python_path, script_path]
        if self.config['pipeline_options']['skip_data_collection']:
            cmd_parts.append('--skip-data-collection')
        if self.config['pipeline_options']['skip_backtesting']:
            cmd_parts.append('--skip-backtesting')
        if self.config['pipeline_options']['skip_paper_trading']:
            cmd_parts.append('--skip-paper-trading')
        if self.config['pipeline_options']['test_mode']:
            cmd_parts.append('--test-mode')
        
        command = ' '.join(cmd_parts)
        
        # Create cron schedule
        schedule_time = self.config['schedule_time']
        hour, minute = schedule_time.split(':')
        
        if self.config['schedule_type'] == 'daily':
            cron_schedule = f"{minute} {hour} * * *"
        elif self.config['schedule_type'] == 'weekly':
            cron_schedule = f"{minute} {hour} * * 1"  # Monday
        elif self.config['schedule_type'] == 'monthly':
            if self.config['schedule_day'] == 'first_monday':
                cron_schedule = f"{minute} {hour} 1-7 * 1"  # First Monday of month
            else:
                day = self.config['schedule_day']
                cron_schedule = f"{minute} {hour} {day} * *"
        
        # Create cron entry
        log_file = os.path.join(self.base_dir, 'scheduler_cron.log')
        cron_entry = f"{cron_schedule} cd {self.base_dir} && {command} >> {log_file} 2>&1"
        
        try:
            # Get current crontab
            result = subprocess.run(['crontab', '-l'], 
                                  capture_output=True, text=True)
            current_crontab = result.stdout if result.returncode == 0 else ""
            
            # Check if our job already exists
            job_marker = "# Quality Momentum Strategy Pipeline"
            if job_marker in current_crontab:
                print("⚠️ Cron job already exists, updating...")
                # Remove existing job
                lines = current_crontab.split('\n')
                filtered_lines = []
                skip_next = False
                for line in lines:
                    if job_marker in line:
                        skip_next = True
                        continue
                    if skip_next and line.strip().startswith(minute):
                        skip_next = False
                        continue
                    if line.strip():
                        filtered_lines.append(line)
                current_crontab = '\n'.join(filtered_lines)
            
            # Add new job
            new_crontab = current_crontab + f"\n{job_marker}\n{cron_entry}\n"
            
            # Write new crontab
            process = subprocess.Popen(['crontab', '-'], 
                                     stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)
            
            if process.returncode == 0:
                print(f"✅ Cron job created: {self.config['schedule_type']} at {schedule_time}")
                print(f"📝 Log file: {log_file}")
                return True
            else:
                print("❌ Failed to create cron job")
                return False
                
        except Exception as e:
            print(f"❌ Error creating cron job: {str(e)}")
            return False
    
    def create_windows_task(self):
        """Create Windows Task Scheduler task."""
        if self.platform != 'windows':
            print(f"❌ Windows Task Scheduler not supported on {self.platform}")
            return False
        
        try:
            script_path = os.path.join(self.base_dir, 'enhanced_complete_pipeline.py')
            python_path = sys.executable
            
            # Build PowerShell command to create scheduled task
            task_name = "QualityMomentumStrategy"
            
            # Create task command
            cmd_parts = [python_path, script_path]
            if self.config['pipeline_options']['skip_data_collection']:
                cmd_parts.append('--skip-data-collection')
            if self.config['pipeline_options']['skip_backtesting']:
                cmd_parts.append('--skip-backtesting')
            if self.config['pipeline_options']['skip_paper_trading']:
                cmd_parts.append('--skip-paper-trading')
            
            command = ' '.join(cmd_parts)
            
            # Create PowerShell script
            ps_script = f'''
$action = New-ScheduledTaskAction -Execute '{python_path}' -Argument '{script_path}' -WorkingDirectory '{self.base_dir}'

$trigger = New-ScheduledTaskTrigger -Weekly -WeeksInterval 1 -DaysOfWeek Monday -At '{self.config["schedule_time"]}'

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName '{task_name}' -Action $action -Trigger $trigger -Settings $settings -Force
'''
            
            # Execute PowerShell script
            result = subprocess.run(['powershell', '-Command', ps_script], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Windows scheduled task created: {task_name}")
                return True
            else:
                print(f"❌ Failed to create Windows task: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating Windows task: {str(e)}")
            return False
    
    def setup_python_scheduler(self):
        """Setup Python-based scheduler using schedule library."""
        print("🐍 Setting up Python-based scheduler...")
        
        def run_pipeline():
            """Execute the pipeline."""
            try:
                logging.info("Starting scheduled pipeline execution")
                
                script_path = os.path.join(self.base_dir, 'enhanced_complete_pipeline.py')
                cmd = [sys.executable, script_path]
                
                if self.config['pipeline_options']['skip_data_collection']:
                    cmd.append('--skip-data-collection')
                if self.config['pipeline_options']['skip_backtesting']:
                    cmd.append('--skip-backtesting')
                if self.config['pipeline_options']['skip_paper_trading']:
                    cmd.append('--skip-paper-trading')
                if self.config['pipeline_options']['test_mode']:
                    cmd.append('--test-mode')
                
                result = subprocess.run(cmd, capture_output=True, text=True, 
                                      cwd=self.base_dir)
                
                if result.returncode == 0:
                    logging.info("Pipeline executed successfully")
                    self.config['last_run'] = datetime.now().isoformat()
                    self.save_config()
                    
                    if self.config['email_notifications']:
                        self.send_notification("SUCCESS", "Pipeline completed successfully")
                else:
                    logging.error(f"Pipeline failed: {result.stderr}")
                    if self.config['email_notifications']:
                        self.send_notification("ERROR", f"Pipeline failed: {result.stderr}")
                        
            except Exception as e:
                logging.error(f"Error running pipeline: {str(e)}")
                if self.config['email_notifications']:
                    self.send_notification("ERROR", f"Exception: {str(e)}")
        
        # Schedule based on configuration
        schedule_time = self.config['schedule_time']
        
        if self.config['schedule_type'] == 'daily':
            schedule.every().day.at(schedule_time).do(run_pipeline)
        elif self.config['schedule_type'] == 'weekly':
            schedule.every().monday.at(schedule_time).do(run_pipeline)
        elif self.config['schedule_type'] == 'monthly':
            # For monthly, we'll approximate with every 4 weeks
            schedule.every(4).weeks.at(schedule_time).do(run_pipeline)
        
        print(f"✅ Python scheduler configured: {self.config['schedule_type']} at {schedule_time}")
        
        # Calculate next run time
        jobs = schedule.get_jobs()
        if jobs:
            next_run = jobs[0].next_run
            self.config['next_run'] = next_run.isoformat() if next_run else None
            self.save_config()
            print(f"📅 Next run scheduled: {next_run}")
        
        return True
    
    def send_notification(self, status, message):
        """Send email notification."""
        if not self.config['email_notifications']:
            return
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            email_config = self.config['email_config']
            
            msg = MIMEMultipart()
            msg['From'] = email_config['email']
            msg['To'] = email_config['email']
            msg['Subject'] = f"Quality Momentum Strategy - {status}"
            
            body = f"""
Quality Momentum Strategy Pipeline Status: {status}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Message: {message}

This is an automated notification from your Quality Momentum Strategy system.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['email'], email_config['password'])
            text = msg.as_string()
            server.sendmail(email_config['email'], email_config['email'], text)
            server.quit()
            
            logging.info("Notification email sent")
            
        except Exception as e:
            logging.error(f"Failed to send notification: {str(e)}")
    
    def run_scheduler_daemon(self):
        """Run the Python scheduler as a daemon."""
        print("🔄 Starting Python scheduler daemon...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            print("\n🛑 Scheduler daemon stopped")
            return True
    
    def install_scheduler(self, scheduler_type='auto'):
        """Install the appropriate scheduler for the platform."""
        print("🛠️ INSTALLING AUTOMATION SCHEDULER")
        print("=" * 50)
        
        if scheduler_type == 'auto':
            if self.platform in ['linux', 'darwin']:
                scheduler_type = 'cron'
            elif self.platform == 'windows':
                scheduler_type = 'windows'
            else:
                scheduler_type = 'python'
        
        success = False
        
        if scheduler_type == 'cron':
            success = self.create_cron_job()
        elif scheduler_type == 'windows':
            success = self.create_windows_task()
        elif scheduler_type == 'python':
            success = self.setup_python_scheduler()
            if success:
                print("\n⚠️ Python scheduler requires manual daemon start:")
                print(f"python {__file__} --run-daemon")
        
        if success:
            print(f"\n✅ Scheduler installed successfully ({scheduler_type})")
            print(f"📅 Schedule: {self.config['schedule_type']} at {self.config['schedule_time']}")
            
            if self.config['email_notifications']:
                print("📧 Email notifications enabled")
            
            return True
        else:
            print(f"\n❌ Failed to install scheduler ({scheduler_type})")
            return False
    
    def status_check(self):
        """Check scheduler status and display information."""
        print("📊 SCHEDULER STATUS")
        print("=" * 30)
        print(f"Platform: {self.platform.title()}")
        print(f"Enabled: {self.config['enabled']}")
        print(f"Schedule: {self.config['schedule_type'].title()} at {self.config['schedule_time']}")
        
        if self.config['last_run']:
            last_run = datetime.fromisoformat(self.config['last_run'])
            print(f"Last Run: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("Last Run: Never")
        
        if self.config['next_run']:
            next_run = datetime.fromisoformat(self.config['next_run'])
            print(f"Next Run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"Email Notifications: {self.config['email_notifications']}")
        
        # Check if cron job exists (Unix systems)
        if self.platform in ['linux', 'darwin']:
            try:
                result = subprocess.run(['crontab', '-l'], 
                                      capture_output=True, text=True)
                if "Quality Momentum Strategy" in result.stdout:
                    print("Cron Job: ✅ Installed")
                else:
                    print("Cron Job: ❌ Not found")
            except:
                print("Cron Job: ❓ Cannot check")

def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Quality Momentum Strategy Automation Scheduler')
    parser.add_argument('--install', choices=['auto', 'cron', 'windows', 'python'],
                       default='auto', help='Install scheduler (default: auto-detect)')
    parser.add_argument('--status', action='store_true', 
                       help='Check scheduler status')
    parser.add_argument('--run-daemon', action='store_true',
                       help='Run Python scheduler daemon')
    parser.add_argument('--test', action='store_true',
                       help='Test run the pipeline once')
    
    args = parser.parse_args()
    
    scheduler = AutomationScheduler()
    
    if args.status:
        scheduler.status_check()
        return 0
    
    if args.run_daemon:
        scheduler.run_scheduler_daemon()
        return 0
    
    if args.test:
        print("🧪 TEST RUN - Executing pipeline once...")
        script_path = os.path.join(scheduler.base_dir, 'enhanced_complete_pipeline.py')
        result = subprocess.run([sys.executable, script_path, '--skip-data-collection'])
        return result.returncode
    
    # Default: install scheduler
    success = scheduler.install_scheduler(args.install)
    
    if success:
        print("\n🎉 AUTOMATION SETUP COMPLETED!")
        print("\n📋 NEXT STEPS:")
        print("1. Verify the schedule meets your needs")
        print("2. Configure email notifications if desired")
        print("3. Test the automation with --test flag")
        print("4. Monitor logs for successful execution")
        
        if args.install == 'python':
            print(f"\n🔄 TO START PYTHON DAEMON:")
            print(f"python {__file__} --run-daemon")
        
        return 0
    else:
        print("\n❌ AUTOMATION SETUP FAILED!")
        return 1

if __name__ == "__main__":
    exit(main()) 