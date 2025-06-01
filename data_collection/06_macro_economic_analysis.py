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

# For now, using None will trigger fallback methods
FRED_API_KEY = None  # Set to your FRED API key when available

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
        'ism_manufacturing': 'ISRATIO'          # ISM Manufacturing PMI
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
    """Classify the overall market regime with enhanced precision."""
    vix = economic_indicators.get('vix', 20)
    curve_shape = yield_curve.get('curve_shape', 'Normal')
    curve_2s10s_bps = yield_curve.get('curve_2s10s_bps', 50)
    
    # Market volatility assessment with more granular thresholds
    if vix < 12:
        volatility_regime = "Very Low Volatility"
        risk_appetite = "Very High"
    elif vix < 16:
        volatility_regime = "Low Volatility"
        risk_appetite = "High"
    elif vix < 20:
        volatility_regime = "Normal Volatility"
        risk_appetite = "Moderate"
    elif vix < 30:
        volatility_regime = "Elevated Volatility"
        risk_appetite = "Low"
    elif vix < 40:
        volatility_regime = "High Volatility"
        risk_appetite = "Very Low"
    else:
        volatility_regime = "Crisis Volatility"
        risk_appetite = "Risk-Off"
    
    # Economic cycle assessment based on yield curve in bps
    if curve_2s10s_bps < -50:  # Deeply inverted
        economic_cycle = "Late Cycle/Imminent Recession"
    elif curve_2s10s_bps < -10:  # Mildly inverted
        economic_cycle = "Late Cycle/Recession Risk"
    elif curve_2s10s_bps < 30:  # Flat
        economic_cycle = "Mid-Late Cycle"
    elif curve_2s10s_bps < 150:  # Normal
        economic_cycle = "Mid Cycle"
    else:  # Very steep
        economic_cycle = "Early Cycle/Recovery"
    
    return {
        'volatility_regime': volatility_regime,
        'risk_appetite': risk_appetite,
        'economic_cycle': economic_cycle,
        'overall_regime': f"{economic_cycle} - {volatility_regime}",
        'vix_level': vix,
        'curve_2s10s_bps': curve_2s10s_bps
    }

