# 🌳 Quality Momentum Strategy - System Decision Trees & Flow Diagrams

## 📊 Main System Decision Tree

```
🚀 START: Enhanced Complete Pipeline
│
├── 🔍 Check Dependencies
│   ├── ✅ All installed → Continue
│   └── ❌ Missing packages → EXIT with error
│
├── 📋 Parse Command Line Arguments
│   ├── --skip-data-collection → Skip to Analysis Phase
│   ├── --skip-backtesting → Skip backtesting
│   ├── --skip-paper-trading → Skip paper trading
│   ├── --test-mode → Use limited data
│   └── --backtest-years N → Set historical period
│
├── 📊 PHASE 1: Data Collection & Preparation
│   │
│   ├── 🌐 01_universe_collection.py
│   │   ├── Connect to S&P 600 data source
│   │   ├── Filter by market cap ($1B-$10B)
│   │   ├── Apply liquidity filters (volume > $1M daily)
│   │   ├── ✅ Success → Save universe to data/processed/
│   │   └── ❌ Failure → ABORT pipeline
│   │
│   └── 📈 02_fundamental_data_collection.py
│       ├── Load universe from previous step
│       ├── FOR each stock in universe:
│       │   ├── Fetch fundamental metrics (ROIC, margins, FCF)
│       │   ├── Calculate momentum indicators (3M, 6M returns)
│       │   ├── Get valuation ratios (P/E, P/B, EV/EBITDA)
│       │   └── Handle missing data → Use sector median
│       ├── ✅ Success → Save to data/processed/
│       └── ❌ Failure → ABORT pipeline
│
├── 🔬 PHASE 2: Analysis & Scoring
│   │
│   ├── 📊 03_sector_scoring_analysis.py
│   │   ├── Load fundamental data
│   │   ├── Group by GICS sectors (11 sectors)
│   │   ├── FOR each sector:
│   │   │   ├── Calculate z-scores for each metric
│   │   │   ├── Rank stocks within sector
│   │   │   └── Apply sector-relative scoring
│   │   ├── Combine scores → Composite Quality Score
│   │   ├── ✅ Success → Save to data/processed/
│   │   └── ❌ Failure → ABORT pipeline
│   │
│   ├── 🏛️ 04_macro_economic_analysis.py
│   │   ├── Fetch Fed policy data (FOMC minutes, rates)
│   │   ├── Calculate recession probability (NY Fed model)
│   │   ├── Analyze yield curve (2Y-10Y spread)
│   │   ├── Get economic indicators (unemployment, inflation)
│   │   ├── DECISION TREE: Fed Policy Classification
│   │   │   ├── Rate changes + FOMC tone → HAWKISH
│   │   │   ├── Rate cuts + dovish tone → DOVISH  
│   │   │   └── No clear direction → NEUTRAL
│   │   ├── DECISION TREE: Market Regime
│   │   │   ├── Recession prob > 40% → RECESSION
│   │   │   ├── Recession prob < 15% → EXPANSION
│   │   │   └── 15% ≤ prob ≤ 40% → NORMAL
│   │   ├── Apply macro adjustments to sectors
│   │   ├── ✅ Success → Save to data/processed/macro_analysis/
│   │   └── ❌ Failure → Continue with warnings
│   │
│   └── 🎲 06_monte_carlo_simulation.py
│       ├── Load portfolio from previous steps
│       ├── Estimate return distributions for each stock
│       ├── Run 10,000 simulations
│       ├── FOR each simulation:
│       │   ├── Sample returns from distributions
│       │   ├── Calculate portfolio return
│       │   └── Track maximum drawdown
│       ├── Calculate risk metrics (VaR, CVaR, Sharpe)
│       ├── ✅ Success → Save to data/processed/monte_carlo_analysis/
│       └── ❌ Failure → Continue with warnings
│
├── 🎯 PHASE 3: Portfolio Construction
│   │
│   └── 💼 05_unified_portfolio_construction.py
│       ├── Load scored companies + macro analysis
│       ├── DECISION TREE: Style Classification
│       │   ├── High growth + momentum → GROWTH
│       │   ├── Low valuation + positive fundamentals → VALUE
│       │   ├── High quality metrics → QUALITY
│       │   └── Mixed characteristics → BLEND
│       ├── Apply macro-based sector adjustments
│       │   ├── Fed HAWKISH → Financials +10%, Real Estate -15%
│       │   ├── Fed DOVISH → Tech +5%, Utilities -10%
│       │   └── RECESSION → Defensives +20%, Cyclicals -15%
│       ├── DECISION TREE: Portfolio Selection
│       │   ├── Top 20% quality scores → Include in portfolio
│       │   ├── Apply diversification rules (max 5% per stock)
│       │   ├── Sector limits (max 25% per sector)
│       │   └── Target 30-50 final positions
│       ├── Optimize weights using Modern Portfolio Theory
│       ├── ✅ Success → Save to data/processed/portfolios/
│       └── ❌ Failure → ABORT pipeline
│
├── 📈 PHASE 4: Validation & Trading (Optional)
│   │
│   ├── 📊 06_historical_backtesting.py
│   │   ├── IF --skip-backtesting → SKIP
│   │   ├── Load portfolio weights
│   │   ├── Fetch historical price data (FMP API)
│   │   ├── FOR each rebalancing period:
│   │   │   ├── Calculate portfolio returns
│   │   │   ├── Compare vs benchmark (IJR)
│   │   │   └── Track performance metrics
│   │   ├── Generate performance charts
│   │   ├── Create HTML report
│   │   ├── ✅ Success → Save to trading/backtesting/
│   │   └── ❌ Failure → Continue with warnings
│   │
│   └── 💰 07_paper_trading_setup.py
│       ├── IF --skip-paper-trading → SKIP
│       ├── Check Alpaca API credentials
│       ├── IF no credentials → Setup demo mode
│       ├── Load current portfolio
│       ├── Calculate target positions
│       ├── Submit paper trading orders
│       ├── Setup monitoring system
│       ├── ✅ Success → Save to trading/paper_trading/
│       └── ❌ Failure → Continue with warnings
│
└── 🎉 COMPLETE: Generate Summary Report
    ├── Count successful steps
    ├── List generated files
    ├── Show next steps
    └── EXIT with status code
```

