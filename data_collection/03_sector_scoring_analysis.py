import os
from dotenv import load_dotenv
import requests
import pandas as pd
from datetime import date, datetime, timedelta
import time
from typing import Dict, List, Optional
import numpy as np
from tqdm import tqdm
import glob

load_dotenv()
API_KEY = os.getenv("FMP_API_KEY")
if not API_KEY:
    raise ValueError("FMP_API_KEY not found in environment variables")

def get_latest_fundamental_momentum_file() -> str:
    """Get the latest fundamental momentum CSV file."""
    pattern = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files', '02_fundamentals_with_momentum*.csv')
    files = glob.glob(pattern)
    
    if not files:
        raise FileNotFoundError("No fundamental momentum CSV file found.")
    
    # Return the most recent file
    return max(files, key=os.path.getctime)

def get_sector_metrics(sector: str, api_key: str) -> Dict:
    """Get sector averages and standard deviations from FMP."""
    try:
        url = f"https://financialmodelingprep.com/api/v3/sector-performance?apikey={api_key}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error fetching sector metrics: {response.text}")
            return {}
            
        sector_data = response.json()
        return next((s for s in sector_data if s['sector'] == sector), {})
    except Exception as e:
        print(f"Error getting sector metrics: {str(e)}")
        return {}

def get_momentum_data(ticker: str, api_key: str) -> Dict:
    """Get 3M and 6M momentum data for a ticker."""
    try:
        # Get historical prices
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)  # 6 months of data
        
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?from={start_date.strftime('%Y-%m-%d')}&to={end_date.strftime('%Y-%m-%d')}&apikey={api_key}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error fetching momentum data for {ticker}: {response.text}")
            return {}
            
        price_data = response.json().get('historical', [])
        if not price_data:
            return {}
            
        # Calculate returns
        current_price = float(price_data[0]['close'])
        price_3m = float(price_data[90]['close']) if len(price_data) > 90 else None
        price_6m = float(price_data[180]['close']) if len(price_data) > 180 else None
        
        return_3m = (current_price - price_3m) / price_3m if price_3m else None
        return_6m = (current_price - price_6m) / price_6m if price_6m else None
        
        return {
            'return_3m': return_3m,
            'return_6m': return_6m
        }
    except Exception as e:
        print(f"Error calculating momentum for {ticker}: {str(e)}")
        return {}

def get_value_metrics(ticker: str, api_key: str) -> Dict:
    """Get value metrics (P/E, P/B, FCF Yield) for a ticker."""
    try:
        url = f"https://financialmodelingprep.com/api/v3/ratios/{ticker}?apikey={api_key}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error fetching value metrics for {ticker}: {response.text}")
            return {}
            
        ratios = response.json()
        if not ratios:
            return {}
            
        latest = ratios[0]
        return {
            'pe_ratio': float(latest.get('priceEarningsRatio', 0)),
            'pb_ratio': float(latest.get('priceToBookRatio', 0)),
            'fcf_yield': float(latest.get('freeCashFlowYield', 0))
        }
    except Exception as e:
        print(f"Error getting value metrics for {ticker}: {str(e)}")
        return {}

