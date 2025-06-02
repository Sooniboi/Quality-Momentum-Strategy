# 🤖 Quality Momentum Strategy - Automated Workflow Documentation

## 📋 Overview
This document explains the complete automated trading workflow that operates with a **two-tier system**:
- **📊 Daily Macro Monitoring** - Check market conditions every day
- **🔄 Weekly Portfolio Reoptimization** - Full rebalancing every Monday (if conditions are favorable)

---

## 🎯 **Two-Tier Automation System**

### **📊 Daily Tier: Macro Economic Monitoring**
**Script:** `daily_macro_monitor.py`  
**Schedule:** Every day at 10:00 AM BST (5:00 AM ET)  
**Purpose:** Monitor market regime, recession risk, Fed policy changes

**Daily Workflow:**
1. Run macro economic analysis (`04_macro_economic_analysis.py`)
2. Extract key market condition signals
3. Determine trading recommendation: `PROCEED` / `CAUTION` / `HALT`
4. Save signals for weekly check

### **🔄 Weekly Tier: Portfolio Reoptimization**
**Script:** `start_live_trading.py`  
**Schedule:** Monday at 10:00 AM BST (5:00 AM ET)  
**Purpose:** Full portfolio rebalancing (if macro conditions permit)

**Weekly Workflow:**
1. Check latest daily macro signals
2. If macro signals = `HALT` → Skip reoptimization
3. If macro signals = `PROCEED`/`CAUTION` → Continue full pipeline
4. Run complete data collection and analysis
5. Generate and execute trades

---

## 🔄 Complete Workflow Pipeline

### 📍 **Entry Points**

**Daily Macro Monitor: `daily_macro_monitor.py`**
```python
1. run_macro_analysis()              # Run macro economic analysis
2. extract_macro_signals()           # Extract trading signals
3. save_daily_signals()              # Save for weekly check
```

**Weekly Trading: `start_live_trading.py`**
```python
1. print_banner()                    # Welcome message
2. test_alpaca_connection()          # Test API connection  
3. check_basic_setup()               # Verify config files exist
4. start_live_automation()           # Start the automation
```

### 🤖 **Weekly Automation Loop: `start_live_automation()` (Lines 280-339)**
```python
1. setup_logging()                   # Create logs directory & handlers
2. scheduled_pipeline()              # Define the main workflow function
3. schedule.every().monday.at("10:00").do(scheduled_pipeline)  # Set weekly schedule
4. Continuous loop checking for scheduled runs
```

### ⚡ **Core Weekly Pipeline: `run_pipeline_once()` (Lines 104-193)**

**This is the MAIN workflow that executes every Monday:**

#### **STEP 1: Macro Signal Check (NEW)**
```python
macro_ok, macro_reason = check_daily_macro_signals()
if not macro_ok:
    # HALT trading - macro conditions unfavorable
    return False
```

#### **STEP 2: Data Collection & Analysis (Lines 109-118)**
```bash
subprocess.run(['python', 'main/enhanced_complete_pipeline.py', '--skip-backtesting'])
```

**This triggers the following sequence:**
1. **`01_universe_collection.py`** - Collect S&P 600 stock list
2. **`02_fundamental_data_collection.py`** - Get financial data for 600 stocks via FMP API
3. **`03_sector_scoring_analysis.py`** - Calculate quality momentum scores
4. **`04_macro_economic_analysis.py`** - Analyze Fed policy & recession risk (already done daily)
5. **`05_unified_portfolio_construction.py`** - Build optimized 38-stock portfolio
6. **`06_monte_carlo_simulation.py`** - Run 10,000 risk simulations

#### **STEP 3: Portfolio Validation (Lines 121-136)**
```python
validation_passed = validate_portfolio_results()
```

**Enhanced Validation Checks:**
- ✅ **Daily macro signals** - Must be PROCEED or CAUTION (not HALT)
- ✅ Monte Carlo risk metrics within acceptable bounds
- ✅ Backtest performance meets criteria
- ✅ Portfolio concentration not excessive
- ✅ Overall risk score passes threshold

**Decision Logic:**
- If validation PASSES → Proceed to trading
- If validation FAILS → Skip trades, protect capital

#### **STEP 4: Trade Execution (Lines 140-191)**
```python
if validation_passed:
    # Generate trading signals
    signal_generator = QualityMomentumSignalGenerator()
    signals = signal_generator.generate_signals({})
    validated_signals = signal_generator.validate_signals(signals)
    
    # Execute trades via Alpaca
    trader = AlpacaPaperTrader()
    results = trader.execute_signals(validated_signals)
```