## 🔄 Data Flow Diagram

```
📊 DATA FLOW THROUGH SYSTEM

🌐 External Data Sources
│
├── S&P 600 Index Data → 01_universe_collection.py
├── Financial Modeling Prep API → 02_fundamental_data_collection.py  
├── Financial Modeling Prep API → 06_historical_backtesting.py
├── Fed/FRED APIs → 04_macro_economic_analysis.py
└── Alpaca Markets → 07_paper_trading_setup.py

⬇️ 

📁 data/raw/
├── sp600_universe.csv
├── fed_policy_data.csv
└── economic_indicators.csv

⬇️ [PROCESSING]

📊 src/data_collection/
├── 01_universe_collection.py
│   ├── INPUT: S&P 600 index
│   ├── FILTER: Market cap, liquidity
│   └── OUTPUT: data/processed/01_universe_sp600_companies_YYYY-MM-DD.csv
│
└── 02_fundamental_data_collection.py
    ├── INPUT: Universe from step 1
    ├── ENRICH: Fundamentals + momentum (FMP API)
    └── OUTPUT: data/processed/02_fundamentals_with_momentum_YYYY-MM-DD.csv

⬇️

🔬 src/analysis/
├── 03_sector_scoring_analysis.py
│   ├── INPUT: Fundamentals from step 2
│   ├── PROCESS: Sector z-scores, rankings
│   └── OUTPUT: data/processed/03_sector_scored_companies_YYYY-MM-DD.csv
│
├── 04_macro_economic_analysis.py
│   ├── INPUT: Economic data from APIs
│   ├── PROCESS: Fed policy, recession probability
│   └── OUTPUT: data/processed/macro_analysis/04_macro_analysis_YYYY-MM-DD.csv
│
└── 06_monte_carlo_simulation.py
    ├── INPUT: Portfolio from step 5
    ├── PROCESS: 10K simulations, risk metrics
    └── OUTPUT: data/processed/monte_carlo_analysis/06_monte_carlo_*.csv

⬇️

🎯 src/portfolio/
└── 05_unified_portfolio_construction.py
    ├── INPUT: Scored companies + macro analysis
    ├── PROCESS: Style classification, optimization
    └── OUTPUT: data/processed/portfolios/05_portfolio_YYYY-MM-DD.csv

⬇️

📈 trading/
├── backtesting/06_historical_backtesting.py
│   ├── INPUT: Portfolio + historical prices (FMP API)
│   ├── PROCESS: Performance analysis vs benchmark
│   └── OUTPUT: trading/backtesting/06_backtest_report_YYYY-MM-DD.html
│
└── paper_trading/07_paper_trading_setup.py
    ├── INPUT: Current portfolio
    ├── PROCESS: Submit orders to Alpaca
    └── OUTPUT: trading/paper_trading/07_trading_log_YYYY-MM-DD.csv

⬇️

📊 reports/
├── Performance_Summary_YYYY-MM-DD.html
├── Risk_Analysis_YYYY-MM-DD.pdf
├── Portfolio_Composition_YYYY-MM-DD.png
└── Macro_Economic_Outlook_YYYY-MM-DD.md
```

## 🤔 Decision Logic Tree

