import os
from dotenv import load_dotenv
import requests
import glob
import pandas as pd
from datetime import date, datetime
import time
from typing import Dict, Optional, List
import json
from datetime import timedelta
from tqdm import tqdm  # Import tqdm for progress bar

print("Script started...")

load_dotenv()

API_KEY = os.getenv("FMP_API_KEY")
if not API_KEY:
    raise ValueError("FMP_API_KEY not found in environment variables")

RATE_LIMIT_CALLS = 300  # Maximum calls per minute
RATE_LIMIT_DELAY = 0.1  # Delay between calls in seconds
last_call_time = 0
call_count = 0
minute_start_time = time.time()

def get_latest_sp600_file() -> str:
    """Get the latest S&P 600 holdings CSV file."""
    pattern = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files', 'sp600_holdings_*.csv')
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError("No S&P 600 holdings CSV files found in csv_data_files directory.")
    return max(files, key=os.path.getmtime)

def get_initial_metrics_batch(tickers: List[str], api_key: str) -> List[Dict]:
    """Get initial metrics for multiple tickers in batch."""
    try:
        print(f"\nFetching data for {len(tickers)} tickers in batch...")
        
        # Convert tickers list to comma-separated string
        tickers_str = ','.join(tickers)
        
        # Get company profiles in batch
        profile_url = f"https://financialmodelingprep.com/api/v3/profile/{tickers_str}?apikey={api_key}"
        profile_response = requests.get(profile_url)
        print(f"Profile API Response Status: {profile_response.status_code}")
        if profile_response.status_code != 200:
            print(f"Error fetching profiles: {profile_response.text}")
            return []
            
        profile_data = profile_response.json()
        if not profile_data:
            print(f"No profile data found")
            return []
            
        # Get key metrics in batch
        metrics_url = f"https://financialmodelingprep.com/api/v3/key-metrics/{tickers_str}?apikey={api_key}"
        metrics_response = requests.get(metrics_url)
        print(f"Metrics API Response Status: {metrics_response.status_code}")
        if metrics_response.status_code != 200:
            print(f"Error fetching metrics: {metrics_response.text}")
            return []
            
        metrics_data = metrics_response.json()
        if not metrics_data:
            print(f"No metrics data found")
            return []
        
        # Get income statements in batch
        income_url = f"https://financialmodelingprep.com/api/v3/income-statement/{tickers_str}?limit=2&apikey={api_key}"
        income_response = requests.get(income_url)
        print(f"Income API Response Status: {income_response.status_code}")
        if income_response.status_code != 200:
            print(f"Error fetching income statements: {income_response.text}")
            return []
            
        income_data = income_response.json()
        if not income_data:
            print(f"No income statement data found")
            return []
            
        # Get cash flow statements in batch
        cash_flow_url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{tickers_str}?limit=1&apikey={api_key}"
        cash_flow_response = requests.get(cash_flow_url)
        print(f"Cash Flow API Response Status: {cash_flow_response.status_code}")
        if cash_flow_response.status_code != 200:
            print(f"Error fetching cash flow statements: {cash_flow_response.text}")
            return []
            
        cash_flow_data = cash_flow_response.json()
        if not cash_flow_data:
            print(f"No cash flow data found")
            return []
        
        # Process the data for each ticker
        results = []
        for ticker in tickers:
            try:
                # Find data for this ticker
                profile = next((p for p in profile_data if p['symbol'] == ticker), None)
                metrics = next((m for m in metrics_data if m['symbol'] == ticker), None)
                income = next((i for i in income_data if i['symbol'] == ticker), None)
                cash_flow = next((cf for cf in cash_flow_data if cf['symbol'] == ticker), None)
                
                if not all([profile, metrics, income, cash_flow]):
                    print(f"Missing data for {ticker}")
                    continue
                
                # Basic metrics
                current_revenue = float(income['revenue'])
                previous_revenue = float(income.get('previousRevenue', 0))
                revenue_growth = (current_revenue - previous_revenue) / previous_revenue if previous_revenue != 0 else None
                
                # Profitability metrics
                net_income = float(income['netIncome'])
                operating_income = float(income['operatingIncome'])
                operating_margin = operating_income / current_revenue if current_revenue != 0 else None
                
                # Cash flow metrics
                operating_cash_flow = float(cash_flow['operatingCashFlow'])
                fcf = float(cash_flow['freeCashFlow']) if cash_flow['freeCashFlow'] else None
                capex = float(cash_flow['capitalExpenditure'])
                
                # Calculate quality metrics
                ocf_to_net_income = operating_cash_flow / net_income if net_income != 0 else None
                fcf_to_net_income = fcf / net_income if net_income != 0 and fcf else None
                capex_to_ocf = abs(capex) / operating_cash_flow if operating_cash_flow != 0 else None
                
                # Create metrics dictionary
                data = {
                    'Ticker': ticker,
                    'Sector': profile.get('sector', 'Unknown'),
                    'ROIC': float(metrics.get('roic', 0)),
                    'Operating Margin': operating_margin,
                    'Asset Turnover': float(metrics.get('assetTurnover', 0)),
                    'Revenue Growth': revenue_growth,
                    'OCF to Net Income': ocf_to_net_income,
                    'FCF to Net Income': fcf_to_net_income,
                    'Capex to OCF': capex_to_ocf,
                    'Net Debt to EBITDA': float(metrics.get('netDebtToEBITDA', 0)),
                    'Current Ratio': float(metrics.get('currentRatio', 0)),
                    'Interest Coverage': float(metrics.get('interestCoverage', 0)),
                    'FCF': fcf,
                    'marketCap': float(metrics.get('marketCap', 0))
                }
                
                # Apply initial filter
                data['Passes Initial Filter'] = passes_initial_filter(data, revenue_growth, fcf)
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
        
        # Process the data
        profile = profile_data[0]
        metrics = metrics_data[0]
        
        # Basic metrics
        current_revenue = float(income_data[0]['revenue'])
        previous_revenue = float(income_data[1]['revenue'])
        revenue_growth = (current_revenue - previous_revenue) / previous_revenue if previous_revenue != 0 else None
        
        # Profitability metrics
        net_income = float(income_data[0]['netIncome'])
        operating_income = float(income_data[0]['operatingIncome'])
        operating_margin = operating_income / current_revenue if current_revenue != 0 else None
        
        # Cash flow metrics
        operating_cash_flow = float(cash_flow_data[0]['operatingCashFlow'])
        fcf = float(cash_flow_data[0]['freeCashFlow']) if cash_flow_data[0]['freeCashFlow'] else None
        capex = float(cash_flow_data[0]['capitalExpenditure'])
        
        # Calculate quality metrics
        ocf_to_net_income = operating_cash_flow / net_income if net_income != 0 else None
        fcf_to_net_income = fcf / net_income if net_income != 0 and fcf else None
        capex_to_ocf = abs(capex) / operating_cash_flow if operating_cash_flow != 0 else None
        
        # Create metrics dictionary
        data = {
            'Ticker': ticker,
            'Sector': profile.get('sector', 'Unknown'),
            'ROIC': float(metrics.get('roic', 0)),
            'Operating Margin': operating_margin,
            'Asset Turnover': float(metrics.get('assetTurnover', 0)),
            'Revenue Growth': revenue_growth,
            'OCF to Net Income': ocf_to_net_income,
            'FCF to Net Income': fcf_to_net_income,
            'Capex to OCF': capex_to_ocf,
            'Net Debt to EBITDA': float(metrics.get('netDebtToEBITDA', 0)),
            'Current Ratio': float(metrics.get('currentRatio', 0)),
            'Interest Coverage': float(metrics.get('interestCoverage', 0)),
            'FCF': fcf,
            'marketCap': float(metrics.get('marketCap', 0))
        }
        
        # Apply initial filter
        data['Passes Initial Filter'] = passes_initial_filter(data, revenue_growth, fcf)
        
        print(f"Successfully processed {ticker}")
        return data
        
    except Exception as e:
        print(f"Error processing {ticker}: {str(e)}")
        return None

