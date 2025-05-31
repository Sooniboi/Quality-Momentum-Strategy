import pandas as pd
import numpy as np
import os
from datetime import date, datetime, timedelta
import requests
from typing import Dict, List, Tuple
import time
from dotenv import load_dotenv

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

def calculate_yield_curve_metrics(treasury_rates: Dict) -> Dict:
    """Calculate yield curve metrics and interpret them."""
    if not treasury_rates:
        return {}
    
    # Yield curve slope (10Y - 2Y)
    yield_curve_slope = treasury_rates.get('10_year', 0) - treasury_rates.get('2_year', 0)
    
    # Term spread (10Y - 3M)
    term_spread = treasury_rates.get('10_year', 0) - treasury_rates.get('3_month', 0)
    
    # Classify yield curve shape
    if yield_curve_slope > 1.0:
        curve_shape = "Steep"
    elif yield_curve_slope > 0.2:
        curve_shape = "Normal"
    elif yield_curve_slope > -0.2:
        curve_shape = "Flat"
    else:
        curve_shape = "Inverted"
    
    return {
        'yield_curve_slope': yield_curve_slope,
        'term_spread': term_spread,
        'curve_shape': curve_shape,
        'recession_risk': 'High' if yield_curve_slope < 0 else 'Low'
    }

def classify_interest_rate_environment(treasury_rates: Dict) -> Dict:
    """Classify the interest rate environment."""
    if not treasury_rates:
        return {}
    
    ten_year_rate = treasury_rates.get('10_year', 0)
    
    # Historical context for 10-year rates
    if ten_year_rate < 2.0:
        rate_environment = "Very Low"
        growth_vs_value = "Favor Growth"
    elif ten_year_rate < 3.5:
        rate_environment = "Low"
        growth_vs_value = "Slight Growth Tilt"
    elif ten_year_rate < 5.0:
        rate_environment = "Moderate"
        growth_vs_value = "Neutral"
    elif ten_year_rate < 6.5:
        rate_environment = "High"
        growth_vs_value = "Favor Value"
    else:
        rate_environment = "Very High"
        growth_vs_value = "Strong Value Tilt"
    
    return {
        'rate_environment': rate_environment,
        'ten_year_rate': ten_year_rate,
        'growth_vs_value': growth_vs_value
    }

def classify_market_regime(economic_indicators: Dict, yield_curve: Dict) -> Dict:
    """Classify the overall market regime."""
    vix = economic_indicators.get('vix', 20)
    curve_shape = yield_curve.get('curve_shape', 'Normal')
    
    # Market volatility assessment
    if vix < 15:
        volatility_regime = "Low Volatility"
        risk_appetite = "High"
    elif vix < 25:
        volatility_regime = "Normal Volatility"
        risk_appetite = "Moderate"
    elif vix < 35:
        volatility_regime = "High Volatility"
        risk_appetite = "Low"
    else:
        volatility_regime = "Crisis Volatility"
        risk_appetite = "Very Low"
    
    # Economic cycle assessment
    if curve_shape == "Inverted":
        economic_cycle = "Late Cycle/Recession Risk"
    elif curve_shape == "Steep":
        economic_cycle = "Early/Mid Cycle"
    else:
        economic_cycle = "Mid Cycle"
    
    return {
        'volatility_regime': volatility_regime,
        'risk_appetite': risk_appetite,
        'economic_cycle': economic_cycle,
        'overall_regime': f"{economic_cycle} - {volatility_regime}"
    }

