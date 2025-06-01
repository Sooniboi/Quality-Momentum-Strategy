#!/usr/bin/env python3
"""
Test script to demonstrate FRED API Fed data capabilities
"""

from fredapi import Fred
import pandas as pd
from datetime import datetime
import requests

def test_fred_without_key():
    """Test what we can get from FRED without API key"""
    print("🔍 TESTING FRED DATA ACCESS (No API Key)")
    print("="*50)
    
    # We can access some FRED data via CSV download
    fred_endpoints = {
        'Fed Funds Rate': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS&cosd=2024-01-01',
        'Unemployment Rate': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE&cosd=2024-01-01',
        'Core PCE Inflation': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=PCEPILFE&cosd=2024-01-01',
        '10Y Treasury': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=GS10&cosd=2024-01-01',
        '2Y Treasury': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=GS2&cosd=2024-01-01'
    }
    
    for name, url in fred_endpoints.items():
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                if len(lines) >= 2:
                    latest_line = lines[-1].split(',')
                    if len(latest_line) >= 2:
                        date, value = latest_line[0], latest_line[1]
                        if value != '.':  # FRED uses '.' for missing data
                            print(f"✅ {name}: {value}% (as of {date})")
                        else:
                            print(f"⚠️ {name}: No recent data")
                    else:
                        print(f"❌ {name}: Invalid data format")
                else:
                    print(f"❌ {name}: No data available")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Error - {str(e)}")
    
    print("\n💡 With a free FRED API key, you get:")
    print("• Real-time updates")
    print("• Historical data")
    print("• Programmatic access")
    print("• 120 requests per minute")
    print("• All Fed economic indicators")

def test_fred_with_key(api_key):
    """Test FRED API with actual key"""
    print(f"\n🔑 TESTING FRED API WITH KEY")
    print("="*50)
    
    try:
        fred = Fred(api_key=api_key)
        
        # Key Fed indicators
        fed_indicators = {
            'Effective Fed Funds Rate': 'FEDFUNDS',
            'Fed Target Rate (Upper)': 'DFEDTARU', 
            'Fed Target Rate (Lower)': 'DFEDTARL',
            'Unemployment Rate': 'UNRATE',
            'Core PCE Inflation': 'PCEPILFE',
            'PCE Inflation': 'PCEPI',
            'CPI Inflation': 'CPIAUCSL',
            '10-Year Treasury': 'GS10',
            '2-Year Treasury': 'GS2',
            '3-Month Treasury': 'GS3M',
            'Consumer Sentiment': 'UMCSENT',
            'Nonfarm Payrolls': 'PAYEMS'
        }
        
        print("📊 CURRENT FED & ECONOMIC DATA:")
        print("-" * 50)
        
        for name, series_id in fed_indicators.items():
            try:
                # Get latest value
                series = fred.get_series(series_id, limit=3)
                if not series.empty:
                    latest_value = series.iloc[-1]
                    latest_date = series.index[-1].strftime('%Y-%m-%d')
                    
                    # Calculate month-over-month change if possible
                    mom_change = ""
                    if len(series) >= 2:
                        prev_value = series.iloc[-2]
                        if prev_value != 0:
                            change = ((latest_value - prev_value) / prev_value) * 100
                            mom_change = f" ({change:+.1f}% MoM)"
                    
                    # Format value based on indicator type
                    if 'Rate' in name or 'Treasury' in name or 'Inflation' in name:
                        value_str = f"{latest_value:.2f}%"
                    elif 'Payrolls' in name:
                        value_str = f"{latest_value:,.0f}K"
                    elif 'Sentiment' in name:
                        value_str = f"{latest_value:.1f}"
                    else:
                        value_str = f"{latest_value:.2f}"
                    
                    print(f"✅ {name:<25}: {value_str:<8} ({latest_date}){mom_change}")
                else:
                    print(f"❌ {name:<25}: No data available")
                    
            except Exception as e:
                print(f"❌ {name:<25}: Error - {str(e)}")
        
        # Test Fed policy analysis
        print(f"\n🎯 FED POLICY ANALYSIS:")
        print("-" * 50)
        
        try:
            # Get current Fed data
            fed_funds = fred.get_series('FEDFUNDS', limit=1).iloc[-1]
            fed_upper = fred.get_series('DFEDTARU', limit=1).iloc[-1] 
            fed_lower = fred.get_series('DFEDTARL', limit=1).iloc[-1]
            unemployment = fred.get_series('UNRATE', limit=1).iloc[-1]
            core_pce = fred.get_series('PCEPILFE', limit=1).iloc[-1]
            
            print(f"Current Fed Funds Rate: {fed_funds:.2f}%")
            print(f"Fed Target Range: {fed_lower:.2f}% - {fed_upper:.2f}%")
            
            # Policy stance analysis
            print(f"\n📈 POLICY STANCE INDICATORS:")
            
            # Dual mandate assessment
            if unemployment < 4.0:
                employment_signal = "🟢 Strong employment (below 4%)"
            elif unemployment > 5.0:
                employment_signal = "🔴 Weak employment (above 5%)"
            else:
                employment_signal = "🟡 Moderate employment"
            
            if core_pce > 2.5:
                inflation_signal = "🔴 Inflation above target (>2.5%)"
            elif core_pce < 1.5:
                inflation_signal = "🔵 Inflation below target (<1.5%)"
            else:
                inflation_signal = "🟢 Inflation near target"
            
            print(f"Employment Mandate: {employment_signal}")
            print(f"Price Stability: {inflation_signal}")
            
            # Policy bias prediction
            hawkish_signals = 0
            dovish_signals = 0
            
            if unemployment < 3.5:
                hawkish_signals += 1
            if unemployment > 5.0:
                dovish_signals += 1
            if core_pce > 2.5:
                hawkish_signals += 1
            if core_pce < 1.5:
                dovish_signals += 1
            
            if hawkish_signals > dovish_signals:
                policy_bias = "🔴 HAWKISH (rate hike pressure)"
            elif dovish_signals > hawkish_signals:
                policy_bias = "🔵 DOVISH (rate cut pressure)"
            else:
                policy_bias = "🟡 NEUTRAL"
            
            print(f"Policy Bias: {policy_bias}")
            
        except Exception as e:
            print(f"Error in policy analysis: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ FRED API Error: {str(e)}")
        return False