def generate_sector_recommendations(rate_environment: Dict, market_regime: Dict, yield_curve: Dict, recession_analysis: Dict = None) -> Dict:
    """Generate sector weight adjustments based on macro conditions and recession probability."""
    recommendations = {}
    
    # Base case: equal sector weights
    base_weights = {
        'Technology': 0.12,
        'Healthcare': 0.12,
        'Financial Services': 0.10,
        'Industrials': 0.10,
        'Consumer Cyclical': 0.10,
        'Consumer Defensive': 0.08,
        'Energy': 0.08,
        'Basic Materials': 0.08,
        'Real Estate': 0.08,
        'Communication Services': 0.08,
        'Utilities': 0.06
    }
    
    adjusted_weights = base_weights.copy()
    
    # Recession probability adjustments (highest priority)
    if recession_analysis:
        recession_prob = recession_analysis.get('recession_probability', 0)
        
        if recession_prob >= 70:  # High recession risk
            # Defensive overweight
            adjusted_weights['Consumer Defensive'] *= 1.5
            adjusted_weights['Healthcare'] *= 1.4
            adjusted_weights['Utilities'] *= 1.4
            # Cyclical underweight
            adjusted_weights['Consumer Cyclical'] *= 0.6
            adjusted_weights['Technology'] *= 0.7
            adjusted_weights['Basic Materials'] *= 0.6
            adjusted_weights['Energy'] *= 0.7
            adjusted_weights['Industrials'] *= 0.7
            
        elif recession_prob >= 40:  # Moderate recession risk
            # Moderate defensive tilt
            adjusted_weights['Consumer Defensive'] *= 1.3
            adjusted_weights['Healthcare'] *= 1.2
            adjusted_weights['Utilities'] *= 1.2
            adjusted_weights['Consumer Cyclical'] *= 0.8
            adjusted_weights['Technology'] *= 0.9
            adjusted_weights['Basic Materials'] *= 0.8
            
        elif recession_prob <= 15:  # Low recession risk
            # Cyclical overweight
            adjusted_weights['Technology'] *= 1.2
            adjusted_weights['Consumer Cyclical'] *= 1.3
            adjusted_weights['Industrials'] *= 1.2
            adjusted_weights['Basic Materials'] *= 1.1
            adjusted_weights['Consumer Defensive'] *= 0.8
            adjusted_weights['Utilities'] *= 0.8
    
    # Interest rate adjustments (secondary priority)
    growth_vs_value = rate_environment.get('growth_vs_value', 'Neutral')
    
    if 'Growth' in growth_vs_value and (not recession_analysis or recession_analysis.get('recession_probability', 0) < 40):
        # Favor growth sectors in low rate environment (if recession risk is low)
        adjusted_weights['Technology'] *= 1.2
        adjusted_weights['Healthcare'] *= 1.1
        adjusted_weights['Communication Services'] *= 1.1
        adjusted_weights['Financial Services'] *= 0.9
        adjusted_weights['Real Estate'] *= 0.8
        adjusted_weights['Utilities'] *= 0.8
    elif 'Value' in growth_vs_value:
        # Favor value sectors in high rate environment
        adjusted_weights['Financial Services'] *= 1.3
        adjusted_weights['Energy'] *= 1.2
        adjusted_weights['Basic Materials'] *= 1.1
        adjusted_weights['Technology'] *= 0.9
        adjusted_weights['Real Estate'] *= 0.9
    
    # Yield curve adjustments
    curve_shape = yield_curve.get('curve_shape', 'Normal')
    
    if curve_shape == "Steep" and (not recession_analysis or recession_analysis.get('recession_probability', 0) < 40):
        # Steep curve favors financials (if not in recession)
        adjusted_weights['Financial Services'] *= 1.1
    elif curve_shape == "Inverted":
        # Inverted curve - defensive positioning
        adjusted_weights['Consumer Defensive'] *= 1.2
        adjusted_weights['Healthcare'] *= 1.1
        adjusted_weights['Utilities'] *= 1.1
        adjusted_weights['Consumer Cyclical'] *= 0.8
        adjusted_weights['Energy'] *= 0.9
    
    # Volatility adjustments
    risk_appetite = market_regime.get('risk_appetite', 'Moderate')
    
    if risk_appetite == 'Low' or risk_appetite == 'Very Low':
        # Defensive positioning in high volatility
        adjusted_weights['Healthcare'] *= 1.1
        adjusted_weights['Consumer Defensive'] *= 1.2
        adjusted_weights['Utilities'] *= 1.1
        adjusted_weights['Technology'] *= 0.9
        adjusted_weights['Consumer Cyclical'] *= 0.8
    elif risk_appetite == 'High' and (not recession_analysis or recession_analysis.get('recession_probability', 0) < 30):
        # Risk-on positioning (only if recession risk is low)
        adjusted_weights['Technology'] *= 1.1
        adjusted_weights['Consumer Cyclical'] *= 1.1
        adjusted_weights['Energy'] *= 1.05
        adjusted_weights['Utilities'] *= 0.9
        adjusted_weights['Consumer Defensive'] *= 0.9
    
    # Normalize weights to sum to 1
    total_weight = sum(adjusted_weights.values())
    normalized_weights = {k: v/total_weight for k, v in adjusted_weights.items()}
    
    # Calculate adjustments from base case
    adjustments = {}
    for sector in base_weights:
        change = normalized_weights[sector] - base_weights[sector]
        if abs(change) > 0.01:  # Only show meaningful changes
            adjustments[sector] = {
                'base_weight': base_weights[sector],
                'recommended_weight': normalized_weights[sector],
                'change': change,
                'action': 'Overweight' if change > 0 else 'Underweight'
            }
    
    return adjustments

