# Enhanced Fed Data Scraper

A comprehensive Federal Reserve data collection system that integrates with your Quality Momentum Strategy.

## 🎯 Overview

This system collects Fed rate projections and economic data from multiple sources:

- **CME FedWatch Tool**: Real-time Fed rate probabilities
- **FRED (Federal Reserve Economic Data)**: Official economic indicators
- **Trading Economics**: Economic calendar and forecasts
- **Federal Reserve Website**: Current rates and announcements

## 📁 Files Structure

```
FED_Scraper/
├── CME FedWatch Scraper.py      # Original simple scraper
├── enhanced_fed_scraper.py      # Comprehensive scraper (NEW)
├── test_cme_endpoint.py         # Connection tester (NEW)
├── fed_data_20250601_002537.csv # Sample scraped data
└── README.md                    # This file
```

## 🚀 Quick Start

### 1. Test the CME Endpoint

```bash
cd FED_Scraper
python test_cme_endpoint.py
```

This will verify if the CME FedWatch JSON endpoint is accessible and working.

### 2. Basic Usage (No API Keys Required)

```python
from enhanced_fed_scraper import EnhancedFedDataScraper

# Initialize without API keys (uses fallback data)
scraper = EnhancedFedDataScraper()

# Get comprehensive Fed data
data = scraper.scrape_all_fed_data()

# Save to CSV
scraper.save_to_csv(data)

# Analyze Fed outlook
analysis = scraper.analyze_fed_outlook(data)
print(f"Most likely outcome: {analysis.get('most_likely_outcome', 'Unknown')}")
```

### 3. Advanced Usage (With API Keys)

```python
# Get your free FRED API key: https://fred.stlouisfed.org/docs/api/api_key.html
fred_key = "your_fred_api_key_here"

# Trading Economics API key (optional, for premium features)
te_key = "your_te_api_key_here"  # Can be None

scraper = EnhancedFedDataScraper(
    fred_api_key=fred_key,
    te_api_key=te_key
)

data = scraper.scrape_all_fed_data()
```

## 🔧 Integration with Macro Analysis

### Using the Integration Module

```python
from data_collection.fed_integration_module import FedIntegrationModule

# Initialize Fed integration
fed_module = FedIntegrationModule(fred_api_key="your_key")

# Get comprehensive Fed data
fed_data = fed_module.get_comprehensive_fed_data()

# Integrate with your existing macro analysis
treasury_rates = {'2_year': 4.2, '10_year': 4.0}
economic_indicators = {'vix': 18.5}

integrated_analysis = fed_module.integrate_with_macro_analysis(
    treasury_rates, economic_indicators
)

# Save analysis
fed_module.save_fed_analysis(integrated_analysis)
```

## 📊 Data Sources & Setup

### 1. CME FedWatch Tool

**What it provides:**
- Fed rate probabilities for upcoming FOMC meetings
- Market-implied Fed funds rate expectations
- Real-time market pricing of Fed policy changes

**Setup:** No API key required (uses JSON endpoint)

**Endpoint:** `https://www.cmegroup.com/CmeWS/mvc/FedWatchTool/targetRateData`

**Status:** ✅ Working (tested)

### 2. FRED (Federal Reserve Economic Data)

**What it provides:**
- Official Fed funds rate
- Economic indicators (unemployment, inflation, GDP)
- Treasury rates
- Consumer sentiment, manufacturing data

**Setup:** 
1. Get free API key: https://fred.stlouisfed.org/docs/api/api_key.html
2. Add to scraper: `EnhancedFedDataScraper(fred_api_key="your_key")`

**Status:** ✅ Available with free API key

### 3. Trading Economics

**What it provides:**
- Economic calendar with Fed events
- Economic forecasts and expectations
- Market outlook data

**Setup:**
1. Get API key: https://tradingeconomics.com/analytics/api
2. Add to scraper: `EnhancedFedDataScraper(te_api_key="your_key")`

**Status:** ⚠️ Optional (premium features)

## 🔍 Data Output

### CME FedWatch Data
```csv
target_rate,probability,meeting_date,implied_rate
4.25-4.50,75.2,20250618,4.45
4.00-4.25,24.8,20250618,4.45
```

### FRED Economic Indicators
```csv
indicator,value,date,mom_change,yoy_change
unemployment_rate,4.2,2025-04-01,-0.1,0.3
core_pce,2.1,2025-04-01,0.2,2.8
effective_fed_funds,4.375,2025-05-01,0.0,1.2
```

