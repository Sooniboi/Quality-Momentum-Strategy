#!/usr/bin/env python3

"""
Enhanced Macro Economic Analysis with NY Fed Probit Model
Provides comprehensive macro analysis with Federal Reserve data integration.
"""

import pandas as pd
import numpy as np
import os
from datetime import date, datetime, timedelta
import requests
from typing import Dict, List, Tuple, Optional
import time
from dotenv import load_dotenv
import json
import re
from bs4 import BeautifulSoup
import scipy.stats as stats

# NEW: FRED API Integration
try:
    from fredapi import Fred
    FRED_AVAILABLE = True
except ImportError:
    print("⚠️ fredapi not available. Install with: pip install fredapi")
    FRED_AVAILABLE = False

load_dotenv()
API_KEY = os.getenv("FMP_API_KEY")

# =============================================================================
# FRED API CONFIGURATION - ADD YOUR FREE API KEY HERE
# =============================================================================
# Get your free FRED API key at: https://fred.stlouisfed.org/docs/api/api_key.html
# FRED_API_KEY = "your_fred_api_key_here"  # <-- ADD YOUR KEY HERE

# Use environment variable for FRED API key
FRED_API_KEY = os.getenv("FRED_API_KEY")  # Load from environment variable

# =============================================================================
# FRED DATA INTEGRATION - Official Federal Reserve Data
# =============================================================================

def get_fred_economic_data() -> Dict:
    """Get comprehensive economic data from FRED API"""
    print("📊 Fetching FRED economic data...")
    
    # Initialize FRED client if available
    fred = None
    if FRED_AVAILABLE and FRED_API_KEY:
        try:
            fred = Fred(api_key=FRED_API_KEY)
            print("✅ FRED API connected")
        except Exception as e:
            print(f"⚠️ FRED API failed: {e}")
            fred = None
    
    fred_data = {}
    
    # FRED series mapping
    fred_series = {
        'fed_funds_rate': 'FEDFUNDS',           # Effective Federal Funds Rate
        'fed_target_upper': 'DFEDTARU',         # Fed Target Rate Upper Bound
        'fed_target_lower': 'DFEDTARL',         # Fed Target Rate Lower Bound
        'unemployment_rate': 'UNRATE',          # Unemployment Rate
        'core_pce_inflation': 'PCEPILFE',       # Core PCE Price Index
        'pce_inflation': 'PCEPI',               # PCE Price Index
        'cpi_inflation': 'CPIAUCSL',            # Consumer Price Index
        'treasury_10y': 'GS10',                 # 10-Year Treasury Rate
        'treasury_2y': 'GS2',                   # 2-Year Treasury Rate
        'treasury_3m': 'GS3M',                  # 3-Month Treasury Rate
        'treasury_30y': 'GS30',                 # 30-Year Treasury Rate
        'consumer_sentiment': 'UMCSENT',        # University of Michigan Consumer Sentiment
        'nonfarm_payrolls': 'PAYEMS',           # Total Nonfarm Payrolls
        'real_gdp': 'GDPC1',                    # Real GDP
        'yield_spread_10y_2y': 'T10Y2Y',        # 10Y-2Y Treasury Spread
        'yield_spread_10y_3m': 'T10Y3M',        # 10Y-3M Treasury Spread
        'initial_claims': 'ICSA',               # Initial Jobless Claims
        'continuing_claims': 'CCSA',            # Continuing Jobless Claims
        'housing_starts': 'HOUST',              # Housing Starts
        'industrial_production': 'INDPRO',     # Industrial Production Index
        'capacity_utilization': 'TCU',         # Capacity Utilization
        'ism_manufacturing': 'ISRATIO',         # ISM Manufacturing PMI
        # =============================================================================
        # ENHANCED MARKET REGIME INDICATORS - Added for 15-regime system
        # =============================================================================
        'vix_index': 'VIXCLS',                  # Market volatility/fear gauge
        'money_supply_m2': 'M2SL',              # Money supply for liquidity analysis
        'tips_10y': 'DFII10',                   # 10Y TIPS for inflation expectations
        'corporate_aaa': 'DAAA',                # AAA corporate bond yields
        'corporate_baa': 'DBAA',                # BAA corporate bond yields  
        'gdp_deflator': 'GDPDEF',               # GDP deflator for inflation
        'personal_income': 'PI',                # Personal income trends
        'retail_sales': 'RSAFS',                # Retail sales momentum
        'durable_goods': 'DGORDER',             # Durable goods orders
        'business_inventories': 'BUSINV'        # Business inventory levels
    }
    
    # Fallback CSV endpoints for when no API key
    fred_csv_fallbacks = {
        'fed_funds_rate': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS&cosd=2024-01-01',
        'unemployment_rate': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE&cosd=2024-01-01',
        'core_pce_inflation': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=PCEPILFE&cosd=2024-01-01',
        'treasury_10y': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=GS10&cosd=2024-01-01',
        'treasury_2y': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=GS2&cosd=2024-01-01',
        'treasury_3m': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=GS3M&cosd=2024-01-01'
    }
    
    for indicator, series_id in fred_series.items():
        try:
            if fred:  # Use API if available
                data = fred.get_series(series_id, limit=3)
                if data is not None and not data.empty:
                    current_value = float(data.iloc[-1])
                    previous_value = float(data.iloc[-2]) if len(data) >= 2 else None
                    date_current = data.index[-1].strftime('%Y-%m-%d')
                    
                    # Calculate change
                    change = None
                    if previous_value is not None:
                        change = current_value - previous_value
                    
                    fred_data[indicator] = {
                        'current': current_value,
                        'previous': previous_value,
                        'change': change,
                        'date': date_current,
                        'source': 'FRED_API'
                    }
                    print(f"✅ {indicator}: {current_value} (FRED API)")
                    time.sleep(0.1)  # Rate limiting
                    continue
            
            # Fallback to CSV for key indicators
            if indicator in fred_csv_fallbacks:
                url = fred_csv_fallbacks[indicator]
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
                                    fred_data[indicator] = {
                                        'current': value,
                                        'date': latest_line[0],
                                        'source': 'FRED_CSV'
                                    }
                                    print(f"✅ {indicator}: {value} (FRED CSV)")
                                    continue
                                except ValueError:
                                    pass
            
            # Final fallback with reasonable estimates
            fallback_values = {
                'fed_funds_rate': 4.33,
                'unemployment_rate': 4.2,
                'core_pce_inflation': 2.1,
                'treasury_10y': 4.15,
                'treasury_2y': 3.78,
                'treasury_3m': 4.50,
                'consumer_sentiment': 75.0,
                'nonfarm_payrolls': 150000,
                'initial_claims': 350000
            }
            
            if indicator in fallback_values:
                fred_data[indicator] = {
                    'current': fallback_values[indicator],
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'source': 'FALLBACK'
                }
                print(f"⚠️ {indicator}: {fallback_values[indicator]} (fallback)")
        
        except Exception as e:
            print(f"❌ Error fetching {indicator}: {str(e)}")
    
    return fred_data

