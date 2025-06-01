# Unified Portfolio Construction System

## Overview

The **Unified Portfolio Construction System** is a streamlined approach that integrates all strategy components into ONE cohesive portfolio construction process. Instead of having separate systems for risk analysis, macro economics, and portfolio construction, everything feeds directly into the portfolio building workflow.

## System Architecture

```
📊 Sector Scoring Data
🌍 Macro Economic Data     ⟶  🎯 UNIFIED PORTFOLIO CONSTRUCTION  ⟶  📈 Final Portfolio
⚠️ Risk Analysis Data
```

## Key Features

### 1. **Integrated Data Loading**
- Automatically loads latest sector scored data (600 companies)
- Pulls macro economic analysis for market regime detection
- Incorporates risk analysis data when available
- Graceful fallbacks when data is missing

### 2. **Market Regime Integration**
- **DEFENSIVE**: Recession probability > 40% OR Fed policy = STRONGLY_DOVISH → Focus on Healthcare, Consumer Defensive
- **CAUTIOUS**: Recession probability 25-40% OR Fed policy = DOVISH/STRONGLY_HAWKISH → Balanced approach with safety tilt  
- **NORMAL**: Recession probability < 25% AND Fed policy = NEUTRAL/HAWKISH → Standard Quality/Growth/Value mix

**Enhanced Fed Policy Integration:**
- **HAWKISH/STRONGLY_HAWKISH**: Boost Financial Services (+10%), reduce Real Estate (-15%), reduce Utilities (-10%)
- **DOVISH/STRONGLY_DOVISH**: Boost Technology (+10%), boost Real Estate (+5%), reduce Financial Services (-10%)
- **Real-time FRED data**: Fed Funds Rate, unemployment, core PCE inflation, treasury rates
- **Fed policy stance**: Employment analysis + inflation analysis + yield curve assessment

### 3. **Risk-Aware Filtering**
- Financial health filters (positive ROIC, FCF, reasonable debt)
- Estimated volatility and beta calculations based on sector
- Risk-adjusted scoring (Quality/Volatility, Momentum/Beta)
- Maximum risk thresholds (40% volatility, 0.5-1.8 beta range)

### 4. **Dynamic Style Allocation**
Market regime automatically adjusts target allocations:

| Market Regime | Quality | Growth | Value | Blend |
|---------------|---------|--------|-------|-------|
| DEFENSIVE     | 30      | 5      | 12    | 3     |
| CAUTIOUS      | 25      | 8      | 15    | 2     |
| NORMAL        | 20      | 15     | 10    | 5     |

### 5. **Integrated Scoring System**
Final score combines multiple factors:
- **Macro-Adjusted Score** (50%): Quality + Momentum + Overall with regime adjustments
- **Risk-Adjusted Quality** (25%): Quality Score / sqrt(Volatility)  
- **Risk-Adjusted Momentum** (15%): Momentum Score / Beta
- **Sharpe Score** (10%): 6M Return / Volatility

### 6. **Risk-Optimized Weighting**
Portfolio weights combine:
- **Score-based weighting** (60%): Higher scores get more weight
- **Risk-parity weighting** (30%): Inverse volatility weighting
- **Equal weighting** (10%): Diversification baseline

### 7. **Portfolio Constraints**
- Maximum 5% per individual stock
- Maximum 25% per sector
- Automatic rebalancing when constraints are violated

## Current Results (June 1, 2025)

### Portfolio Summary
- **29 companies** across **10 sectors**
- **Market Regime**: NORMAL
- **Quality Score**: 1.14
- **Momentum Score**: 0.95  
- **Estimated Volatility**: 5.0%
- **Estimated Beta**: 1.11

### Style Distribution
- **Quality**: 70.5% (dominant allocation)
- **Blend**: 21.9%
- **Growth**: 7.6%
- **Value**: 0% (no companies met criteria)

### Top Holdings
1. **HCI** (Financial Services) - Quality - 5.06%
2. **CRVL** (Financial Services) - Blend - 5.06%  
3. **FIZZ** (Consumer Defensive) - Quality - 4.82%
4. **PRDO** (Consumer Defensive) - Blend - 4.73%
5. **YOU** (Technology) - Quality - 4.46%

