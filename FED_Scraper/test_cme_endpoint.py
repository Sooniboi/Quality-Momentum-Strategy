#!/usr/bin/env python3
"""
Simple test script for CME FedWatch endpoint
"""

import requests
import json
from datetime import datetime

def test_cme_endpoint():
    """Test CME FedWatch JSON endpoint"""
    
    print("Testing CME FedWatch JSON endpoint...")
    
    # Test with next FOMC meeting date (June 18, 2025)
    url = "https://www.cmegroup.com/CmeWS/mvc/FedWatchTool/targetRateData"
    params = {
        'eventDate': '20250618',  # June 18, 2025 FOMC meeting
        'unit': '0'  # 0 for Fed Funds, 1 for SOFR
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html'
    }
    
    try:
        print(f"URL: {url}")
        print(f"Params: {params}")
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("\n✅ SUCCESS! CME data received:")
                print(json.dumps(data, indent=2))
                
                # Parse probabilities
                if 'targetRateProbabilities' in data:
                    print(f"\n📊 Rate Probabilities for June 18, 2025 FOMC:")
                    for prob in data['targetRateProbabilities']:
                        rate = prob.get('targetRate', 'Unknown')
                        probability = prob.get('probability', 0)
                        print(f"  {rate}: {probability}%")
                
                return True
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"Raw response: {response.text[:500]}...")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout - CME server may be slow")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_alternative_approach():
    """Test alternative approach for getting Fed data"""
    
    print("\n" + "="*50)
    print("TESTING ALTERNATIVE APPROACHES")
    print("="*50)
    
    # Test 1: Direct CME market data page
    try:
        print("\n1. Testing CME main page accessibility...")
        response = requests.get("https://www.cmegroup.com", timeout=10)
        print(f"CME main page: {response.status_code}")
    except Exception as e:
        print(f"CME main page error: {e}")
    
    # Test 2: Check if we can access FRED without API key
    try:
        print("\n2. Testing FRED accessibility...")
        fred_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS&cosd=2024-01-01"
        response = requests.get(fred_url, timeout=10)
        print(f"FRED data: {response.status_code}")
        if response.status_code == 200:
            print("✅ FRED data accessible!")
            lines = response.text.split('\n')[:5]
            for line in lines:
                print(f"  {line}")
    except Exception as e:
        print(f"FRED error: {e}")
    
    # Test 3: Test a working financial API
    try:
        print("\n3. Testing alternative financial data source...")
        # Using a free financial API as test
        test_url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(test_url, timeout=10)
        print(f"Exchange rate API: {response.status_code}")
        if response.status_code == 200:
            print("✅ Alternative financial APIs working!")
    except Exception as e:
        print(f"Alternative API error: {e}")

if __name__ == "__main__":
    print("🔍 CME FEDWATCH ENDPOINT TESTER")
    print("="*40)
    
    success = test_cme_endpoint()
    
    if not success:
        test_alternative_approach()
        
        print("\n💡 RECOMMENDATIONS:")
        print("1. Check your internet connection")
        print("2. Try running this script at different times (CME servers may be busy)")
        print("3. Consider using FRED API with a free API key")
        print("4. The fallback mode in the integration module will work without external data")
    else:
        print("\n🎉 CME endpoint is working! Your enhanced Fed scraper should work perfectly.") 