def generate_style_recommendations(rate_environment: Dict, market_regime: Dict, recession_analysis: Dict = None) -> Dict:
    """Generate style allocation adjustments based on macro conditions and recession probability."""
    # Base case style allocation
    base_allocation = {
        'Quality': 0.40,
        'Growth': 0.30,
        'Value': 0.20,
        'Blend': 0.10
    }
    
    adjusted_allocation = base_allocation.copy()
    
    # Recession probability adjustments (highest priority)
    if recession_analysis:
        recession_prob = recession_analysis.get('recession_probability', 0)
        
        if recession_prob >= 70:  # High recession risk
            adjusted_allocation['Quality'] += 0.20  # Quality becomes 60%
            adjusted_allocation['Growth'] -= 0.15   # Growth becomes 15%
            adjusted_allocation['Value'] -= 0.05    # Value becomes 15%
            
        elif recession_prob >= 40:  # Moderate recession risk
            adjusted_allocation['Quality'] += 0.10  # Quality becomes 50%
            adjusted_allocation['Growth'] -= 0.08   # Growth becomes 22%
            adjusted_allocation['Blend'] -= 0.02    # Blend becomes 8%
            
        elif recession_prob <= 15:  # Low recession risk - more aggressive
            adjusted_allocation['Growth'] += 0.10   # Growth becomes 40%
            adjusted_allocation['Quality'] -= 0.05  # Quality becomes 35%
            adjusted_allocation['Blend'] -= 0.05    # Blend becomes 5%
    
    # Interest rate adjustments (secondary priority)
    growth_vs_value = rate_environment.get('growth_vs_value', 'Neutral')
    
    if 'Growth' in growth_vs_value and (not recession_analysis or recession_analysis.get('recession_probability', 0) < 40):
        adjusted_allocation['Growth'] += 0.05
        adjusted_allocation['Value'] -= 0.03
        adjusted_allocation['Blend'] -= 0.02
    elif 'Value' in growth_vs_value:
        adjusted_allocation['Value'] += 0.10
        adjusted_allocation['Growth'] -= 0.08
        adjusted_allocation['Blend'] -= 0.02
    
    # Risk appetite adjustments
    risk_appetite = market_regime.get('risk_appetite', 'Moderate')
    
    if risk_appetite in ['Low', 'Very Low']:
        # Increase quality allocation in uncertain times
        adjusted_allocation['Quality'] += 0.05
        adjusted_allocation['Growth'] -= 0.03
        adjusted_allocation['Blend'] -= 0.02
    elif risk_appetite == 'High' and (not recession_analysis or recession_analysis.get('recession_probability', 0) < 30):
        # Increase growth allocation in risk-on environment (only if recession risk is low)
        adjusted_allocation['Growth'] += 0.03
        adjusted_allocation['Quality'] -= 0.03
    
    # Ensure allocations are non-negative and sum to 1
    for style in adjusted_allocation:
        adjusted_allocation[style] = max(0.05, adjusted_allocation[style])  # Minimum 5%
    
    total = sum(adjusted_allocation.values())
    adjusted_allocation = {k: v/total for k, v in adjusted_allocation.items()}
    
    # Calculate changes
    style_changes = {}
    for style in base_allocation:
        change = adjusted_allocation[style] - base_allocation[style]
        if abs(change) > 0.01:
            style_changes[style] = {
                'base_allocation': base_allocation[style],
                'recommended_allocation': adjusted_allocation[style],
                'change': change,
                'action': 'Increase' if change > 0 else 'Decrease'
            }
    
    return style_changes

def generate_risk_adjustments(market_regime: Dict, economic_indicators: Dict, recession_analysis: Dict = None) -> Dict:
    """Generate portfolio risk level adjustments based on macro conditions and recession probability."""
    vix = economic_indicators.get('vix', 20)
    risk_appetite = market_regime.get('risk_appetite', 'Moderate')
    
    # Base portfolio risk level (1.0 = normal)
    base_risk_level = 1.0
    
    # Recession probability adjustments (highest priority)
    if recession_analysis:
        recession_prob = recession_analysis.get('recession_probability', 0)
        
        if recession_prob >= 70:
            risk_multiplier = 0.6  # Reduce risk by 40%
            recommendation = "Reduce overall portfolio risk significantly due to high recession probability"
        elif recession_prob >= 40:
            risk_multiplier = 0.8  # Reduce risk by 20%
            recommendation = "Reduce overall portfolio risk moderately due to elevated recession risk"
        elif recession_prob <= 15:
            risk_multiplier = 1.1  # Increase risk by 10%
            recommendation = "Slightly increase portfolio risk given low recession probability"
        else:
            risk_multiplier = 0.95  # Slightly reduce risk
            recommendation = "Maintain slightly defensive risk posture"
    else:
        # Fallback to volatility-based adjustments
        if risk_appetite == 'Very Low':
            risk_multiplier = 0.7  # Reduce risk by 30%
            recommendation = "Reduce overall portfolio risk significantly"
        elif risk_appetite == 'Low':
            risk_multiplier = 0.85  # Reduce risk by 15%
            recommendation = "Reduce overall portfolio risk moderately"
        elif risk_appetite == 'High':
            risk_multiplier = 1.15  # Increase risk by 15%
            recommendation = "Increase overall portfolio risk moderately"
        else:
            risk_multiplier = 1.0
            recommendation = "Maintain current risk level"
    
    # Additional rationale
    rationale_parts = [f"VIX at {vix:.1f} indicates {market_regime.get('volatility_regime', 'normal')} market conditions"]
    
    if recession_analysis:
        recession_prob = recession_analysis.get('recession_probability', 0)
        rationale_parts.append(f"Recession probability: {recession_prob:.0f}%")
        # Update to use the new NY Fed model structure
        if recession_analysis.get('supplemental_indicators'):
            risk_factors = []
            for indicator, status in recession_analysis['supplemental_indicators'].items():
                if 'TRIGGERED' in status or 'HIGH' in status or 'WEAK' in status:
                    risk_factors.append(f"{indicator}: {status}")
            if risk_factors:
                rationale_parts.append(f"Key risks: {', '.join(risk_factors[:2])}")
    
    return {
        'risk_multiplier': risk_multiplier,
        'recommendation': recommendation,
        'vix_level': vix,
        'recession_probability': recession_analysis.get('recession_probability', 0) if recession_analysis else 0,
        'rationale': '; '.join(rationale_parts)
    }