**Trading Actions:**
- 🎯 Generate BUY/SELL signals for portfolio rebalancing
- 💼 Place orders in Alpaca paper trading account
- 📊 Log all trade executions and results

---

## 🎯 **Enhanced Validation Logic**

### **Daily Macro Signal Check: `check_daily_macro_signals()` (Lines 42-73)**

**Macro Risk Assessment:**
```python
1. Load latest daily macro signals
2. Check trading recommendation:
   - HALT → Stop trading immediately
   - CAUTION → Proceed with heightened risk awareness
   - PROCEED → Normal trading conditions
3. Return authorization for weekly reoptimization
```

### **Weekly Validation: `validate_portfolio_results()` (Lines 195-254)**

**Comprehensive Risk Management Process:**
```python
1. Check daily macro signals first (NEW)
2. Check if Monte Carlo analysis files exist
3. Check if backtest result files exist  
4. Run technical threshold validations:
   - Maximum drawdown limits
   - Volatility constraints
   - Sharpe ratio minimums
   - Concentration limits
5. Return True/False for trading permission (requires 3/4 checks)
```

**Fail-Safe Design:**
- Default action: DO NOT TRADE if validation unclear
- Macro check has veto power over all trading
- Protects capital from both technical and macro risks
- Comprehensive logging of all decisions

---

## 📂 **File Dependencies & Data Flow**

### **Daily Macro Monitoring:**
```
daily_macro_monitor.py
└── src/analysis/04_macro_economic_analysis.py      # Macro conditions
    └── data/processed/daily_macro_signals/         # Daily signal storage
```

### **Weekly Portfolio Reoptimization:**
```
start_live_trading.py
├── Daily macro signal check (NEW)
└── main/enhanced_complete_pipeline.py
    ├── src/data_collection/01_universe_collection.py      # S&P 600 stocks
    ├── src/data_collection/02_fundamental_data_collection.py  # Financial data (FMP API)
    ├── src/analysis/03_sector_scoring_analysis.py         # Quality scoring
    ├── src/analysis/04_macro_economic_analysis.py         # Macro conditions
    ├── src/portfolio/05_unified_portfolio_construction.py # Portfolio optimization
    └── src/analysis/06_monte_carlo_simulation.py          # Risk analysis
```

### **Trading Execution Files:**
```
src/signals/signal_generator.py          # Generate BUY/SELL signals
trading/paper_trading/alpaca_connector.py # Execute trades via Alpaca API
```

### **Configuration Files:**
```
.env                                     # API keys (Alpaca, FMP)
config/trading_config.json              # Trading parameters
```

---

## 🕙 **Enhanced Scheduling & Automation**

### **Cron Job Schedule:**
```bash
# Daily macro economic monitoring (10:00 AM BST / 5:00 AM ET)
0 10 * * * cd /path/to/project && python daily_macro_monitor.py >> logs/macro_monitor.log 2>&1

# Weekly portfolio reoptimization (Monday 10:00 AM BST / 5:00 AM ET)  
0 10 * * 1 cd /path/to/project && python start_live_trading.py >> logs/cron.log 2>&1
```

### **Mac Auto-Wake Schedule:**
```bash
# Wake computer every day at 9:55 AM (5 min before analysis)
sudo pmset repeat wake MTWRFSU 09:55:00
```

### **Enhanced Daily Timeline:**
- **9:30 AM ET** - US Market opens
- **9:55 AM BST** - Computer wakes up automatically
- **10:00 AM BST** - **DAILY**: Macro monitoring runs (all days)
- **10:00 AM BST** - **WEEKLY**: Portfolio reoptimization (Monday only)

**Monday (Full Reoptimization Day):**
- **10:00-10:05 AM** - Daily macro check + Data collection (600 stocks)
- **10:05-10:15 AM** - Analysis & portfolio construction
- **10:15-10:20 AM** - Monte Carlo validation
- **10:20-10:25 AM** - Trade execution (if validation passes)
- **10:25-10:30 AM** - Logging & cleanup

**Tuesday-Sunday (Macro Monitoring Only):**
- **10:00-10:02 AM** - Macro economic analysis
- **10:02-10:03 AM** - Signal extraction and storage
- **10:03-10:05 AM** - Logging and reporting

---

## 📊 **Enhanced Monitoring & Logs**

