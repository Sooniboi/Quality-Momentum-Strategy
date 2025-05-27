import os
from dotenv import load_dotenv
import requests
import glob
import pandas as pd
from datetime import date
import time
import logging
from typing import Dict, Optional, List
import json
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_collection.log'),
        logging.StreamHandler()
    ]
)

load_dotenv()

API_KEY = os.getenv("FMP_API_KEY")
if not API_KEY:
    raise ValueError("FMP_API_KEY not found in environment variables")

# Rate limiting parameters
RATE_LIMIT_CALLS = 300  # Maximum calls per minute
RATE_LIMIT_DELAY = 0.1  # Delay between calls in seconds
last_call_time = 0
call_count = 0
minute_start_time = time.time()

def check_rate_limit():
    global last_call_time, call_count, minute_start_time
    current_time = time.time()
    
    # Reset counter if a minute has passed
    if current_time - minute_start_time >= 60:
        call_count = 0
        minute_start_time = current_time
    
    # Check if we've hit the rate limit
    if call_count >= RATE_LIMIT_CALLS:
        sleep_time = 60 - (current_time - minute_start_time)
        if sleep_time > 0:
            logging.warning(f"Rate limit reached (300 calls per minute). Waiting {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
            call_count = 0
            minute_start_time = time.time()
    
    # Add delay between calls
    if last_call_time > 0:
        time_since_last_call = current_time - last_call_time
        if time_since_last_call < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - time_since_last_call)
    
    last_call_time = time.time()
    call_count += 1

def validate_financial_data(data: Dict) -> bool:
    """Validate the financial data for reasonable ranges and apply strategy rules."""
    if not data:
        return False
        
    # Check for required fields
    required_fields = ['ROE', 'P/B', 'D/E', 'P/E', 'Market Cap', 'Revenue Growth', 'FCF']
    if not all(field in data for field in required_fields):
        return False
        
    try:
        # Convert values to float, handling None values
        pe_ratio = float(data['P/E']) if data['P/E'] is not None else None
        fcf = float(data['FCF']) if data['FCF'] is not None else None
        revenue_growth = float(data['Revenue Growth']) if data['Revenue Growth'] is not None else None
        roe = float(data['ROE']) if data['ROE'] is not None else None
        pb_ratio = float(data['P/B']) if data['P/B'] is not None else None
        de_ratio = float(data['D/E']) if data['D/E'] is not None else None

        # Handle negative P/E ratios according to strategy
        if pe_ratio is not None and pe_ratio < 0:
            # Check if company qualifies as "unprofitable momentum play"
            qualifies = False
            
            # Check for strong FCF
            if fcf is not None and fcf > 0:
                logging.info(f"{data['Ticker']} has negative P/E but positive FCF: {fcf}")
                qualifies = True
                
            # Check for high revenue growth
            if revenue_growth is not None and revenue_growth > 0.25:  # 25% growth threshold
                logging.info(f"{data['Ticker']} has negative P/E but high revenue growth: {revenue_growth}")
                qualifies = True
                
            # Check for strong ROE
            if roe is not None and roe > 0.15:  # 15% ROE threshold
                logging.info(f"{data['Ticker']} has negative P/E but strong ROE: {roe}")
                qualifies = True
                
            if not qualifies:
                logging.warning(f"{data['Ticker']} rejected: Negative P/E ({pe_ratio}) without qualifying metrics")
                return False
            else:
                logging.info(f"{data['Ticker']} accepted as unprofitable momentum play")
                
        # Validate other metrics
        if pb_ratio is not None and not 0 <= pb_ratio <= 100:
            logging.warning(f"P/B value {pb_ratio} outside expected range for {data['Ticker']}")
            return False
            
        if de_ratio is not None and not 0 <= de_ratio <= 100:
            logging.warning(f"D/E value {de_ratio} outside expected range for {data['Ticker']}")
            return False
            
        # For positive P/E ratios, maintain reasonable upper limit
        if pe_ratio is not None and pe_ratio > 0 and pe_ratio > 1000:
            logging.warning(f"P/E value {pe_ratio} too high for {data['Ticker']}")
            return False
            
    except (ValueError, TypeError) as e:
        logging.error(f"Error validating data for {data['Ticker']}: {str(e)}")
        return False
        
    return True

def make_api_request(url: str, ticker: str) -> Optional[dict]:
    """Make API request with retry logic and rate limiting."""
    if not check_rate_limit():
        logging.error(f"Cannot make API request for {ticker} - rate limit reached")
        return None

    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(RATE_LIMIT_DELAY)  # Rate limiting
            response = requests.get(url)
            
            if response.status_code == 429:  # Rate limit exceeded
                wait_time = RETRY_DELAY * (attempt + 1)
                logging.warning(f"Rate limit exceeded for {ticker}. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed for {ticker} (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")
            if attempt == MAX_RETRIES - 1:
                return None
            time.sleep(RETRY_DELAY)
            
    return None

