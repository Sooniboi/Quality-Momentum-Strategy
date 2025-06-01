# 🚀 Quality Momentum Strategy - Complete Pipeline

A comprehensive, automated investment strategy system that combines quality metrics, momentum factors, and macro-economic analysis to construct and manage portfolios.

## 📋 Overview

This system implements a sophisticated **Quality Momentum Strategy** with the following features:

- ✅ **Automated Universe Collection** (S&P 600 small-cap stocks)
- ✅ **Fundamental Data Analysis** with momentum integration
- ✅ **Sector-Relative Scoring** using z-score methodology
- ✅ **Macro-Economic Integration** (Fed policy, recession analysis)
- ✅ **Portfolio Construction** with risk optimization
- ✅ **Monte Carlo Simulation** for risk assessment
- ✅ **Historical Backtesting** with comprehensive metrics
- ✅ **Paper Trading Integration** (Alpaca Markets)
- ✅ **Automated Scheduling** with notifications

## 🏗️ System Architecture

```
📁 Quality-Momentum-Strategy/
├── 🚀 enhanced_complete_pipeline.py      # Main pipeline executor
├── 📊 run_complete_pipeline.py           # Legacy pipeline (core steps only)
├── ⚙️ 08_automation_scheduler.py         # Automation & scheduling
├── 📋 requirements.txt                   # Dependencies
├── 📖 README.md                          # This file
│
├── 📂 universe/
│   └── 01_universe_collection.py         # S&P 600 data collection
│
├── 📂 data_collection/
│   ├── 01_fundamental_data_collection.py # Financial metrics + momentum
│   ├── 02_sector_scoring_analysis.py     # Sector relative scoring
│   ├── 03_macro_economic_analysis.py     # Fed policy + economic analysis  
│   ├── 04_unified_portfolio_construction.py # Portfolio optimization
│   └── 05_monte_carlo_simulation.py      # Risk simulation
│
├── 📂 backtesting/
│   └── 06_historical_backtesting.py      # Performance validation
│
├── 📂 paper_trading/
│   └── 07_paper_trading_setup.py         # Live paper trading
│
└── 📂 csv_data_files/                    # Generated data & results
    ├── 📊 *.csv                          # Core data files
    ├── 📁 portfolios/                    # Portfolio selections
    ├── 📁 monte_carlo_analysis/          # Risk analysis results
    ├── 📁 macro_analysis/                # Economic analysis
    └── 📁 risk_analysis/                 # Risk metrics & correlations
```

## 🛠️ Installation & Setup

### 1. **Clone & Install Dependencies**
```bash
git clone <your-repo-url>
cd Quality-Momentum-Strategy
pip install -r requirements.txt
```

### 2. **API Keys Setup** (Optional but Recommended)
- **Financial Modeling Prep**: Get free API key for fundamental data
- **Alpaca Markets**: Free paper trading account for live testing
- **FRED**: Economic data (free registration)

### 3. **Verify Installation**
```bash
python enhanced_complete_pipeline.py --help
```

## 🎯 Usage

### **Quick Start - Run Complete Pipeline**
```bash
# Run everything (first time)
python enhanced_complete_pipeline.py

# Skip data collection (use existing data)  
python enhanced_complete_pipeline.py --skip-data-collection

# Skip optional components
python enhanced_complete_pipeline.py --skip-backtesting --skip-paper-trading
```

### **Individual Components**

#### **Core Strategy Pipeline**
```bash
# 1. Collect S&P 600 universe
python universe/01_universe_collection.py

# 2. Get fundamental data + momentum
python data_collection/01_fundamental_data_collection.py

# 3. Calculate sector scores
python data_collection/02_sector_scoring_analysis.py

# 4. Construct portfolio
python data_collection/04_unified_portfolio_construction.py

# 5. Run Monte Carlo simulation
python data_collection/05_monte_carlo_simulation.py

# 6. Macro economic analysis
python data_collection/03_macro_economic_analysis.py
```

#### **Backtesting & Validation**
```bash
# Historical performance analysis
python backtesting/06_historical_backtesting.py

# View results in: backtesting/06_backtest_report_YYYY-MM-DD.html
```

#### **Paper Trading**
```bash
# Setup paper trading (one time)
python paper_trading/07_paper_trading_setup.py

# Monitor performance & rebalance monthly
```

#### **Automation**
```bash
# Install scheduler (auto-detects platform)
python 08_automation_scheduler.py --install

# Check status
python 08_automation_scheduler.py --status

# Test run
python 08_automation_scheduler.py --test
```

## 📊 Strategy Methodology