def calculate_z_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate z-scores for each metric within sectors."""
    metrics = ['ROIC', 'Operating Margin', 'Revenue Growth', 'Net Debt to EBITDA', 'FCF', '3M Return', '6M Return']
    
    # Calculate sector-specific z-scores
    for metric in metrics:
        df[f'{metric}_sector_z'] = df.groupby('Sector')[metric].transform(
            lambda x: (x - x.mean()) / x.std()
        )
    
    return df

def get_sector_weights() -> Dict:
    """Define sector-specific weights for scoring."""
    return {
        'Technology': {
            'ROIC': 0.20,
            'Operating Margin': 0.15,
            'Revenue Growth': 0.25,
            'FCF': 0.15,
            'Net Debt to EBITDA': 0.10,
            '3M Return': 0.10,
            '6M Return': 0.05
        },
        'Healthcare': {
            'ROIC': 0.15,
            'Operating Margin': 0.20,
            'Revenue Growth': 0.20,
            'FCF': 0.20,
            'Net Debt to EBITDA': 0.10,
            '3M Return': 0.10,
            '6M Return': 0.05
        },
        'Financial Services': {
            'ROIC': 0.25,
            'Operating Margin': 0.15,
            'Revenue Growth': 0.15,
            'FCF': 0.15,
            'Net Debt to EBITDA': 0.15,
            '3M Return': 0.10,
            '6M Return': 0.05
        },
        'Real Estate': {
            'ROIC': 0.15,
            'Operating Margin': 0.15,
            'Revenue Growth': 0.10,
            'FCF': 0.30,
            'Net Debt to EBITDA': 0.15,
            '3M Return': 0.10,
            '6M Return': 0.05
        },
        'Consumer Cyclical': {
            'ROIC': 0.20,
            'Operating Margin': 0.20,
            'Revenue Growth': 0.15,
            'FCF': 0.15,
            'Net Debt to EBITDA': 0.10,
            '3M Return': 0.10,
            '6M Return': 0.10
        },
        'Consumer Defensive': {
            'ROIC': 0.15,
            'Operating Margin': 0.20,
            'Revenue Growth': 0.10,
            'FCF': 0.20,
            'Net Debt to EBITDA': 0.15,
            '3M Return': 0.10,
            '6M Return': 0.10
        },
        'Industrials': {
            'ROIC': 0.20,
            'Operating Margin': 0.15,
            'Revenue Growth': 0.15,
            'FCF': 0.20,
            'Net Debt to EBITDA': 0.10,
            '3M Return': 0.10,
            '6M Return': 0.10
        },
        'Energy': {
            'ROIC': 0.15,
            'Operating Margin': 0.15,
            'Revenue Growth': 0.10,
            'FCF': 0.25,
            'Net Debt to EBITDA': 0.15,
            '3M Return': 0.10,
            '6M Return': 0.10
        },
        'Basic Materials': {
            'ROIC': 0.20,
            'Operating Margin': 0.15,
            'Revenue Growth': 0.10,
            'FCF': 0.20,
            'Net Debt to EBITDA': 0.15,
            '3M Return': 0.10,
            '6M Return': 0.10
        },
        'Communication Services': {
            'ROIC': 0.15,
            'Operating Margin': 0.15,
            'Revenue Growth': 0.20,
            'FCF': 0.15,
            'Net Debt to EBITDA': 0.15,
            '3M Return': 0.10,
            '6M Return': 0.10
        },
        'Utilities': {
            'ROIC': 0.15,
            'Operating Margin': 0.15,
            'Revenue Growth': 0.05,
            'FCF': 0.30,
            'Net Debt to EBITDA': 0.20,
            '3M Return': 0.10,
            '6M Return': 0.05
        }
    }

def normalize_metric(series: pd.Series) -> pd.Series:
    """Normalize a series to 0-1 scale."""
    return (series - series.min()) / (series.max() - series.min())

def calculate_sector_score(row: pd.Series, sector: str, sector_weights: Dict) -> float:
    """Calculate weighted sector score for a stock."""
    if sector not in sector_weights:
        sector = 'Technology'  # Default fallback
    
    weights = sector_weights[sector]
    score = 0
    
    for metric, weight in weights.items():
        z_score_col = f'{metric}_sector_z'
        if z_score_col in row and not pd.isna(row[z_score_col]):
            # Convert z-score to 0-10 scale (cap at ±3 standard deviations)
            normalized_z = max(-3, min(3, row[z_score_col]))
            metric_score = (normalized_z + 3) / 6 * 10  # Scale to 0-10
            score += weight * metric_score
    
    return score

def determine_style(row) -> str:
    """Determine investment style based on metrics."""
    roic = row.get('ROIC', 0)
    revenue_growth = row.get('Revenue Growth', 0)
    pe_ratio = row.get('pe_ratio', 0)
    momentum_3m = row.get('3M Return', 0)
    operating_margin = row.get('Operating Margin', 0)
    
    # Weak companies (filtered out)
    if roic < 0 or operating_margin < 0:
        return 'Weak'
    
    # Quality: High ROIC, good margins, stable growth
    if roic > 0.15 and operating_margin > 0.10:
        return 'Quality'
    
    # Growth: High revenue growth and momentum
    if revenue_growth > 0.15 and momentum_3m > 0.05:
        return 'Growth'
    
    # Value: Low PE, positive fundamentals
    if 0 < pe_ratio < 15 and roic > 0.05:
        return 'Value'
    
    # Default to Blend
    return 'Blend'

def calculate_sector_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate sector-relative scores using z-score methodology."""
    print(f"Calculating sector scores for {len(df)} companies...")
    
    # Calculate z-scores
    df = calculate_z_scores(df)
    
    # Get sector weights
    sector_weights = get_sector_weights()
    
    # Calculate sector scores
    df['Sector Score'] = df.apply(lambda row: calculate_sector_score(row, row['Sector'], sector_weights), axis=1)
    
    # Calculate quality and momentum scores
    quality_metrics = ['ROIC_sector_z', 'Operating Margin_sector_z', 'FCF_sector_z']
    momentum_metrics = ['3M Return_sector_z', '6M Return_sector_z']
    
    df['Quality Score'] = df[quality_metrics].mean(axis=1)
    df['Momentum Score'] = df[momentum_metrics].mean(axis=1)
    df['Overall Score'] = 0.6 * df['Quality Score'] + 0.4 * df['Momentum Score']
    
    # Add style classification
    df['Style'] = df.apply(determine_style, axis=1)
    
    # Add sector ranking
    df['Sector Rank'] = df.groupby('Sector')['Overall Score'].rank(ascending=False, method='min')
    
    # Sort by overall score
    df = df.sort_values('Overall Score', ascending=False)
    
    print(f"Scoring complete! Top sectors: {df.groupby('Sector')['Overall Score'].mean().sort_values(ascending=False).head(3).to_dict()}")
    
    return df

