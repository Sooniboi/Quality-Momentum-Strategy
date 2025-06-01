# 🚀 Quality Momentum Strategy - Complete System

A professional-grade, automated investment strategy system that combines quality metrics, momentum factors, and macro-economic analysis for systematic portfolio construction and management.

## 📋 Project Overview

This system implements a sophisticated **Quality Momentum Strategy** with enterprise-level features:

- ✅ **Automated Data Collection** (S&P 600 small-cap universe)
- ✅ **Advanced Financial Analysis** (quality + momentum metrics via FMP API)
- ✅ **Macro-Economic Integration** (Fed policy, recession indicators)
- ✅ **Portfolio Optimization** with risk constraints
- ✅ **Monte Carlo Risk Analysis** with stress testing
- ✅ **Historical Backtesting** with comprehensive metrics (FMP historical data)
- ✅ **Live Paper Trading** (Alpaca Markets integration)
- ✅ **Automated Scheduling** with cross-platform support

## 🏗️ Clean Project Structure

```
📁 Quality-Momentum-Strategy/
├── 🎯 main/                          # Main executables
│   ├── enhanced_complete_pipeline.py # 🚀 MAIN ENTRY POINT
│   └── run_complete_pipeline.py      # Basic pipeline runner
│
├── 📊 src/                           # Source code modules
│   ├── data_collection/              # Data gathering scripts
│   │   ├── 01_universe_collection.py
│   │   └── 02_fundamental_data_collection.py (FMP API)
│   ├── analysis/                     # Analysis & scoring
│   │   ├── 03_sector_scoring_analysis.py
│   │   ├── 04_macro_economic_analysis.py
│   │   └── 06_monte_carlo_simulation.py
│   ├── portfolio/                    # Portfolio construction
│   │   └── 05_unified_portfolio_construction.py
│   └── utils/                        # Utility functions
│       ├── economic_calendar.py
│       ├── fama_french_factors.py
│       └── operational_scheduler.py
│
├── 📈 trading/                       # Trading systems
│   ├── backtesting/                  # Historical analysis
│   │   └── 06_historical_backtesting.py (FMP API)
│   └── paper_trading/                # Live paper trading
│       └── 07_paper_trading_setup.py
│
├── 🔄 automation/                    # Scheduling & automation
│   └── 08_automation_scheduler.py
│
├── 📁 data/                          # All data files
│   ├── raw/                          # Raw downloaded data
│   ├── processed/                    # Processed datasets
│   │   ├── portfolios/               # Final portfolio selections
│   │   ├── monte_carlo_analysis/     # Risk analysis
│   │   ├── macro_analysis/           # Economic data
│   │   └── risk_analysis/            # Risk metrics
│   └── results/                      # Final outputs
│
├── 📊 reports/                       # Generated reports
├── 🔧 config/                        # Configuration files
│   ├── requirements.txt              # Dependencies
│   └── tasks.txt                     # Development tasks
│
└── 📖 docs/                          # Documentation
    ├── README.md                     # This file
    ├── UNIFIED_PORTFOLIO_SYSTEM.md
    ├── SYSTEM_SUMMARY.md
    └── Quality_Momentum_Strategy_Documentation.tex
```

## 🚀 Quick Start

### 1. **Installation**
```bash
# Clone repository
git clone <your-repo-url>
cd Quality-Momentum-Strategy

# Install dependencies
pip install -r config/requirements.txt
```

### 2. **Run Complete System**
```bash
# 🎯 MAIN ENTRY POINT - Run everything
python main/enhanced_complete_pipeline.py

# Skip data collection (use existing data)
python main/enhanced_complete_pipeline.py --skip-data-collection

# Skip optional components
python main/enhanced_complete_pipeline.py --skip-backtesting --skip-paper-trading

# Test mode with limited data
python main/enhanced_complete_pipeline.py --test-mode
```

### 3. **Individual Components**
```bash
# Core strategy pipeline only
python main/run_complete_pipeline.py

# Just backtesting
python trading/backtesting/06_historical_backtesting.py

# Just paper trading setup
python trading/paper_trading/07_paper_trading_setup.py

# Setup automation
python automation/08_automation_scheduler.py --install
```

## 📊 System Features