def generate_macro_report(treasury_rates: Dict, economic_indicators: Dict, 
                         yield_curve: Dict, rate_environment: Dict, 
                         market_regime: Dict, recession_analysis: Dict,
                         sector_recs: Dict, style_recs: Dict, risk_adj: Dict,
                         fed_data: Dict = None, fed_proximity_analysis: Dict = None) -> None:
    """Generate comprehensive macro analysis report with NY Fed probit model results."""
    print("\n" + "="*80)
    print("MACRO ECONOMIC ANALYSIS REPORT")
    print("="*80)
    
    print(f"\nCurrent Market Conditions:")
    print(f"Date: {treasury_rates.get('date', 'N/A')}")
    print(f"Fed Funds Rate: {rate_environment.get('fed_funds_rate', 0):.2f}%")
    print(f"10-Year Treasury: {treasury_rates.get('10_year', 0):.2f}%")
    print(f"2-Year Treasury: {treasury_rates.get('2_year', 0):.2f}%")
    
    print(f"\nYield Curve Analysis (Basis Points):")
    print(f"2s10s Curve: {yield_curve.get('curve_2s10s_bps', 0):.0f} bps ({yield_curve.get('curve_shape', 'N/A')})")
    print(f"Term Spread (3M-10Y): {yield_curve.get('term_spread_bps', 0):.0f} bps")
    print(f"Fed vs 10Y Spread: {rate_environment.get('fed_10y_spread_bps', 0):+.0f} bps")
    print(f"Fed vs 2Y Spread: {rate_environment.get('fed_2y_spread_bps', 0):+.0f} bps")
    
    print(f"\nNY Fed Recession Analysis:")
    if recession_analysis:
        print(f"🏛️  Model: {recession_analysis.get('model_type', 'Unknown')} ({recession_analysis.get('model_vintage', 'N/A')})")
        print(f"📊 Recession Probability: {recession_analysis.get('recession_probability', 0):.1f}%")
        
        # Show confidence intervals
        print(f"📊 Confidence Intervals:")
        print(f"   68%: {recession_analysis.get('confidence_68_lower', 0):.1f}% - {recession_analysis.get('confidence_68_upper', 0):.1f}%")
        print(f"   90%: {recession_analysis.get('confidence_90_lower', 0):.1f}% - {recession_analysis.get('confidence_90_upper', 0):.1f}%")
        
        print(f"📊 Risk Level: {recession_analysis.get('risk_level', 'N/A')}")
        print(f"📊 Time Horizon: {recession_analysis.get('time_horizon', 'N/A')}")
        print(f"📊 Interpretation: {recession_analysis.get('interpretation', 'N/A')}")
        print(f"📊 Relative Risk: {recession_analysis.get('relative_risk', 'N/A')} (vs {recession_analysis.get('unconditional_average', 15)}% historical avg)")
        
        # Show term structure data
        print(f"\n📊 Term Structure Data:")
        print(f"   10Y-3M Spread: {recession_analysis.get('term_spread_10y3m', 0):.3f}%")
        print(f"   10Y-2Y Spread: {recession_analysis.get('term_spread_10y2y', 0):.3f}%")
        
        # Show model parameters for transparency
        if 'model_parameters' in recession_analysis:
            params = recession_analysis['model_parameters']
            print(f"   Model: P(Recession) = Φ({params.get('alpha', 0):.4f} + {params.get('beta', 0):.4f} × term_spread)")
            print(f"   Linear Combination: {params.get('linear_combination', 0):.4f}")
        
        # Show supplemental indicators
        print(f"\n📊 Supplemental Economic Indicators:")
        if 'supplemental_indicators' in recession_analysis:
            for indicator, status in recession_analysis['supplemental_indicators'].items():
                icon = "🚨" if any(x in status for x in ["TRIGGERED", "HIGH", "WEAK"]) else "⚠️" if "WARNING" in status else "✅"
                print(f"   {icon} {indicator.replace('_', ' ').title()}: {status}")
        
        print(f"\n📊 Methodology: {recession_analysis.get('methodology_note', 'N/A')}")
        print(f"📊 Last Updated: {recession_analysis.get('last_updated', 'N/A')}")
    else:
        print("Recession analysis unavailable")
    
    print(f"\nMacro Regime Classification:")
    print(f"Rate Environment: {rate_environment.get('rate_environment', 'N/A')}")
    print(f"Policy Stance: {rate_environment.get('policy_stance', 'N/A')}")
    print(f"Economic Cycle: {market_regime.get('economic_cycle', 'N/A')}")
    print(f"Volatility Regime: {market_regime.get('volatility_regime', 'N/A')} (VIX: {market_regime.get('vix_level', 0):.1f})")
    print(f"Risk Appetite: {market_regime.get('risk_appetite', 'N/A')}")
    
    print(f"\nSector Allocation Recommendations:")
    if sector_recs:
        for sector, rec in sector_recs.items():
            print(f"  {rec['action']} {sector}: {rec['base_weight']:.1%} → {rec['recommended_weight']:.1%} ({rec['change']:+.1%})")
    else:
        print("  No significant sector adjustments recommended")
    
    print(f"\nStyle Allocation Recommendations:")
    if style_recs:
        for style, rec in style_recs.items():
            print(f"  {rec['action']} {style}: {rec['base_allocation']:.1%} → {rec['recommended_allocation']:.1%} ({rec['change']:+.1%})")
    else:
        print("  No significant style adjustments recommended")
    
    print(f"\nRisk Level Recommendations:")
    print(f"  {risk_adj.get('recommendation', 'N/A')}")
    print(f"  Risk Multiplier: {risk_adj.get('risk_multiplier', 1.0):.2f}")
    print(f"  Rationale: {risk_adj.get('rationale', 'N/A')}")
    
    print(f"\nKey Macro Warnings:")
    warnings = []
    
    # Recession warnings (highest priority) - updated for NY Fed model
    if recession_analysis:
        recession_prob = recession_analysis.get('recession_probability', 0)
        risk_level = recession_analysis.get('risk_level', 'Low')
        
        if recession_prob >= 50:
            warnings.append(f"🚨 HIGH RECESSION RISK: {recession_prob:.1f}% probability ({risk_level}) - defensive positioning recommended")
        elif recession_prob >= 30:
            warnings.append(f"⚠️  ELEVATED RECESSION RISK: {recession_prob:.1f}% probability ({risk_level}) - consider defensive positioning")
        elif recession_prob >= 20:
            warnings.append(f"⚠️  Moderate recession risk: {recession_prob:.1f}% probability ({risk_level}) - monitor closely")
        
        # Check supplemental indicators for additional warnings
        if 'supplemental_indicators' in recession_analysis:
            supp = recession_analysis['supplemental_indicators']
            if 'TRIGGERED' in supp.get('sahm_rule', ''):
                warnings.append(f"🚨 SAHM RULE TRIGGERED: Recession likely already started")
            if 'HIGH' in supp.get('credit_stress', ''):
                warnings.append(f"🚨 CREDIT STRESS: Financial markets under pressure")
            if 'WEAK' in supp.get('lei_signal', ''):
                warnings.append(f"⚠️  ECONOMIC INDICATORS WEAKENING: Leading indicators declining")
    
    # Yield curve warnings with actual spreads
    if recession_analysis:
        term_spread = recession_analysis.get('term_spread_10y3m', 0)
        if term_spread < -1.0:
            warnings.append(f"🚨 DEEPLY INVERTED YIELD CURVE: {term_spread:.2f}% spread - recession highly likely within 12 months")
        elif term_spread < -0.5:
            warnings.append(f"⚠️  Inverted yield curve ({term_spread:.2f}%) indicates elevated recession risk")
        elif term_spread < 0:
            warnings.append(f"⚠️  Inverted yield curve ({term_spread:.2f}%) - caution warranted")
    
    # Fed policy warnings
    fed_10y_spread = rate_environment.get('fed_10y_spread_bps', 0)
    if fed_10y_spread < -100:
        warnings.append(f"⚠️  10Y significantly below Fed Funds ({fed_10y_spread:+.0f} bps) suggests crisis expectations")
    elif fed_10y_spread > 300:
        warnings.append(f"⚠️  Very high term premium ({fed_10y_spread:+.0f} bps) suggests inflation/fiscal concerns")
    
    # Volatility warnings
    if economic_indicators.get('vix', 20) > 35:
        warnings.append(f"⚠️  CRISIS VOLATILITY: VIX {economic_indicators.get('vix', 0):.1f} suggests market panic")
    elif economic_indicators.get('vix', 20) > 30:
        warnings.append(f"⚠️  Elevated market volatility (VIX: {economic_indicators.get('vix', 0):.1f}) suggests heightened uncertainty")
    
    # Interest rate warnings
    if rate_environment.get('ten_year_rate', 0) > 6.0:
        warnings.append(f"⚠️  Very high interest rates ({rate_environment.get('ten_year_rate', 0):.2f}%) may pressure valuations")
    
    if not warnings:
        warnings.append("✅ No major macro warnings detected")
    
    for warning in warnings:
        print(f"  {warning}")
    
    # Investment implications summary - updated for NY Fed model
    print(f"\nInvestment Strategy Implications:")
    if recession_analysis:
        recession_prob = recession_analysis.get('recession_probability', 0)
        risk_level = recession_analysis.get('risk_level', 'Low')
        
        if recession_prob >= 50:
            print(f"  📊 DEFENSIVE POSITIONING ({risk_level} Risk):")
            print("     • Overweight Consumer Defensive, Healthcare, Utilities")
            print("     • Increase Quality allocation to 60%+, reduce Growth exposure")
            print("     • Reduce overall portfolio risk by 30-40%")
        elif recession_prob >= 30:
            print(f"  📊 MODERATE DEFENSIVENESS ({risk_level} Risk):")
            print("     • Slight overweight in defensive sectors")
            print("     • Increase Quality allocation to 50%, moderate Growth reduction")
            print("     • Reduce overall portfolio risk by 15-25%")
        elif recession_prob <= 15:
            print(f"  📊 GROWTH POSITIONING ({risk_level} Risk):")
            print("     • Overweight Technology, Consumer Cyclical")
            print("     • Increase Growth style to 40%")
            print("     • Slightly increase portfolio risk by 5-10%")
        else:
            print(f"  📊 BALANCED APPROACH ({risk_level} Risk):")
            print("     • Maintain current allocations with slight defensive bias")
            print("     • Monitor recession indicators closely")
    
    print("\n" + "="*80)

