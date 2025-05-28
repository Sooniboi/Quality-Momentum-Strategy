import pandas as pd
import requests
from datetime import datetime
import os

def load_sp600_from_wikipedia(save_csv: bool = True) -> pd.DataFrame:
    # Wikipedia URL for S&P 600 constituents
    wiki_url = "https://en.wikipedia.org/wiki/List_of_S%26P_600_companies"
    tables = pd.read_html(wiki_url)
    
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

    # Save the CSV directly to csv_data_files
    if save_csv:
        today = datetime.today().strftime("%Y-%m-%d")
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"sp600_holdings_{today}.csv")
        df.to_csv(output_path, index=False)
        print(f"\nSaved S&P 600 holdings to: {output_path}")

    return df

# Example usage
if __name__ == "__main__":
    holdings = load_sp600_from_wikipedia()
    print("\nFirst few rows of S&P 600 holdings:")
    print(holdings.head())