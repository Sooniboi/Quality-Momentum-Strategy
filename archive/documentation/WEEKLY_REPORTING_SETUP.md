# 📊 Weekly Performance Reporting System - Setup Guide

## 🎯 **Overview**

Your enhanced trading system now includes automated weekly performance reporting that generates professional LaTeX-formatted PDF reports and emails them to you every Friday after market close.

---

## 📋 **Features**

### **📄 Professional LaTeX Reports Include:**
- Executive summary with key highlights
- Market regime analysis (15-regime system)
- Portfolio composition and allocation charts
- Risk management metrics
- Trading signals summary
- Economic calendar events
- Performance charts and visualizations
- System status and next week outlook

### **📧 Automated Email Delivery:**
- PDF report attached
- Summary in email body
- Sent every Friday at 5:00 PM EST
- Professional formatting

### **📈 Performance Charts:**
- Style allocation pie chart
- Sector allocation bar chart
- Weekly regime progression
- Trading recommendations timeline

---

## 🛠️ **Installation & Setup**

### **Step 1: Install Additional Dependencies**

```bash
# Install chart generation libraries
pip install matplotlib seaborn

# Or install from requirements file
pip install -r config/weekly_reporting_requirements.txt
```

### **Step 2: Install LaTeX Distribution**

**For macOS:**
```bash
# Install MacTeX (large download ~4GB)
brew install --cask mactex

# Or smaller BasicTeX
brew install --cask basictex
```

**For Ubuntu/Linux:**
```bash
# Install TeX Live
sudo apt-get update
sudo apt-get install texlive-full

# Or minimal installation
sudo apt-get install texlive-latex-base texlive-latex-recommended texlive-latex-extra
```