def pull_fundamentals_from_sp600() -> None:
    try:
        print("Starting initial screening process...")
        holdings_path = get_latest_sp600_file()
        print(f"Reading holdings from: {holdings_path}")
        
        holdings = pd.read_csv(holdings_path)
        if 'Symbol' not in holdings.columns:
            raise ValueError("Required column 'Symbol' not found in holdings file")
            
        tickers = holdings['Symbol'].dropna().unique().tolist()
        print(f"Processing {len(tickers)} tickers")

        # Try batch processing first
        batch_size = 10  # Reduced batch size
        all_results = []
        
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i + batch_size]
            print(f"\nProcessing batch {i//batch_size + 1} of {(len(tickers) + batch_size - 1)//batch_size}")
            
            # Try batch processing
            batch_results = get_initial_metrics_batch(batch, API_KEY)
            
            # If batch processing fails, fall back to individual processing
            if not batch_results:
                print("Batch processing failed, falling back to individual processing...")
                for ticker in batch:
                    data = get_initial_metrics_single(ticker, API_KEY)
                    if data:
                        all_results.append(data)
                    time.sleep(0.1)  # Rate limiting for individual calls
            else:
                all_results.extend(batch_results)
            
            # Add delay between batches to respect rate limits
            if i + batch_size < len(tickers):
                time.sleep(1)  # 1 second delay between batches

        if not all_results:
            raise ValueError("No data was collected for any tickers")

        # Create DataFrame and filter
        df = pd.DataFrame(all_results)
        filtered_df = df[df['Passes Initial Filter'] == True]
        
        print(f"\nInitial screening results:")
        print(f"Total companies processed: {len(df)}")
        print(f"Companies passing filter: {len(filtered_df)}")
        print(f"Pass rate: {(len(filtered_df)/len(df))*100:.2f}%")
        
        # Print detailed results for each company
        print("\nDetailed Results:")
        for _, row in df.iterrows():
            status = "PASSED" if row['Passes Initial Filter'] else "FAILED"
            print(f"{row['Ticker']} ({row.get('Sector', 'Unknown')}): {status}")
        
        # Save both full and filtered results
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files')
        os.makedirs(output_dir, exist_ok=True)
        today = date.today().strftime('%Y-%m-%d')
        
        # Save full results
        full_output_path = os.path.join(output_dir, f"sp600_initial_metrics_{today}.csv")
        df.to_csv(full_output_path, index=False)
        print(f"Full initial metrics saved to: {full_output_path}")
        
        # Save filtered results for style analysis
        if not filtered_df.empty:
            filtered_output_path = os.path.join(output_dir, f"sp600_filtered_tickers_{today}.csv")
            filtered_df[['Ticker']].to_csv(filtered_output_path, index=False)
            print(f"Filtered tickers saved to: {filtered_output_path}")
        else:
            print("No companies passed the initial filter")
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise

