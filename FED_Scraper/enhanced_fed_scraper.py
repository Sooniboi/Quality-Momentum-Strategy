import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Import the new libraries
try:
    from fredapi import Fred
    FRED_AVAILABLE = True
except ImportError:
    print("Warning: fredapi not available. Install with: pip install fredapi")
    FRED_AVAILABLE = False

try:
    import tradingeconomics as te
    TE_AVAILABLE = True
except ImportError:
    print("Warning: tradingeconomics not available. Install with: pip install tradingeconomics")
    TE_AVAILABLE = False

# =============================================================================
# FRED API CONFIGURATION - ADD YOUR FREE API KEY HERE
# =============================================================================
# Get your free FRED API key at: https://fred.stlouisfed.org/docs/api/api_key.html
# Then uncomment and add your key below:

# FRED_API_KEY = "your_fred_api_key_here"  # <-- ADD YOUR KEY HERE

# For testing without key, we'll use fallback methods
FRED_API_KEY = None  # Set to None to use fallback CSV scraping

# =============================================================================

class EnhancedFedDataScraper:
    def __init__(self, fred_api_key: Optional[str] = FRED_API_KEY, te_api_key: Optional[str] = None):
        """
        Enhanced Fed Data Scraper with FRED API integration
        
        Args:
            fred_api_key: Free FRED API key from https://fred.stlouisfed.org/docs/api/api_key.html
            te_api_key: Trading Economics API key (optional)
        """
        # Store API keys
        self.fred_api_key = fred_api_key
        self.te_api_key = te_api_key
        
        # Initialize FRED client if key provided
        self.fred = None
        if FRED_AVAILABLE and self.fred_api_key:
            try:
                from fredapi import Fred
                self.fred = Fred(api_key=self.fred_api_key)
                print("✅ FRED API initialized successfully")
            except Exception as e:
                print(f"⚠️ FRED API initialization failed: {e}")
                self.fred = None
        elif not self.fred_api_key:
            print("💡 FRED API key not provided - using fallback CSV method")
            print("📋 Get your free key at: https://fred.stlouisfed.org/docs/api/api_key.html")
        
        # Initialize Trading Economics if available
        self.te_client = None
        if TE_AVAILABLE and self.te_api_key:
            try:
                import tradingeconomics as te
                te.login(self.te_api_key)
                self.te_client = te
                print("✅ Trading Economics API initialized")
            except Exception as e:
                print(f"⚠️ Trading Economics initialization failed: {e}")
        
        # Fed data mapping
        self.fred_series_map = {
            'fed_funds_rate': 'FEDFUNDS',
            'fed_target_upper': 'DFEDTARU',
            'fed_target_lower': 'DFEDTARL', 
            'unemployment_rate': 'UNRATE',
            'core_pce_inflation': 'PCEPILFE',
            'pce_inflation': 'PCEPI',
            'cpi_inflation': 'CPIAUCSL',
            'treasury_10y': 'GS10',
            'treasury_2y': 'GS2',
            'treasury_3m': 'GS3M',
            'treasury_30y': 'GS30',
            'consumer_sentiment': 'UMCSENT',
            'nonfarm_payrolls': 'PAYEMS',
            'real_gdp': 'GDPC1',
            'yield_spread_10y_2y': 'T10Y2Y',
            'yield_spread_10y_3m': 'T10Y3M'
        }
        
        # Fallback CSV endpoints for FRED data (when no API key)
        self.fred_csv_endpoints = {
            'fed_funds_rate': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS&cosd=2024-01-01',
            'unemployment_rate': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE&cosd=2024-01-01',
            'core_pce_inflation': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=PCEPILFE&cosd=2024-01-01',
            'treasury_10y': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=GS10&cosd=2024-01-01',
            'treasury_2y': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=GS2&cosd=2024-01-01',
            'treasury_3m': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=GS3M&cosd=2024-01-01'
        }

    def get_fred_data_api(self, indicator: str, periods: int = 12) -> Optional[pd.Series]:
        """Get FRED data using official API"""
        if not self.fred:
            return None
            
        try:
            series_id = self.fred_series_map.get(indicator)
            if not series_id:
                print(f"❌ Unknown indicator: {indicator}")
                return None
                
            # Get data
            data = self.fred.get_series(series_id, limit=periods)
            if data is not None and not data.empty:
                print(f"✅ {indicator}: Retrieved {len(data)} points via FRED API")
                return data
            else:
                print(f"⚠️ {indicator}: No data returned from FRED API")
                return None
                
        except Exception as e:
            print(f"❌ FRED API error for {indicator}: {str(e)}")
            return None
    
    def get_fred_data_csv(self, indicator: str) -> Optional[float]:
        """Fallback: Get latest FRED data via CSV download"""
        try:
            url = self.fred_csv_endpoints.get(indicator)
            if not url:
                return None
                
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                if len(lines) >= 2:
                    latest_line = lines[-1].split(',')
                    if len(latest_line) >= 2:
                        value_str = latest_line[1]
                        if value_str != '.' and value_str != '':
                            try:
                                value = float(value_str)
                                print(f"✅ {indicator}: {value} (CSV fallback)")
                                return value
                            except ValueError:
                                pass
            
            print(f"⚠️ {indicator}: No data via CSV fallback")
            return None
            
        except Exception as e:
            print(f"❌ CSV fallback error for {indicator}: {str(e)}")
            return None

    def get_current_fed_data(self) -> Dict:
        """Get comprehensive current Fed data"""
        print("\n🏦 COLLECTING CURRENT FED DATA")
        print("="*50)
        
        fed_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_source': 'FRED_API' if self.fred else 'FRED_CSV_Fallback'
        }
        
        # Core Fed indicators to collect
        indicators = [
            'fed_funds_rate',
            'fed_target_upper', 
            'fed_target_lower',
            'unemployment_rate',
            'core_pce_inflation',
            'treasury_10y',
            'treasury_2y',
            'treasury_3m'
        ]
        
        for indicator in indicators:
            try:
                # Try API first, then fallback to CSV
                if self.fred:
                    series = self.get_fred_data_api(indicator, periods=3)
                    if series is not None and not series.empty:
                        fed_data[indicator] = {
                            'current': float(series.iloc[-1]),
                            'previous': float(series.iloc[-2]) if len(series) >= 2 else None,
                            'date': series.index[-1].strftime('%Y-%m-%d'),
                            'source': 'FRED_API'
                        }
                        
                        # Calculate change
                        if len(series) >= 2:
                            current = float(series.iloc[-1])
                            previous = float(series.iloc[-2])
                            change = current - previous
                            fed_data[indicator]['change'] = change
                        continue
                
                # Fallback to CSV
                value = self.get_fred_data_csv(indicator)
                if value is not None:
                    fed_data[indicator] = {
                        'current': value,
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'source': 'FRED_CSV'
                    }
                else:
                    # Use mock data as last resort
                    mock_values = {
                        'fed_funds_rate': 4.33,
                        'unemployment_rate': 4.2,
                        'treasury_2y': 3.78,
                        'treasury_10y': 4.15,
                        'core_pce_inflation': 2.1
                    }
                    if indicator in mock_values:
                        fed_data[indicator] = {
                            'current': mock_values[indicator],
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'source': 'FALLBACK_MOCK'
                        }
                        print(f"⚠️ {indicator}: Using mock data")
                        
            except Exception as e:
                print(f"❌ Error collecting {indicator}: {str(e)}")
        
        return fed_data

    def analyze_fed_policy_stance(self, fed_data: Dict) -> Dict:
        """Analyze current Fed policy stance"""
        print("\n🎯 ANALYZING FED POLICY STANCE")
        print("="*50)
        
        analysis = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'policy_signals': {}
        }
        
        try:
            # Extract current values
            fed_funds = fed_data.get('fed_funds_rate', {}).get('current', 4.33)
            unemployment = fed_data.get('unemployment_rate', {}).get('current', 4.2)
            core_pce = fed_data.get('core_pce_inflation', {}).get('current', 2.1)
            treasury_10y = fed_data.get('treasury_10y', {}).get('current', 4.15)
            treasury_2y = fed_data.get('treasury_2y', {}).get('current', 3.78)
            
            print(f"📊 Current Fed Funds Rate: {fed_funds:.2f}%")
            print(f"📊 Unemployment Rate: {unemployment:.1f}%")
            print(f"📊 Core PCE Inflation: {core_pce:.1f}%")
            
            # Dual mandate analysis
            employment_score = 0
            inflation_score = 0
            
            # Employment mandate (target ~4%)
            if unemployment < 3.5:
                employment_score = 2  # Very strong, hawkish signal
                employment_signal = "🟢 Very Strong Employment (hawkish)"
            elif unemployment < 4.0:
                employment_score = 1  # Strong, mildly hawkish
                employment_signal = "🟢 Strong Employment (mildly hawkish)"
            elif unemployment < 5.0:
                employment_score = 0  # Neutral
                employment_signal = "🟡 Moderate Employment (neutral)"
            elif unemployment < 6.0:
                employment_score = -1  # Weak, dovish signal
                employment_signal = "🔴 Weak Employment (dovish)"
            else:
                employment_score = -2  # Very weak, very dovish
                employment_signal = "🔴 Very Weak Employment (very dovish)"
            
            # Price stability mandate (target 2%)
            if core_pce > 3.0:
                inflation_score = 2  # High inflation, hawkish signal
                inflation_signal = "🔴 High Inflation (hawkish)"
            elif core_pce > 2.5:
                inflation_score = 1  # Above target, mildly hawkish
                inflation_signal = "🟡 Above Target Inflation (mildly hawkish)"
            elif core_pce >= 1.5:
                inflation_score = 0  # Near target, neutral
                inflation_signal = "🟢 Near Target Inflation (neutral)"
            elif core_pce >= 1.0:
                inflation_score = -1  # Below target, dovish
                inflation_signal = "🔵 Below Target Inflation (dovish)"
            else:
                inflation_score = -2  # Very low, very dovish
                inflation_signal = "🔵 Very Low Inflation (very dovish)"
            
            # Yield curve analysis
            yield_spread = treasury_10y - treasury_2y
            if yield_spread < 0:
                curve_signal = "🔴 Inverted Yield Curve (recession risk)"
                curve_score = -1
            elif yield_spread < 0.5:
                curve_signal = "🟡 Flat Yield Curve (caution)"
                curve_score = 0
            else:
                curve_signal = "🟢 Normal Yield Curve (healthy)"
                curve_score = 1
            
            # Overall policy bias calculation
            total_score = employment_score + inflation_score + curve_score
            
            if total_score >= 2:
                policy_bias = "🔴 STRONGLY HAWKISH"
                bias_explanation = "Rate hikes likely"
            elif total_score >= 1:
                policy_bias = "🟡 HAWKISH"
                bias_explanation = "Rate hike pressure"
            elif total_score <= -2:
                policy_bias = "🔵 STRONGLY DOVISH"
                bias_explanation = "Rate cuts likely"
            elif total_score <= -1:
                policy_bias = "🟡 DOVISH"
                bias_explanation = "Rate cut pressure"
            else:
                policy_bias = "🟢 NEUTRAL"
                bias_explanation = "Hold rates steady"
            
            # Store analysis results
            analysis['policy_signals'] = {
                'employment': {
                    'signal': employment_signal,
                    'score': employment_score,
                    'value': unemployment
                },
                'inflation': {
                    'signal': inflation_signal,
                    'score': inflation_score,
                    'value': core_pce
                },
                'yield_curve': {
                    'signal': curve_signal,
                    'score': curve_score,
                    'spread': yield_spread
                },
                'overall_bias': {
                    'bias': policy_bias,
                    'explanation': bias_explanation,
                    'total_score': total_score
                }
            }
            
            print("\n📈 POLICY ASSESSMENT:")
            print(f"Employment Mandate: {employment_signal}")
            print(f"Price Stability: {inflation_signal}")
            print(f"Yield Curve: {curve_signal}")
            print("\n🎯 OVERALL BIAS: {policy_bias}")
            print(f"Implication: {bias_explanation}")
            
        except Exception as e:
            print(f"❌ Error in policy analysis: {str(e)}")
            analysis['error'] = str(e)
        
        return analysis

    def scrape_cme_fedwatch_data(self, event_date: str = None) -> Dict:
        """
        Scrape CME FedWatch data using the JSON endpoint
        
        Args:
            event_date: FOMC meeting date in YYYYMMDD format. If None, uses next meeting.
            
        Returns:
            Dictionary containing Fed rate probabilities
        """
        print("Scraping CME FedWatch data...")
        
        # Use next FOMC meeting if no date specified
        if not event_date:
            current_date = datetime.now().strftime('%Y%m%d')
            future_dates = [d for d in self.fomc_dates_2025 if d > current_date]
            event_date = future_dates[0] if future_dates else self.fomc_dates_2025[-1]
        
        url = "https://www.cmegroup.com/CmeWS/mvc/FedWatchTool/targetRateData"
        params = {
            'eventDate': event_date,
            'unit': '0'  # 0 for Fed Funds, 1 for SOFR
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract rate probabilities
                rate_probs = []
                if 'targetRateProbabilities' in data:
                    for item in data['targetRateProbabilities']:
                        rate_probs.append({
                            'target_rate': item.get('targetRate', ''),
                            'probability': float(item.get('probability', 0)),
                            'meeting_date': event_date
                        })
                
                # Calculate implied rate expectations
                weighted_rate = 0
                total_prob = 0
                
                for prob in rate_probs:
                    try:
                        # Parse rate ranges like "4.75-5.00"
                        rate_str = prob['target_rate']
                        if '-' in rate_str:
                            low, high = rate_str.split('-')
                            midpoint = (float(low) + float(high)) / 2
                        else:
                            midpoint = float(rate_str)
                        
                        weighted_rate += midpoint * prob['probability'] / 100
                        total_prob += prob['probability']
                        
                    except (ValueError, AttributeError):
                        continue
                
                return {
                    'meeting_date': event_date,
                    'rate_probabilities': rate_probs,
                    'implied_rate': weighted_rate,
                    'total_probability': total_prob,
                    'scrape_timestamp': datetime.now(),
                    'source': 'CME_FedWatch'
                }
                
            else:
                print(f"Error: HTTP {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"Error scraping CME data: {str(e)}")
            return {}

    def get_fred_economic_data(self) -> Dict:
        """
        Get key economic indicators from FRED
        """
        if not self.fred:
            print("FRED API not available")
            return {}
            
        print("Fetching FRED economic data...")
        
        # Key economic indicators
        indicators = {
            'effective_fed_funds': 'FEDFUNDS',
            'gdp_growth_rate': 'GDPC1',
            'unemployment_rate': 'UNRATE',
            'cpi_inflation': 'CPIAUCSL',
            'pce_inflation': 'PCEPI',
            'core_pce': 'PCEPILFE',
            '10y_treasury': 'GS10',
            '2y_treasury': 'GS2',
            '3m_treasury': 'GS3M',
            'real_gdp': 'GDPC1',
            'nonfarm_payrolls': 'PAYEMS',
            'consumer_sentiment': 'UMCSENT',
            'ism_manufacturing': 'ISRATIO',
            'housing_starts': 'HOUST',
            'retail_sales': 'RSAFS'
        }
        
        fred_data = {}
        
        for name, series_id in indicators.items():
            try:
                # Get most recent data (last 5 observations)
                series = self.fred.get_series(series_id, limit=5)
                if not series.empty:
                    latest_value = series.iloc[-1]
                    latest_date = series.index[-1]
                    
                    # Calculate month-over-month and year-over-year changes
                    mom_change = None
                    yoy_change = None
                    
                    if len(series) >= 2:
                        mom_change = ((latest_value / series.iloc[-2]) - 1) * 100
                    
                    if len(series) >= 12:
                        yoy_change = ((latest_value / series.iloc[-12]) - 1) * 100
                    
                    fred_data[name] = {
                        'value': latest_value,
                        'date': latest_date,
                        'mom_change': mom_change,
                        'yoy_change': yoy_change
                    }
                    
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                print(f"Error fetching {name}: {str(e)}")
                continue
        
        return {
            'indicators': fred_data,
            'scrape_timestamp': datetime.now(),
            'source': 'FRED'
        }

    def get_trading_economics_data(self) -> Dict:
        """
        Get economic forecasts from Trading Economics
        """
        if not TE_AVAILABLE:
            print("Trading Economics not available")
            return {}
            
        print("Fetching Trading Economics forecasts...")
        
        try:
            # Get economic calendar for next 30 days
            calendar = te.getCalendarData(
                country='United States',
                initDate=datetime.now().strftime('%Y-%m-%d'),
                endDate=(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            )
            
            # Get Fed rate forecasts if available
            forecasts = {}
            
            # Filter for important Fed-related events
            fed_events = ['Federal Funds Rate', 'FOMC', 'Interest Rate Decision']
            
            relevant_events = []
            for event in calendar:
                if any(fed_term in event.get('Event', '') for fed_term in fed_events):
                    relevant_events.append({
                        'event': event.get('Event'),
                        'date': event.get('Date'),
                        'actual': event.get('Actual'),
                        'forecast': event.get('Forecast'),
                        'previous': event.get('Previous'),
                        'importance': event.get('Importance')
                    })
            
            return {
                'fed_events': relevant_events,
                'full_calendar': calendar[:20],  # First 20 events
                'scrape_timestamp': datetime.now(),
                'source': 'TradingEconomics'
            }
            
        except Exception as e:
            print(f"Error fetching Trading Economics data: {str(e)}")
            return {}

    def scrape_all_fed_data(self) -> Dict:
        """
        Comprehensive Fed data collection from all sources
        """
        print("=" * 60)
        print("ENHANCED FED DATA SCRAPER")
        print("=" * 60)
        
        all_data = {
            'scrape_timestamp': datetime.now(),
            'sources': {}
        }
        
        # 1. CME FedWatch Data
        cme_data = self.scrape_cme_fedwatch_data()
        if cme_data:
            all_data['sources']['cme_fedwatch'] = cme_data
            print(f"✓ CME FedWatch: {len(cme_data.get('rate_probabilities', []))} rate probabilities")
        
        # 2. FRED Economic Data
        fred_data = self.get_fred_economic_data()
        if fred_data:
            all_data['sources']['fred'] = fred_data
            print(f"✓ FRED: {len(fred_data.get('indicators', {}))} economic indicators")
        
        # 3. Trading Economics Data
        te_data = self.get_trading_economics_data()
        if te_data:
            all_data['sources']['trading_economics'] = te_data
            print(f"✓ Trading Economics: {len(te_data.get('fed_events', []))} Fed events")
        
        return all_data

    def save_to_csv(self, data: Dict, base_filename: str = "enhanced_fed_data") -> str:
        """
        Save the scraped data to CSV files
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save CME FedWatch probabilities
        if 'cme_fedwatch' in data.get('sources', {}):
            cme_data = data['sources']['cme_fedwatch']
            if 'rate_probabilities' in cme_data:
                df_cme = pd.DataFrame(cme_data['rate_probabilities'])
                df_cme['implied_rate'] = cme_data.get('implied_rate', 0)
                df_cme['scrape_timestamp'] = cme_data.get('scrape_timestamp')
                
                cme_filename = f"cme_fedwatch_{timestamp}.csv"
                df_cme.to_csv(cme_filename, index=False)
                print(f"✓ CME data saved to {cme_filename}")
        
        # Save FRED indicators
        if 'fred' in data.get('sources', {}):
            fred_data = data['sources']['fred']
            if 'indicators' in fred_data:
                indicators_list = []
                for name, info in fred_data['indicators'].items():
                    indicators_list.append({
                        'indicator': name,
                        'value': info['value'],
                        'date': info['date'],
                        'mom_change': info.get('mom_change'),
                        'yoy_change': info.get('yoy_change')
                    })
                
                df_fred = pd.DataFrame(indicators_list)
                df_fred['scrape_timestamp'] = fred_data.get('scrape_timestamp')
                
                fred_filename = f"fred_indicators_{timestamp}.csv"
                df_fred.to_csv(fred_filename, index=False)
                print(f"✓ FRED data saved to {fred_filename}")
        
        # Save Trading Economics events
        if 'trading_economics' in data.get('sources', {}):
            te_data = data['sources']['trading_economics']
            if 'fed_events' in te_data and te_data['fed_events']:
                df_te = pd.DataFrame(te_data['fed_events'])
                df_te['scrape_timestamp'] = te_data.get('scrape_timestamp')
                
                te_filename = f"trading_economics_events_{timestamp}.csv"
                df_te.to_csv(te_filename, index=False)
                print(f"✓ Trading Economics data saved to {te_filename}")
        
        # Save summary
        summary_filename = f"{base_filename}_{timestamp}.csv"
        summary_data = [{
            'scrape_timestamp': data['scrape_timestamp'],
            'cme_available': 'cme_fedwatch' in data.get('sources', {}),
            'fred_available': 'fred' in data.get('sources', {}),
            'te_available': 'trading_economics' in data.get('sources', {}),
            'total_sources': len(data.get('sources', {}))
        }]
        
        pd.DataFrame(summary_data).to_csv(summary_filename, index=False)
        print(f"✓ Summary saved to {summary_filename}")
        
        return summary_filename

    def analyze_fed_outlook(self, data: Dict) -> Dict:
        """
        Analyze the Fed outlook based on all collected data
        """
        analysis = {
            'current_assessment': '',
            'rate_direction': '',
            'probability_next_meeting': {},
            'economic_signals': [],
            'confidence_level': 'Unknown'
        }
        
        # Analyze CME data
        if 'cme_fedwatch' in data.get('sources', {}):
            cme_data = data['sources']['cme_fedwatch']
            implied_rate = cme_data.get('implied_rate', 0)
            
            if implied_rate > 0:
                analysis['implied_fed_funds_rate'] = implied_rate
                
                # Find highest probability rate
                probs = cme_data.get('rate_probabilities', [])
                if probs:
                    max_prob = max(probs, key=lambda x: x['probability'])
                    analysis['most_likely_rate'] = max_prob['target_rate']
                    analysis['probability_next_meeting'] = {
                        'rate': max_prob['target_rate'], 
                        'probability': max_prob['probability']
                    }
        
        # Analyze FRED data for economic signals
        if 'fred' in data.get('sources', {}):
            indicators = data['sources']['fred'].get('indicators', {})
            
            # Check inflation trends
            if 'core_pce' in indicators:
                pce = indicators['core_pce']['value']
                if pce > 2.5:
                    analysis['economic_signals'].append("Core PCE above Fed target")
                elif pce < 2.0:
                    analysis['economic_signals'].append("Core PCE below Fed target")
            
            # Check unemployment
            if 'unemployment_rate' in indicators:
                unemployment = indicators['unemployment_rate']['value']
                if unemployment > 5.0:
                    analysis['economic_signals'].append("Elevated unemployment")
                elif unemployment < 3.5:
                    analysis['economic_signals'].append("Very low unemployment")
        
        return analysis


def main():
    """
    Main function to run the enhanced Fed scraper
    """
    # Initialize scraper (add your API keys here)
    # Get FRED API key from: https://fred.stlouisfed.org/docs/api/api_key.html
    fred_key = None  # Add your FRED API key here
    te_key = None    # Add your Trading Economics API key here (optional)
    
    scraper = EnhancedFedDataScraper(fred_api_key=fred_key, te_api_key=te_key)
    
    # Scrape all data
    data = scraper.scrape_all_fed_data()
    
    # Save to CSV
    filename = scraper.save_to_csv(data)
    
    # Analyze Fed outlook
    analysis = scraper.analyze_fed_outlook(data)
    
    print("\n" + "=" * 60)
    print("FED OUTLOOK ANALYSIS")
    print("=" * 60)
    
    if analysis.get('implied_fed_funds_rate'):
        print(f"Implied Fed Funds Rate: {analysis['implied_fed_funds_rate']:.2f}%")
    
    if analysis.get('most_likely_rate'):
        print(f"Most Likely Rate: {analysis['most_likely_rate']}")
    
    if analysis.get('probability_next_meeting'):
        prob_info = analysis['probability_next_meeting']
        print(f"Next Meeting: {prob_info.get('rate')} ({prob_info.get('probability'):.1f}% probability)")
    
    if analysis.get('economic_signals'):
        print(f"Economic Signals: {', '.join(analysis['economic_signals'])}")
    
    return data, analysis


if __name__ == "__main__":
    main() 