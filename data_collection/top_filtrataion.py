import pandas as pd
import os
from datetime import date
import glob
import numpy as np
from typing import Dict, List

def get_latest_quality_file() -> str:
    """Get the latest quality momentum analysis CSV file."""
    pattern = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files', 'sp600_fundamental_momentum.csv')
    if not os.path.exists(pattern):
        raise FileNotFoundError("Quality momentum analysis CSV file not found.")
    return pattern

def normalize_metric(series: pd.Series) -> pd.Series:
    """Normalize a metric using z-score within its sector."""
    return (series - series.mean()) / series.std()

def calculate_sector_score(row: pd.Series, sector: str) -> float:
    """Calculate sector-specific composite score with enhanced metrics."""
    # Define sector-specific weights with enhanced metrics
    sector_weights = {
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
        # Read quality momentum analysis results
        input_path = get_latest_quality_file()
        print(f"Reading quality momentum analysis from: {input_path}")
        
        df = pd.read_csv(input_path)
        
        if test_mode:
            # In test mode, take 2 companies from each sector
            test_df = pd.DataFrame()
            for sector in df['Sector'].unique():
                sector_companies = df[df['Sector'] == sector].head(2)
                test_df = pd.concat([test_df, sector_companies])
            df = test_df
            print(f"\nTEST MODE: Processing {len(df)} companies (2 per sector)")
        
        # Normalize metrics within sectors
        metrics_to_normalize = [
            'ROIC', 'Operating Margin', 'Revenue Growth', 'FCF', 
            'Net Debt to EBITDA', '3M Return', '6M Return'
        ]
        
        for metric in metrics_to_normalize:
            df[f'{metric}_Normalized'] = df.groupby('Sector')[metric].transform(normalize_metric)
        
        # Calculate sector-specific scores
        df['Sector Score'] = df.apply(lambda row: calculate_sector_score(row, row['Sector']), axis=1)
        
        # Rank within sectors
        df['Sector Rank'] = df.groupby('Sector')['Sector Score'].rank(ascending=False)
        
        # Keep top 5 companies per sector
        top_companies = df[df['Sector Rank'] <= 5].copy()
        
        # Sort by sector and rank
        top_companies = top_companies.sort_values(['Sector', 'Sector Rank'])
        
        # Save results
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files')
        today = date.today().strftime('%Y-%m-%d')
        
        # Add test mode suffix if in test mode
        suffix = "_test" if test_mode else ""
        
        # Save top companies
        output_path = os.path.join(output_dir, f"sector_scored_companies_{today}{suffix}.csv")
        top_companies.to_csv(output_path, index=False)
        print(f"\nSector scored companies saved to: {output_path}")
        
        # Print detailed summary
        print("\nDetailed Sector Summary:")
        for sector in sorted(top_companies['Sector'].unique()):
            sector_companies = top_companies[top_companies['Sector'] == sector]
            print(f"\n{sector} (Top {len(sector_companies)} companies):")
            print("-" * 80)
            for _, row in sector_companies.iterrows():
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
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    # Run full analysis
    main(test_mode=False) 