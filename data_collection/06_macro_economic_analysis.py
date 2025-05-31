import pandas as pd
import numpy as np
import os
from datetime import date, datetime, timedelta
import requests
from typing import Dict, List, Tuple
import time
from dotenv import load_dotenv
import json
import re
from bs4 import BeautifulSoup

load_dotenv()
API_KEY = os.getenv("FMP_API_KEY")

def get_treasury_rates() -> Dict:
    """Get current treasury rates from FMP."""
    print("Fetching treasury rates...")
    
    try:
        url = f"https://financialmodelingprep.com/api/v4/treasury?apikey={API_KEY}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                # Get most recent data
                latest = data[0]
                return {
                    'date': latest.get('date'),
                    '3_month': float(latest.get('month3', 0)),
                    '2_year': float(latest.get('year2', 0)),
                    '10_year': float(latest.get('year10', 0)),
                    '30_year': float(latest.get('year30', 0))
                }
        
        print(f"Error fetching treasury rates: {response.status_code}")
        return {}
        
    except Exception as e:
        print(f"Error getting treasury rates: {str(e)}")
        return {}

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
    """Get recession-specific indicators from various sources."""
    print("Fetching recession indicators...")
    
    indicators = {}
    
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
        print(f"Error getting HY spreads: {str(e)}")
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
        print(f"Error getting IG spreads: {str(e)}")
        indicators['ig_spreads'] = 150  # Default assumption
    
    # Unemployment rate (approximate from recent data)
    try:
        # Use DGS10 as a proxy to get FRED-style data structure
        # In production, would use FRED API for unemployment
        indicators['unemployment_rate'] = 4.1  # Approximate current level
        indicators['sahm_indicator'] = 0.2  # Approximate current Sahm rule value
    except Exception as e:
        print(f"Error getting labor data: {str(e)}")
        indicators['unemployment_rate'] = 4.1
        indicators['sahm_indicator'] = 0.2
    
    # Initial jobless claims (approximate)
    indicators['initial_claims_4wk'] = 350000  # Approximate current level
    
    # Leading Economic Index (approximate trend)
    indicators['lei_6m_change'] = -0.5  # Approximate current 6-month change
    
    return indicators

def get_fed_funds_rate() -> float:
    """Get current Fed Funds rate from FMP."""
    try:
        url = f"https://financialmodelingprep.com/api/v4/economic?name=federalFundsRate&apikey={API_KEY}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                return float(data[0].get('value', 5.25))  # Default to recent rate
        
        # Fallback - approximate current rate
        return 5.25
        
    except Exception as e:
        print(f"Error getting Fed Funds rate: {str(e)}")
        return 5.25

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

def calculate_recession_probability(treasury_rates: Dict, recession_indicators: Dict, 
                                  economic_indicators: Dict) -> Dict:
    """Calculate comprehensive recession probability using weighted indicators."""
    print("Calculating recession probability...")
    
    # Extract key metrics
    curve_2s10s_bps = (treasury_rates.get('10_year', 0) - treasury_rates.get('2_year', 0)) * 100
    term_spread_bps = (treasury_rates.get('10_year', 0) - treasury_rates.get('3_month', 0)) * 100
    
    # Tier 1 indicators (60% weight)
    yield_curve_score = 0
    if curve_2s10s_bps < -50:  # Deep inversion
        yield_curve_score = 40
    elif curve_2s10s_bps < -20:  # Inverted
        yield_curve_score = 25
    elif curve_2s10s_bps < 20:  # Flat
        yield_curve_score = 10
    
    # Additional yield curve confirmation
    if term_spread_bps < -30:  # 3m10s deeply inverted
        yield_curve_score = min(yield_curve_score + 15, 45)
    elif term_spread_bps < -10:  # 3m10s inverted
        yield_curve_score = min(yield_curve_score + 8, 40)
    
    lei_score = 0
    lei_6m_change = recession_indicators.get('lei_6m_change', 0)
    if lei_6m_change < -3.0:
        lei_score = 20
    elif lei_6m_change < -2.0:
        lei_score = 15
    elif lei_6m_change < -1.0:
        lei_score = 8
    
    # Tier 2 indicators (30% weight)
    labor_score = 0
    sahm_indicator = recession_indicators.get('sahm_indicator', 0)
    claims_4wk = recession_indicators.get('initial_claims_4wk', 300000)
    
    if sahm_indicator >= 0.5:  # Recession likely started
        labor_score = 15
    elif claims_4wk > 450000:
        labor_score = 10
    elif claims_4wk > 400000:
        labor_score = 5
    
    credit_score = 0
    hy_spreads = recession_indicators.get('hy_spreads', 500)
    ig_spreads = recession_indicators.get('ig_spreads', 150)
    
    if hy_spreads > 800:
        credit_score = 15
    elif hy_spreads > 600:
        credit_score = 10
    elif ig_spreads > 300:
        credit_score = 5
    
    # Tier 3 indicators (10% weight)
    macro_score = 0
    fed_funds_rate = get_fed_funds_rate()
    ten_year_rate = treasury_rates.get('10_year', 0)
    real_fed_rate = fed_funds_rate - 2.5  # Approximate real rate (Fed Funds - inflation target)
    dxy = economic_indicators.get('usd_index', 100)
    
    if real_fed_rate > 4.0:
        macro_score += 5
    if dxy > 110:  # Very strong dollar
        macro_score += 3
    if economic_indicators.get('oil_price', 70) > 120:  # Oil shock
        macro_score += 2
    
    # Calculate total score
    total_score = yield_curve_score + lei_score + labor_score + credit_score + macro_score
    recession_probability = min(total_score, 95)  # Cap at 95%
    
    # Determine confidence level
    if yield_curve_score >= 25 and (labor_score >= 10 or credit_score >= 10):
        confidence = "High"
    elif yield_curve_score >= 10:
        confidence = "Moderate"
    else:
        confidence = "Low"
    
    # Determine time horizon
    if sahm_indicator >= 0.5:
        time_horizon = "0-3 months (likely started)"
    elif curve_2s10s_bps < -30:
        time_horizon = "6-18 months"
    elif curve_2s10s_bps < 0:
        time_horizon = "12-24 months"
    else:
        time_horizon = "24+ months"
    
    return {
        'recession_probability': recession_probability,
        'confidence': confidence,
        'time_horizon': time_horizon,
        'yield_curve_score': yield_curve_score,
        'lei_score': lei_score,
        'labor_score': labor_score,
        'credit_score': credit_score,
        'macro_score': macro_score,
        'key_risks': get_recession_risk_factors(curve_2s10s_bps, term_spread_bps, sahm_indicator, 
                                              hy_spreads, real_fed_rate)
    }