def get_fmp_fundamentals(ticker: str, api_key: str) -> Optional[Dict]:
    logging.info(f"Fetching fundamentals for {ticker}...")
    result = {
        'Ticker': ticker,
        'ROE': None,
        'P/B': None,
        'D/E': None,
        'P/E': None,
        'Market Cap': None,
        'Revenue Growth': None,
        'FCF': None,
        'Category': 'Standard'  # New field to track company category
    }

    # Key metrics TTM
    url_key = f"https://financialmodelingprep.com/api/v3/key-metrics-ttm/{ticker}?apikey={api_key}"
    data = make_api_request(url_key, ticker)
    if data:
        data = data[0] if data else None
        if data:
            result.update({
                'ROE': data.get('roeTTM'),
                'P/B': data.get('pbRatioTTM'),
                'D/E': data.get('debtToEquityTTM'),
                'P/E': data.get('peRatioTTM'),
                'Market Cap': data.get('marketCapTTM'),
                'FCF': data.get('freeCashFlowPerShareTTM')
            })

    # Revenue Growth
    url_rev = f"https://financialmodelingprep.com/api/v3/income-statement-growth/{ticker}?apikey={api_key}"
    data = make_api_request(url_rev, ticker)
    if data:
        result['Revenue Growth'] = data[0].get('growthRevenue') if data else None

    # Free Cash Flow
    url_fcf = f"https://financialmodelingprep.com/api/v3/cash-flow-statement-ttm/{ticker}?apikey={api_key}"
    data = make_api_request(url_fcf, ticker)
    if data:
        result['FCF'] = data[0].get('freeCashFlow') if data else None

    # Determine company category
    if result['P/E'] is not None and float(result['P/E']) < 0:
        if (result['FCF'] is not None and float(result['FCF']) > 0) or \
           (result['Revenue Growth'] is not None and float(result['Revenue Growth']) > 0.25) or \
           (result['ROE'] is not None and float(result['ROE']) > 0.15):
            result['Category'] = 'Unprofitable Momentum'
        else:
            result['Category'] = 'Rejected'

    if validate_financial_data(result):
        return result
    return None

def get_latest_iwm_file() -> str:
    pattern = os.path.join(os.path.dirname(__file__), '..', 'data', 'universe', 'iwm_holdings_*.csv')
    logging.info(f"Looking for IWM holdings files matching pattern: {pattern}")
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError("No IWM holdings CSV files found.")
    latest_file = max(files, key=os.path.getmtime)
    logging.info(f"Found latest IWM holdings file: {latest_file}")
    return latest_file

def backup_existing_file(file_path: str) -> None:
    """Create a backup of existing file if it exists."""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.bak"
        try:
            os.rename(file_path, backup_path)
            logging.info(f"Created backup of existing file: {backup_path}")
        except Exception as e:
            logging.error(f"Failed to create backup: {str(e)}")

def pull_fundamentals_from_iwm_holdings() -> None:
    try:
        logging.info("Starting fundamentals pull process...")
        holdings_path = get_latest_iwm_file()
        logging.info(f"Reading holdings from: {holdings_path}")
        
        holdings = pd.read_csv(holdings_path)
        if 'Ticker' not in holdings.columns:
            raise ValueError("Required column 'Ticker' not found in holdings file")
            
        tickers = holdings['Ticker'].dropna().unique().tolist()
        logging.info(f"Found {len(tickers)} unique tickers")
        
        # Calculate estimated API calls needed
        estimated_calls = len(tickers) * 3  # 3 API calls per ticker
        if estimated_calls > RATE_LIMIT_CALLS:
            logging.warning(f"Warning: Estimated API calls ({estimated_calls}) exceeds rate limit ({RATE_LIMIT_CALLS})")
            logging.warning("Consider processing tickers in batches across multiple days")

        fundamentals_list = []
        for ticker in tickers:
            data = get_fmp_fundamentals(ticker, API_KEY)
            if data:
                fundamentals_list.append(data)
            else:
                logging.warning(f"Failed to get data for {ticker}")

        if not fundamentals_list:
            raise ValueError("No fundamental data was collected for any tickers")

        df = pd.DataFrame(fundamentals_list)
        logging.info(f"Created DataFrame with {len(df)} rows")
        logging.info(f"API calls made today: {call_count}")

        output_dir = os.path.dirname(__file__)
        today = date.today().strftime('%Y-%m-%d')
        output_path = os.path.join(output_dir, f"iwm_fundamentals_{today}.csv")
        
        # Backup existing file if it exists
        backup_existing_file(output_path)
        
        df.to_csv(output_path, index=False)
        logging.info(f"Fundamentals successfully saved to: {output_path}")
            
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    pull_fundamentals_from_iwm_holdings()