def generate_sector_recommendations(rate_environment: Dict, market_regime: Dict, yield_curve: Dict) -> Dict:
    """Generate sector weight adjustments based on macro conditions."""
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
    
    # Interest rate adjustments
    growth_vs_value = rate_environment.get('growth_vs_value', 'Neutral')
    
    if 'Growth' in growth_vs_value:
        # Favor growth sectors in low rate environment
        adjusted_weights['Technology'] *= 1.3
        adjusted_weights['Healthcare'] *= 1.2
        adjusted_weights['Communication Services'] *= 1.2
        adjusted_weights['Financial Services'] *= 0.8
        adjusted_weights['Real Estate'] *= 0.7
        adjusted_weights['Utilities'] *= 0.7
    elif 'Value' in growth_vs_value:
        # Favor value sectors in high rate environment
        adjusted_weights['Financial Services'] *= 1.4
        adjusted_weights['Energy'] *= 1.3
        adjusted_weights['Basic Materials'] *= 1.2
        adjusted_weights['Technology'] *= 0.8
        adjusted_weights['Real Estate'] *= 0.8
    
    # Yield curve adjustments
    curve_shape = yield_curve.get('curve_shape', 'Normal')
    
    if curve_shape == "Steep":
        # Steep curve favors financials
        adjusted_weights['Financial Services'] *= 1.2
    elif curve_shape == "Inverted":
        # Inverted curve - defensive positioning
        adjusted_weights['Consumer Defensive'] *= 1.3
        adjusted_weights['Healthcare'] *= 1.2
        adjusted_weights['Utilities'] *= 1.2
        adjusted_weights['Consumer Cyclical'] *= 0.7
        adjusted_weights['Energy'] *= 0.8
    
    # Volatility adjustments
    risk_appetite = market_regime.get('risk_appetite', 'Moderate')
    
    if risk_appetite == 'Low' or risk_appetite == 'Very Low':
        # Defensive positioning in high volatility
        adjusted_weights['Healthcare'] *= 1.2
        adjusted_weights['Consumer Defensive'] *= 1.3
        adjusted_weights['Utilities'] *= 1.2
        adjusted_weights['Technology'] *= 0.8
        adjusted_weights['Consumer Cyclical'] *= 0.7
    elif risk_appetite == 'High':
        # Risk-on positioning
        adjusted_weights['Technology'] *= 1.2
        adjusted_weights['Consumer Cyclical'] *= 1.2
        adjusted_weights['Energy'] *= 1.1
        adjusted_weights['Utilities'] *= 0.8
        adjusted_weights['Consumer Defensive'] *= 0.8
    
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

def generate_style_recommendations(rate_environment: Dict, market_regime: Dict) -> Dict:
    """Generate style allocation adjustments based on macro conditions."""
    # Base case style allocation
    base_allocation = {
        'Quality': 0.40,
        'Growth': 0.30,
        'Value': 0.20,
        'Blend': 0.10
    }
    
    adjusted_allocation = base_allocation.copy()
    
    # Interest rate adjustments
    growth_vs_value = rate_environment.get('growth_vs_value', 'Neutral')
    
    if 'Growth' in growth_vs_value:
        adjusted_allocation['Growth'] += 0.10
        adjusted_allocation['Value'] -= 0.05
        adjusted_allocation['Blend'] -= 0.05
    elif 'Value' in growth_vs_value:
        adjusted_allocation['Value'] += 0.15
        adjusted_allocation['Growth'] -= 0.10
        adjusted_allocation['Blend'] -= 0.05
    
    # Risk appetite adjustments
    risk_appetite = market_regime.get('risk_appetite', 'Moderate')
    
    if risk_appetite in ['Low', 'Very Low']:
        # Increase quality allocation in uncertain times
        adjusted_allocation['Quality'] += 0.10
        adjusted_allocation['Growth'] -= 0.05
        adjusted_allocation['Blend'] -= 0.05
    elif risk_appetite == 'High':
        # Increase growth allocation in risk-on environment
        adjusted_allocation['Growth'] += 0.05
        adjusted_allocation['Quality'] -= 0.05
    
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

def generate_risk_adjustments(market_regime: Dict, economic_indicators: Dict) -> Dict:
    """Generate portfolio risk level adjustments based on macro conditions."""
    vix = economic_indicators.get('vix', 20)
    risk_appetite = market_regime.get('risk_appetite', 'Moderate')
    
    # Base portfolio risk level (1.0 = normal)
    base_risk_level = 1.0
    
    # Adjust based on volatility regime
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
    
    return {
        'risk_multiplier': risk_multiplier,
        'recommendation': recommendation,
        'vix_level': vix,
        'rationale': f"VIX at {vix:.1f} indicates {market_regime.get('volatility_regime', 'normal')} market conditions"
    }

