# Quality Momentum Strategy

A systematic small-cap equity investing strategy that combines quality metrics, momentum indicators, risk analysis, and macro-economic conditions into a unified portfolio construction process.

## 🎯 Strategy Overview

- **Universe**: S&P 600 Small Cap (~600 stocks)
- **Approach**: Quality + Momentum + Risk Management + Macro Overlay
- **Target**: 50-stock portfolio with style diversification
- **Rebalancing**: Monthly with daily risk monitoring

## 🚀 Quick Start

Run the complete strategy in 4 simple steps:

```bash
cd data_collection

# Step 1: Collect S&P 600 universe and fundamentals
python 01_fundamental_data_collection.py

# Step 2: Perform sector-relative scoring
python 02_sector_scoring_analysis.py  

# Step 3: Analyze macro economic conditions
python 03_macro_economic_analysis.py

# Step 4: Construct unified portfolio (MAIN SYSTEM)
python 04_unified_portfolio_construction.py
```

The final portfolio will be saved to `csv_data_files/portfolios/` with full metadata.

## 📊 System Architecture

The **Unified Portfolio Construction System** integrates all components:

- **Sector Scoring** → Company selection and style classification
- **Risk Analysis** → Volatility estimation and weight optimization  
- **Macro Economics** → Market regime detection and sector adjustments
- **Portfolio Construction** → Final 50-stock allocation with constraints

## 📁 Organized File Structure

```
📁 data_collection/           # Python scripts
📁 csv_data_files/
  ├── 📁 fundamental_data/    # S&P 600 → fundamentals → sector scoring
  ├── 📁 macro_analysis/      # Economic conditions & recession probability  
  ├── 📁 portfolios/          # Final portfolio outputs ⭐
  └── 📁 risk_analysis/       # Risk metrics & correlations
```

## 🎯 Current Results

**Latest Portfolio (June 1, 2025)**:
- **29 companies** across 10 sectors
- **Quality-focused**: 70.5% allocation (appropriate for current market)
- **Risk-controlled**: 5% max per stock, 25% max per sector
- **Estimated volatility**: 5.0% with beta of 1.11

## 📋 Key Features

✅ **Market Regime Adaptation**: Defensive/Cautious/Normal allocations  
✅ **Risk-Optimized Weighting**: Score-based + risk-parity + equal weighting  
✅ **Dynamic Style Allocation**: Quality/Growth/Value/Blend targets adjust to market  
✅ **Comprehensive Risk Management**: Volatility limits, correlation filters, concentration limits  
✅ **Full Audit Trail**: Detailed metadata and construction parameters saved  

## 📖 Documentation

See [UNIFIED_PORTFOLIO_SYSTEM.md](UNIFIED_PORTFOLIO_SYSTEM.md) for complete system documentation.

---

**Built for systematic, risk-conscious small-cap investing with adaptive allocation based on market conditions.** 