def demonstrate_fred_capabilities():
    """Show what's possible with FRED"""
    print(f"\n🚀 FRED API CAPABILITIES FOR FED DATA")
    print("="*50)
    
    capabilities = {
        "Real-Time Fed Data": [
            "• Effective Federal Funds Rate (daily updates)",
            "• Fed Target Rate Range (upper & lower bounds)", 
            "• FOMC meeting dates and decisions",
            "• Fed policy statements analysis"
        ],
        "Economic Indicators": [
            "• Unemployment rate (monthly)",
            "• PCE & Core PCE inflation (monthly)",
            "• CPI inflation (monthly)",
            "• Nonfarm payrolls (monthly)"
        ],
        "Treasury & Yield Curve": [
            "• 3-month, 2-year, 10-year, 30-year rates",
            "• Daily yield curve data",
            "• Term spreads and inversions",
            "• Real yields (TIPS)"
        ],
        "Market Sentiment": [
            "• Consumer sentiment (University of Michigan)",
            "• Business sentiment indicators",
            "• Financial conditions indices"
        ],
        "Advanced Features": [
            "• Historical data back to 1950s",
            "• Real-time data transformations",
            "• Economic nowcasting indicators",
            "• Regional Fed district data"
        ]
    }
    
    for category, items in capabilities.items():
        print(f"\n📊 {category}:")
        for item in items:
            print(f"   {item}")
    
    print(f"\n💰 COST: Completely FREE")
    print(f"📈 RATE LIMITS: 120 requests/minute")
    print(f"🔄 UPDATES: Real-time (some daily, some monthly)")
    print(f"📚 DATA QUALITY: Official Federal Reserve data")

def main():
    """Main test function"""
    print("🏦 FRED API FED DATA TESTING")
    print("="*60)
    
    # Test without API key first
    test_fred_without_key()
    
    # Show capabilities
    demonstrate_fred_capabilities()
    
    print(f"\n🎯 NEXT STEPS:")
    print("1. Get your free FRED API key: https://fred.stlouisfed.org/docs/api/api_key.html")
    print("2. Add it to your enhanced_fed_scraper.py")
    print("3. Run: python enhanced_fed_scraper.py")
    print("4. Get real-time Fed data for your Quality Momentum Strategy!")
    
    # If they want to test with an actual key
    print(f"\n🔑 TO TEST WITH API KEY:")
    print("Edit this file and add your API key to test_fred_with_key('your_key_here')")

if __name__ == "__main__":
    main()
    
    # Uncomment and add your key to test:
    # test_fred_with_key('your_fred_api_key_here') 