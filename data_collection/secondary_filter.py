import pandas as pd
import os
from datetime import date
import glob

def get_latest_filtered_file() -> str:
    """Get the latest filtered tickers CSV file."""
    pattern = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files', 'sp600_filtered_tickers_*.csv')
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError("No filtered tickers CSV files found.")
    return max(files, key=os.path.getmtime)

def get_latest_metrics_file() -> str:
    """Get the latest full metrics CSV file."""
    pattern = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files', 'sp600_initial_metrics_*.csv')
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError("No initial metrics CSV files found.")
    return max(files, key=os.path.getmtime)

def calculate_composite_score(row: pd.Series) -> float:
    """Calculate a composite score based on sector-adjusted weights."""
    # Example weights (adjust as needed)
    weights = {
        'ROE': 0.3,
        'Revenue Growth': 0.2,
        'FCF': 0.2,
        'Momentum 3M': 0.15,
        'Momentum 6M': 0.15
    }
    
    score = 0
    for metric, weight in weights.items():
        if metric in row and pd.notna(row[metric]):
            score += row[metric] * weight
    return score

def tag_style(row: pd.Series) -> str:
    """Tag company as value, growth, momentum, or quality based on metrics."""
    if row['PE'] < 15 and row['ROE'] > 0.15:
        return 'Value'
    elif row['Revenue Growth'] > 0.15:
        return 'Growth'
    elif row['Momentum 3M'] > 0.1 or row['Momentum 6M'] > 0.15:
        return 'Momentum'
    else:
        return 'Quality'

def main():
    # Read filtered tickers and full metrics
    filtered_path = get_latest_filtered_file()
    metrics_path = get_latest_metrics_file()
    
    filtered_df = pd.read_csv(filtered_path)
    metrics_df = pd.read_csv(metrics_path)
    
    # Merge filtered tickers with full metrics
    merged_df = pd.merge(filtered_df, metrics_df, on='Ticker', how='left')
    
    # Calculate composite score
    merged_df['Composite Score'] = merged_df.apply(calculate_composite_score, axis=1)
    
    # Tag style
    merged_df['Style'] = merged_df.apply(tag_style, axis=1)
    
    # Rank within sector and overall
    merged_df['Sector Rank'] = merged_df.groupby('Sector')['Composite Score'].rank(ascending=False)
    merged_df['Overall Rank'] = merged_df['Composite Score'].rank(ascending=False)
    
    # Save results
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files')
    today = date.today().strftime('%Y-%m-%d')
    output_path = os.path.join(output_dir, f"sp600_secondary_filtered_{today}.csv")
    merged_df.to_csv(output_path, index=False)
    print(f"Secondary filter results saved to: {output_path}")

if __name__ == "__main__":
    main() 