def get_recession_risk_factors(curve_2s10s_bps: float, term_spread_bps: float, 
                              sahm_indicator: float, hy_spreads: float, 
                              real_fed_rate: float) -> List[str]:
    """Identify specific recession risk factors."""
    risks = []
    
    if curve_2s10s_bps < -20:
        risks.append("Inverted 2s10s yield curve")
    if term_spread_bps < -10:
        risks.append("Inverted 3m10s yield curve")
    if sahm_indicator >= 0.3:
        risks.append("Rising unemployment (Sahm Rule trigger)")
    if hy_spreads > 600:
        risks.append("Widening credit spreads")
    if real_fed_rate > 3.0:
        risks.append("Restrictive monetary policy")
    
    return risks

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
        if recession_analysis.get('key_risks'):
            rationale_parts.append(f"Key risks: {', '.join(recession_analysis['key_risks'][:2])}")
    
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
    """Generate comprehensive macro analysis report with recession probability and basis points precision."""
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
    
    print(f"\nRecession Analysis:")
    if recession_analysis:
        print(f"Recession Probability: {recession_analysis.get('recession_probability', 0):.0f}%")
        print(f"Confidence Level: {recession_analysis.get('confidence', 'N/A')}")
        print(f"Time Horizon: {recession_analysis.get('time_horizon', 'N/A')}")
        print(f"Key Risk Factors: {', '.join(recession_analysis.get('key_risks', ['None']))}")
        
        # Breakdown by indicator type
        print(f"\nRecession Indicator Breakdown:")
        print(f"  Yield Curve Score: {recession_analysis.get('yield_curve_score', 0)}/45 points")
        print(f"  Leading Indicators Score: {recession_analysis.get('lei_score', 0)}/20 points")
        print(f"  Labor Market Score: {recession_analysis.get('labor_score', 0)}/15 points")
        print(f"  Credit Market Score: {recession_analysis.get('credit_score', 0)}/15 points")
        print(f"  Macro Environment Score: {recession_analysis.get('macro_score', 0)}/10 points")
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
    
    # Recession warnings (highest priority)
    if recession_analysis:
        recession_prob = recession_analysis.get('recession_probability', 0)
        if recession_prob >= 70:
            warnings.append(f"🚨 HIGH RECESSION RISK: {recession_prob:.0f}% probability - defensive positioning recommended")
        elif recession_prob >= 40:
            warnings.append(f"⚠️  ELEVATED RECESSION RISK: {recession_prob:.0f}% probability - consider defensive positioning")
        elif recession_prob >= 25:
            warnings.append(f"⚠️  Moderate recession risk: {recession_prob:.0f}% probability - monitor closely")
    
    # Yield curve warnings with basis points thresholds
    curve_2s10s_bps = yield_curve.get('curve_2s10s_bps', 50)
    if curve_2s10s_bps < -50:
        warnings.append(f"🚨 DEEPLY INVERTED YIELD CURVE: {curve_2s10s_bps:.0f} bps - recession highly likely within 12-18 months")
    elif curve_2s10s_bps < -20:
        warnings.append(f"⚠️  Inverted yield curve ({curve_2s10s_bps:.0f} bps) indicates elevated recession risk")
    
    # Fed policy warnings
    fed_10y_spread = rate_environment.get('fed_10y_spread_bps', 0)
    if fed_10y_spread < -100:
        warnings.append(f"⚠️  10Y significantly below Fed Funds ({fed_10y_spread:+.0f} bps) suggests crisis expectations")
    elif fed_10y_spread > 300:
        warnings.append(f"⚠️  Very high term premium ({fed_10y_spread:+.0f} bps) suggests inflation/fiscal concerns")
    
    # Credit market warnings
    if recession_analysis:
        hy_spreads = recession_analysis.get('credit_score', 0) * 50 + 400  # Rough approximation
        if hy_spreads > 800:
            warnings.append(f"⚠️  Credit stress detected - high yield spreads indicating financial strain")
    
    # Volatility warnings
    if economic_indicators.get('vix', 20) > 35:
        warnings.append(f"⚠️  CRISIS VOLATILITY: VIX {economic_indicators.get('vix', 0):.1f} suggests market panic")
    elif economic_indicators.get('vix', 20) > 30:
        warnings.append(f"⚠️  Elevated market volatility (VIX: {economic_indicators.get('vix', 0):.1f}) suggests heightened uncertainty")
    
    # Interest rate warnings
    if rate_environment.get('ten_year_rate', 0) > 6.0:
        warnings.append(f"⚠️  Very high interest rates ({rate_environment.get('ten_year_rate', 0):.2f}%) may pressure valuations")
    
    # Labor market warnings
    if recession_analysis and recession_analysis.get('labor_score', 0) >= 10:
        warnings.append(f"⚠️  Labor market deterioration detected - rising unemployment signals")
    
    if not warnings:
        warnings.append("✅ No major macro warnings detected")
    
    for warning in warnings:
        print(f"  {warning}")
    
    # Investment implications summary
    print(f"\nInvestment Strategy Implications:")
    if recession_analysis:
        recession_prob = recession_analysis.get('recession_probability', 0)
        if recession_prob >= 70:
            print("  📊 DEFENSIVE POSITIONING: Overweight Consumer Defensive, Healthcare, Utilities")
            print("  📊 QUALITY FOCUS: Increase Quality allocation to 60%+, reduce Growth exposure")
            print("  📊 RISK REDUCTION: Reduce overall portfolio risk by 40%")
        elif recession_prob >= 40:
            print("  📊 MODERATE DEFENSIVENESS: Slight overweight in defensive sectors")
            print("  📊 QUALITY TILT: Increase Quality allocation to 50%, moderate Growth reduction")
            print("  📊 RISK MANAGEMENT: Reduce overall portfolio risk by 20%")
        elif recession_prob <= 15:
            print("  📊 GROWTH POSITIONING: Overweight Technology, Consumer Cyclical")
            print("  📊 GROWTH ALLOCATION: Increase Growth style to 40%")
            print("  📊 RISK ENHANCEMENT: Slightly increase portfolio risk by 10%")
        else:
            print("  📊 BALANCED APPROACH: Maintain current allocations with slight defensive bias")

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
        print("Starting Macro Economic Analysis...")
        start_time = time.time()
        
        # Collect macro economic data
        print("\n=== STEP 1: Data Collection ===")
        treasury_rates = get_treasury_rates()
        economic_indicators = get_economic_indicators()
        recession_indicators = get_recession_indicators()
        
        # NEW: Scrape Fed rate probabilities
        print("\n=== STEP 2: Fed Rate Analysis ===")
        fed_data = scrape_fed_rate_probabilities()
        
        # Calculate Fed meeting proximity if next meeting exists
        fed_proximity_analysis = None
        if fed_data.get('next_meeting'):
            try:
                next_meeting_date = datetime.strptime(fed_data['next_meeting'], '%Y-%m-%d').date()
                days_to_meeting = (next_meeting_date - datetime.now().date()).days
                fed_proximity_analysis = analyze_fed_proximity_impact(fed_data, days_to_meeting)
            except:
                fed_proximity_analysis = None
        
        print("\n=== STEP 3: Economic Analysis ===")
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
        
        print("\n=== STEP 4: Investment Recommendations ===")
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
        
        print("\n=== STEP 5: Report Generation ===")
        # Generate comprehensive report (updated with Fed data)
        generate_macro_report(
            treasury_rates, economic_indicators, yield_curve, 
            rate_environment, market_regime, recession_analysis,
            sector_recs, style_recs, risk_adj,
            fed_data, fed_proximity_analysis
        )
        
        # Save comprehensive data with Fed integration
        timestamp = datetime.now().strftime('%Y-%m-%d')
        
        # Create comprehensive macro analysis dataset
        macro_data = {
            'analysis_date': timestamp,
            'treasury_rates': treasury_rates,
            'economic_indicators': economic_indicators,
            'recession_indicators': recession_indicators,
            'fed_rate_data': fed_data,
            'fed_proximity_analysis': fed_proximity_analysis,
            'yield_curve_analysis': yield_curve,
            'recession_analysis': recession_analysis,
            'rate_environment': rate_environment,
            'market_regime': market_regime,
            'sector_recommendations': sector_recs,
            'style_recommendations': style_recs,
            'risk_adjustments': risk_adj
        }
        
        # Save as CSV for easy integration
        macro_df = pd.DataFrame([{
            'Date': timestamp,
            'VIX': economic_indicators.get('vix', 0),
            'USD_Index': economic_indicators.get('usd_index', 0),
            'Gold_Price': economic_indicators.get('gold_price', 0),
            'Oil_Price': economic_indicators.get('oil_price', 0),
            '10Y_Treasury': treasury_rates.get('10_year', 0),
            '2Y_Treasury': treasury_rates.get('2_year', 0),
            'Yield_Curve_2s10s': yield_curve.get('curve_2s10s_bps', 0),
            'Recession_Probability': recession_analysis.get('recession_probability', 0),
            'Market_Regime': market_regime.get('overall_regime', 'N/A'),
            'Fed_Rate_Cut_Prob': fed_data.get('aggregate_probabilities', {}).get('rate_cut_total', 0),
            'Fed_Rate_Hold_Prob': fed_data.get('aggregate_probabilities', {}).get('rate_hold', 0),
            'Fed_Rate_Hike_Prob': fed_data.get('aggregate_probabilities', {}).get('rate_hike_total', 0),
            'Days_To_Fed_Meeting': fed_proximity_analysis.get('days_to_meeting', 999) if fed_proximity_analysis else 999,
            'Fed_Data_Confidence': fed_data.get('confidence', 'low'),
            'Recommended_Tech_Weight': sector_recs.get('Technology', {}).get('weight_adjustment', 1.0),
            'Recommended_Healthcare_Weight': sector_recs.get('Healthcare', {}).get('weight_adjustment', 1.0),
            'Recommended_Financials_Weight': sector_recs.get('Financials', {}).get('weight_adjustment', 1.0),
            'Risk_Adjustment_Factor': risk_adj.get('risk_multiplier', 1.0)
        }])
        
        # Save macro analysis data
        macro_file = f"05_macro_economic_analysis_{timestamp}.csv"
        macro_df.to_csv(macro_file, index=False)
        print(f"💾 Macro analysis saved to {macro_file}")
        
        # Save detailed Fed data separately for event-driven system
        fed_file = f"fed_rate_data_{timestamp}.json"
        with open(fed_file, 'w') as f:
            json.dump(macro_data['fed_rate_data'], f, indent=2)
        print(f"🎯 Fed rate data saved to {fed_file}")
        
        # Performance summary
        end_time = time.time()
        duration = end_time - start_time
        print(f"\n✅ Macro Economic Analysis completed in {duration:.1f} seconds")
        
        # Event-driven trigger check
        if fed_proximity_analysis and fed_proximity_analysis.get('days_to_meeting', 999) <= 7:
            print(f"\n🚨 EVENT TRIGGER: Fed meeting in {fed_proximity_analysis['days_to_meeting']} days!")
            print(f"📊 Recommended actions: {', '.join(fed_proximity_analysis.get('tactical_adjustments', []))}")
            
            # Save trigger file for event-driven system
            trigger_data = {
                'trigger_type': 'fed_meeting_proximity',
                'urgency': 'high' if fed_proximity_analysis['days_to_meeting'] <= 2 else 'medium',
                'days_to_meeting': fed_proximity_analysis['days_to_meeting'],
                'recommended_actions': fed_proximity_analysis.get('tactical_adjustments', []),
                'rate_cut_probability': fed_data.get('aggregate_probabilities', {}).get('rate_cut_total', 0),
                'timestamp': datetime.now().isoformat()
            }
            
            with open('event_trigger.json', 'w') as f:
                json.dump(trigger_data, f, indent=2)
            print("🎯 Event trigger saved for automatic reoptimization")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in macro economic analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main() 