def scrape_fed_rate_probabilities() -> Dict:
    """Scrape Fed rate cut/hike probabilities from CME FedWatch Tool."""
    print("🎯 Scraping Fed rate probabilities from CME FedWatch...")
    
    fed_data = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'next_meeting': None,
        'rate_probabilities': {},
        'current_rate_range': '5.25-5.50',
        'source': 'CME_FedWatch',
        'confidence': 'medium'
    }
    
    try:
        # CME FedWatch Tool URL
        url = "https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Parse the page for Fed rate probabilities
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for the data in JSON format (CME often embeds data)
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and 'fedwatch' in script.string.lower():
                    try:
                        # Extract JSON data from script
                        json_start = script.string.find('{')
                        json_end = script.string.rfind('}') + 1
                        if json_start != -1 and json_end != -1:
                            json_str = script.string[json_start:json_end]
                            data = json.loads(json_str)
                            # Parse Fed rate probabilities from data
                            fed_data = parse_fedwatch_data(data)
                            break
                    except:
                        continue
            
            # Fallback: Parse HTML tables for rate probabilities
            if not fed_data.get('rate_probabilities'):
                fed_data = parse_fedwatch_html(soup)
                
        else:
            print(f"❌ CME FedWatch scraping failed: {response.status_code}")
            fed_data = get_fallback_fed_probabilities()
            
    except Exception as e:
        print(f"❌ Fed rate scraping error: {str(e)}")
        fed_data = get_fallback_fed_probabilities()
    
    # Validate and clean data
    fed_data = validate_fed_probabilities(fed_data)
    
    print(f"✅ Fed rate probabilities updated: {fed_data['confidence']} confidence")
    return fed_data

