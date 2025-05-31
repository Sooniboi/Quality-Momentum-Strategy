# Quality Momentum Strategy

A professional-grade quantitative investment system that combines traditional fundamental analysis with academic Fama-French factor models to construct quality-momentum focused portfolios from the S&P 600 Small Cap universe.

## 🚀 Quick Start

```bash
# Run complete pipeline
python run_complete_pipeline.py

# Skip data collection (use existing data)  
python run_complete_pipeline.py --skip-data-collection

# Run individual steps
python universe/01_universe_collection.py
python data_collection/02_fundamental_data_collection.py
python data_collection/03_sector_scoring_analysis.py
python data_collection/04_portfolio_construction.py
python data_collection/05_risk_analysis_with_ff.py
python data_collection/06_macro_economic_analysis.py
```

## 📂 File Structure

### Python Scripts (Sequential Pipeline)
```
universe/
└── 01_universe_collection.py              # S&P 600 universe from Wikipedia

data_collection/
├── 02_fundamental_data_collection.py      # Fundamental + momentum data via FMP API
├── 03_sector_scoring_analysis.py          # Sector-relative z-score analysis
├── 04_portfolio_construction.py           # Quality-filtered portfolio selection
├── 05_risk_analysis_with_ff.py           # Risk metrics + Fama-French attribution
├── 06_macro_economic_analysis.py         # Macro regime & allocation recommendations
└── fama_french_factors.py                # FF factor data utilities

run_complete_pipeline.py                   # Master pipeline runner
```

### Generated Output Files
```
csv_data_files/
├── 01_universe_sp600_companies_YYYY-MM-DD.csv     # S&P 600 holdings list
├── 02_fundamentals_with_momentum_YYYY-MM-DD.csv   # Raw fundamental metrics
├── 03_sector_scored_companies_YYYY-MM-DD.csv      # Sector z-scores & rankings  
├── 04_final_portfolio_selection_YYYY-MM-DD.csv    # Final 25-50 stock portfolio
├── 05_macro_economic_analysis_YYYY-MM-DD.csv      # Macro regime analysis
└── risk_analysis/
    ├── portfolio_correlations_YYYY-MM-DD.csv      # Stock correlation matrix
    └── portfolio_risk_metrics_YYYY-MM-DD.csv      # Individual stock risk metrics
```

## 🎯 Strategy Overview

### Core Methodology
1. **Universe Definition**: S&P 600 Small Cap Index (~600 stocks)
2. **Quality Metrics**: ROIC, Operating Margin, FCF, Net Debt/EBITDA
3. **Momentum Signals**: 3M and 6M price returns  
4. **Sector-Relative Scoring**: Z-score methodology within each sector
5. **Style Classification**: Quality, Growth, Value, Blend
6. **Risk Management**: Correlation analysis, concentration limits, Fama-French attribution

### Portfolio Construction
- **Target Allocation**: Quality 40%, Growth 30%, Value 20%, Blend 10%
- **Quality Filters**: Positive ROIC, positive operating margins, top 10 per sector
- **Concentration Limits**: Max 25% per sector, equal-weighted positions
- **Risk Overlay**: Macro regime adjustments, FF factor analysis

## 📊 Key Features

### ✅ **Professional-Grade Analysis**
- Sector-relative z-score methodology
- Fama-French 5-factor + momentum attribution  
- Comprehensive risk analytics
- Macro regime classification

### ✅ **Clean Data Pipeline**
- Sequential numbered files prevent duplicates
- Update-in-place logic for iterative runs
- Comprehensive error handling
- Professional file organization

### ✅ **Institutional Quality**
- Real-time data from Financial Modeling Prep API
- Kenneth French's actual factor data
- Recession probability modeling
- Style-based portfolio allocation

## 🔧 Configuration

### Required Environment Variables
```bash
# .env file
FMP_API_KEY=your_financial_modeling_prep_api_key
```

### Dependencies
```bash
pip install pandas numpy requests python-dotenv tqdm scikit-learn pandas-datareader
```

## 📈 Pipeline Steps Explained

### Step 1: Universe Collection
- Scrapes S&P 600 constituents from Wikipedia
- Extracts ticker symbols, sectors, company names
- **Output**: `01_universe_sp600_companies_YYYY-MM-DD.csv`

### Step 2: Fundamental Data Collection  
- Pulls financial metrics via FMP API for all universe stocks
- Calculates momentum returns (3M, 6M)
- **Runtime**: ~45-60 minutes for full universe
- **Output**: `02_fundamentals_with_momentum_YYYY-MM-DD.csv`

### Step 3: Sector Scoring Analysis
- Calculates sector-relative z-scores for all metrics
- Generates weighted composite scores using sector-specific weights
- Classifies stocks by investment style (Quality/Growth/Value/Blend)
- **Output**: `03_sector_scored_companies_YYYY-MM-DD.csv`

### Step 4: Portfolio Construction
- Applies quality filters (positive ROIC/margins, top sector rankings)
- Selects stocks based on style targets (Quality 40%, Growth 30%, etc.)
- Enforces concentration limits and equal weighting
- **Output**: `04_final_portfolio_selection_YYYY-MM-DD.csv`

### Step 5: Risk Analysis with Fama-French
- Downloads real factor data from Kenneth French's library
- Calculates portfolio-level factor exposures via regression
- Analyzes correlations, volatility, concentration risks
- **Output**: Risk analysis files in `risk_analysis/` folder

### Step 6: Macro Economic Analysis
- Fetches treasury rates, economic indicators, recession signals
- Calculates professional recession probability model
- Generates sector/style allocation recommendations
- **Output**: `05_macro_economic_analysis_YYYY-MM-DD.csv`

## 🎨 Usage Examples

### Run Full Pipeline (New Data)
```bash
python run_complete_pipeline.py
# Runtime: ~60-90 minutes
```

### Quick Analysis (Existing Data)
```bash
python run_complete_pipeline.py --skip-data-collection  
# Runtime: ~2-3 minutes
```

### Individual Step Analysis
```bash
# Update scoring with new methodology
python data_collection/03_sector_scoring_analysis.py

# Rebuild portfolio with different parameters
python data_collection/04_portfolio_construction.py
```

## 📋 System Requirements

- **Python**: 3.8+
- **Memory**: 2GB+ RAM
- **Storage**: 500MB for data files
- **API**: Financial Modeling Prep account (free tier sufficient)
- **Internet**: Required for data downloads

## 🔍 Quality Assurance

### File Management
- ✅ No duplicate files created
- ✅ Clear sequential naming (01, 02, 03...)
- ✅ Update-in-place for iterative runs
- ✅ Archived old files for safety

### Data Integrity  
- ✅ Comprehensive error handling
- ✅ Data validation at each step
- ✅ Missing data warnings
- ✅ Coverage reporting

### Professional Standards
- ✅ Academic factor model integration
- ✅ Institutional risk analytics
- ✅ Production-ready code structure
- ✅ Comprehensive documentation

---

**Built with institutional-quality standards for professional portfolio management.** 