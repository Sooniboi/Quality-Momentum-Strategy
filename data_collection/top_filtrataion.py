import pandas as pd
import os
from datetime import date
import glob
import numpy as np
from typing import Dict, List

def get_latest_stage1_file() -> str:
    """Get the latest stage1 passed companies CSV file."""
    pattern = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files', 'stage1_passed_companies_*.csv')
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError("No stage1 passed companies CSV files found.")
    return max(files, key=os.path.getmtime)

def normalize_metric(series: pd.Series) -> pd.Series:
    """Normalize a metric using z-score within its sector."""
    return (series - series.mean()) / series.std()

def calculate_sector_score(row: pd.Series, sector: str) -> float:
    """Calculate sector-specific composite score."""
    # Define sector-specific weights
    sector_weights = {
        'Technology': {
            'ROIC': 0.25,
            'Operating Margin': 0.20,
            'Revenue Growth': 0.30,
            'FCF': 0.15,
            'Net Debt to EBITDA': 0.10
        },
        'Healthcare': {
            'ROIC': 0.20,
            'Operating Margin': 0.25,
            'Revenue Growth': 0.25,
            'FCF': 0.20,
            'Net Debt to EBITDA': 0.10
        },
        'Financial Services': {
            'ROIC': 0.30,
            'Operating Margin': 0.20,
            'Revenue Growth': 0.15,
            'FCF': 0.20,
            'Net Debt to EBITDA': 0.15
        },
        'Real Estate': {
            'ROIC': 0.15,
            'Operating Margin': 0.15,
            'Revenue Growth': 0.10,
            'FCF': 0.40,
            'Net Debt to EBITDA': 0.20
        },
        'Consumer Cyclical': {
            'ROIC': 0.25,
            'Operating Margin': 0.25,
            'Revenue Growth': 0.20,
            'FCF': 0.20,
            'Net Debt to EBITDA': 0.10
        },
        'Consumer Defensive': {
            'ROIC': 0.20,
            'Operating Margin': 0.25,
            'Revenue Growth': 0.15,
            'FCF': 0.25,
            'Net Debt to EBITDA': 0.15
        },
        'Industrials': {
            'ROIC': 0.25,
            'Operating Margin': 0.20,
            'Revenue Growth': 0.15,
            'FCF': 0.25,
            'Net Debt to EBITDA': 0.15
        },
        'Energy': {
            'ROIC': 0.20,
            'Operating Margin': 0.20,
            'Revenue Growth': 0.15,
            'FCF': 0.30,
            'Net Debt to EBITDA': 0.15
        },
        'Basic Materials': {
            'ROIC': 0.25,
            'Operating Margin': 0.20,
            'Revenue Growth': 0.15,
            'FCF': 0.25,
            'Net Debt to EBITDA': 0.15
        },
        'Communication Services': {
            'ROIC': 0.20,
            'Operating Margin': 0.20,
            'Revenue Growth': 0.25,
            'FCF': 0.20,
            'Net Debt to EBITDA': 0.15
        },
        'Utilities': {
            'ROIC': 0.15,
            'Operating Margin': 0.20,
            'Revenue Growth': 0.10,
            'FCF': 0.35,
            'Net Debt to EBITDA': 0.20
        }
    }
    
    # Get weights for the sector (default to equal weights if sector not found)
    weights = sector_weights.get(sector, {
        'ROIC': 0.20,
        'Operating Margin': 0.20,
        'Revenue Growth': 0.20,
        'FCF': 0.20,
        'Net Debt to EBITDA': 0.20
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
        # Read stage1 passed companies
        stage1_path = get_latest_stage1_file()
        print(f"Reading stage1 passed companies from: {stage1_path}")
        
        df = pd.read_csv(stage1_path)
        
        if test_mode:
            # In test mode, take 2 companies from each sector
            test_df = pd.DataFrame()
            for sector in df['Sector'].unique():
                sector_companies = df[df['Sector'] == sector].head(2)
                test_df = pd.concat([test_df, sector_companies])
            df = test_df
            print(f"\nTEST MODE: Processing {len(df)} companies (2 per sector)")
        
        # Normalize metrics within sectors
        metrics_to_normalize = ['ROIC', 'Operating Margin', 'Revenue Growth', 'FCF', 'Net Debt to EBITDA']
        
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
        output_path = os.path.join(output_dir, f"stage2_companies_{today}{suffix}.csv")
        top_companies.to_csv(output_path, index=False)
        print(f"\nTop companies saved to: {output_path}")
        
        # Print summary
        print("\nSector Summary:")
        for sector in sorted(top_companies['Sector'].unique()):
            sector_companies = top_companies[top_companies['Sector'] == sector]
            print(f"\n{sector}:")
            for _, row in sector_companies.iterrows():
                print(f"  {row['Ticker']} (Score: {row['Sector Score']:.2f}, Rank: {row['Sector Rank']:.0f})")
                if test_mode:
                    print(f"    ROIC: {row['ROIC']:.2%}")
                    print(f"    Operating Margin: {row['Operating Margin']:.2%}")
                    print(f"    Revenue Growth: {row['Revenue Growth']:.2%}")
                    print(f"    FCF: ${row['FCF']:,.0f}")
                    print(f"    Net Debt to EBITDA: {row['Net Debt to EBITDA']:.2f}")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    # Run full analysis
    main(test_mode=False) 