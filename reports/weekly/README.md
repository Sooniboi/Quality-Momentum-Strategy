# Weekly Performance Reports

Automated weekly portfolio performance reporting system with professional LaTeX output.

## 📁 Directory Structure

```
reports/weekly/
├── README.md                          # This documentation
├── templates/                         # LaTeX templates
│   └── enhanced_weekly_performance_report_template.tex
└── generated/                         # Generated reports
    ├── weekly_performance_report_YYYY_MM_DD.tex
    └── weekly_performance_report_YYYY_MM_DD.pdf
```

## 🚀 Quick Start

### Generate Report Now
```bash
cd src/utils
python weekly_performance_reporter.py --run-now
```

### Run Automated Scheduler
```bash
cd src/utils
python weekly_performance_reporter.py
```

## 📊 Report Features

### ✅ Real Data Integration
- **Live Alpaca Positions**: 27 stock positions with real prices and P&L
- **Cash Position**: $24,379 cash (24.4% allocation) 
- **Total Portfolio**: $99,856 (matches Alpaca exactly)

### ✅ Professional Formatting
- **Native LaTeX**: No external image dependencies
- **Sector Mapping**: Proper sectors (Industrials, Healthcare, Technology, etc.)
- **Clean Numbers**: No scientific notation, proper formatting
- **Color Coding**: Sector-specific colors and performance indicators

### ✅ Comprehensive Analysis
- Executive Summary with key metrics
- Complete Holdings table (stocks + cash)
- Sector Allocation with visual charts
- Performance Attribution and risk analysis
- Quality Metrics and factor exposure
- Market Context and outlook

## 📧 Email Delivery

Reports are automatically emailed with:
- Professional PDF attachment
- LaTeX source code
- Comprehensive portfolio analysis

## 🔧 Configuration

Email settings configured via environment variables:
- `SENDER_EMAIL`
- `SENDER_PASSWORD` 
- `RECIPIENT_EMAIL`
- `SMTP_SERVER` (default: smtp.gmail.com)
- `SMTP_PORT` (default: 587)

## 📅 Schedule

- **Automatic**: Every Friday at 4:00 PM EST
- **Manual**: Run anytime with `--run-now` flag

## 🎯 Latest Report

**Location**: `generated/weekly_performance_report_2025_06_04.pdf`
**Status**: ✅ All formatting issues resolved
**Portfolio Value**: $99,856 (real Alpaca data)
**Positions**: 27 stocks + cash 

## 📍 File Locations

- **Reporter Script**: `../../src/utils/weekly_performance_reporter.py`
- **Templates**: `templates/enhanced_weekly_performance_report_template.tex`
- **Generated Reports**: `generated/weekly_performance_report_*.{tex,pdf}`
- **Logs**: `../../logs/weekly_performance_reporter.log` 