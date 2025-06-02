import os
from dotenv import load_dotenv
import requests
import glob
import pandas as pd
from datetime import date, datetime, timedelta
import time
from typing import Dict, Optional, List
from tqdm import tqdm

print("Script started...")

load_dotenv()

API_KEY = os.getenv("FMP_API_KEY")
if not API_KEY:
    raise ValueError("FMP_API_KEY not found in environment variables")

# Optimized for 300 calls/minute = 5 calls/second = 0.2 seconds between calls
RATE_LIMIT_DELAY = 0.2  # Conservative delay for 300 calls/minute
BATCH_SIZE = 20  # Process more symbols at once

def get_latest_sp600_file() -> str:
    """Get the latest S&P 600 holdings CSV file."""
    try:
        pattern = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files', '01_universe_sp600_companies_*.csv')
        files = glob.glob(pattern)
        if not files:
            raise FileNotFoundError("No S&P 600 holdings CSV files found in csv_data_files directory.")
        return max(files, key=os.path.getmtime)
    except Exception as e:
        print(f"Error finding S&P 600 holdings file: {str(e)}")
        raise

def get_momentum_data(ticker: str, api_key: str) -> Dict:
    """Get 3M and 6M momentum data for a ticker."""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)  # 6 months
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?from={start_date.strftime('%Y-%m-%d')}&to={end_date.strftime('%Y-%m-%d')}&apikey={api_key}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error fetching momentum data for {ticker}: {response.text}")
            return {'return_3m': None, 'return_6m': None}
        price_data = response.json().get('historical', [])
        if not price_data:
            return {'return_3m': None, 'return_6m': None}
        current_price = float(price_data[0]['close'])
        price_3m = float(price_data[63]['close']) if len(price_data) > 63 else None  # ~63 trading days in 3 months
        price_6m = float(price_data[-1]['close']) if len(price_data) > 120 else None  # oldest price in 6 months
        return_3m = (current_price - price_3m) / price_3m if price_3m else None
        return_6m = (current_price - price_6m) / price_6m if price_6m else None
        return {'return_3m': return_3m, 'return_6m': return_6m}
    except Exception as e:
        print(f"Error calculating momentum for {ticker}: {str(e)}")
        return {'return_3m': None, 'return_6m': None}

def get_initial_metrics_batch(tickers: List[str], api_key: str) -> List[Dict]:
    """Get initial metrics for multiple tickers in batch."""
    try:
        print(f"\nFetching data for {len(tickers)} tickers in batch...")
        tickers_str = ','.join(tickers)
        
        # Get company profiles
        profile_url = f"https://financialmodelingprep.com/api/v3/profile/{tickers_str}?apikey={api_key}"
        profile_response = requests.get(profile_url)
        if profile_response.status_code != 200:
            print(f"Error fetching profiles: {profile_response.text}")
            return []
        profile_data = profile_response.json()
        if not profile_data:
            print(f"No profile data found")
            return []
            
        # Get key metrics
        metrics_url = f"https://financialmodelingprep.com/api/v3/key-metrics/{tickers_str}?apikey={api_key}"
        metrics_response = requests.get(metrics_url)
        if metrics_response.status_code != 200:
            print(f"Error fetching metrics: {metrics_response.text}")
            return []
        metrics_data = metrics_response.json()
        if not metrics_data:
            print(f"No metrics data found")
            return []
            
        # Get income statements
        income_url = f"https://financialmodelingprep.com/api/v3/income-statement/{tickers_str}?limit=2&apikey={api_key}"
        income_response = requests.get(income_url)
        if income_response.status_code != 200:
            print(f"Error fetching income statements: {income_response.text}")
            return []
        income_data = income_response.json()
        if not income_data:
            print(f"No income statement data found")
            return []
            
        # Get cash flow statements
        cash_flow_url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{tickers_str}?limit=1&apikey={api_key}"
        cash_flow_response = requests.get(cash_flow_url)
        if cash_flow_response.status_code != 200:
            print(f"Error fetching cash flow statements: {cash_flow_response.text}")
            return []
        cash_flow_data = cash_flow_response.json()
        if not cash_flow_data:
            print(f"No cash flow data found")
            return []
            
        results = []
        for ticker in tickers:
            try:
                profile = next((p for p in profile_data if p['symbol'] == ticker), None)
                metrics = next((m for m in metrics_data if m['symbol'] == ticker), None)
                income = next((i for i in income_data if i['symbol'] == ticker), None)
                cash_flow = next((cf for cf in cash_flow_data if cf['symbol'] == ticker), None)
                
                if not all([profile, metrics, income, cash_flow]):
                    print(f"Missing data for {ticker}")
                    continue
                    
                current_revenue = float(income['revenue'])
                previous_revenue = float(income.get('previousRevenue', 0))
                revenue_growth = (current_revenue - previous_revenue) / previous_revenue if previous_revenue != 0 else None
                
                operating_income = float(income['operatingIncome'])
                operating_margin = operating_income / current_revenue if current_revenue != 0 else None
                
                fcf = float(cash_flow['freeCashFlow']) if cash_flow['freeCashFlow'] else None
                
                # Get momentum data
                momentum = get_momentum_data(ticker, api_key)
                
                data = {
                    'Ticker': ticker,
                    'Sector': profile.get('sector', 'Unknown'),
                    'ROIC': float(metrics.get('roic', 0)),
                    'Operating Margin': operating_margin,
                    'Revenue Growth': revenue_growth,
                    'Net Debt to EBITDA': float(metrics.get('netDebtToEBITDA', 0)),
                    'FCF': fcf,
                    'marketCap': float(metrics.get('marketCap', 0)),
                    '3M Return': momentum['return_3m'],
                    '6M Return': momentum['return_6m']
                }
                results.append(data)
                
            except Exception as e:
                print(f"Error processing {ticker}: {str(e)}")
                continue
                
        return results
        
    except Exception as e:
        print(f"Error in batch processing: {str(e)}")
        return []