### **Log Files:**
```
logs/daily_macro_monitor.log            # Daily macro monitoring (NEW)
logs/macro_monitor.log                  # Macro monitor cron output (NEW)
logs/live_trading_automation.log        # Weekly automation log
logs/alpaca_trading.log                 # Trading execution log
logs/cron.log                          # Weekly reoptimization cron output
logs/signals.log                       # Signal generation log
```

### **Data Output Files:**
```
data/processed/daily_macro_signals/     # Daily macro signals (NEW)
├── macro_signals_YYYY-MM-DD.json      # Daily timestamped signals
└── latest_macro_signals.json          # Latest for easy access

data/processed/portfolios/              # Generated portfolios (weekly)
data/processed/monte_carlo_*            # Risk analysis results (weekly)
trading/backtesting/                   # Backtest results (weekly)
```

### **Enhanced Monitoring Commands:**
```bash
# Check cron job status
crontab -l

# Check wake schedule  
pmset -g sched

# View recent macro monitoring logs
tail -50 logs/daily_macro_monitor.log

# View recent automation logs
tail -50 logs/live_trading_automation.log

# Check latest macro signals
cat data/processed/daily_macro_signals/latest_macro_signals.json

# Check current positions
python -c "from trading.paper_trading.alpaca_connector import AlpacaPaperTrader; trader = AlpacaPaperTrader(); print(trader.get_current_positions())"
```

---

## 🛡️ **Enhanced Risk Management Features**

### **Two-Tier Risk Control:**
1. **Daily Macro Risk Gate** - Can halt all trading if conditions deteriorate
2. **Weekly Portfolio Validation** - Technical analysis before execution
3. **Position Limits** - Maximum single stock & sector exposure
4. **Quality Filters** - Only high-quality companies selected
5. **Regime Adaptation** - Strategy adjusts to economic conditions

### **Macro Risk Thresholds:**
- **HALT → DEFENSIVE REOPTIMIZATION**: Recession probability > 50% OR bear market/crisis regime
  - **Action**: Immediately reoptimize to defensive/value allocation  
  - **Sectors**: Boost Healthcare, Consumer Defensive, Utilities, Financial Services
  - **Reduce**: Technology, Real Estate, Energy, Consumer Cyclical
- **CAUTION Mode**: Recession probability > 35% OR stressed market conditions  
  - **Action**: Proceed with heightened risk awareness
- **PROCEED**: Normal market conditions with recession probability < 35%
  - **Action**: Standard quality momentum optimization

### **Fail-Safe Mechanisms:**
- Daily macro veto power over weekly trades
- Skip trades if validation fails
- Log all decisions for review
- Maintain cash buffer for market downturns
- Automatic retry logic for temporary failures

---

## 🎯 **Updated System Status**

### **Current Configuration:**
- ✅ **Daily Macro Monitoring**: Active every day at 10:00 AM BST
- ✅ **Weekly Reoptimization**: Active Monday at 10:00 AM BST
- ✅ **Alpaca Connection**: Active paper trading account
- ✅ **API Limits**: 300 FMP calls/minute configured
- ✅ **Auto-Wake**: Every day at 9:55 AM via pmset
- ✅ **Enhanced Risk Management**: Macro + portfolio validation enabled
- ✅ **Comprehensive Logging**: All activities tracked

### **Next Automated Runs:**
- **Daily Macro Check**: Every day at 10:00 AM BST
- **Weekly Reoptimization**: Next Monday at 10:00 AM BST
- **Action**: Continuous macro monitoring + weekly rebalancing (if conditions permit)
- **User Input**: None required - fully automated

---

## 🚀 **Enhanced Summary**

This Quality Momentum Strategy now runs with **intelligent two-tier automation**:

**📊 Daily Macro Intelligence:**
- Monitors market regime and recession risk every day
- Can halt trading if conditions become unfavorable
- Lightweight analysis that protects capital

**🔄 Weekly Portfolio Optimization:**
- Complete rebalancing every Monday morning
- Only proceeds if macro conditions are acceptable
- Full fundamental analysis of 600 stocks
- Risk-managed execution via Alpaca paper trading

**🛡️ Superior Risk Management:**
- Daily macro early warning system
- Technical portfolio validation
- Multi-layer fail-safe mechanisms
- Institutional-level risk controls

**The system is designed to be both aggressive in capturing opportunities and defensive in protecting capital during adverse conditions.**

---

*Last Updated: 2025-06-02*
*Documentation Version: 2.0 - Two-Tier System* 🎯 