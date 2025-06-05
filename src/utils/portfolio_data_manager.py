#!/usr/bin/env python3
"""
Portfolio Data Manager

Manages portfolio data from various sources - CSV files, JSON, manual input.
Provides real portfolio data instead of mock data.
"""

import pandas as pd
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime

class PortfolioDataManager:
    """Manages portfolio data from user-specified sources."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.portfolio_file = None
        self.portfolio_data = pd.DataFrame()
        
    def load_portfolio_from_csv(self, csv_file: str) -> pd.DataFrame:
        """Load portfolio from CSV file."""
        try:
            if not Path(csv_file).exists():
                self.logger.error(f"❌ Portfolio file not found: {csv_file}")
                return pd.DataFrame()
            
            df = pd.read_csv(csv_file)
            self.logger.info(f"✅ Loaded portfolio from {csv_file}: {len(df)} positions")
            
            # Standardize column names
            column_mapping = {
                'symbol': 'ticker',
                'Symbol': 'ticker',
                'Ticker': 'ticker',
                'TICKER': 'ticker',
                'quantity': 'shares',
                'Quantity': 'shares',
                'Shares': 'shares',
                'qty': 'shares',
                'price': 'current_price',
                'Price': 'current_price',
                'current_price': 'current_price',
                'value': 'market_value',
                'Value': 'market_value',
                'market_value': 'market_value'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df = df.rename(columns={old_col: new_col})
            
            # Calculate missing fields
            if 'shares' in df.columns and 'current_price' in df.columns:
                df['market_value'] = df['shares'] * df['current_price']
            
            # Add default values for missing columns
            required_columns = ['ticker', 'shares', 'current_price', 'market_value']
            for col in required_columns:
                if col not in df.columns:
                    if col == 'ticker':
                        df[col] = 'UNKNOWN'
                    else:
                        df[col] = 0
            
            self.portfolio_data = df
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Error loading portfolio from CSV: {e}")
            return pd.DataFrame()
    
    def load_portfolio_from_json(self, json_file: str) -> pd.DataFrame:
        """Load portfolio from JSON file."""
        try:
            if not Path(json_file).exists():
                self.logger.error(f"❌ Portfolio file not found: {json_file}")
                return pd.DataFrame()
            
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Convert to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict) and 'positions' in data:
                df = pd.DataFrame(data['positions'])
            else:
                df = pd.DataFrame([data])
            
            self.logger.info(f"✅ Loaded portfolio from {json_file}: {len(df)} positions")
            self.portfolio_data = df
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Error loading portfolio from JSON: {e}")
            return pd.DataFrame()
    
    def create_manual_portfolio(self, positions: List[Dict]) -> pd.DataFrame:
        """Create portfolio from manual input."""
        try:
            df = pd.DataFrame(positions)
            self.logger.info(f"✅ Created manual portfolio: {len(df)} positions")
            self.portfolio_data = df
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Error creating manual portfolio: {e}")
            return pd.DataFrame()
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary statistics."""
        if self.portfolio_data.empty:
            return {'error': 'No portfolio data loaded'}
        
        try:
            summary = {
                'total_positions': len(self.portfolio_data),
                'total_value': self.portfolio_data.get('market_value', pd.Series()).sum(),
                'symbols': self.portfolio_data.get('ticker', pd.Series()).tolist(),
                'largest_position': '',
                'smallest_position': ''
            }
            
            if 'market_value' in self.portfolio_data.columns:
                max_idx = self.portfolio_data['market_value'].idxmax()
                min_idx = self.portfolio_data['market_value'].idxmin()
                summary['largest_position'] = self.portfolio_data.loc[max_idx, 'ticker']
                summary['smallest_position'] = self.portfolio_data.loc[min_idx, 'ticker']
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Error getting portfolio summary: {e}")
            return {'error': str(e)}
    
    def save_portfolio_template(self, filename: str = 'portfolio_template.csv'):
        """Save a portfolio template for user to fill out."""
        template_data = {
            'ticker': ['AAPL', 'MSFT', 'GOOGL'],
            'shares': [100, 50, 25],
            'current_price': [150.00, 300.00, 2500.00],
            'sector': ['Technology', 'Technology', 'Technology'],
            'avg_entry_price': [140.00, 280.00, 2400.00]
        }
        
        template_df = pd.DataFrame(template_data)
        template_df['market_value'] = template_df['shares'] * template_df['current_price']
        
        template_df.to_csv(filename, index=False)
        self.logger.info(f"✅ Portfolio template saved to {filename}")
        
        print(f"""
📋 Portfolio Template Created: {filename}

To use your real portfolio:
1. Edit {filename} with your actual holdings
2. Update tickers, shares, and prices
3. Save the file
4. The system will use this instead of mock data

Example format:
ticker,shares,current_price,sector,avg_entry_price
AAPL,100,150.00,Technology,140.00
MSFT,50,300.00,Technology,280.00
        """)
        
        return filename
    
    def auto_detect_portfolio_file(self) -> Optional[str]:
        """Auto-detect portfolio file in common locations."""
        possible_files = [
            'portfolio.csv',
            'holdings.csv',
            'positions.csv',
            'portfolio.json',
            'data/portfolio.csv',
            'data/holdings.csv',
            'user_portfolio.csv'
        ]
        
        for file_path in possible_files:
            if Path(file_path).exists():
                self.logger.info(f"📂 Found portfolio file: {file_path}")
                return file_path
        
        return None

def main():
    """Test portfolio data manager."""
    logging.basicConfig(level=logging.INFO)
    
    manager = PortfolioDataManager()
    
    # Check for existing portfolio file
    portfolio_file = manager.auto_detect_portfolio_file()
    
    if portfolio_file:
        if portfolio_file.endswith('.csv'):
            df = manager.load_portfolio_from_csv(portfolio_file)
        elif portfolio_file.endswith('.json'):
            df = manager.load_portfolio_from_json(portfolio_file)
    else:
        # Create template
        template_file = manager.save_portfolio_template()
        print(f"No portfolio file found. Created template: {template_file}")
        return
    
    # Show summary
    summary = manager.get_portfolio_summary()
    print("Portfolio Summary:", summary)

if __name__ == "__main__":
    main() 