def get_initial_metrics_single(ticker: str, api_key: str) -> Optional[Dict]:
    """Get initial metrics for a single ticker."""
    try:
        print(f"\nFetching data for {ticker}...")
        
        # Get company profile
        profile_url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={api_key}"
        profile_response = requests.get(profile_url)
        if profile_response.status_code != 200:
            print(f"Error fetching profile for {ticker}")
            return None
        profile_data = profile_response.json()
        if not profile_data:
            print(f"No profile data found for {ticker}")
            return None
            
        # Get key metrics
        metrics_url = f"https://financialmodelingprep.com/api/v3/key-metrics/{ticker}?limit=1&apikey={api_key}"
        metrics_response = requests.get(metrics_url)
        if metrics_response.status_code != 200:
            print(f"Error fetching metrics for {ticker}")
            return None
        metrics_data = metrics_response.json()
        if not metrics_data:
            print(f"No metrics data found for {ticker}")
            return None
            
        # Get income statement
        income_url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?limit=2&apikey={api_key}"
        income_response = requests.get(income_url)
        if income_response.status_code != 200:
            print(f"Error fetching income statement for {ticker}")
            return None
        income_data = income_response.json()
        if not income_data or len(income_data) < 2:
            print(f"Insufficient income statement data for {ticker}")
            return None
            
        # Get cash flow
        cash_flow_url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?limit=1&apikey={api_key}"
        cash_flow_response = requests.get(cash_flow_url)
        if cash_flow_response.status_code != 200:
            print(f"Error fetching cash flow for {ticker}")
            return None
        cash_flow_data = cash_flow_response.json()
        if not cash_flow_data:
            print(f"No cash flow data found for {ticker}")
            return None
            
        profile = profile_data[0]
        metrics = metrics_data[0]
        
        current_revenue = float(income_data[0]['revenue'])
        previous_revenue = float(income_data[1]['revenue'])
        revenue_growth = (current_revenue - previous_revenue) / previous_revenue if previous_revenue != 0 else None
        
        operating_income = float(income_data[0]['operatingIncome'])
        operating_margin = operating_income / current_revenue if current_revenue != 0 else None
        
        fcf = float(cash_flow_data[0]['freeCashFlow']) if cash_flow_data[0]['freeCashFlow'] else None
        
        # Get momentum data
        momentum = get_momentum_data(ticker, api_key)
        
        data = {
            'Ticker': ticker,
            'Sector': profile.get('sector', 'Unknown'),
            'ROIC': float(metrics.get('roic', 0)),
            'Operating Margin': operating_margin,
            'Revenue Growth': revenue_growth,
            'Net Debt to EBITDA': float(metrics.get('netDebtToEBITDA', 0)),
            'FCF': fcf,
            'marketCap': float(metrics.get('marketCap', 0)),
            '3M Return': momentum['return_3m'],
            '6M Return': momentum['return_6m']
        }
        return data
        
    except Exception as e:
        print(f"Error processing {ticker}: {str(e)}")
        return None

def pull_sp600_fundamental_and_momentum(test_mode: bool = False, test_ticker_count: int = 10) -> None:
    try:
        print("Starting S&P 600 data pull...")
        holdings_path = get_latest_sp600_file()
        print(f"Reading holdings from: {holdings_path}")
        
        holdings = pd.read_csv(holdings_path)
        if 'Symbol' not in holdings.columns:
            raise ValueError("Required column 'Symbol' not found in holdings file")
            
        tickers = holdings['Symbol'].dropna().unique().tolist()
        
        if test_mode:
            tickers = tickers[:test_ticker_count]
            print(f"TEST MODE: Processing only {len(tickers)} tickers")
        else:
            print(f"Processing {len(tickers)} tickers")
            
        batch_size = 10
        all_results = []
        
        for i in tqdm(range(0, len(tickers), batch_size)):
            batch = tickers[i:i + batch_size]
            batch_results = get_initial_metrics_batch(batch, API_KEY)
            
            if not batch_results:
                print("Batch processing failed, falling back to individual processing...")
                for ticker in batch:
                    data = get_initial_metrics_single(ticker, API_KEY)
                    if data:
                        all_results.append(data)
                    time.sleep(RATE_LIMIT_DELAY)
            else:
                all_results.extend(batch_results)
                
            if i + batch_size < len(tickers):
                time.sleep(1)  # Rate limiting between batches
                
        if not all_results:
            raise ValueError("No data was collected for any tickers")
            
        df = pd.DataFrame(all_results)
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files')
        os.makedirs(output_dir, exist_ok=True)
        
        # Add date stamp for consistency
        today = date.today().strftime('%Y-%m-%d')
        output_path = os.path.join(output_dir, f"02_fundamentals_with_momentum_{today}.csv")
        
        # Check if file exists and update it, otherwise create new
        if os.path.exists(output_path):
            print(f"Updating existing file: {output_path}")
        else:
            print(f"Creating new file: {output_path}")
        
        # Always overwrite with latest data
        df.to_csv(output_path, index=False)
        print(f"\nData pull complete. File: {output_path}")
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    pull_sp600_fundamental_and_momentum(test_mode=False)  # Run full universe 