## Advantages of Unified System

### ✅ **Simplified Architecture**
- ONE system instead of multiple disconnected components
- Clear data flow from inputs to final portfolio
- Easier to understand, maintain, and modify

### ✅ **Integrated Decision Making**  
- Macro conditions directly influence company selection
- Risk metrics directly affect portfolio weights
- All components work together toward portfolio optimization

### ✅ **Adaptive to Market Conditions**
- Market regime detection drives allocation decisions
- Sector adjustments based on economic environment
- Dynamic style targets based on market conditions

### ✅ **Risk-Conscious Throughout**
- Risk filtering at company selection stage
- Risk-adjusted scoring methodology
- Risk-optimized weight allocation
- Portfolio-level risk constraints

### ✅ **Comprehensive Output**
- Final portfolio with weights and scores
- Detailed metadata and construction parameters
- Portfolio-level risk and return metrics
- Clear audit trail of decisions

## Usage

```python
from unified_portfolio_construction import UnifiedPortfolioConstructor

# Initialize system
constructor = UnifiedPortfolioConstructor(target_size=50)

# Run unified construction process
portfolio = constructor.construct_portfolio()

# Results automatically saved to CSV with metadata
```

## File Structure

```
📁 Quality-Momentum-Strategy/
├── 📁 data_collection/
│   ├── 📄 01_fundamental_data_collection.py      # Step 1: Collect S&P 600 + fundamentals
│   ├── 📄 02_sector_scoring_analysis.py          # Step 2: Sector scoring
│   ├── 📄 03_macro_economic_analysis.py          # Step 3: Macro analysis  
│   ├── 📄 04_unified_portfolio_construction.py   # Step 4: Final portfolio (MAIN SYSTEM)
│   ├── 📄 fama_french_factors.py                 # Fama-French integration
│   ├── 📄 operational_scheduler.py               # Daily operations
│   └── 📄 economic_calendar.py                   # Economic events
│
├── 📁 csv_data_files/
│   ├── 📁 fundamental_data/                      # Core data pipeline
│   │   ├── 📄 01_universe_sp600_companies_*.csv         # S&P 600 universe
│   │   ├── 📄 02_fundamentals_with_momentum_*.csv       # Fundamentals + momentum
│   │   └── 📄 03_sector_scored_companies_*.csv          # Sector scoring results
│   │
│   ├── 📁 macro_analysis/                        # Macro economic data
│   │   └── 📄 05_macro_economic_analysis_*.csv          # Recession probability, etc.
│   │
│   ├── 📁 portfolios/                            # Final portfolio outputs
│   │   ├── 📄 04_unified_portfolio_selection_*.csv      # Final portfolio
│   │   └── 📄 04_unified_portfolio_selection_*_metadata.json  # Portfolio metadata
│   │
│   └── 📁 risk_analysis/                         # Risk metrics & correlations
│       ├── 📄 portfolio_risk_metrics_*.csv              # Individual stock risk
│       ├── 📄 portfolio_correlations_*.csv              # Correlation matrix
│       ├── 📄 macro_risk_analysis_latest.json           # Comprehensive macro risk (LATEST) ⭐
│       ├── 📄 fed_policy_analysis_latest.json           # Fed policy analysis (LATEST) ⭐
│       └── 📄 fred_economic_data_latest.json            # FRED economic data (LATEST) ⭐
│
└── 📄 UNIFIED_PORTFOLIO_SYSTEM.md               # This documentation
```

## Data Flow

```
1. S&P 600 Universe → 2. Fundamentals + Momentum → 3. Sector Scoring
                                    ↓
    📊 fundamental_data/           🌍 macro_analysis/    ⚠️ risk_analysis/
                                    ↓
                        🎯 UNIFIED PORTFOLIO CONSTRUCTION
                                    ↓
                            📈 portfolios/
```

This unified approach eliminates complexity while ensuring all strategic components (quality scoring, momentum analysis, risk management, macro economics) contribute meaningfully to the final portfolio construction process. 