```
🧠 CORE DECISION LOGIC

📊 UNIVERSE FILTERING
├── Market Cap Filter
│   ├── IF market_cap < $1B → EXCLUDE
│   ├── IF market_cap > $10B → EXCLUDE  
│   └── ELSE → INCLUDE in universe
├── Liquidity Filter
│   ├── IF avg_daily_volume < $1M → EXCLUDE
│   └── ELSE → CONTINUE
└── Data Quality Filter
    ├── IF missing_data > 50% → EXCLUDE
    └── ELSE → INCLUDE

💰 FUNDAMENTAL SCORING  
├── Quality Metrics (40% weight)
│   ├── ROIC > 15% → High score
│   ├── Operating Margin > 10% → High score
│   ├── Free Cash Flow positive → High score
│   └── Net Debt/EBITDA < 3 → High score
├── Momentum Metrics (35% weight)
│   ├── 3M return > sector median → High score
│   ├── 6M return > sector median → High score
│   └── Revenue growth > 5% → High score
└── Valuation Metrics (25% weight)
    ├── P/E < sector median → High score
    ├── P/B < sector median → High score
    └── EV/EBITDA < sector median → High score

🏛️ MACRO REGIME CLASSIFICATION
├── Fed Policy Analysis
│   ├── IF (rate_hikes > 0) AND (fomc_tone = "hawkish") → HAWKISH
│   ├── IF (rate_cuts > 0) AND (fomc_tone = "dovish") → DOVISH
│   └── ELSE → NEUTRAL
├── Market Regime Analysis  
│   ├── IF recession_probability > 40% → RECESSION
│   ├── IF recession_probability < 15% → EXPANSION
│   └── ELSE → NORMAL
└── Sector Adjustments
    ├── IF Fed = HAWKISH
    │   ├── Financials weight +10%
    │   ├── Real Estate weight -15%
    │   └── Growth weight +5%
    ├── IF Fed = DOVISH
    │   ├── Technology weight +5%
    │   ├── Utilities weight -10%
    │   └── Value weight +5%
    └── IF Regime = RECESSION
        ├── Consumer Staples +20%
        ├── Healthcare +15%
        └── Industrials -15%

🎯 PORTFOLIO CONSTRUCTION
├── Style Classification
│   ├── IF (growth_score > 75th percentile) AND (momentum > 75th) → GROWTH
│   ├── IF (value_score > 75th percentile) AND (fundamentals > 50th) → VALUE
│   ├── IF (quality_score > 90th percentile) → QUALITY
│   └── ELSE → BLEND
├── Position Sizing
│   ├── Base weight = 1/N (equal weight)
│   ├── Quality adjustment = score_rank * 0.02
│   ├── Macro adjustment = sector_bias * 0.01
│   └── Final weight = MIN(base_weight + adjustments, 5%)
├── Diversification Rules
│   ├── Maximum 5% per position
│   ├── Maximum 25% per sector
│   ├── Minimum 30 positions
│   └── Maximum 50 positions
└── Risk Controls
    ├── Portfolio beta target: 0.8 - 1.2
    ├── Tracking error target: < 8%
    ├── Maximum drawdown limit: 20%
    └── Turnover limit: < 50% annually

📊 REBALANCING DECISIONS
├── Monthly Check
│   ├── IF position drift > 2% → Rebalance
│   ├── IF new data available → Re-score
│   └── IF macro regime change → Adjust allocations
├── Quarterly Review
│   ├── Full fundamental update
│   ├── Universe reconstitution  
│   └── Strategy parameter review
└── Annual Review
    ├── Complete strategy backtesting
    ├── Performance attribution analysis
    └── Parameter optimization
```

## 🔧 Error Handling Decision Tree

```
🚨 ERROR HANDLING & RECOVERY

📡 DATA COLLECTION ERRORS
├── API Rate Limit Hit
│   ├── Wait 60 seconds
│   ├── Retry with exponential backoff
│   └── IF still failing → Use cached data
├── Missing Fundamental Data
│   ├── Use sector median for missing values
│   ├── Flag stock for manual review
│   └── Continue processing
├── Network/API Failure
│   ├── Retry 3 times
│   ├── IF persistent → Switch to backup source
│   └── IF all fail → ABORT with error
└── Data Quality Issues
    ├── IF data age > 6 months → Flag as stale
    ├── IF extreme outliers → Winsorize at 95th percentile
    └── IF incomplete → Use previous period data

⚖️ PORTFOLIO CONSTRUCTION ERRORS
├── Optimization Failure
│   ├── Fall back to equal weighting
│   ├── Apply manual constraints
│   └── Continue with warnings
├── Insufficient Universe
│   ├── IF stocks < 30 → Expand universe criteria
│   ├── Reduce minimum liquidity requirement
│   └── Continue with modified parameters
└── Risk Constraint Violations
    ├── Adjust position sizes down
    ├── Remove problematic positions
    └── Re-optimize with tighter constraints

🏦 TRADING SYSTEM ERRORS
├── Alpaca API Failure
│   ├── Log error details
│   ├── Continue in simulation mode
│   └── Send alert notification
├── Order Rejection
│   ├── Check position limits
│   ├── Modify order size
│   └── Retry with market order
└── Portfolio Sync Issues
    ├── Reconcile positions manually
    ├── Update tracking system
    └── Generate exception report

🔄 RECOVERY PROCEDURES
├── Partial System Failure
│   ├── Save intermediate results
│   ├── Resume from last successful step
│   └── Generate recovery report
├── Complete System Failure
│   ├── Email alert to administrator
│   ├── Save system state
│   └── Schedule automatic retry
└── Data Corruption
    ├── Restore from backup
    ├── Re-run validation checks
    └── Manual review required
```

This comprehensive decision tree and flow diagram shows exactly how every component of your Quality Momentum Strategy system works together, makes decisions, and handles different scenarios. Each step has clear inputs, processing logic, outputs, and error handling procedures. 