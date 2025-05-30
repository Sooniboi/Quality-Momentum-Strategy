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
    pattern = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files', 'sp600_fundamental_momentum.csv')
    if not os.path.exists(pattern):
        raise FileNotFoundError("No fundamental momentum CSV file found.")
    return pattern

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
    """Calculate z-scores for each metric, both overall and sector-specific."""
    metrics = ['ROIC', 'Operating Margin', 'Revenue Growth', 'Net Debt to EBITDA', 'FCF', '3M Return', '6M Return']
    
    # Calculate overall z-scores
    for metric in metrics:
        df[f'{metric}_z'] = (df[metric] - df[metric].mean()) / df[metric].std()
    
    # Calculate sector-specific z-scores
    for metric in metrics:
        df[f'{metric}_sector_z'] = df.groupby('Sector')[metric].transform(
            lambda x: (x - x.mean()) / x.std()
        )
    
    return df

def calculate_composite_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate composite scores based on z-scores."""
    # Quality metrics weights
    quality_weights = {
        'ROIC': 0.3,
        'Operating Margin': 0.3,
        'FCF': 0.2,
        'Net Debt to EBITDA': 0.2
    }
    
    # Momentum metrics weights
    momentum_weights = {
        '3M Return': 0.5,
        '6M Return': 0.5
    }
    
    # Calculate composite scores using sector-specific z-scores
    df['Quality Score'] = (
        df['ROIC_sector_z'] * quality_weights['ROIC'] +
        df['Operating Margin_sector_z'] * quality_weights['Operating Margin'] +
        df['FCF_sector_z'] * quality_weights['FCF'] +
        (-df['Net Debt to EBITDA_sector_z']) * quality_weights['Net Debt to EBITDA']
    )
    
    df['Momentum Score'] = (
        df['3M Return_sector_z'] * momentum_weights['3M Return'] +
        df['6M Return_sector_z'] * momentum_weights['6M Return']
    )
    
    # Calculate overall score
    df['Overall Score'] = df['Quality Score'] * 0.6 + df['Momentum Score'] * 0.4
    
    return df

def determine_style(row) -> str:
    """Determine investment style based on z-scores.
    
    Style Definitions:
    - Quality: Quality Score > 1.0 (excellent fundamentals)
    - Growth: Quality Score > 0.5 AND Momentum Score > 0.5 (good fundamentals with strong momentum)
    - Value: Quality Score > 0.5 AND Momentum Score <= 0.5 (good fundamentals but lower momentum)
    - Blend: Quality Score between -0.5 and 0.5 (average fundamentals)
    - Weak: Quality Score < -0.5 (poor fundamentals)
    """
    if row['Quality Score'] > 1.0:
        return "Quality"
    elif row['Quality Score'] > 0.5:
        if row['Momentum Score'] > 0.5:
            return "Growth"
        else:
            return "Value"
    elif row['Quality Score'] >= -0.5:
        return "Blend"
    else:
        return "Weak"

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
            'Net Debt to EBITDA': 0.15,
            '3M Return': 0.10,
            '6M Return': 0.10
        }
    }

def normalize_metric(series: pd.Series) -> pd.Series:
    """Normalize a metric using z-score within its sector."""
    return (series - series.mean()) / series.std()

def calculate_sector_score(row: pd.Series, sector: str, sector_weights: Dict) -> float:
    """Calculate sector-specific composite score."""
    # Get weights for the sector (default to equal weights if sector not found)
    weights = sector_weights.get(sector, {
        'ROIC': 0.15,
        'Operating Margin': 0.15,
        'Revenue Growth': 0.15,
        'FCF': 0.15,
        'Net Debt to EBITDA': 0.15,
        '3M Return': 0.15,
        '6M Return': 0.10
    })
    
    # Calculate weighted score
    score = 0
    for metric, weight in weights.items():
        if pd.notna(row[metric]):
            # For Net Debt to EBITDA, lower is better, so we invert the score
            if metric == 'Net Debt to EBITDA':
                score += (1 - row[metric]) * weight
            else:
                score += row[metric] * weight
    
    return score

def main(test_mode: bool = False):
    try:
        # Read fundamental momentum data
        input_path = get_latest_fundamental_momentum_file()
        print(f"Reading data from: {input_path}")
        
        df = pd.read_csv(input_path)
        
        # If in test mode, take first 10 companies
        if test_mode:
            df = df.head(10)
            print(f"\nTEST MODE: Processing {len(df)} companies")
        else:
            print(f"\nProcessing {len(df)} companies")
        
        # Calculate z-scores
        print("\nCalculating z-scores...")
        df = calculate_z_scores(df)
        
        # Calculate composite scores
        print("Calculating composite scores...")
        df = calculate_composite_scores(df)
        
        # Determine investment style
        df['Style'] = df.apply(determine_style, axis=1)
        
        # Get sector weights
        sector_weights = get_sector_weights()
        
        # Normalize metrics within sectors
        metrics_to_normalize = [
            'ROIC', 'Operating Margin', 'Revenue Growth', 'FCF', 
            'Net Debt to EBITDA', '3M Return', '6M Return'
        ]
        
        for metric in metrics_to_normalize:
            df[f'{metric}_Normalized'] = df.groupby('Sector')[metric].transform(normalize_metric)
        
        # Calculate sector-specific scores
        df['Sector Score'] = df.apply(lambda row: calculate_sector_score(row, row['Sector'], sector_weights), axis=1)
        
        # Rank within sectors
        df['Sector Rank'] = df.groupby('Sector')['Sector Score'].rank(ascending=False)
        
        # Sort by sector and rank
        df = df.sort_values(['Sector', 'Sector Rank'])
        
        # Save results
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files')
        today = date.today().strftime('%Y-%m-%d')
        
        # Save all companies with scores
        output_path = os.path.join(output_dir, f"sp600_sector_scored_{today}.csv")
        df.to_csv(output_path, index=False)
        print(f"\nAll companies with sector scores saved to: {output_path}")
        
        # Print detailed summary by sector
        print("\nDetailed Sector Summary:")
        for sector in sorted(df['Sector'].unique()):
            sector_companies = df[df['Sector'] == sector]
            print(f"\n{sector} (Total companies: {len(sector_companies)}):")
            print("-" * 80)
            
            # Print top 5 companies in each sector
            top_5 = sector_companies.head(5)
            for _, row in top_5.iterrows():
                print(f"\n{row['Ticker']} (Score: {row['Sector Score']:.2f}, Rank: {row['Sector Rank']:.0f})")
                print(f"  Quality Metrics:")
                print(f"    ROIC: {row['ROIC']:.2%}")
                print(f"    Operating Margin: {row['Operating Margin']:.2%}")
                print(f"    FCF: ${row['FCF']:,.0f}")
                print(f"    Net Debt to EBITDA: {row['Net Debt to EBITDA']:.2f}")
                print(f"  Growth Metrics:")
                print(f"    Revenue Growth: {row['Revenue Growth']:.2%}")
                print(f"  Momentum Metrics:")
                print(f"    3M Return: {row['3M Return']:.2%}")
                print(f"    6M Return: {row['6M Return']:.2%}")
            
            # Print sector statistics
            print(f"\nSector Statistics:")
            print(f"  Average Score: {sector_companies['Sector Score'].mean():.2f}")
            print(f"  Median Score: {sector_companies['Sector Score'].median():.2f}")
            print(f"  Score Range: {sector_companies['Sector Score'].min():.2f} to {sector_companies['Sector Score'].max():.2f}")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main(test_mode=False)  # Run full analysis 