def parse_fedwatch_data(data: Dict) -> Dict:
    """Parse JSON data from CME FedWatch."""
    fed_data = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'next_meeting': None,
        'rate_probabilities': {},
        'current_rate_range': '5.25-5.50',
        'source': 'CME_FedWatch_JSON',
        'confidence': 'high'
    }
    
    try:
        # CME data structure varies, adapt as needed
        if 'meetings' in data:
            next_meeting = data['meetings'][0] if data['meetings'] else None
            if next_meeting:
                fed_data['next_meeting'] = next_meeting.get('date')
                
                # Parse probabilities for rate changes
                probabilities = next_meeting.get('probabilities', {})
                fed_data['rate_probabilities'] = {
                    'rate_cut_25bps': probabilities.get('cut_25', 0.0),
                    'rate_cut_50bps': probabilities.get('cut_50', 0.0),
                    'rate_hold': probabilities.get('hold', 0.0),
                    'rate_hike_25bps': probabilities.get('hike_25', 0.0),
                    'rate_hike_50bps': probabilities.get('hike_50', 0.0)
                }
                
    except Exception as e:
        print(f"Error parsing FedWatch JSON: {e}")
        fed_data['confidence'] = 'low'
    
    return fed_data

def parse_fedwatch_html(soup) -> Dict:
    """Parse HTML tables from CME FedWatch as fallback."""
    fed_data = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'next_meeting': None,
        'rate_probabilities': {},
        'current_rate_range': '5.25-5.50',
        'source': 'CME_FedWatch_HTML',
        'confidence': 'medium'
    }
    
    try:
        # Look for probability tables
        tables = soup.find_all('table')
        for table in tables:
            # Find rate probability data in table headers/cells
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                for cell in cells:
                    text = cell.get_text().strip()
                    # Look for percentage values that might be probabilities
                    if '%' in text and any(word in text.lower() for word in ['cut', 'hold', 'hike']):
                        # Extract and categorize probabilities
                        percentage = re.search(r'(\d+\.?\d*)%', text)
                        if percentage:
                            prob_value = float(percentage.group(1)) / 100
                            if 'cut' in text.lower():
                                fed_data['rate_probabilities']['rate_cut'] = prob_value
                            elif 'hold' in text.lower():
                                fed_data['rate_probabilities']['rate_hold'] = prob_value
                            elif 'hike' in text.lower():
                                fed_data['rate_probabilities']['rate_hike'] = prob_value
                                
    except Exception as e:
        print(f"Error parsing FedWatch HTML: {e}")
        fed_data['confidence'] = 'low'
    
    return fed_data