def main():
    try:
        print("=== QUALITY MOMENTUM ANALYSIS (SECTOR Z-SCORE) ===")
        
        # Read fundamental momentum data
        input_path = get_latest_fundamental_momentum_file()
        print(f"Reading data from: {input_path}")
        
        df = pd.read_csv(input_path)
        print(f"Loaded {len(df)} companies")
        
        # Calculate scores
        df_scored = calculate_sector_scores(df)
        
        # Save results
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files')
        today = date.today().strftime('%Y-%m-%d')
        output_path = os.path.join(output_dir, f"03_sector_scored_companies_{today}.csv")
        
        # Check if updating existing file
        if os.path.exists(output_path):
            print(f"Updating existing file: {output_path}")
        else:
            print(f"Creating new file: {output_path}")
        
        df_scored.to_csv(output_path, index=False)
        print(f"\nResults saved to: {output_path}")
        
        # Display summary
        print("\n" + "="*80)
        print("ANALYSIS SUMMARY")
        print("="*80)
        print(f"Total companies analyzed: {len(df_scored)}")
        print(f"Average Overall Score: {df_scored['Overall Score'].mean():.2f}")
        
        print("\nTop 10 Companies:")
        print("-" * 80)
        
        for _, row in df_scored.head(10).iterrows():
            print(f"{row['Ticker']:<8} {row['Sector']:<20} {row['Style']:<8} {row['Overall Score']:.2f}")
        
        print("\nStyle Distribution:")
        style_counts = df_scored['Style'].value_counts()
        for style, count in style_counts.items():
            print(f"  {style}: {count} companies ({count/len(df_scored)*100:.1f}%)")
        
        return df_scored
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    result = main() 