**For Windows:**
- Download and install [MikTeX](https://miktex.org/download) or [TeX Live](https://www.tug.org/texlive/)

### **Step 3: Configure Email Settings**

1. **Copy the email configuration template:**
```bash
cp config/email_config_template.env .env
```

2. **Edit `.env` file with your email settings:**
```bash
# For Gmail (recommended)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password  # NOT your regular password!
RECIPIENT_EMAIL=your_email@gmail.com
```

3. **Set up Gmail App Password (if using Gmail):**
   - Enable 2-factor authentication on your Gmail account
   - Go to Google Account → Security → 2-Step Verification
   - Click "App passwords" at the bottom
   - Select "Mail" and "Other (custom)" → name it "Trading Reports"
   - Use the 16-character password generated (not your regular Gmail password)

### **Step 4: Update Cron Schedule**

```bash
# Apply the updated cron schedule with weekly reporting
crontab updated_cron_schedule.txt

# Verify the schedule
crontab -l
```

**New Complete Schedule:**
```bash
# Daily: 6:00 AM EST - Pre-market macro monitoring
0 11 * * * python daily_macro_monitor.py

# Monday: 5:00 AM EST - Weekly portfolio reoptimization  
0 10 * * 1 python start_live_trading.py

# Friday: 5:00 PM EST - Weekly performance report
0 22 * * 5 python weekly_performance_reporter.py
```

---

## 🧪 **Testing the System**

### **Test the Reporter Manually:**
```bash
# Test the weekly performance reporter
python weekly_performance_reporter.py

# Check for generated files
ls -la reports/weekly/
ls -la reports/weekly/latex/
ls -la reports/weekly/charts/
```

### **Expected Output:**
```
📊 WEEKLY PERFORMANCE REPORTER - Friday Edition
📅 Date: 2025-06-03 17:00:00
📈 Generating weekly performance report...
📊 Collecting weekly performance data...
📈 Generating performance charts...
✅ Generated 3 charts
📄 Generating LaTeX report...
✅ LaTeX report written to reports/weekly/latex/weekly_performance_report_2025_06_03.tex
🔧 Compiling LaTeX to PDF...
✅ PDF generated: reports/weekly/latex/weekly_performance_report_2025_06_03.pdf
📧 Sending email report...
✅ Email sent successfully
✅ Weekly performance report generated and sent successfully!
```

### **Check Email Configuration:**
```bash
# Test email sending without full report
python -c "
from src.utils.weekly_performance_reporter import WeeklyPerformanceReporter
reporter = WeeklyPerformanceReporter()
print('Email config:', reporter.email_config)
"
```

---

## 📁 **File Structure**

### **New Files Created:**
```
📁 Quality-Momentum-Strategy/
├── weekly_performance_reporter.py          # Main weekly reporter script
├── src/utils/weekly_performance_reporter.py # Reporter class implementation
├── config/email_config_template.env        # Email configuration template
├── config/weekly_reporting_requirements.txt # Additional dependencies
├── updated_cron_schedule.txt               # Complete automation schedule
└── reports/weekly/                         # Weekly reports directory
    ├── latex/                             # LaTeX source files
    ├── charts/                            # Generated charts
    └── performance_data_YYYY_MM_DD.json   # Raw data backups
```

---

## 🎨 **Report Customization**

### **Modify Report Content:**
Edit `src/utils/weekly_performance_reporter.py`:

```python
# Customize LaTeX styling
def create_latex_content(self, performance_data, chart_files):
    # Add your custom sections here
    
# Add custom charts
def generate_charts(self, performance_data):
    # Add your custom chart generation
```

### **Custom Chart Types:**
- Performance vs benchmark
- Drawdown charts
- Correlation matrices
- Risk contribution analysis

### **Email Customization:**
- Change subject line format
- Modify email body content
- Add additional attachments
- Custom recipient lists

---

## 🔧 **Troubleshooting**

### **Common Issues:**

**1. LaTeX Not Found:**
```bash
# Check if pdflatex is installed
which pdflatex

# If not found, install LaTeX distribution
# macOS: brew install --cask mactex
# Ubuntu: sudo apt-get install texlive-full
```

**2. Email Authentication Failed:**
```bash
# For Gmail: Use App Password, not regular password
# Check 2-factor authentication is enabled
# Verify SMTP settings in .env file
```

**3. Charts Not Generating:**
```bash
# Install missing chart dependencies
pip install matplotlib seaborn

# Check for Qt/display issues on headless systems
export MPLBACKEND=Agg
```

**4. Permission Errors:**
```bash
# Make scripts executable
chmod +x weekly_performance_reporter.py
chmod +x daily_macro_monitor.py
chmod +x start_live_trading.py
```

### **Debug Mode:**
```bash
# Run with verbose logging
python weekly_performance_reporter.py --debug

# Check log files
tail -f logs/weekly_reporter.log
```

---

## 📅 **Schedule Overview**

### **Complete Automation Timeline:**
```
Monday 5:00 AM EST    → Portfolio Reoptimization
Daily 6:00 AM EST     → Pre-Market Macro Analysis  
Friday 5:00 PM EST    → Weekly Performance Report

📧 Email Report Contents:
• Executive summary
• Market regime analysis
• Portfolio performance charts
• Risk metrics
• Trading signals summary
• Economic calendar
• Next week outlook
```

---

## 🚀 **Advanced Features**

### **Future Enhancements:**
- Real-time performance tracking
- Benchmark comparison charts
- Sector rotation analysis
- Risk attribution analysis
- Custom performance metrics
- Multi-period comparisons

### **Integration Options:**
- Slack/Discord notifications
- Database storage
- Web dashboard
- Mobile notifications
- Cloud backup

---

## ✅ **Verification Checklist**

- [ ] LaTeX distribution installed and `pdflatex` available
- [ ] Email configuration in `.env` file completed
- [ ] Gmail App Password created (if using Gmail)
- [ ] Dependencies installed (`matplotlib`, `seaborn`)
- [ ] Cron schedule updated with Friday reporting
- [ ] Test run completed successfully
- [ ] Email received with PDF attachment
- [ ] Charts generated properly
- [ ] Report directory structure created

---

**Your enhanced trading system now provides professional weekly performance reporting with LaTeX-formatted PDFs delivered automatically to your email every Friday! 📊📧**

*Setup Date: June 3, 2025*
*Status: ✅ Ready for Implementation* 