# Define universal thresholds (same for all sectors)
universal_thresholds = {
    'roic_min': 0.10,              # 10% minimum ROIC
    'operating_margin_min': 0.10,  # 10% minimum operating margin
    'asset_turnover_min': 0.5,     # 0.5x minimum asset turnover
    'revenue_growth_min': 0.05,    # 5% minimum revenue growth
    'ocf_to_net_income_min': 1.0,  # Operating cash flow should exceed net income
    'fcf_to_net_income_min': 0.8,  # Free cash flow should be at least 80% of net income
    'capex_to_ocf_max': 0.5,       # Capex should not exceed 50% of operating cash flow
    'net_debt_to_ebitda_max': 3.0, # Net debt should not exceed 3x EBITDA
    'current_ratio_min': 1.0,      # Current ratio should be at least 1.0
    'interest_coverage_min': 3.0   # Interest coverage should be at least 3.0
}

def passes_initial_filter(data: Dict, revenue_growth: Optional[float], fcf: Optional[float]) -> bool:
    """Universal fundamental filter for companies."""
    try:
        # Log the actual values being checked
        print(f"\nChecking fundamentals for {data.get('Ticker')} in {data.get('Sector')} sector:")
        print(f"ROIC: {data.get('ROIC')}")
        print(f"Operating Margin: {data.get('Operating Margin')}")
        print(f"Asset Turnover: {data.get('Asset Turnover')}")
        print(f"Revenue Growth: {revenue_growth}")
        print(f"OCF to Net Income: {data.get('OCF to Net Income')}")
        print(f"FCF to Net Income: {data.get('FCF to Net Income')}")
        print(f"Capex to OCF: {data.get('Capex to OCF')}")
        print(f"Net Debt to EBITDA: {data.get('Net Debt to EBITDA')}")
        print(f"Current Ratio: {data.get('Current Ratio')}")
        print(f"Interest Coverage: {data.get('Interest Coverage')}")
        print(f"FCF: {fcf}")
        
        print(f"\nUniversal thresholds:")
        for key, value in universal_thresholds.items():
            print(f"{key}: {value}")
        
        # Exception 1: Strong Cash Flow Exception
        if fcf and fcf > 0:
            market_cap = float(data.get('marketCap', 0))
            if market_cap > 0:
                fcf_yield = fcf / market_cap
                if fcf_yield > 0.10:  # 10% FCF yield
                    print(f"Passed: Strong FCF yield of {fcf_yield:.2%}")
                    return True
        
        # Check ROIC
        if data.get('ROIC', 0) < universal_thresholds['roic_min']:
            print(f"Failed: ROIC too low ({data.get('ROIC')})")
            return False
            
        # Check Operating Margin
        if data.get('Operating Margin', 0) < universal_thresholds['operating_margin_min']:
            print(f"Failed: Operating margin too low ({data.get('Operating Margin')})")
            return False
            
        # Check Asset Turnover
        if data.get('Asset Turnover', 0) < universal_thresholds['asset_turnover_min']:
            print(f"Failed: Asset turnover too low ({data.get('Asset Turnover')})")
            return False
            
        # Check Revenue Growth
        if revenue_growth is not None and revenue_growth < universal_thresholds['revenue_growth_min']:
            print(f"Failed: Revenue growth too low ({revenue_growth})")
            return False
            
        # Check OCF to Net Income
        if data.get('OCF to Net Income', 0) < universal_thresholds['ocf_to_net_income_min']:
            print(f"Failed: OCF to net income too low ({data.get('OCF to Net Income')})")
            return False
            
        # Check FCF to Net Income
        if data.get('FCF to Net Income', 0) < universal_thresholds['fcf_to_net_income_min']:
            print(f"Failed: FCF to net income too low ({data.get('FCF to Net Income')})")
            return False
            
        # Check Capex to OCF
        if data.get('Capex to OCF', 0) > universal_thresholds['capex_to_ocf_max']:
            print(f"Failed: Capex to OCF too high ({data.get('Capex to OCF')})")
            return False
            
        # Check Net Debt to EBITDA
        if data.get('Net Debt to EBITDA', 0) > universal_thresholds['net_debt_to_ebitda_max']:
            print(f"Failed: Net debt to EBITDA too high ({data.get('Net Debt to EBITDA')})")
            return False
            
        # Check Current Ratio
        if data.get('Current Ratio', 0) < universal_thresholds['current_ratio_min']:
            print(f"Failed: Current ratio too low ({data.get('Current Ratio')})")
            return False
            
        # Check Interest Coverage
        if data.get('Interest Coverage', 0) < universal_thresholds['interest_coverage_min']:
            print(f"Failed: Interest coverage too low ({data.get('Interest Coverage')})")
            return False
            
        print(f"Passed all universal fundamental criteria!")
        return True
            
    except (ValueError, TypeError) as e:
        print(f"Error in filter calculation: {str(e)}")
        return False

if __name__ == "__main__":
    pull_fundamentals_from_sp600() 