### **Investment Strategy**
- **Quality Metrics**: ROIC, Operating Margin, Free Cash Flow, Debt Management
- **Momentum Factors**: 3M/6M returns, Revenue Growth, Price momentum
- **Macro Integration**: Fed policy analysis, Recession probability, Yield curve
- **Portfolio Construction**: Style allocation (Quality/Growth/Value/Blend), Sector rotation

### **Risk Management**
- **Monte Carlo Simulation**: 10,000 scenarios, VaR calculation, Stress testing
- **Position Limits**: Max 5% per stock, 25% per sector
- **Volatility Controls**: Beta constraints, Correlation limits
- **Drawdown Management**: Maximum drawdown monitoring

### **Trading & Validation**
- **Historical Backtesting**: 3+ years performance analysis vs benchmarks (FMP historical data)
- **Paper Trading**: Live testing with Alpaca Markets (free account)
- **Performance Metrics**: Sharpe ratio, Information ratio, Win rate, Calmar ratio
- **Automated Rebalancing**: Monthly/quarterly frequency options

## 🔧 Configuration

### **API Keys** (Optional but Recommended)
Create configuration files in `config/` directory:

```json
// config/api_keys.json
{
  "financial_modeling_prep": "YOUR_FMP_API_KEY",
  "alpaca_api_key": "YOUR_ALPACA_KEY", 
  "alpaca_secret_key": "YOUR_ALPACA_SECRET",
  "fred_api_key": "YOUR_FRED_KEY"
}
```

**🔑 Financial Modeling Prep (FMP) API**
- **Free tier available**: https://financialmodelingprep.com/
- **Used for**: Fundamental data + Historical price data for backtesting
- **Alternative**: System will use demo/limited data without API key

### **Pipeline Options**
Edit command line arguments in main scripts:
- `--skip-data-collection`: Use existing data
- `--skip-backtesting`: Skip historical analysis
- `--skip-paper-trading`: Skip live trading setup
- `--test-mode`: Limited data for testing
- `--backtest-years N`: Historical data period

## 📈 Expected Outputs

### **Core Data Files** (`data/processed/`)
- Universe selection with 600+ small-cap stocks
- Fundamental metrics with momentum integration (FMP API)
- Sector-relative scoring and rankings
- Final portfolio with optimized weights

### **Analysis Reports** (`reports/`)
- Monte Carlo risk analysis with stress tests
- Historical backtesting with performance charts (FMP historical data)
- Macro-economic analysis and Fed policy tracking
- Portfolio composition and style allocation

### **Performance Tracking**
- **Target Returns**: 10-15% annually
- **Risk Metrics**: Sharpe ratio >1.0, Max drawdown <20%
- **Benchmark**: S&P 600 Small Cap Index (IJR)
- **Rebalancing**: Monthly frequency

## 🛠️ Development

### **Adding New Features**
1. Place scripts in appropriate `src/` subdirectory
2. Update main pipeline in `main/enhanced_complete_pipeline.py`
3. Add tests and documentation
4. Update configuration files

### **File Organization Rules**
- **main/**: Executable entry points only
- **src/**: All source code, organized by function
- **trading/**: Backtesting and live trading systems
- **data/**: All data files, organized by processing stage
- **config/**: Configuration and requirement files
- **docs/**: Documentation and reports

## 🚨 Risk Warnings

- **Educational Purpose**: This system is for research and education
- **No Investment Advice**: Past performance doesn't guarantee future results
- **Paper Trading First**: Always test with simulated money before real capital
- **Monitor Performance**: Review and adjust strategy based on market conditions

## 📧 Support

For issues or questions:
1. Check `docs/` for comprehensive documentation
2. Review error logs in console output
3. Test with `--test-mode` flag first
4. Verify all dependencies are installed

## 🎯 Roadmap

### **Completed Features**
- ✅ Complete pipeline automation
- ✅ Professional file organization
- ✅ Historical backtesting system (FMP API integration)
- ✅ Paper trading integration
- ✅ Macro-economic analysis
- ✅ Monte Carlo risk simulation

### **Future Enhancements**
- [ ] Web dashboard (Streamlit/Dash)
- [ ] Machine learning integration
- [ ] Alternative data sources (ESG, sentiment)
- [ ] Multi-asset class support
- [ ] Real-time monitoring dashboard

---

**🎯 Ready to run? Execute: `python main/enhanced_complete_pipeline.py`**

*Professional quantitative finance system - Built with ❤️ for systematic investing* 