def generate_macro_report(treasury_rates: Dict, economic_indicators: Dict, 
                         yield_curve: Dict, rate_environment: Dict, 
                         market_regime: Dict, sector_recs: Dict, 
                         style_recs: Dict, risk_adj: Dict) -> None:
    """Generate comprehensive macro analysis report."""
    print("\n" + "="*80)
    print("MACRO ECONOMIC ANALYSIS REPORT")
    print("="*80)
    
    print(f"\nCurrent Market Conditions:")
    print(f"Date: {treasury_rates.get('date', 'N/A')}")
    print(f"10-Year Treasury: {treasury_rates.get('10_year', 0):.2f}%")
    print(f"2-Year Treasury: {treasury_rates.get('2_year', 0):.2f}%")
    print(f"Yield Curve Slope: {yield_curve.get('yield_curve_slope', 0):.2f}%")
    print(f"Curve Shape: {yield_curve.get('curve_shape', 'N/A')}")
    print(f"VIX: {economic_indicators.get('vix', 0):.1f}")
    
    print(f"\nMacro Regime Classification:")
    print(f"Interest Rate Environment: {rate_environment.get('rate_environment', 'N/A')}")
    print(f"Economic Cycle: {market_regime.get('economic_cycle', 'N/A')}")
    print(f"Volatility Regime: {market_regime.get('volatility_regime', 'N/A')}")
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
    
    if yield_curve.get('recession_risk') == 'High':
        warnings.append("⚠️  Inverted yield curve indicates elevated recession risk")
    
    if economic_indicators.get('vix', 20) > 30:
        warnings.append("⚠️  Elevated market volatility suggests heightened uncertainty")
    
    if rate_environment.get('ten_year_rate', 0) > 5.0:
        warnings.append("⚠️  High interest rates may pressure valuations")
    
    if not warnings:
        warnings.append("✅ No major macro warnings detected")
    
    for warning in warnings:
        print(f"  {warning}")

def main():
    try:
        print("Starting macro economic analysis...")
        
        # Collect macro data
        treasury_rates = get_treasury_rates()
        economic_indicators = get_economic_indicators()
        
        # Analyze macro conditions
        yield_curve = calculate_yield_curve_metrics(treasury_rates)
        rate_environment = classify_interest_rate_environment(treasury_rates)
        market_regime = classify_market_regime(economic_indicators, yield_curve)
        
        # Generate recommendations
        sector_recommendations = generate_sector_recommendations(rate_environment, market_regime, yield_curve)
        style_recommendations = generate_style_recommendations(rate_environment, market_regime)
        risk_adjustments = generate_risk_adjustments(market_regime, economic_indicators)
        
        # Generate report
        generate_macro_report(
            treasury_rates, economic_indicators, yield_curve, 
            rate_environment, market_regime, sector_recommendations,
            style_recommendations, risk_adjustments
        )
        
        # Save macro analysis results
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files')
        today = date.today().strftime('%Y-%m-%d')
        
        macro_summary = {
            'analysis_date': today,
            'ten_year_rate': treasury_rates.get('10_year', 0),
            'yield_curve_slope': yield_curve.get('yield_curve_slope', 0),
            'curve_shape': yield_curve.get('curve_shape', 'N/A'),
            'vix': economic_indicators.get('vix', 0),
            'rate_environment': rate_environment.get('rate_environment', 'N/A'),
            'market_regime': market_regime.get('overall_regime', 'N/A'),
            'risk_multiplier': risk_adjustments.get('risk_multiplier', 1.0)
        }
        
        macro_df = pd.DataFrame([macro_summary])
        macro_path = os.path.join(output_dir, f"macro_analysis_{today}.csv")
        macro_df.to_csv(macro_path, index=False)
        print(f"\nMacro analysis saved to: {macro_path}")
        
        return {
            'sector_recommendations': sector_recommendations,
            'style_recommendations': style_recommendations,
            'risk_adjustments': risk_adjustments,
            'treasury_rates': treasury_rates,
            'market_regime': market_regime
        }
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main() 