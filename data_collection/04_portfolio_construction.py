import pandas as pd
import os
from datetime import date
import numpy as np
from typing import Dict, List

def get_latest_sector_scored_file() -> str:
    """Get the latest sector scored CSV file."""
    pattern = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files', '03_sector_scored_companies_*.csv')
    import glob
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError("No sector scored CSV file found.")
    return max(files, key=os.path.getctime)  # Get the most recent file

def apply_quality_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Apply minimum quality filters to remove weak companies."""
    print("Applying quality filters...")
    
    initial_count = len(df)
    
    # Remove companies with weak fundamentals
    df_filtered = df[
        (df['Style'] != 'Weak') &                    # Exclude weak companies
        (df['Quality Score'] > -0.5) &               # Minimum quality threshold
        (df['Momentum Score'] > -1.0) &              # Not complete momentum disasters
        (df['Sector Rank'] <= 10) &                  # Top 10 in each sector
        (df['ROIC'] > 0) &                          # Positive ROIC
        (df['Operating Margin'] > 0)                 # Positive operating margins
    ].copy()
    
    print(f"Filtered from {initial_count} to {len(df_filtered)} companies")
    return df_filtered

def create_selection_pool(df: pd.DataFrame, companies_per_sector: int = 5) -> pd.DataFrame:
    """Create a selection pool by taking top companies from each sector."""
    print(f"Creating selection pool: top {companies_per_sector} companies per sector...")
    
    selection_pool = pd.DataFrame()
    
    for sector in df['Sector'].unique():
        sector_companies = df[df['Sector'] == sector].head(companies_per_sector)
        selection_pool = pd.concat([selection_pool, sector_companies])
    
    print(f"Selection pool size: {len(selection_pool)} companies")
    return selection_pool

def select_by_style(df: pd.DataFrame, style_targets: Dict[str, int]) -> pd.DataFrame:
    """Select companies based on style targets."""
    print("Selecting companies by style targets...")
    
    portfolio = pd.DataFrame()
    
    for style, target_count in style_targets.items():
        if target_count == 0:
            continue
            
        style_companies = df[df['Style'] == style].copy()
        
        if len(style_companies) == 0:
            print(f"Warning: No {style} companies available")
            continue
        
        # Sort by Overall Score to get best companies in each style
        style_companies = style_companies.sort_values('Overall Score', ascending=False)
        
        # Take up to target count, but don't exceed available companies
        selected_count = min(target_count, len(style_companies))
        selected = style_companies.head(selected_count)
        
        portfolio = pd.concat([portfolio, selected])
        print(f"Selected {selected_count} {style} companies (target: {target_count})")
    
    return portfolio

def check_sector_concentration(df: pd.DataFrame, max_sector_weight: float = 0.25) -> pd.DataFrame:
    """Check and adjust sector concentration limits."""
    print(f"Checking sector concentration (max {max_sector_weight:.1%} per sector)...")
    
    sector_counts = df['Sector'].value_counts()
    total_companies = len(df)
    
    # Identify sectors that exceed the limit
    over_limit_sectors = []
    for sector, count in sector_counts.items():
        weight = count / total_companies
        if weight > max_sector_weight:
            over_limit_sectors.append(sector)
            print(f"Warning: {sector} has {weight:.1%} allocation (limit: {max_sector_weight:.1%})")
    
    # If any sectors are over limit, we should adjust
    if over_limit_sectors:
        print("Consider reducing allocation to over-concentrated sectors")
    
    return df

def calculate_portfolio_stats(df: pd.DataFrame) -> Dict:
    """Calculate portfolio statistics."""
    stats = {
        'total_companies': len(df),
        'sectors': df['Sector'].nunique(),
        'style_distribution': df['Style'].value_counts().to_dict(),
        'sector_distribution': df['Sector'].value_counts().to_dict(),
        'avg_quality_score': df['Quality Score'].mean(),
        'avg_momentum_score': df['Momentum Score'].mean(),
        'avg_overall_score': df['Overall Score'].mean(),
        'avg_sector_score': df['Sector Score'].mean()
    }
    return stats

def main():
    try:
        # Read the latest sector scored data
        input_path = get_latest_sector_scored_file()
        print(f"Reading sector scored data from: {input_path}")
        
        df = pd.read_csv(input_path)
        print(f"Initial universe: {len(df)} companies across {df['Sector'].nunique()} sectors")
        
        # Apply quality filters
        df_filtered = apply_quality_filters(df)
        
        # Create selection pool (top 5 per sector)
        selection_pool = create_selection_pool(df_filtered, companies_per_sector=5)
        
        # Define style targets (total target: 50 companies)
        style_targets = {
            'Quality': 20,    # 40% of portfolio
            'Growth': 15,     # 30% of portfolio
            'Value': 10,      # 20% of portfolio
            'Blend': 5,       # 10% of portfolio
            'Weak': 0         # Exclude these
        }
        
        # Select companies by style
        portfolio = select_by_style(selection_pool, style_targets)
        
        # Check sector concentration
        portfolio = check_sector_concentration(portfolio, max_sector_weight=0.25)
        
        # Calculate equal weights
        portfolio['Portfolio Weight'] = 1.0 / len(portfolio)
        
        # Sort by sector and overall score
        portfolio = portfolio.sort_values(['Sector', 'Overall Score'], ascending=[True, False])
        
        # Save the selected portfolio
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files')
        os.makedirs(output_dir, exist_ok=True)
        today = date.today().strftime('%Y-%m-%d')
        output_path = os.path.join(output_dir, f"04_final_portfolio_selection_{today}.csv")
        
        # Check if updating existing file
        if os.path.exists(output_path):
            print(f"Updating existing portfolio: {output_path}")
        else:
            print(f"Creating new portfolio: {output_path}")
        
        # Select key columns for output
        output_columns = [
            'Ticker', 'Sector', 'Style', 'Portfolio Weight',
            'Sector Score', 'Sector Rank', 'Quality Score', 'Momentum Score', 'Overall Score',
            'ROIC', 'Operating Margin', 'Revenue Growth', 'FCF', 'Net Debt to EBITDA',
            '3M Return', '6M Return', 'marketCap'
        ]
        
        portfolio[output_columns].to_csv(output_path, index=False)
        print(f"\nPortfolio saved to: {output_path}")
        
        # Calculate and display portfolio statistics
        stats = calculate_portfolio_stats(portfolio)
        
        print("\n" + "="*80)
        print("PORTFOLIO SUMMARY")
        print("="*80)
        print(f"Total Companies: {stats['total_companies']}")
        print(f"Sectors Represented: {stats['sectors']}")
        print(f"Average Quality Score: {stats['avg_quality_score']:.2f}")
        print(f"Average Momentum Score: {stats['avg_momentum_score']:.2f}")
        print(f"Average Overall Score: {stats['avg_overall_score']:.2f}")
        
        print("\nStyle Distribution:")
        for style, count in stats['style_distribution'].items():
            percentage = (count / stats['total_companies']) * 100
            print(f"  {style}: {count} companies ({percentage:.1f}%)")
        
        print("\nSector Distribution:")
        for sector, count in stats['sector_distribution'].items():
            percentage = (count / stats['total_companies']) * 100
            print(f"  {sector}: {count} companies ({percentage:.1f}%)")
        
        print("\nTop 10 Holdings:")
        print("-" * 80)
        top_10 = portfolio.head(10)
        for _, row in top_10.iterrows():
            print(f"{row['Ticker']} ({row['Sector']}) - {row['Style']} - Score: {row['Overall Score']:.2f}")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main() 