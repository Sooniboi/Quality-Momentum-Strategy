#!/usr/bin/env python3
"""
Test Email Reporter

Test the weekly performance reporter with simulated email sending.
"""

import os
import sys
from pathlib import Path

# Add the src path
sys.path.insert(0, 'src/utils')
from weekly_performance_reporter import WeeklyPerformanceReporter

# Mock email configuration for testing
os.environ['SENDER_EMAIL'] = 'maxsooni.quant@gmail.com'
os.environ['SENDER_APP_PASSWORD'] = 'test_password'  # This would be your Gmail app password
os.environ['RECIPIENT_EMAIL'] = 'you@example.com'
os.environ['SMTP_SERVER'] = 'smtp.gmail.com'
os.environ['SMTP_PORT'] = '587'

class TestEmailReporter(WeeklyPerformanceReporter):
    """Test version of the reporter that simulates email sending."""
    
    def send_email_report(self, pdf_file: str, latex_file: str) -> bool:
        """Simulate email sending for testing."""
        self.logger.info("📧 SIMULATING email send (test mode)...")
        
        # Check if files exist
        if pdf_file and os.path.exists(pdf_file):
            pdf_size = os.path.getsize(pdf_file) / 1024  # KB
            self.logger.info(f"✅ PDF ready: {os.path.basename(pdf_file)} ({pdf_size:.1f} KB)")
        else:
            self.logger.error("❌ PDF file not found")
            return False
            
        if latex_file and os.path.exists(latex_file):
            latex_size = os.path.getsize(latex_file) / 1024  # KB
            self.logger.info(f"✅ LaTeX ready: {os.path.basename(latex_file)} ({latex_size:.1f} KB)")
        else:
            self.logger.error("❌ LaTeX file not found")
            return False
        
        # Simulate email content
        subject = f"Weekly Performance Report - {self.report_date.strftime('%B %d, %Y')}"
        self.logger.info(f"📧 Email Subject: {subject}")
        self.logger.info(f"📧 From: {self.email_config['sender_email']}")
        self.logger.info(f"📧 To: {self.email_config['recipient_email']}")
        self.logger.info("📧 Attachments: PDF report + LaTeX source")
        
        # Simulate successful send
        self.logger.info("✅ EMAIL SIMULATION SUCCESSFUL!")
        self.logger.info("📧 In production, this would send a professional PDF via Gmail")
        
        return True

def main():
    """Test the email reporter."""
    print("🧪 Testing Weekly Performance Reporter with Email Simulation")
    print("=" * 60)
    
    try:
        # Create test reporter
        reporter = TestEmailReporter()
        
        # Generate and "send" report
        success = reporter.generate_weekly_report()
        
        if success:
            print("\n🎉 TEST SUCCESSFUL!")
            print("✅ LaTeX report generation: WORKING")
            print("✅ PDF compilation: WORKING")
            print("✅ Email simulation: WORKING")
            print()
            print("📧 To enable real email sending:")
            print("1. Get a Gmail App Password from Google Account settings")
            print("2. Set SENDER_APP_PASSWORD in your environment")
            print("3. The system will automatically send real emails")
        else:
            print("\n❌ TEST FAILED!")
            print("Check the logs above for details")
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        return False
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 