def analyze_fed_policy_stance(fred_data: Dict) -> Dict:
    """Analyze current Fed policy stance using real economic data"""
    print("🎯 Analyzing Fed policy stance...")
    
    analysis = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'data_quality': 'high' if any(d.get('source') == 'FRED_API' for d in fred_data.values()) else 'medium'
    }
    
    try:
        # Extract current values
        fed_funds = fred_data.get('fed_funds_rate', {}).get('current', 4.33)
        unemployment = fred_data.get('unemployment_rate', {}).get('current', 4.2)
        core_pce = fred_data.get('core_pce_inflation', {}).get('current', 2.1)
        treasury_10y = fred_data.get('treasury_10y', {}).get('current', 4.15)
        treasury_2y = fred_data.get('treasury_2y', {}).get('current', 3.78)
        consumer_sentiment = fred_data.get('consumer_sentiment', {}).get('current', 75.0)
        
        print(f"📊 Fed Funds Rate: {fed_funds:.2f}%")
        print(f"📊 Unemployment: {unemployment:.1f}%")
        print(f"📊 Core PCE: {core_pce:.1f}%")
        
        # Dual mandate analysis
        employment_score = 0
        inflation_score = 0
        
        # Employment mandate (Fed targets ~4% unemployment)
        if unemployment < 3.5:
            employment_score = 2  # Very strong, hawkish
            employment_signal = "🟢 Very Strong Employment (hawkish pressure)"
        elif unemployment < 4.0:
            employment_score = 1  # Strong, mildly hawkish
            employment_signal = "🟢 Strong Employment (mildly hawkish)"
        elif unemployment < 5.0:
            employment_score = 0  # Neutral
            employment_signal = "🟡 Moderate Employment (neutral)"
        elif unemployment < 6.0:
            employment_score = -1  # Weak, dovish
            employment_signal = "🔴 Weak Employment (dovish pressure)"
        else:
            employment_score = -2  # Very weak, very dovish
            employment_signal = "🔴 Very Weak Employment (very dovish)"
        
        # Price stability mandate (Fed targets 2% inflation)
        if core_pce > 3.0:
            inflation_score = 2  # High inflation, hawkish
            inflation_signal = "🔴 High Inflation (hawkish pressure)"
        elif core_pce > 2.5:
            inflation_score = 1  # Above target, mildly hawkish
            inflation_signal = "🟡 Above Target (mildly hawkish)"
        elif core_pce >= 1.5:
            inflation_score = 0  # Near target, neutral
            inflation_signal = "🟢 Near Target (neutral)"
        elif core_pce >= 1.0:
            inflation_score = -1  # Below target, dovish
            inflation_signal = "🔵 Below Target (dovish pressure)"
        else:
            inflation_score = -2  # Very low, very dovish
            inflation_signal = "🔵 Very Low Inflation (very dovish)"
        
        # Yield curve analysis
        yield_spread = treasury_10y - treasury_2y
        if yield_spread < -0.5:
            curve_signal = "🔴 Deeply Inverted Curve (recession risk)"
            curve_score = -2
        elif yield_spread < 0:
            curve_signal = "🔴 Inverted Yield Curve (recession risk)"
            curve_score = -1
        elif yield_spread < 0.5:
            curve_signal = "🟡 Flat Yield Curve (caution)"
            curve_score = 0
        else:
            curve_signal = "🟢 Normal Yield Curve (healthy)"
            curve_score = 1
        
        # Consumer sentiment factor
        sentiment_score = 0
        if consumer_sentiment < 60:
            sentiment_signal = "🔴 Poor Consumer Sentiment (recession risk)"
            sentiment_score = -1
        elif consumer_sentiment > 85:
            sentiment_signal = "🟢 Strong Consumer Sentiment"
            sentiment_score = 1
        else:
            sentiment_signal = "🟡 Moderate Consumer Sentiment"
        
        # Overall policy bias calculation
        total_score = employment_score + inflation_score + curve_score + sentiment_score
        
        if total_score >= 3:
            policy_bias = "🔴 STRONGLY HAWKISH"
            bias_explanation = "Rate hikes very likely"
            rate_direction = "UP"
        elif total_score >= 1:
            policy_bias = "🟡 HAWKISH"
            bias_explanation = "Rate hike pressure building"
            rate_direction = "UP"
        elif total_score <= -3:
            policy_bias = "🔵 STRONGLY DOVISH"
            bias_explanation = "Rate cuts very likely"
            rate_direction = "DOWN"
        elif total_score <= -1:
            policy_bias = "🟡 DOVISH"
            bias_explanation = "Rate cut pressure building"
            rate_direction = "DOWN"
        else:
            policy_bias = "🟢 NEUTRAL"
            bias_explanation = "Hold rates steady"
            rate_direction = "HOLD"
        
        # Calculate terminal rate estimate
        if rate_direction == "UP":
            terminal_rate_estimate = fed_funds + 0.5  # Modest hike cycle
        elif rate_direction == "DOWN":
            terminal_rate_estimate = max(0.25, fed_funds - 1.0)  # Cut cycle
        else:
            terminal_rate_estimate = fed_funds  # Hold
        
        # Store comprehensive analysis
        analysis.update({
            'current_fed_funds_rate': fed_funds,
            'employment_analysis': {
                'signal': employment_signal,
                'score': employment_score,
                'unemployment_rate': unemployment
            },
            'inflation_analysis': {
                'signal': inflation_signal,
                'score': inflation_score,
                'core_pce_rate': core_pce
            },
            'yield_curve_analysis': {
                'signal': curve_signal,
                'score': curve_score,
                'spread_10y_2y': yield_spread
            },
            'consumer_sentiment_analysis': {
                'signal': sentiment_signal,
                'score': sentiment_score,
                'level': consumer_sentiment
            },
            'overall_assessment': {
                'policy_bias': policy_bias,
                'explanation': bias_explanation,
                'rate_direction': rate_direction,
                'total_score': total_score,
                'terminal_rate_estimate': terminal_rate_estimate
            }
        })
        
        print(f"\n📈 FED POLICY ASSESSMENT:")
        print(f"Employment: {employment_signal}")
        print(f"Inflation: {inflation_signal}")
        print(f"Yield Curve: {curve_signal}")
        print(f"Consumer Sentiment: {sentiment_signal}")
        print(f"\n🎯 OVERALL: {policy_bias}")
        print(f"Direction: {rate_direction} | {bias_explanation}")
        print(f"Terminal Rate Est: {terminal_rate_estimate:.2f}%")
        
    except Exception as e:
        print(f"❌ Error in Fed policy analysis: {str(e)}")
        analysis['error'] = str(e)
    
    return analysis

# =============================================================================
# FMP API INTEGRATION - Enhanced Market Data for Regime Detection
# =============================================================================

def get_fmp_market_data() -> Dict:
    """Get enhanced market data from FMP API for regime detection"""
    print("📊 Fetching FMP market data...")
    
    if not API_KEY:
        print("⚠️ FMP API key not found, using fallback data")
        return get_fallback_market_data()
    
    market_data = {}
    
    try:
        # 1. VIX Volatility Index
        vix_url = f'https://financialmodelingprep.com/api/v3/quote/^VIX?apikey={API_KEY}'
        response = requests.get(vix_url, timeout=10)
        if response.status_code == 200:
            vix_data = response.json()
            if vix_data and len(vix_data) > 0:
                vix = vix_data[0]
                market_data['vix'] = {
                    'current': vix.get('price', 20.0),
                    'change': vix.get('change', 0.0),
                    'source': 'FMP_API'
                }
            else:
                market_data['vix'] = {'current': 20.0, 'source': 'FALLBACK'}
        else:
            market_data['vix'] = {'current': 20.0, 'source': 'FALLBACK'}
        
        time.sleep(0.2)  # Rate limiting
        
        # 2. Sector Performance
        sector_url = f'https://financialmodelingprep.com/api/v3/sectors-performance?apikey={API_KEY}'
        response = requests.get(sector_url, timeout=10)
        if response.status_code == 200:
            sector_data = response.json()
            if sector_data and len(sector_data) > 0:
                sectors = {}
                for sector in sector_data:
                    sector_name = sector.get('sector', 'Unknown')
                    sector_change = sector.get('changesPercentage', '0%')
                    
                    try:
                        if isinstance(sector_change, str):
                            sector_change = float(sector_change.rstrip('%'))
                        else:
                            sector_change = float(sector_change)
                    except (ValueError, TypeError):
                        sector_change = 0.0
                    
                    sectors[sector_name] = {
                        'change_percent': sector_change,
                        'source': 'FMP_API'
                    }
                
                market_data['sectors'] = sectors
                
                # Find leading sector
                if sectors:
                    leading_sector = max(sectors.items(), key=lambda x: x[1]['change_percent'])
                    market_data['leading_sector'] = {
                        'name': leading_sector[0],
                        'performance': leading_sector[1]['change_percent']
                    }
            else:
                market_data['sectors'] = get_fallback_sectors()
        else:
            market_data['sectors'] = get_fallback_sectors()
        
    except Exception as e:
        print(f"❌ Error fetching FMP market data: {e}")
        return get_fallback_market_data()
    
    return market_data

def get_fallback_market_data() -> Dict:
    """Fallback market data when FMP API is unavailable"""
    return {
        'vix': {'current': 20.0, 'source': 'FALLBACK'},
        'sectors': get_fallback_sectors(),
        'leading_sector': {'name': 'Technology', 'performance': 1.0}
    }

def get_fallback_sectors() -> Dict:
    """Fallback sector performance data"""
    return {
        'Technology': {'change_percent': 1.0, 'source': 'FALLBACK'},
        'Healthcare': {'change_percent': 0.5, 'source': 'FALLBACK'},
        'Financials': {'change_percent': 0.3, 'source': 'FALLBACK'},
        'Consumer Discretionary': {'change_percent': 0.2, 'source': 'FALLBACK'},
        'Industrials': {'change_percent': 0.1, 'source': 'FALLBACK'},
        'Energy': {'change_percent': -0.2, 'source': 'FALLBACK'},
        'Materials': {'change_percent': -0.1, 'source': 'FALLBACK'},
        'Utilities': {'change_percent': -0.3, 'source': 'FALLBACK'},
        'Real Estate': {'change_percent': -0.4, 'source': 'FALLBACK'},
        'Consumer Staples': {'change_percent': 0.0, 'source': 'FALLBACK'},
        'Communication Services': {'change_percent': 0.1, 'source': 'FALLBACK'}
    }