### Fed Analysis Output
```csv
metric,value,type,timestamp
fed_integration_market_pricing_most_likely_outcome,Rate Hold,str,2025-06-01
fed_integration_policy_assessment_policy_bias,Neutral,str,2025-06-01
fed_policy_impact_growth_vs_value_signal,Neutral,str,2025-06-01
```

## 🛠️ Troubleshooting

### Common Issues

**1. CME Connection Timeout**
```
Error: HTTPSConnectionPool(host='www.cmegroup.com', port=443): Read timed out
```
**Solution:** CME servers can be slow. The system will use fallback data.

**2. FRED API Not Available**
```
FRED API not available
```
**Solution:** Get a free FRED API key and add it to the scraper initialization.

**3. Trading Economics Error**
```
Error: module 'tradingeconomics.glob' has no attribute 'apikey'
```
**Solution:** This is expected without a Trading Economics API key. System will continue without this data.

### Connection Testing

Run the connection tester to diagnose issues:

```bash
python test_cme_endpoint.py
```

### Fallback Mode

The system is designed to work even when external APIs are unavailable:

- **CME Timeout**: Uses estimated Fed rate probabilities
- **No FRED Key**: Uses approximate economic indicators  
- **No TE Key**: Skips economic calendar data

**Data Quality Score:** The system provides a completeness score (0-100) showing how much real data vs. fallback data is being used.

## 🔗 Integration Points

### With Existing Macro Analysis

The Fed integration module seamlessly connects to your existing `06_macro_economic_analysis.py`:

```python
# In your macro analysis file
from data_collection.fed_integration_module import FedIntegrationModule

# Add Fed data enhancement
fed_module = FedIntegrationModule(fred_api_key="your_key")
fed_analysis = fed_module.integrate_with_macro_analysis(treasury_rates, economic_indicators)

# Enhanced Fed-aware recession probability
enhanced_recession_analysis = calculate_recession_probability_with_fed(
    treasury_rates, recession_indicators, economic_indicators, fed_analysis
)
```

### Key Integration Benefits

1. **Market-Based Fed Expectations**: Real CME FedWatch probabilities vs. estimated expectations
2. **Enhanced Treasury Analysis**: Compare market rates with Fed-implied rates
3. **Policy Impact Assessment**: Automatic sector/style recommendations based on Fed outlook
4. **Data Quality Scoring**: Know when you're using real vs. fallback data

## 📅 Automation & Scheduling

### Daily Data Collection

```python
import schedule
import time

def daily_fed_update():
    scraper = EnhancedFedDataScraper(fred_api_key="your_key")
    data = scraper.scrape_all_fed_data()
    scraper.save_to_csv(data, "daily_fed_data")

# Schedule daily at 9 AM
schedule.every().day.at("09:00").do(daily_fed_update)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### FOMC Meeting Alerts

The system automatically tracks FOMC meeting dates and can provide enhanced analysis around Fed meetings.

## 🔐 API Keys & Security

### Getting Free FRED API Key

1. Go to: https://fred.stlouisfed.org/docs/api/api_key.html
2. Create free account
3. Generate API key
4. Add to your environment or script

### Environment Variables (Recommended)

```bash
# Add to .env file
FRED_API_KEY=your_fred_api_key_here
TE_API_KEY=your_trading_economics_key_here
```

```python
import os
from dotenv import load_dotenv

load_dotenv()
scraper = EnhancedFedDataScraper(
    fred_api_key=os.getenv("FRED_API_KEY"),
    te_api_key=os.getenv("TE_API_KEY")
)
```

## 📈 Performance & Reliability

- **CME Data**: Usually available, but can timeout during high traffic
- **FRED Data**: Very reliable with API key, rate limited to 120 calls/minute
- **Trading Economics**: Premium service, high reliability
- **Fallback System**: Always provides reasonable estimates even when all external sources fail

## 🆕 Recent Updates

- ✅ Added CME FedWatch JSON endpoint integration
- ✅ Implemented FRED API support
- ✅ Created comprehensive integration module
- ✅ Added fallback data system
- ✅ Built data quality scoring
- ✅ Enhanced treasury analysis with Fed expectations

## 🤝 Contributing

To add new data sources or enhance the Fed analysis:

1. Add new scraping method to `EnhancedFedDataScraper`
2. Update `_process_fed_data()` to handle new data format
3. Enhance `_assess_policy_impact()` for new insights
4. Add tests to `test_cme_endpoint.py`

## 📞 Support

For issues with:
- **CME Data**: Check connection with `test_cme_endpoint.py`
- **FRED API**: Verify API key at https://fred.stlouisfed.org/
- **Integration**: Review `fed_integration_module.py` examples
- **Fallback Mode**: System will always provide some data 