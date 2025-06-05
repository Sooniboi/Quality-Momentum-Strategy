# Quality Momentum Strategy - Project Structure

## 📁 Organized Directory Structure

```
Quality-Momentum-Strategy.git/
├── README.md                          # Main project documentation
├── .gitignore                         # Git ignore patterns
├── start_live_trading.py             # Main trading system entry point
│
├── 📂 src/                           # Source code
│   ├── analysis/                     # Analysis and research tools
│   ├── data_collection/              # Data gathering utilities
│   ├── portfolio/                    # Portfolio management
│   ├── signals/                      # Trading signal generation
│   ├── utils/                        # Utility functions and tools
│   │   ├── weekly_performance_reporter.py  # Automated reporting
│   │   └── daily_macro_monitor.py          # Economic monitoring
│   └── csv_data_files/               # Data files
│
├── 📂 trading/                       # Trading implementations
│   ├── paper_trading/                # Paper trading system
│   ├── live/                         # Live trading system
│   └── backtesting/                  # Backtesting framework
│
├── 📂 reports/                       # Generated reports
│   └── weekly/                       # Weekly performance reports
│       ├── templates/                # LaTeX templates
│       └── generated/                # Generated reports
│
├── 📂 data/                          # Data storage
│   └── processed/                    # Processed data files
│
├── 📂 docs/                          # Documentation
│   ├── README.md                     # Documentation index
│   ├── SYSTEM_ARCHITECTURE.md       # System design
│   ├── QUICK_REFERENCE.md           # Quick reference guide
│   └── Quality_Momentum_Strategy_Documentation.tex
│
├── 📂 config/                        # Configuration files
│   ├── trading_config.json          # Trading parameters
│   └── economic_monitoring_config.json # Monitoring settings
│
├── 📂 logs/                          # System logs
│   ├── weekly_performance_reporter.log  # Report generation logs
│   ├── daily_macro_monitor.log          # Monitoring logs
│   ├── alpaca_trading.log               # Trading logs
│   └── *.log                            # Other system logs
│
├── 📂 tests/                         # Test files
│   ├── test_formatting_fixes.py     # Report formatting tests
│   ├── test_portfolio_with_cash.py  # Portfolio tests
│   ├── test_get_current_positions.py # Position tests
│   └── test_*.py                     # Other test files
│
├── 📂 archive/                       # Archived files
│   ├── documentation/                # Old documentation
│   └── configs/                      # Old configuration files
│
└── 📂 main/                          # Legacy main directory
```

## 🚀 Key Entry Points

### Main Systems
- **`start_live_trading.py`** - Complete automated trading system
- **`src/utils/weekly_performance_reporter.py`** - Automated weekly reports
- **`src/utils/daily_macro_monitor.py`** - Economic monitoring

### Trading Systems
- **`trading/paper_trading/`** - Paper trading with Alpaca
- **`trading/live/`** - Live trading implementation
- **`trading/backtesting/`** - Strategy backtesting

### Data & Analysis
- **`src/analysis/`** - Research and analysis tools
- **`src/signals/`** - Signal generation algorithms
- **`src/portfolio/`** - Portfolio management tools

## 📊 Current Status

### ✅ Production Systems
- **Weekly Reporting**: Fully automated with real Alpaca data
- **Portfolio Value**: $99,856 (27 stocks + cash)
- **Email Delivery**: Professional PDF reports every Friday

### ✅ Clean Organization
- **9 test files** organized in `tests/`
- **14 documentation files** archived in `archive/documentation/`
- **Configuration files** organized in `archive/configs/`
- **Empty log files** removed
- **Python cache** cleaned up

### ✅ Active Components
- Live Alpaca integration with real portfolio data
- Professional LaTeX report generation
- Automated scheduling system
- Comprehensive logging

## 🔧 Quick Commands

```bash
# Generate weekly report now
cd src/utils && python weekly_performance_reporter.py --run-now

# Start automated reporting
cd src/utils && python weekly_performance_reporter.py

# Run tests
cd tests && python test_formatting_fixes.py

# Start live trading
python start_live_trading.py
```

## 📈 Recent Achievements

1. **Real Data Integration**: Connected to Alpaca with $99,856 portfolio
2. **Professional Reports**: LaTeX-generated PDFs with proper formatting
3. **Clean Project Structure**: Organized 23+ files into logical directories
4. **Automated Systems**: Weekly reports and economic monitoring
5. **Comprehensive Testing**: Full test suite in organized structure

## 🎯 Next Steps

- Focus on trading algorithm improvements
- Enhance backtesting capabilities
- Expand economic monitoring features
- Develop additional analysis tools

---

**Last Updated**: January 2025
**Project Status**: ✅ Production Ready with Clean Organization 