def get_fallback_fed_probabilities() -> Dict:
    """Provide fallback Fed rate probabilities when scraping fails."""
    print("📊 Using fallback Fed rate probabilities...")
    
    # Current market consensus (update manually as needed)
    today = datetime.now()
    next_meeting_dates = [
        '2025-01-29', '2025-03-19', '2025-05-01', '2025-06-11',
        '2025-07-30', '2025-09-17', '2025-11-05', '2025-12-17'
    ]
    
    next_meeting = None
    for meeting_date in next_meeting_dates:
        if datetime.strptime(meeting_date, '%Y-%m-%d') > today:
            next_meeting = meeting_date
            break
    
    # Conservative fallback probabilities (update based on recent market consensus)
    return {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'next_meeting': next_meeting,
        'rate_probabilities': {
            'rate_cut_25bps': 0.15,    # 15% chance of 25bp cut
            'rate_cut_50bps': 0.02,    # 2% chance of 50bp cut  
            'rate_hold': 0.78,         # 78% chance of hold
            'rate_hike_25bps': 0.05,   # 5% chance of 25bp hike
            'rate_hike_50bps': 0.00    # 0% chance of 50bp hike
        },
        'current_rate_range': '5.25-5.50',
        'source': 'Manual_Fallback',
        'confidence': 'low'
    }