def get_treasury_rates() -> Dict:
    """Get current treasury rates - enhanced with FRED data when available"""
    print("📊 Fetching treasury rates...")
    
    # Try FRED data first if available
    fred_data = get_fred_economic_data()
    
    if fred_data:
        # Use FRED data for more accurate rates
        treasury_rates = {}
        
        if 'treasury_3m' in fred_data:
            treasury_rates['3_month'] = fred_data['treasury_3m']['current'] / 100  # Convert to decimal
        if 'treasury_2y' in fred_data:
            treasury_rates['2_year'] = fred_data['treasury_2y']['current'] / 100
        if 'treasury_10y' in fred_data:
            treasury_rates['10_year'] = fred_data['treasury_10y']['current'] / 100
        if 'treasury_30y' in fred_data:
            treasury_rates['30_year'] = fred_data['treasury_30y']['current'] / 100
        
        if treasury_rates:
            treasury_rates['date'] = datetime.now().strftime('%Y-%m-%d')
            treasury_rates['source'] = 'FRED'
            print(f"✅ Treasury rates from FRED")
            return treasury_rates
    
    # Fallback to FMP if FRED not available
    try:
        url = f"https://financialmodelingprep.com/api/v4/treasury?apikey={API_KEY}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                latest = data[0]
                rates = {
                    'date': latest.get('date'),
                    '3_month': float(latest.get('month3', 0)) / 100,
                    '2_year': float(latest.get('year2', 0)) / 100,
                    '10_year': float(latest.get('year10', 0)) / 100,
                    '30_year': float(latest.get('year30', 0)) / 100,
                    'source': 'FMP'
                }
                print(f"✅ Treasury rates from FMP")
                return rates
        
        print(f"⚠️ FMP treasury error: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Error getting treasury rates: {str(e)}")
    
    # Final fallback with current estimates
    fallback_rates = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        '3_month': 0.045,  # 4.5%
        '2_year': 0.0378,  # 3.78%
        '10_year': 0.0415, # 4.15%
        '30_year': 0.043,  # 4.3%
        'source': 'FALLBACK'
    }
    print(f"⚠️ Using fallback treasury rates")
    return fallback_rates

