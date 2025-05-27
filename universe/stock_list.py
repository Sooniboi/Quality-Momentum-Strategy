import pandas as pd
import requests
from io import StringIO
from datetime import datetime
import os

def load_russell_2000_from_ishares(save_csv: bool = True) -> pd.DataFrame:
    # iShares IWM ETF holdings CSV URL
    csv_url = "https://www.ishares.com/us/products/239710/ishares-russell-2000-etf/1467271812596.ajax?fileType=csv&fileName=IWM_holdings&dataType=fund"
    
    response = requests.get(csv_url)
    csv_data = response.content.decode("utf-8")

    # Skip the metadata rows (iShares typically starts data after 10 lines)
    df = pd.read_csv(StringIO(csv_data), skiprows=9)
    
    # Clean column names if needed
    df.columns = df.columns.str.strip()

    # Optional: Save the CSV to your data folder
    if save_csv:
        today = datetime.today().strftime("%Y-%m-%d")
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'universe')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"iwm_holdings_{today}.csv")
        df.to_csv(output_path, index=False)

    return df

# Example usage
if __name__ == "__main__":
    holdings = load_russell_2000_from_ishares()
    print(holdings.head())


122