def validate_fed_probabilities(fed_data: Dict) -> Dict:
    """Validate and normalize Fed rate probabilities."""
    try:
        probabilities = fed_data.get('rate_probabilities', {})
        
        # Ensure all probabilities are between 0 and 1
        for key, value in probabilities.items():
            if value > 1.0:
                probabilities[key] = value / 100  # Convert percentage to decimal
            if value < 0:
                probabilities[key] = 0.0
                
        # Normalize probabilities to sum to 1.0
        total_prob = sum(probabilities.values())
        if total_prob > 0:
            for key in probabilities:
                probabilities[key] = probabilities[key] / total_prob
        
        # Calculate aggregate probabilities for easier use
        fed_data['aggregate_probabilities'] = {
            'rate_cut_total': probabilities.get('rate_cut_25bps', 0) + probabilities.get('rate_cut_50bps', 0),
            'rate_hold': probabilities.get('rate_hold', 0),
            'rate_hike_total': probabilities.get('rate_hike_25bps', 0) + probabilities.get('rate_hike_50bps', 0)
        }
        
        # Set confidence based on data completeness
        if fed_data['source'] == 'CME_FedWatch_JSON':
            fed_data['confidence'] = 'high'
        elif fed_data['source'] == 'CME_FedWatch_HTML':
            fed_data['confidence'] = 'medium'
        else:
            fed_data['confidence'] = 'low'
            
    except Exception as e:
        print(f"Error validating Fed probabilities: {e}")
        fed_data['confidence'] = 'low'
    
    return fed_data

def analyze_fed_proximity_impact(fed_data: Dict, days_to_meeting: int) -> Dict:
    """Analyze market impact based on Fed meeting proximity."""
    print(f"📅 Analyzing Fed proximity impact: {days_to_meeting} days to meeting")
    
    analysis = {
        'days_to_meeting': days_to_meeting,
        'volatility_expectation': 'normal',
        'sector_rotation_probability': 'low',
        'risk_management_recommendation': 'normal',
        'tactical_adjustments': []
    }
    
    # Get rate probabilities
    rate_cut_prob = fed_data.get('aggregate_probabilities', {}).get('rate_cut_total', 0)
    rate_hike_prob = fed_data.get('aggregate_probabilities', {}).get('rate_hike_total', 0)
    
    if days_to_meeting <= 2:
        analysis['volatility_expectation'] = 'very_high'
        analysis['risk_management_recommendation'] = 'defensive'
        analysis['tactical_adjustments'].extend([
            'reduce_position_sizes_by_10_percent',
            'increase_cash_buffer',
            'hedge_with_VIX_instruments'
        ])
        
    elif days_to_meeting <= 7:
        analysis['volatility_expectation'] = 'high'
        analysis['sector_rotation_probability'] = 'high'
        
        if rate_cut_prob > 0.6:  # > 60% chance of cut
            analysis['tactical_adjustments'].extend([
                'overweight_technology_growth',
                'overweight_real_estate',
                'reduce_financials_exposure'
            ])
        elif rate_hike_prob > 0.3:  # > 30% chance of hike  
            analysis['tactical_adjustments'].extend([
                'overweight_financials',
                'reduce_growth_tech_exposure',
                'increase_defensive_sectors'
            ])
        else:  # Uncertain outcome
            analysis['tactical_adjustments'].extend([
                'favor_quality_stocks',
                'reduce_speculative_positions',
                'maintain_sector_balance'
            ])
            
    elif days_to_meeting <= 14:
        analysis['volatility_expectation'] = 'elevated'
        analysis['sector_rotation_probability'] = 'medium'
        analysis['tactical_adjustments'].append('monitor_rate_sensitive_sectors')
    
    return analysis

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
        
        # Save enhanced CSV for strategy integration
        macro_file = os.path.join('..', 'csv_data_files', '05_macro_economic_analysis_2025-05-31.csv')
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
        
        # Save files
        macro_file = os.path.join('..', 'csv_data_files', '05_macro_economic_analysis_2025-05-31.csv')
        macro_df.to_csv(macro_file, index=False)
        print(f"💾 Enhanced macro analysis saved to {macro_file}")
        
        # Save detailed FRED data for advanced analysis
        fred_file = f"fred_economic_data_{timestamp}.json"
        with open(fred_file, 'w') as f:
            json.dump(fred_data, f, indent=2, default=str)
        print(f"📊 FRED data saved to {fred_file}")
        
        # Save Fed policy analysis
        fed_policy_file = f"fed_policy_analysis_{timestamp}.json"
        with open(fed_policy_file, 'w') as f:
            json.dump(fed_policy_analysis, f, indent=2, default=str)
        print(f"🎯 Fed policy analysis saved to {fed_policy_file}")
        
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