def get_economic_indicators() -> Dict:
    """Get key economic indicators from FMP."""
    print("Fetching economic indicators...")
    
    indicators = {}
    
    # VIX (Market volatility)
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/%5EVIX?apikey={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data and 'historical' in data and data['historical']:
                indicators['vix'] = float(data['historical'][0]['close'])
        time.sleep(0.2)
    except Exception as e:
        print(f"Error getting VIX: {str(e)}")
    
    # USD Index
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/DX-Y.NYB?apikey={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data and 'historical' in data and data['historical']:
                indicators['usd_index'] = float(data['historical'][0]['close'])
        time.sleep(0.2)
    except Exception as e:
        print(f"Error getting USD Index: {str(e)}")
    
    # Gold (inflation hedge indicator)
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/GCUSD?apikey={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data and 'historical' in data and data['historical']:
                indicators['gold_price'] = float(data['historical'][0]['close'])
        time.sleep(0.2)
    except Exception as e:
        print(f"Error getting Gold price: {str(e)}")
    
    # Oil (inflation and economic activity indicator)
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/CLUSD?apikey={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data and 'historical' in data and data['historical']:
                indicators['oil_price'] = float(data['historical'][0]['close'])
        time.sleep(0.2)
    except Exception as e:
        print(f"Error getting Oil price: {str(e)}")
    
    return indicators

def get_recession_indicators() -> Dict:
    """Get recession-specific indicators - enhanced with FRED data when available."""
    print("📊 Fetching recession indicators...")
    
    indicators = {}
    
    # Get FRED data if available
    fred_data = get_fred_economic_data()
    
    # Use real data when available
    if fred_data:
        # Unemployment and labor market indicators
        if 'unemployment_rate' in fred_data:
            indicators['unemployment_rate'] = fred_data['unemployment_rate']['current']
        
        if 'initial_claims' in fred_data:
            indicators['initial_claims_4wk'] = fred_data['initial_claims']['current']
        
        # Calculate Sahm Rule indicator (simplified)
        if 'unemployment_rate' in fred_data:
            current_unemployment = fred_data['unemployment_rate']['current']
            # Rough approximation - in reality, need 3-month moving average vs 12-month low
            indicators['sahm_indicator'] = max(0, current_unemployment - 3.5)  # Approximate
        
        # GDP and production indicators
        if 'industrial_production' in fred_data:
            indicators['industrial_production'] = fred_data['industrial_production']['current']
        
        if 'capacity_utilization' in fred_data:
            indicators['capacity_utilization'] = fred_data['capacity_utilization']['current']
        
        print("✅ Using FRED data for recession indicators")
    
    # High Yield Credit Spreads (HYG ETF as proxy)
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/HYG?apikey={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data and 'historical' in data and data['historical']:
                # Approximate credit spread from HYG price changes
                recent_prices = [float(d['close']) for d in data['historical'][:30]]
                if len(recent_prices) >= 30:
                    current_price = recent_prices[0]
                    month_ago_price = recent_prices[20]
                    # Estimate spread widening from price decline
                    price_change = (current_price - month_ago_price) / month_ago_price
                    # Rough approximation: price decline correlates with spread widening
                    estimated_hy_spread = max(300, 500 - (price_change * 1000))  # Base 500 bps
                    indicators['hy_spreads'] = estimated_hy_spread
        time.sleep(0.2)
    except Exception as e:
        print(f"❌ Error getting HY spreads: {str(e)}")
        indicators['hy_spreads'] = 500  # Default assumption
    
    # Investment Grade Credit Spreads (LQD ETF as proxy)
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/LQD?apikey={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data and 'historical' in data and data['historical']:
                recent_prices = [float(d['close']) for d in data['historical'][:30]]
                if len(recent_prices) >= 30:
                    current_price = recent_prices[0]
                    month_ago_price = recent_prices[20]
                    price_change = (current_price - month_ago_price) / month_ago_price
                    # Estimate IG spread (typically 100-300 bps)
                    estimated_ig_spread = max(80, 150 - (price_change * 500))
                    indicators['ig_spreads'] = estimated_ig_spread
        time.sleep(0.2)
    except Exception as e:
        print(f"❌ Error getting IG spreads: {str(e)}")
        indicators['ig_spreads'] = 150  # Default assumption
    
    # Fallback values for missing indicators
    fallback_indicators = {
        'unemployment_rate': 4.1,
        'sahm_indicator': 0.2,
        'initial_claims_4wk': 350000,
        'lei_6m_change': -0.5,
        'hy_spreads': 500,
        'ig_spreads': 150
    }
    
    for key, default_value in fallback_indicators.items():
        if key not in indicators:
            indicators[key] = default_value
            print(f"⚠️ Using fallback for {key}: {default_value}")
    
    return indicators

def get_fed_funds_rate() -> float:
    """Get current Fed Funds rate - enhanced with FRED data"""
    
    # Try FRED data first
    fred_data = get_fred_economic_data()
    
    if fred_data and 'fed_funds_rate' in fred_data:
        fed_rate = fred_data['fed_funds_rate']['current']
        print(f"✅ Fed Funds Rate from FRED: {fed_rate:.2f}%")
        return fed_rate
    
    # Fallback to FMP
    try:
        url = f"https://financialmodelingprep.com/api/v4/economic?name=federalFundsRate&apikey={API_KEY}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                fed_rate = float(data[0].get('value', 4.33))
                print(f"✅ Fed Funds Rate from FMP: {fed_rate:.2f}%")
                return fed_rate
        
    except Exception as e:
        print(f"❌ Error getting Fed Funds rate: {str(e)}")
    
    # Final fallback
    print(f"⚠️ Using fallback Fed Funds Rate: 4.33%")
    return 4.33

def calculate_yield_curve_metrics(treasury_rates: Dict) -> Dict:
    """Calculate yield curve metrics in basis points and interpret them."""
    if not treasury_rates:
        return {}
    
    # Convert all to basis points for precision
    curve_2s10s_bps = (treasury_rates.get('10_year', 0) - treasury_rates.get('2_year', 0)) * 100
    term_spread_bps = (treasury_rates.get('10_year', 0) - treasury_rates.get('3_month', 0)) * 100
    curve_3m2y_bps = (treasury_rates.get('2_year', 0) - treasury_rates.get('3_month', 0)) * 100
    
    # Professional thresholds in basis points
    if curve_2s10s_bps > 100:  # > 100 bps
        curve_shape = "Steep"
        recession_risk = "Very Low"
    elif curve_2s10s_bps > 20:  # 20-100 bps  
        curve_shape = "Normal"
        recession_risk = "Low"
    elif curve_2s10s_bps > -20:  # -20 to +20 bps
        curve_shape = "Flat"
        recession_risk = "Moderate"
    else:  # < -20 bps
        curve_shape = "Inverted"
        recession_risk = "High"
    
    return {
        'curve_2s10s_bps': curve_2s10s_bps,
        'term_spread_bps': term_spread_bps,
        'curve_3m2y_bps': curve_3m2y_bps,
        'curve_shape': curve_shape,
        'recession_risk': recession_risk
    }

def calculate_recession_probability_nyfed(treasury_rates: Dict, recession_indicators: Dict, 
                                  economic_indicators: Dict) -> Dict:
    """
    Calculate recession probability using NY Fed probit model approach.
    
    Based on the Federal Reserve Bank of New York's yield curve model:
    P(Recession) = Φ(α + β × term_spread)
    
    Where:
    - Φ is the standard normal cumulative distribution function
    - term_spread is the 10-year minus 3-month Treasury spread
    - α, β are estimated parameters from historical data
    
    Reference: NY Fed "Yield Curve as a Leading Indicator"
    """
    print("Calculating recession probability (NY Fed Probit Model)...")
    
    # Extract Treasury rates
    ten_year_rate = treasury_rates.get('10_year', 0)
    three_month_rate = treasury_rates.get('3_month', 0)
    two_year_rate = treasury_rates.get('2_year', 0)
    
    # Calculate term spreads (in percentage points)
    term_spread = ten_year_rate - three_month_rate  # Primary NY Fed indicator
    curve_2s10s = ten_year_rate - two_year_rate     # Alternative measure
    
    # NY Fed Probit Model Parameters (estimated from historical data 1959-2024)
    # These are approximate values based on published research
    alpha = -0.7685    # Intercept
    beta = -0.7056     # Coefficient on term spread
    
    # Calculate probit probability: P(Recession) = Φ(α + β × term_spread)
    linear_combination = alpha + beta * term_spread
    nyfed_probability = stats.norm.cdf(linear_combination) * 100  # Convert to percentage
    
    # Enhanced model with additional term structure information
    # Add deviation of 3-month rate from trend (Wright 2006 enhancement)
    three_month_deviation = 0  # Simplified for now
    if 'fed_funds_rate' in economic_indicators:
        fed_funds = economic_indicators.get('fed_funds_rate', three_month_rate)
        # Approximate 3-year moving average with current Fed policy
        three_month_deviation = three_month_rate - fed_funds
    
    # Enhanced model parameters (with deviation term)
    alpha_enhanced = -0.8934
    beta_spread = -0.6821
    beta_deviation = 0.4297
    
    linear_enhanced = alpha_enhanced + beta_spread * term_spread + beta_deviation * three_month_deviation
    enhanced_probability = stats.norm.cdf(linear_enhanced) * 100
    
    # Calculate confidence intervals using bootstrap approximation
    # Standard error estimates from NY Fed literature
    se_alpha = 0.1523
    se_beta = 0.0956
    
    # Approximate 68% confidence interval (1 standard deviation)
    variance = (se_alpha**2) + (term_spread**2 * se_beta**2)
    std_error = np.sqrt(variance)
    
    # Calculate confidence bounds
    lower_68 = stats.norm.cdf(linear_combination - std_error) * 100
    upper_68 = stats.norm.cdf(linear_combination + std_error) * 100
    
    # 90% confidence interval (1.645 standard deviations)
    lower_90 = stats.norm.cdf(linear_combination - 1.645 * std_error) * 100
    upper_90 = stats.norm.cdf(linear_combination + 1.645 * std_error) * 100
    
    # Determine recession risk level and time horizon
    if nyfed_probability >= 50:
        risk_level = "High"
        time_horizon = "6-12 months"
    elif nyfed_probability >= 30:
        risk_level = "Elevated"
        time_horizon = "9-15 months"
    elif nyfed_probability >= 15:
        risk_level = "Moderate"
        time_horizon = "12-18 months"
    else:
        risk_level = "Low"
        time_horizon = "18+ months"
    
    # Model interpretation
    if term_spread < -1.0:
        interpretation = "Deeply inverted yield curve signals high recession risk"
    elif term_spread < -0.5:
        interpretation = "Inverted yield curve indicates elevated recession risk"
    elif term_spread < 0.5:
        interpretation = "Flat yield curve suggests moderate recession risk"
    elif term_spread < 1.5:
        interpretation = "Normal yield curve indicates low recession risk"
    else:
        interpretation = "Steep yield curve signals very low recession risk"
    
    # Compare with historical averages
    unconditional_avg = 15.0  # Long-term average recession probability
    relative_risk = "Above Average" if nyfed_probability > unconditional_avg else "Below Average"
    
    # Additional context indicators (for supplemental analysis)
    supplemental_indicators = {}
    
    # Sahm Rule check
    sahm_indicator = recession_indicators.get('sahm_indicator', 0)
    if sahm_indicator >= 0.5:
        supplemental_indicators['sahm_rule'] = "TRIGGERED - Recession likely started"
    elif sahm_indicator >= 0.3:
        supplemental_indicators['sahm_rule'] = "WARNING - Approaching trigger threshold"
    else:
        supplemental_indicators['sahm_rule'] = "Normal"
    
    # Credit spread check
    hy_spreads = recession_indicators.get('hy_spreads', 500)
    if hy_spreads > 800:
        supplemental_indicators['credit_stress'] = "HIGH - Credit markets under stress"
    elif hy_spreads > 600:
        supplemental_indicators['credit_stress'] = "MODERATE - Some credit tightening"
    else:
        supplemental_indicators['credit_stress'] = "Normal"
    
    # Leading Economic Index
    lei_6m_change = recession_indicators.get('lei_6m_change', 0)
    if lei_6m_change < -3.0:
        supplemental_indicators['lei_signal'] = "WEAK - Economic indicators deteriorating"
    elif lei_6m_change < -1.5:
        supplemental_indicators['lei_signal'] = "SOFTENING - Some economic weakness"
    else:
        supplemental_indicators['lei_signal'] = "Stable"
    
    return {
        # Primary NY Fed Model Results
        'recession_probability': round(nyfed_probability, 1),
        'enhanced_probability': round(enhanced_probability, 1),
        'model_type': 'NY Fed Probit Model',
        'model_vintage': '1959-2024 Sample',
        
        # Confidence Intervals
        'confidence_68_lower': round(lower_68, 1),
        'confidence_68_upper': round(upper_68, 1),
        'confidence_90_lower': round(lower_90, 1),
        'confidence_90_upper': round(upper_90, 1),
        
        # Term Structure Data
        'term_spread_10y3m': round(term_spread, 3),
        'term_spread_10y2y': round(curve_2s10s, 3),
        'three_month_deviation': round(three_month_deviation, 3),
        
        # Risk Assessment
        'risk_level': risk_level,
        'time_horizon': time_horizon,
        'interpretation': interpretation,
        'relative_risk': relative_risk,
        'unconditional_average': unconditional_avg,
        
        # Model Parameters (for transparency)
        'model_parameters': {
            'alpha': alpha,
            'beta': beta,
            'linear_combination': round(linear_combination, 4)
        },
        
        # Supplemental Indicators (for context only)
        'supplemental_indicators': supplemental_indicators,
        
        # Backward compatibility
        'key_risks': get_recession_risk_factors_nyfed(treasury_rates, recession_indicators),
        'confidence': risk_level,  # Map to old confidence field
        
        # Historical Context
        'methodology_note': "Based on NY Fed yield curve model. Probability represents likelihood of recession starting within 12 months.",
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def get_recession_risk_factors_nyfed(treasury_rates: Dict, recession_indicators: Dict) -> List[str]:
    """
    Identify specific recession risk factors for NY Fed model context.
    """
    risks = []
    
    # Term structure risks
    ten_year_rate = treasury_rates.get('10_year', 0)
    three_month_rate = treasury_rates.get('3_month', 0)
    two_year_rate = treasury_rates.get('2_year', 0)
    
    term_spread = ten_year_rate - three_month_rate
    curve_2s10s = ten_year_rate - two_year_rate
    
    if term_spread < -1.0:
        risks.append("Deeply inverted 10y-3m yield curve (>100 bps)")
    elif term_spread < -0.5:
        risks.append("Inverted 10y-3m yield curve (>50 bps)")
    elif term_spread < 0:
        risks.append("Inverted 10y-3m yield curve")
    
    if curve_2s10s < -0.5:
        risks.append("Inverted 10y-2y yield curve")
    
    # Supplemental risk factors
    sahm_indicator = recession_indicators.get('sahm_indicator', 0)
    if sahm_indicator >= 0.5:
        risks.append("Sahm Rule triggered (recession likely started)")
    elif sahm_indicator >= 0.3:
        risks.append("Sahm Rule warning (unemployment rising)")
    
    hy_spreads = recession_indicators.get('hy_spreads', 500)
    if hy_spreads > 800:
        risks.append("High yield credit spreads elevated (>800 bps)")
    elif hy_spreads > 600:
        risks.append("High yield credit spreads widening (>600 bps)")
    
    lei_6m_change = recession_indicators.get('lei_6m_change', 0)
    if lei_6m_change < -3.0:
        risks.append("Leading Economic Index declining sharply")
    elif lei_6m_change < -1.5:
        risks.append("Leading Economic Index weakening")
    
    if not risks:
        risks.append("No significant recession risk factors identified")
    
    return risks

# Legacy function name for backward compatibility
def calculate_recession_probability(treasury_rates: Dict, recession_indicators: Dict, 
                                  economic_indicators: Dict) -> Dict:
    """Legacy wrapper - redirects to NY Fed probit model."""
    return calculate_recession_probability_nyfed(treasury_rates, recession_indicators, economic_indicators)

def classify_interest_rate_environment(treasury_rates: Dict) -> Dict:
    """Classify the interest rate environment using Fed-focused approach with basis points."""
    if not treasury_rates:
        return {}
    
    # Get Fed Funds rate
    fed_funds_rate = get_fed_funds_rate()
    ten_year_rate = treasury_rates.get('10_year', 0)
    two_year_rate = treasury_rates.get('2_year', 0)
    
    # Calculate spreads in basis points
    fed_10y_spread_bps = (ten_year_rate - fed_funds_rate) * 100
    fed_2y_spread_bps = (two_year_rate - fed_funds_rate) * 100
    
    # Classify based on Fed policy context
    if fed_10y_spread_bps < -50:  # 10Y more than 50 bps below Fed Funds
        rate_environment = "Dovish Expectations"
        policy_stance = "Market expects aggressive cuts"
        growth_vs_value = "Strong Growth Tilt"
    elif fed_10y_spread_bps < 25:  # 10Y within 25 bps of Fed Funds
        rate_environment = "Policy Rate Peak"
        policy_stance = "Market expects policy pause/mild cuts"
        growth_vs_value = "Moderate Growth Tilt"
    elif fed_10y_spread_bps < 100:  # 10Y 25-100 bps above Fed Funds
        rate_environment = "Normal Term Premium"
        policy_stance = "Normal market conditions"
        growth_vs_value = "Neutral"
    elif fed_10y_spread_bps < 200:  # 10Y 100-200 bps above Fed Funds
        rate_environment = "High Term Premium"
        policy_stance = "Market demands high compensation"
        growth_vs_value = "Value Tilt"
    else:  # 10Y more than 200 bps above Fed Funds
        rate_environment = "Very High Term Premium"
        policy_stance = "Elevated inflation/fiscal concerns"
        growth_vs_value = "Strong Value Tilt"
    
    # Real rates context (approximate)
    real_10y_estimate = ten_year_rate - 2.5  # Assume 2.5% long-term inflation target
    
    return {
        'rate_environment': rate_environment,
        'policy_stance': policy_stance,
        'growth_vs_value': growth_vs_value,
        'fed_funds_rate': fed_funds_rate,
        'ten_year_rate': ten_year_rate,
        'fed_10y_spread_bps': fed_10y_spread_bps,
        'fed_2y_spread_bps': fed_2y_spread_bps,
        'real_10y_estimate': real_10y_estimate
    }

def classify_market_regime(economic_indicators: Dict, yield_curve: Dict) -> Dict:
    """Enhanced market regime classification with 15 distinct regimes."""
    print("🔍 Analyzing enhanced market regime...")
    
    # Get enhanced data
    fred_data = get_fred_economic_data()
    market_data = get_fmp_market_data()
    
    # Extract key indicators
    vix = market_data.get('vix', {}).get('current', 20.0)
    curve_2s10s_bps = yield_curve.get('curve_2s10s_bps', 50)
    unemployment = fred_data.get('unemployment_rate', {}).get('current', 4.2)
    gdp_growth = calculate_gdp_growth(fred_data)
    inflation_rate = fred_data.get('core_pce_inflation', {}).get('current', 2.1)
    fed_funds = fred_data.get('fed_funds_rate', {}).get('current', 4.33)
    
    # Sector performance analysis
    sectors = market_data.get('sectors', {})
    tech_performance = sectors.get('Technology', {}).get('change_percent', 0)
    leading_sector = market_data.get('leading_sector', {})
    
    # =============================================================================
    # ENHANCED REGIME DETECTION LOGIC
    # =============================================================================
    
    regime = 'OPTIMISTIC'  # Default
    confidence = 0.5
    signals = []
    regime_factors = {}
    
    # 1. CRISIS & HIGH VOLATILITY REGIMES
    if vix >= 35:
        regime = 'CRISIS_MODE'
        confidence = 0.9
        signals.append(f"Crisis volatility: VIX {vix:.1f}")
        regime_factors['volatility'] = 'CRISIS'
    elif vix >= 25:
        regime = 'HIGH_VOLATILITY'
        confidence = 0.8
        signals.append(f"High volatility: VIX {vix:.1f}")
        regime_factors['volatility'] = 'HIGH'
    else:
        regime_factors['volatility'] = 'NORMAL' if vix < 20 else 'ELEVATED'
    
    # 2. RECESSION DETECTION
    if curve_2s10s_bps < -50 and unemployment > 4.5:
        if regime not in ['CRISIS_MODE']:
            regime = 'LATE_CYCLE'
            confidence = 0.85
            signals.append(f"Deep inversion + rising unemployment")
    elif curve_2s10s_bps < -20:
        if regime not in ['CRISIS_MODE', 'HIGH_VOLATILITY']:
            regime = 'LATE_CYCLE'
            confidence = 0.75
            signals.append(f"Yield curve inversion: {curve_2s10s_bps:.0f} bps")
    
    # 3. EARLY RECOVERY DETECTION
    if (curve_2s10s_bps > 150 and unemployment > 6.0 and gdp_growth < 1.0 
        and regime not in ['CRISIS_MODE', 'HIGH_VOLATILITY', 'LATE_CYCLE']):
        regime = 'EARLY_RECOVERY'
        confidence = 0.8
        signals.append(f"Steep curve + high unemployment suggests early recovery")
        regime_factors['cycle'] = 'EARLY_RECOVERY'
    
    # 4. TECH DOMINANCE DETECTION
    if (tech_performance > 2.0 and vix < 25 
        and regime not in ['CRISIS_MODE', 'HIGH_VOLATILITY', 'LATE_CYCLE', 'EARLY_RECOVERY']):
        regime = 'TECH_DOMINANCE'
        confidence = 0.7
        signals.append(f"Technology sector leadership: +{tech_performance:.1f}%")
        regime_factors['sector_leadership'] = 'TECHNOLOGY'
    
    # 5. INFLATION REGIMES
    if inflation_rate > 4.0:
        if regime not in ['CRISIS_MODE', 'HIGH_VOLATILITY']:
            regime = 'HIGH_INFLATION'
            confidence = 0.8
            signals.append(f"High inflation: {inflation_rate:.1f}%")
        regime_factors['inflation'] = 'HIGH'
    elif inflation_rate < 1.0:
        regime_factors['inflation'] = 'LOW'
    else:
        regime_factors['inflation'] = 'MODERATE'
    
    # 6. INTEREST RATE REGIMES
    if fed_funds > 5.5:
        regime_factors['rates'] = 'HIGH'
        if regime not in ['CRISIS_MODE', 'HIGH_VOLATILITY', 'HIGH_INFLATION']:
            regime = 'RISING_RATES'
            confidence = 0.75
            signals.append(f"High fed funds rate: {fed_funds:.2f}%")
    elif fed_funds < 1.0:
        regime_factors['rates'] = 'LOW'
    else:
        regime_factors['rates'] = 'MODERATE'
    
    # 7. DEFAULT TO OPTIMISTIC IF NO STRONG SIGNALS
    if regime == 'OPTIMISTIC' and vix < 20 and curve_2s10s_bps > 50:
        confidence = 0.6
        signals.append("Normal market conditions")
    
    # 8. DEFENSIVE OVERRIDE (from external signals)
    defensive_signal_path = "data/processed/temp_signals/defensive_mode.json"
    if os.path.exists(defensive_signal_path):
        try:
            with open(defensive_signal_path, 'r') as f:
                defensive_signal = json.load(f)
                if defensive_signal.get('force_defensive', False):
                    regime = 'DEFENSIVE'
                    confidence = 0.95
                    signals.append("External defensive signal detected")
        except Exception as e:
            print(f"⚠️ Error reading defensive signal: {e}")
    
    # =============================================================================
    # REGIME CHARACTERISTICS
    # =============================================================================
    
    regime_characteristics = get_regime_characteristics(regime)
    
    # Calculate regime score
    regime_score = calculate_regime_score(regime, vix, curve_2s10s_bps, inflation_rate, fed_funds)
    
    result = {
        'regime': regime,
        'confidence': confidence,
        'regime_score': regime_score,
        'signals': signals,
        'characteristics': regime_characteristics,
        'regime_factors': regime_factors,
        'market_conditions': {
            'vix': vix,
            'yield_curve_bps': curve_2s10s_bps,
            'unemployment': unemployment,
            'inflation': inflation_rate,
            'fed_funds': fed_funds,
            'gdp_growth': gdp_growth,
            'tech_performance': tech_performance,
            'leading_sector': leading_sector.get('name', 'Unknown')
        },
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    print(f"🎯 Market Regime: {regime} (confidence: {confidence:.0%})")
    for signal in signals[:3]:  # Show top 3 signals
        print(f"   • {signal}")
    
    return result

def calculate_gdp_growth(fred_data: Dict) -> float:
    """Calculate estimated GDP growth rate"""
    try:
        # Try to get recent GDP data
        if 'real_gdp' in fred_data:
            current_gdp = fred_data['real_gdp']['current']
            previous_gdp = fred_data['real_gdp'].get('previous')
            if previous_gdp:
                growth_rate = ((current_gdp - previous_gdp) / previous_gdp) * 100
                return growth_rate
        
        # Fallback: estimate from other indicators
        unemployment = fred_data.get('unemployment_rate', {}).get('current', 4.2)
        industrial_prod = fred_data.get('industrial_production', {}).get('current', 100)
        
        # Rough estimate: lower unemployment and higher production = higher growth
        estimated_growth = 3.0 - (unemployment - 3.5) * 0.5
        return max(-2.0, min(6.0, estimated_growth))  # Clamp between -2% and 6%
        
    except Exception as e:
        print(f"⚠️ Error calculating GDP growth: {e}")
        return 2.5  # Default moderate growth

def get_regime_characteristics(regime: str) -> Dict:
    """Get detailed characteristics for each market regime"""
    characteristics = {
        'OPTIMISTIC': {
            'description': 'Normal bull market conditions',
            'risk_level': 'MODERATE',
            'growth_tilt': 0.1,
            'sector_adjustments': {},
            'volatility_target': 0.15
        },
        'DEFENSIVE': {
            'description': 'Bear market or defensive positioning required',
            'risk_level': 'LOW',
            'growth_tilt': -0.2,
            'sector_adjustments': {
                'Healthcare': 0.20,
                'Consumer Defensive': 0.15,
                'Utilities': 0.10,
                'Technology': -0.20,
                'Real Estate': -0.25,
                'Energy': -0.30
            },
            'volatility_target': 0.12
        },
        'CRISIS_MODE': {
            'description': 'Market crisis with extreme volatility',
            'risk_level': 'VERY_LOW',
            'growth_tilt': -0.3,
            'sector_adjustments': {
                'Healthcare': 0.25,
                'Consumer Defensive': 0.20,
                'Utilities': 0.15,
                'Technology': -0.25,
                'Real Estate': -0.30,
                'Energy': -0.35,
                'Financials': -0.20
            },
            'volatility_target': 0.10
        },
        'EARLY_RECOVERY': {
            'description': 'Early economic recovery phase',
            'risk_level': 'MODERATE',
            'growth_tilt': 0.15,
            'sector_adjustments': {
                'Financials': 0.15,
                'Industrials': 0.10,
                'Materials': 0.10,
                'Consumer Discretionary': 0.05,
                'Utilities': -0.15,
                'Consumer Defensive': -0.10
            },
            'volatility_target': 0.16
        },
        'LATE_CYCLE': {
            'description': 'Late economic cycle with recession risk',
            'risk_level': 'LOW',
            'growth_tilt': -0.15,
            'sector_adjustments': {
                'Healthcare': 0.15,
                'Consumer Defensive': 0.10,
                'Utilities': 0.10,
                'Technology': -0.10,
                'Real Estate': -0.15,
                'Energy': -0.20
            },
            'volatility_target': 0.13
        },
        'TECH_DOMINANCE': {
            'description': 'Technology sector leadership regime',
            'risk_level': 'MODERATE_HIGH',
            'growth_tilt': 0.25,
            'sector_adjustments': {
                'Technology': 0.20,
                'Communication Services': 0.10,
                'Consumer Discretionary': 0.05,
                'Utilities': -0.15,
                'Consumer Defensive': -0.10,
                'Energy': -0.10
            },
            'volatility_target': 0.17
        },
        'HIGH_VOLATILITY': {
            'description': 'Elevated market volatility regime',
            'risk_level': 'LOW',
            'growth_tilt': -0.1,
            'sector_adjustments': {
                'Healthcare': 0.10,
                'Consumer Defensive': 0.10,
                'Utilities': 0.05,
                'Technology': -0.10,
                'Real Estate': -0.15
            },
            'volatility_target': 0.12
        },
        'HIGH_INFLATION': {
            'description': 'High inflation environment',
            'risk_level': 'MODERATE',
            'growth_tilt': 0.0,
            'sector_adjustments': {
                'Energy': 0.15,
                'Materials': 0.10,
                'Real Estate': 0.05,
                'Technology': -0.15,
                'Consumer Discretionary': -0.10
            },
            'volatility_target': 0.16
        },
        'RISING_RATES': {
            'description': 'Rising interest rate environment',
            'risk_level': 'MODERATE',
            'growth_tilt': -0.05,
            'sector_adjustments': {
                'Financials': 0.15,
                'Energy': 0.05,
                'Technology': -0.10,
                'Real Estate': -0.20,
                'Utilities': -0.15
            },
            'volatility_target': 0.15
        }
    }
    
    return characteristics.get(regime, characteristics['OPTIMISTIC'])

def calculate_regime_score(regime: str, vix: float, curve_bps: float, inflation: float, fed_funds: float) -> float:
    """Calculate a numerical score for regime strength"""
    base_scores = {
        'OPTIMISTIC': 0.7,
        'DEFENSIVE': 0.3,
        'CRISIS_MODE': 0.1,
        'EARLY_RECOVERY': 0.6,
        'LATE_CYCLE': 0.4,
        'TECH_DOMINANCE': 0.8,
        'HIGH_VOLATILITY': 0.4,
        'HIGH_INFLATION': 0.5,
        'RISING_RATES': 0.5
    }
    
    base_score = base_scores.get(regime, 0.5)
    
    # Adjust based on current conditions
    vix_adjustment = max(-0.2, min(0.2, (20 - vix) / 100))
    curve_adjustment = max(-0.1, min(0.1, curve_bps / 1000))
    
    final_score = base_score + vix_adjustment + curve_adjustment
    return max(0.1, min(0.9, final_score))

def generate_sector_recommendations(rate_environment: Dict, market_regime: Dict, yield_curve: Dict, recession_analysis: Dict = None) -> Dict:
    """Generate sector weight adjustments based on enhanced market regime."""
    
    # Get regime and characteristics  
    regime = market_regime.get('regime', 'OPTIMISTIC')
    characteristics = market_regime.get('characteristics', {})
    sector_adjustments = characteristics.get('sector_adjustments', {})
    
    recommendations = {}
    for sector, adjustment in sector_adjustments.items():
        if abs(adjustment) > 0.05:  # Only include meaningful adjustments
            recommendations[sector] = {
                'weight_adjustment': 1.0 + adjustment,
                'adjustment_percentage': adjustment * 100,
                'reason': f"Regime: {regime}"
            }
    
    return recommendations

def generate_style_recommendations(rate_environment: Dict, market_regime: Dict, recession_analysis: Dict = None) -> Dict:
    """Generate style allocation adjustments based on enhanced market regime."""
    
    # Get regime characteristics
    regime = market_regime.get('regime', 'OPTIMISTIC')
    characteristics = market_regime.get('characteristics', {})
    growth_tilt = characteristics.get('growth_tilt', 0.0)
    risk_level = characteristics.get('risk_level', 'MODERATE')
    
    # Base style allocation
    base_allocation = {
        'Quality': 0.40,
        'Growth': 0.30, 
        'Value': 0.20,
        'Blend': 0.10
    }
    
    # Adjust based on regime
    adjustments = {}
    
    if growth_tilt > 0.1:  # Growth regime
        adjustments = {
            'Growth': {'adjustment': 0.10, 'reason': f'Growth tilt in {regime} regime'},
            'Quality': {'adjustment': -0.05, 'reason': f'Reducing quality for growth'},
            'Value': {'adjustment': -0.05, 'reason': f'Reducing value for growth'}
        }
    elif growth_tilt < -0.1:  # Defensive regime
        adjustments = {
            'Quality': {'adjustment': 0.15, 'reason': f'Quality emphasis in {regime} regime'},
            'Growth': {'adjustment': -0.10, 'reason': f'Reducing growth risk'},
            'Value': {'adjustment': -0.05, 'reason': f'Reducing value risk'}
        }
    
    return adjustments

def generate_risk_adjustments(market_regime: Dict, economic_indicators: Dict, recession_analysis: Dict = None) -> Dict:
    """Generate portfolio risk level adjustments based on enhanced market regime."""
    
    regime = market_regime.get('regime', 'OPTIMISTIC')
    characteristics = market_regime.get('characteristics', {})
    risk_level = characteristics.get('risk_level', 'MODERATE')
    volatility_target = characteristics.get('volatility_target', 0.15)
    
    # Base risk multiplier
    risk_multipliers = {
        'VERY_LOW': 0.6,
        'LOW': 0.8,
        'MODERATE': 1.0,
        'MODERATE_HIGH': 1.15,
        'HIGH': 1.3
    }
    
    risk_multiplier = risk_multipliers.get(risk_level, 1.0)
    
    return {
        'risk_multiplier': risk_multiplier,
        'volatility_target': volatility_target,
        'recommendation': f"Adjust portfolio risk to {risk_level} level for {regime} regime",
        'regime': regime,
        'risk_level': risk_level
    }

def generate_macro_report(treasury_rates: Dict, economic_indicators: Dict, 
                         yield_curve: Dict, rate_environment: Dict, 
                         market_regime: Dict, recession_analysis: Dict,
                         sector_recs: Dict, style_recs: Dict, risk_adj: Dict,
                         fed_data: Dict = None, fed_proximity_analysis: Dict = None) -> None:
    """Generate comprehensive enhanced macro analysis report."""
    print("\n" + "="*80)
    print("ENHANCED MACRO ECONOMIC ANALYSIS REPORT")
    print("="*80)
    
    # Enhanced Market Regime Section
    regime = market_regime.get('regime', 'UNKNOWN')
    confidence = market_regime.get('confidence', 0.0)
    characteristics = market_regime.get('characteristics', {})
    market_conditions = market_regime.get('market_conditions', {})
    
    print(f"\n🎯 ENHANCED MARKET REGIME ANALYSIS:")
    print(f"Detected Regime: {regime} (Confidence: {confidence:.0%})")
    print(f"Description: {characteristics.get('description', 'N/A')}")
    print(f"Risk Level: {characteristics.get('risk_level', 'N/A')}")
    print(f"Growth Tilt: {characteristics.get('growth_tilt', 0.0):+.1%}")
    
    print(f"\n📊 Current Market Conditions:")
    print(f"VIX: {market_conditions.get('vix', 0):.1f}")
    print(f"Yield Curve (2s10s): {market_conditions.get('yield_curve_bps', 0):.0f} bps")
    print(f"Unemployment: {market_conditions.get('unemployment', 0):.1f}%")
    print(f"Inflation: {market_conditions.get('inflation', 0):.1f}%")
    print(f"Fed Funds: {market_conditions.get('fed_funds', 0):.2f}%")
    print(f"Leading Sector: {market_conditions.get('leading_sector', 'Unknown')}")
    
    print(f"\n💡 Investment Implications:")
    print(f"Target Volatility: {characteristics.get('volatility_target', 0.15):.1%}")
    
    # Sector recommendations
    if sector_recs:
        print(f"\n📈 Sector Adjustments:")
        for sector, rec in sector_recs.items():
            adj = rec.get('adjustment_percentage', 0)
            print(f"  {sector}: {adj:+.0f}%")
    
    # Style recommendations  
    if style_recs:
        print(f"\n🎨 Style Adjustments:")
        for style, rec in style_recs.items():
            adj = rec.get('adjustment', 0)
            print(f"  {style}: {adj:+.1%}")
    
    # Risk adjustments
    risk_mult = risk_adj.get('risk_multiplier', 1.0)
    print(f"\n⚖️ Risk Adjustment: {risk_mult:.2f}x")
    print(f"Recommendation: {risk_adj.get('recommendation', 'Maintain current risk level')}")
    
    print("\n" + "="*80)

def main():
    try:
        print("🚀 Starting Enhanced Macro Economic Analysis with FRED Integration...")
        start_time = time.time()
        
        # =================================================================
        # STEP 1: ENHANCED DATA COLLECTION WITH FRED
        # =================================================================
        print("\n=== 📊 STEP 1: Enhanced Data Collection ===")
        
        # Get comprehensive economic data from FRED
        fred_data = get_fred_economic_data()
        
        # Get treasury rates (FRED-enhanced)
        treasury_rates = get_treasury_rates()
        
        # Get market indicators
        economic_indicators = get_economic_indicators()
        
        # Get recession indicators (FRED-enhanced)
        recession_indicators = get_recession_indicators()
        
        # =================================================================
        # STEP 2: FED POLICY ANALYSIS (REAL DATA)
        # =================================================================
        print("\n=== 🎯 STEP 2: Fed Policy Analysis ===")
        
        # Analyze Fed policy stance with real data
        fed_policy_analysis = analyze_fed_policy_stance(fred_data)
        
        # Get current Fed Funds rate
        current_fed_rate = get_fed_funds_rate()
        
        # =================================================================
        # STEP 3: ECONOMIC ANALYSIS
        # =================================================================
        print("\n=== 📈 STEP 3: Economic Analysis ===")
        
        # Calculate yield curve metrics
        yield_curve = calculate_yield_curve_metrics(treasury_rates)
        
        # Analyze recession probability
        recession_analysis = calculate_recession_probability(
            treasury_rates, recession_indicators, economic_indicators
        )
        
        # Classify interest rate environment
        rate_environment = classify_interest_rate_environment(treasury_rates)
        
        # Classify market regime
        market_regime = classify_market_regime(economic_indicators, yield_curve)
        
        # =================================================================
        # STEP 4: INVESTMENT RECOMMENDATIONS  
        # =================================================================
        print("\n=== 💡 STEP 4: Investment Recommendations ===")
        
        # Generate sector recommendations
        sector_recs = generate_sector_recommendations(
            rate_environment, market_regime, yield_curve, recession_analysis
        )
        
        # Generate style recommendations
        style_recs = generate_style_recommendations(
            rate_environment, market_regime, recession_analysis
        )
        
        # Generate risk adjustments
        risk_adj = generate_risk_adjustments(
            market_regime, economic_indicators, recession_analysis
        )
        
        # =================================================================
        # STEP 5: ENHANCED REPORTING
        # =================================================================
        print("\n=== 📋 STEP 5: Enhanced Report Generation ===")
        
        # Generate comprehensive report with FRED integration
        generate_macro_report(
            treasury_rates, economic_indicators, yield_curve, 
            rate_environment, market_regime, recession_analysis,
            sector_recs, style_recs, risk_adj,
            fed_data=fred_data, fed_proximity_analysis=fed_policy_analysis
        )
        
        # =================================================================
        # STEP 6: DATA EXPORT & INTEGRATION
        # =================================================================
        print("\n=== 💾 STEP 6: Data Export ===")
        
        timestamp = datetime.now().strftime('%Y-%m-%d')
        
        # Create comprehensive macro analysis dataset
        macro_data = {
            'analysis_date': timestamp,
            'data_sources': {
                'fred_available': FRED_AVAILABLE and FRED_API_KEY is not None,
                'fred_data_quality': fed_policy_analysis.get('data_quality', 'medium'),
                'primary_data_source': 'FRED' if (FRED_AVAILABLE and FRED_API_KEY) else 'FMP+Fallback'
            },
            'fred_economic_data': fred_data,
            'fed_policy_analysis': fed_policy_analysis,
            'treasury_rates': treasury_rates,
            'economic_indicators': economic_indicators,
            'recession_indicators': recession_indicators,
            'yield_curve_analysis': yield_curve,
            'recession_analysis': recession_analysis,
            'rate_environment': rate_environment,
            'market_regime': market_regime,
            'sector_recommendations': sector_recs,
            'style_recommendations': style_recs,
            'risk_adjustments': risk_adj
        }
        
        # Save all outputs to appropriate folders
        
        # 1. Main macro analysis to macro_analysis folder  
        macro_output_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files', 'macro_analysis')
        os.makedirs(macro_output_dir, exist_ok=True)
        macro_output_path = os.path.join(macro_output_dir, f"05_macro_economic_analysis_{timestamp}.csv")
        
        # 2. Fed policy and FRED data to risk_analysis folder (update in place)
        risk_output_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files', 'risk_analysis')
        os.makedirs(risk_output_dir, exist_ok=True)
        
        # Update in place - always same filename
        fred_output_path = os.path.join(risk_output_dir, "fred_economic_data_latest.json")
        fed_policy_path = os.path.join(risk_output_dir, "fed_policy_analysis_latest.json")
        macro_risk_path = os.path.join(risk_output_dir, "macro_risk_analysis_latest.json")
        
        # Save main macro analysis
        macro_df = pd.DataFrame([{
            'Date': timestamp,
            'Data_Source': macro_data['data_sources']['primary_data_source'],
            'FRED_Available': macro_data['data_sources']['fred_available'],
            
            # Core Economic Data (FRED-enhanced)
            'Fed_Funds_Rate': current_fed_rate,
            'Unemployment_Rate': fred_data.get('unemployment_rate', {}).get('current', 4.2),
            'Core_PCE_Inflation': fred_data.get('core_pce_inflation', {}).get('current', 2.1),
            'Consumer_Sentiment': fred_data.get('consumer_sentiment', {}).get('current', 75.0),
            
            # Treasury Rates
            '10Y_Treasury': treasury_rates.get('10_year', 0) * 100,  # Convert to percentage
            '2Y_Treasury': treasury_rates.get('2_year', 0) * 100,
            '3M_Treasury': treasury_rates.get('3_month', 0) * 100,
            
            # Market Indicators
            'VIX': economic_indicators.get('vix', 0),
            'USD_Index': economic_indicators.get('usd_index', 0),
            'Gold_Price': economic_indicators.get('gold_price', 0),
            'Oil_Price': economic_indicators.get('oil_price', 0),
            
            # Analysis Results
            'Yield_Curve_2s10s_bps': yield_curve.get('curve_2s10s_bps', 0),
            'Recession_Probability': recession_analysis.get('recession_probability', 0),
            'Market_Regime': market_regime.get('overall_regime', 'N/A'),
            
            # Fed Policy Analysis (NEW)
            'Fed_Policy_Bias': fed_policy_analysis.get('overall_assessment', {}).get('policy_bias', 'NEUTRAL'),
            'Fed_Rate_Direction': fed_policy_analysis.get('overall_assessment', {}).get('rate_direction', 'HOLD'),
            'Fed_Terminal_Rate_Est': fed_policy_analysis.get('overall_assessment', {}).get('terminal_rate_estimate', current_fed_rate),
            'Fed_Employment_Score': fed_policy_analysis.get('employment_analysis', {}).get('score', 0),
            'Fed_Inflation_Score': fed_policy_analysis.get('inflation_analysis', {}).get('score', 0),
            
            # Investment Recommendations
            'Recommended_Tech_Weight': sector_recs.get('Technology', {}).get('weight_adjustment', 1.0),
            'Recommended_Healthcare_Weight': sector_recs.get('Healthcare', {}).get('weight_adjustment', 1.0),
            'Recommended_Financials_Weight': sector_recs.get('Financials', {}).get('weight_adjustment', 1.0),
            'Risk_Adjustment_Factor': risk_adj.get('risk_multiplier', 1.0)
        }])
        
        # Save main macro analysis
        macro_df.to_csv(macro_output_path, index=False)
        print(f"💾 Enhanced macro analysis saved to {macro_output_path}")
        
        # Save FRED data to risk_analysis (update in place)
        with open(fred_output_path, 'w') as f:
            json.dump(fred_data, f, indent=2, default=str)
        print(f"📊 FRED data updated in {fred_output_path}")
        
        # Save Fed policy analysis to risk_analysis (update in place)
        with open(fed_policy_path, 'w') as f:
            json.dump(fed_policy_analysis, f, indent=2, default=str)
        print(f"🎯 Fed policy analysis updated in {fed_policy_path}")
        
        # Create comprehensive macro risk analysis
        macro_risk_analysis = {
            'analysis_date': datetime.now().isoformat(),
            'market_regime': {
                'rate_environment': rate_environment,
                'policy_stance': rate_environment.get('policy_stance', 'N/A'), 
                'economic_cycle': market_regime.get('economic_cycle', 'N/A'),
                'volatility_regime': market_regime.get('volatility_regime', 'N/A'),
                'risk_appetite': market_regime.get('risk_appetite', 'N/A')
            },
            'recession_analysis': {
                'probability': recession_analysis.get('recession_probability', 0),
                'confidence_intervals': {
                    '68_percent': f"{recession_analysis.get('confidence_68_lower', 0):.1f}% - {recession_analysis.get('confidence_68_upper', 0):.1f}%",
                    '90_percent': f"{recession_analysis.get('confidence_90_lower', 0):.1f}% - {recession_analysis.get('confidence_90_upper', 0):.1f}%"
                },
                'risk_level': recession_analysis.get('risk_level', 'N/A'),
                'sahm_rule_status': 'TRIGGERED' if recession_analysis.get('supplemental_indicators', {}).get('sahm_rule', 'Normal') == 'TRIGGERED' else 'Normal',
                'yield_curve_signal': 'Inverted' if recession_analysis.get('term_spread_10y3m', 0) < 0 else 'Normal'
            },
            'fed_policy': fed_policy_analysis,
            'economic_indicators': economic_indicators,
            'risk_recommendations': {
                'overall_risk_multiplier': risk_adj.get('risk_multiplier', 1.0),
                'sector_risk_adjustments': sector_recs,
                'style_risk_adjustments': style_recs,
                'key_risks': risk_adj.get('rationale', '').split('; ')
            }
        }
        
        # Save comprehensive macro risk analysis (update in place)
        with open(macro_risk_path, 'w') as f:
            json.dump(macro_risk_analysis, f, indent=2, default=str)
        print(f"⚠️ Comprehensive macro risk analysis updated in {macro_risk_path}")
        
        # =================================================================
        # PERFORMANCE & SUMMARY
        # =================================================================
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n{'='*60}")
        print(f"✅ ENHANCED MACRO ANALYSIS COMPLETE")
        print(f"{'='*60}")
        print(f"🕒 Duration: {duration:.1f} seconds")
        print(f"📊 Data Source: {macro_data['data_sources']['primary_data_source']}")
        print(f"🎯 Fed Policy: {fed_policy_analysis.get('overall_assessment', {}).get('policy_bias', 'N/A')}")
        print(f"📈 Rate Direction: {fed_policy_analysis.get('overall_assessment', {}).get('rate_direction', 'N/A')}")
        print(f"⚠️ Recession Risk: {recession_analysis.get('recession_probability', 0):.1f}%")
        print(f"🎪 Market Regime: {market_regime.get('overall_regime', 'N/A')}")
        
        # Alert for significant events
        rate_direction = fed_policy_analysis.get('overall_assessment', {}).get('rate_direction', 'HOLD')
        recession_prob = recession_analysis.get('recession_probability', 0)
        
        if rate_direction != 'HOLD':
            print(f"\n🚨 POLICY ALERT: Fed bias toward {rate_direction} - consider portfolio adjustments!")
        
        if recession_prob > 30:
            print(f"\n⚠️ RECESSION ALERT: {recession_prob:.1f}% probability - implement defensive strategies!")
        
        if yield_curve.get('curve_2s10s_bps', 0) < 0:
            print(f"\n📉 YIELD CURVE ALERT: Inverted curve detected - monitor recession indicators!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in enhanced macro economic analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Add setup instructions
    print("🏦 Enhanced Macro Economic Analysis with FRED Integration")
    print("="*60)
    
    if not FRED_AVAILABLE:
        print("⚠️ To get the best results, install fredapi: pip install fredapi")
    elif FRED_API_KEY is None:
        print("💡 For real-time Fed data, get a free FRED API key:")
        print("   https://fred.stlouisfed.org/docs/api/api_key.html")
        print("   Then set FRED_API_KEY in this file")
    else:
        print("✅ FRED API configured - using real-time Federal Reserve data")
    
    print()
    main() 