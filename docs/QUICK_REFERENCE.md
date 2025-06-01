# 🚀 Quick Reference Guide - Quality Momentum Strategy

## 🎯 How to Use This System

### **🏃‍♂️ Quick Start (30 seconds)**
```bash
# Clone and run everything
python run.py

# Or skip data collection (use existing)
python run.py --skip-data-collection
```

### **🔧 Advanced Usage**
```bash
# Full control
python main/enhanced_complete_pipeline.py [options]

# Individual components  
python src/data_collection/01_universe_collection.py
python src/analysis/03_sector_scoring_analysis.py
python trading/backtesting/06_historical_backtesting.py
```

## 🌳 Decision Tree Summary

### **📊 Main System Flow**
```
START → Check Dependencies → Parse Args → 
Data Collection → Analysis → Portfolio Construction → 
Validation/Trading → Reports → END
```

### **🤔 Key Decision Points**

| **Stage** | **Decision** | **Action** |
|-----------|--------------|------------|
| **Universe** | Market cap $1B-$10B? | Include/Exclude |
| **Quality** | ROIC > 15%? | High score |
| **Fed Policy** | Rate hikes + hawkish? | Classify HAWKISH |
| **Style** | Growth score > 75th%? | Label GROWTH |
| **Portfolio** | Position > 5%? | Cap at 5% |
| **Trading** | API credentials? | Live/Demo mode |

## 📁 File Structure Navigation

### **🎯 Main Entry Points**
- `run.py` - Simplest start
- `main/enhanced_complete_pipeline.py` - Full control
- `main/run_complete_pipeline.py` - Core pipeline only

### **📊 Source Code Organization**
```
src/
├── data_collection/    # Get universe & fundamentals
├── analysis/          # Score, macro, Monte Carlo  
├── portfolio/         # Construct optimal portfolio
└── utils/             # Helper functions
```

### **📈 Trading & Validation**
```
trading/
├── backtesting/       # Historical performance
└── paper_trading/     # Live simulation
```

### **📁 Data Organization**
```
data/
├── raw/              # Downloaded data
├── processed/        # Cleaned datasets
└── results/          # Final outputs
```

## 🔗 Component Dependencies

### **📊 Sequential Dependencies**
```
01_universe → 02_fundamentals → 03_sector_scoring → 
05_portfolio ← 04_macro_analysis
     ↓
06_monte_carlo
     ↓
07_backtesting & 08_paper_trading
```

### **🔄 Data Flow Chain**
```
External APIs → Raw Data → Processed Data → 
Analysis Results → Portfolio → Trading/Reports
```

## 🧠 Core Algorithm Logic

### **💰 Quality Scoring (Weights)**
- **Quality Metrics**: 40% (ROIC, margins, FCF)
- **Momentum Metrics**: 35% (3M/6M returns, growth)
- **Valuation Metrics**: 25% (P/E, P/B, EV/EBITDA)

### **🏛️ Macro Classification**
| **Fed Policy** | **Condition** | **Sector Impact** |
|----------------|---------------|-------------------|
| HAWKISH | Rate hikes + hawkish tone | Financials +10%, Real Estate -15% |
| DOVISH | Rate cuts + dovish tone | Tech +5%, Utilities -10% |
| RECESSION | Probability > 40% | Staples +20%, Industrials -15% |

### **🎯 Portfolio Rules**
- **Max position**: 5% per stock
- **Max sector**: 25% per sector
- **Target positions**: 30-50 stocks
- **Rebalancing**: Monthly review

## 📊 Output Files Guide

### **📁 Core Data Files** (`data/processed/`)
```
01_universe_sp600_companies_YYYY-MM-DD.csv     # Stock universe
02_fundamentals_with_momentum_YYYY-MM-DD.csv   # Financial data
03_sector_scored_companies_YYYY-MM-DD.csv      # Ranked stocks
portfolios/05_portfolio_YYYY-MM-DD.csv         # Final portfolio
```

### **📈 Analysis Results**
```
monte_carlo_analysis/06_monte_carlo_*.csv      # Risk metrics
macro_analysis/04_macro_analysis_YYYY-MM-DD.csv # Economic outlook
risk_analysis/                                 # Risk attribution
```

### **💼 Trading Outputs**
```
trading/backtesting/06_backtest_report_YYYY-MM-DD.html # Performance
trading/paper_trading/07_trading_log_YYYY-MM-DD.csv    # Live trades
```

## 🚨 Error Handling Quick Reference

### **🔧 Common Issues & Solutions**

| **Error** | **Quick Fix** |
|-----------|---------------|
| "Missing API key" | Run with `--test-mode` or add to config/ |
| "No data files" | Run full pipeline first |
| "Package not found" | `pip install -r config/requirements.txt` |
| "Pipeline failed" | Check logs, retry individual steps |

### **🔄 Recovery Procedures**
1. **Partial failure**: Resume from last successful step
2. **Data corruption**: Restore from backup in data/processed/
3. **API failure**: Switch to cached/demo data

## ⚙️ Configuration Quick Setup

### **📝 Essential Config Files**
```
config/requirements.txt         # Install: pip install -r
config/api_keys.json           # Optional: Add your API keys
.env                           # Environment variables
```

### **🔑 API Keys (Optional)**
- **Financial Modeling Prep**: Fundamental data
- **Alpaca Markets**: Paper trading
- **FRED**: Economic indicators

## 📈 Performance Expectations

### **🎯 Target Metrics**
- **Expected Return**: 10-15% annually
- **Sharpe Ratio**: >1.0
- **Max Drawdown**: <20%
- **Win Rate**: >55% days vs benchmark
- **Turnover**: <50% annually

### **📊 Benchmark Comparison**
- **Primary**: IJR (S&P 600 Small Cap ETF)
- **Secondary**: IWM (Russell 2000 ETF)

## 🔄 Automation & Scheduling

### **⏰ Setup Automation**
```bash
# Install scheduler (auto-detects platform)
python automation/08_automation_scheduler.py --install

# Check status
python automation/08_automation_scheduler.py --status
```

### **📅 Recommended Schedule**
- **Daily**: Market data updates
- **Weekly**: Portfolio monitoring
- **Monthly**: Full rebalancing
- **Quarterly**: Strategy review

## 🎓 Learning Path

### **👶 Beginner**
1. Run `python run.py` to see full system
2. Explore generated files in `data/processed/`
3. Review backtest report in `trading/backtesting/`

### **🔍 Intermediate** 
1. Modify parameters in individual scripts
2. Add custom metrics to scoring system
3. Experiment with different rebalancing frequencies

### **🚀 Advanced**
1. Integrate additional data sources
2. Implement machine learning enhancements
3. Deploy to cloud for 24/7 automation

## 📚 Documentation Hierarchy

### **📖 Start Here**
1. `README.md` - Project overview & setup
2. `QUICK_REFERENCE.md` - This file
3. `SYSTEM_FLOW_DIAGRAM.md` - Detailed decision trees

### **🔍 Deep Dive**
4. `SYSTEM_ARCHITECTURE.md` - Technical architecture
5. `UNIFIED_PORTFOLIO_SYSTEM.md` - Portfolio theory
6. Individual script docstrings - Implementation details

---

**💡 Pro Tip**: Always start with `python run.py --test-mode` to understand the system before using real data/APIs! 