### **Quality Metrics**
- **ROIC** (Return on Invested Capital)
- **Operating Margin** 
- **Free Cash Flow**
- **Debt Management** (Net Debt to EBITDA)

### **Momentum Factors**  
- **3-Month Returns**
- **6-Month Returns**
- **Revenue Growth**

### **Macro Integration**
- **Fed Policy Analysis** (hawkish/dovish bias)
- **Recession Probability** (NY Fed model)
- **Yield Curve Analysis**
- **Economic Indicators** (unemployment, inflation)

### **Portfolio Construction**
- **Style Allocation**: Quality, Growth, Value, Blend
- **Sector Adjustments**: Based on macro conditions
- **Risk Optimization**: Volatility and beta constraints
- **Position Sizing**: Maximum 5% per stock, 25% per sector

## 📈 Expected Outputs

### **Data Files**
- `01_universe_sp600_companies_YYYY-MM-DD.csv` - Stock universe
- `02_fundamentals_with_momentum_YYYY-MM-DD.csv` - Financial metrics
- `03_sector_scored_companies_YYYY-MM-DD.csv` - Sector rankings
- `04_unified_portfolio_selection_YYYY-MM-DD.csv` - Final portfolio

### **Analysis Reports**
- **Monte Carlo**: Risk metrics, VaR, stress tests
- **Backtesting**: Historical performance vs benchmark
- **Macro Analysis**: Fed policy, recession probability
- **Paper Trading**: Live performance tracking

### **Key Metrics Tracked**
- **Expected Return**: 10-15% annually
- **Sharpe Ratio**: Target >1.0
- **Maximum Drawdown**: Target <20%
- **Win Rate**: Days outperforming benchmark
- **Beta**: Market sensitivity (target 0.8-1.2)

## 🔧 Configuration

### **Pipeline Options**
Edit `enhanced_complete_pipeline.py` command line args:
- `--skip-data-collection`: Use existing data
- `--skip-backtesting`: Skip historical analysis  
- `--skip-paper-trading`: Skip live trading setup
- `--test-mode`: Run with limited data for testing
- `--backtest-years N`: Years of historical data (default: 3)

### **Scheduling Configuration** 
Edit `08_scheduler_config.json`:
```json
{
  "schedule_type": "monthly",
  "schedule_time": "09:00", 
  "email_notifications": true,
  "pipeline_options": {
    "skip_data_collection": false
  }
}
```

### **Trading Configuration**
Edit `paper_trading/07_alpaca_config.json`:
```json
{
  "api_key": "YOUR_ALPACA_API_KEY",
  "secret_key": "YOUR_ALPACA_SECRET_KEY",
  "portfolio_value": 10000,
  "max_position_size": 0.05
}
```

## 🚨 Risk Warnings

- **Past performance does not guarantee future results**
- **This system is for educational and research purposes**
- **Always validate strategy with paper trading before real money**
- **Consider transaction costs and market impact**
- **Monitor macro conditions and adjust as needed**

## 🛠️ Troubleshooting

### **Common Issues**

1. **"No API key found"**
   - Add API keys to configuration files
   - Or run with `--test-mode` for simulated data

2. **"No data files found"**
   - Run full pipeline first: `python enhanced_complete_pipeline.py`
   - Check `csv_data_files/` directory exists

3. **"Package not found"**
   - Install dependencies: `pip install -r requirements.txt`
   - Check Python version (3.8+ recommended)

4. **Scheduler not working**
   - Check platform compatibility
   - Try Python scheduler: `--install python`
   - Verify cron permissions on Unix systems

### **Performance Optimization**
- Use `--skip-data-collection` for faster runs
- Set up caching for API calls
- Run backtesting on subset of data first
- Monitor system resources during full pipeline

## 📧 Support & Contributing

For issues, feature requests, or contributions:
1. Check existing issues and documentation
2. Test with `--test-mode` first
3. Include error logs and system information
4. Follow coding standards and add tests

## 📄 License

This project is for educational purposes. See LICENSE file for details.

## 🎯 Roadmap

### **Planned Features**
- [ ] Interactive web dashboard (Streamlit/Dash)
- [ ] Alternative data integration (ESG, sentiment)
- [ ] Machine learning enhancements
- [ ] Multi-asset class support
- [ ] Real-time position monitoring
- [ ] Advanced risk attribution
- [ ] Performance attribution analysis

### **Recent Updates**
- ✅ Complete pipeline automation
- ✅ Paper trading integration  
- ✅ Historical backtesting system
- ✅ Enhanced macro analysis
- ✅ Cross-platform scheduling

---

**Built with ❤️ for quantitative finance enthusiasts**

*Last updated: 2025-06-01* 