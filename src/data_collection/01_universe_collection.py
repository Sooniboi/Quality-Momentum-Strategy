import pandas as pd
import requests
from datetime import datetime, date
import os

def load_sp600_from_wikipedia(save_csv: bool = True) -> pd.DataFrame:
    # Wikipedia URL for S&P 600 constituents
    wiki_url = "https://en.wikipedia.org/wiki/List_of_S%26P_600_companies"
    # Wikipedia refuses requests without a browser-like User-Agent (HTTP 403).
    from io import StringIO
    html = requests.get(wiki_url, headers={"User-Agent": "Mozilla/5.0 (quality-momentum-strategy; research use)"}, timeout=30)
    html.raise_for_status()
    tables = pd.read_html(StringIO(html.text))
    
    # The first table on the page is the constituents table
    df = tables[0]
    
    # Print column names for debugging
    print("Available columns:", df.columns.tolist())

    # Keep only relevant columns (using exact column names from Wikipedia)
    keep_cols = [
        'Symbol',
        'Company',
        'GICS Sector',
        'GICS Sub-Industry',
        'Headquarters Location',
        'SEC filings',
        'CIK'
    ]
    
    # Select columns
    df = df[keep_cols]

    # Save to CSV with proper naming
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files')
    os.makedirs(output_dir, exist_ok=True)
    today = date.today().strftime('%Y-%m-%d')
    output_path = os.path.join(output_dir, f"01_universe_sp600_companies_{today}.csv")
    df.to_csv(output_path, index=False)
    print(f"\nSaved S&P 600 holdings to: {output_path}")

    return df

# Example usage
if __name__ == "__main__":
    holdings = load_sp600_from_wikipedia()
    print("\nFirst few rows of S&P 600 holdings:")
    print(holdings.head())