#!/usr/bin/env python3
"""
Paper Trading Setup for Quality Momentum Strategy

This module sets up live paper trading using Alpaca Markets API:
- Loads current portfolio and submits paper trading orders
- Tracks live performance vs benchmark
- Handles rebalancing and position management
- Generates trading logs and performance reports

Requires Alpaca paper trading account (free):
https://alpaca.markets/
"""

import pandas as pd
import numpy as np
import json
import os
import glob
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    print("⚠️ alpaca-trade-api not installed. Install with: pip install alpaca-trade-api")

class PaperTradingManager:
    def __init__(self, config_file='07_alpaca_config.json'):
        """
        Initialize paper trading manager.
        
        Args:
            config_file (str): Path to Alpaca configuration file
        """
        self.config_file = os.path.join(os.path.dirname(__file__), config_file)
        self.api = None
        self.portfolio_value = 10000  # Starting value
        self.load_config()
        
    def load_config(self):
        """Load or create Alpaca configuration."""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            if config.get('api_key') and config.get('secret_key'):
                self.setup_api(config['api_key'], config['secret_key'])
            else:
                print("⚠️ Alpaca API keys not configured")
        else:
            self.create_config_template()
    
    def create_config_template(self):
        """Create configuration template file."""
        config_template = {
            "api_key": "YOUR_ALPACA_API_KEY_HERE",
            "secret_key": "YOUR_ALPACA_SECRET_KEY_HERE",
            "base_url": "https://paper-api.alpaca.markets",
            "data_url": "https://data.alpaca.markets",
            "portfolio_value": 10000,
            "max_position_size": 0.05,
            "rebalance_frequency": "monthly",
            "setup_instructions": [
                "1. Sign up for free Alpaca paper trading account at https://alpaca.markets/",
                "2. Get your API keys from the dashboard",
                "3. Replace YOUR_ALPACA_API_KEY_HERE with your actual API key",
                "4. Replace YOUR_ALPACA_SECRET_KEY_HERE with your actual secret key",
                "5. Save this file and run the script again"
            ]
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_template, f, indent=2)
        
        print(f"📝 Configuration template created: {self.config_file}")
        print("🔧 Please follow the setup instructions in the file")
        return False
    
    def setup_api(self, api_key, secret_key):
        """Setup Alpaca API connection."""
        if not ALPACA_AVAILABLE:
            print("❌ alpaca-trade-api package not available")
            return False
        
        try:
            self.api = tradeapi.REST(
                api_key, 
                secret_key, 
                'https://paper-api.alpaca.markets',
                api_version='v2'
            )
            
            # Test connection
            account = self.api.get_account()
            print(f"✅ Connected to Alpaca (Paper Trading)")
            print(f"📊 Account Status: {account.status}")
            print(f"💰 Buying Power: ${float(account.buying_power):,.2f}")
            
            self.portfolio_value = float(account.portfolio_value)
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to Alpaca: {str(e)}")
            return False
    
    def load_current_portfolio(self):
        """Load the most recent portfolio selection."""
        portfolio_pattern = os.path.join(
            os.path.dirname(__file__), '..', 'csv_data_files', 'portfolios', 
            '04_unified_portfolio_selection_*.csv'
        )
        portfolio_files = glob.glob(portfolio_pattern)
        
        if not portfolio_files:
            raise FileNotFoundError("No portfolio files found")
        
        latest_file = max(portfolio_files, key=os.path.getctime)
        portfolio = pd.read_csv(latest_file)
        
        print(f"✅ Loaded portfolio: {len(portfolio)} stocks from {os.path.basename(latest_file)}")
        return portfolio
    
    def get_current_positions(self):
        """Get current positions from Alpaca account."""
        if not self.api:
            return {}
        
        try:
            positions = self.api.list_positions()
            current_positions = {}
            
            for position in positions:
                current_positions[position.symbol] = {
                    'qty': float(position.qty),
                    'market_value': float(position.market_value),
                    'avg_entry_price': float(position.avg_entry_price),
                    'unrealized_pl': float(position.unrealized_pl),
                    'unrealized_plpc': float(position.unrealized_plpc)
                }
            
            return current_positions
            
        except Exception as e:
            print(f"❌ Error getting positions: {str(e)}")
            return {}
    
    def get_stock_price(self, ticker):
        """Get current stock price."""
        if not self.api:
            return None
        
        try:
            # Get latest trade
            trade = self.api.get_latest_trade(ticker)
            return float(trade.price)
            
        except Exception as e:
            print(f"⚠️ Could not get price for {ticker}: {str(e)}")
            return None
    
    def calculate_target_positions(self, portfolio):
        """Calculate target positions based on portfolio weights."""
        target_positions = {}
        
        # Get current account value
        if self.api:
            account = self.api.get_account()
            total_value = float(account.portfolio_value)
        else:
            total_value = self.portfolio_value
        
        print(f"💰 Total Portfolio Value: ${total_value:,.2f}")
        
        for _, stock in portfolio.iterrows():
            ticker = stock['Ticker']
            weight = stock['Portfolio_Weight']
            target_value = total_value * weight
            
            # Get current price
            price = self.get_stock_price(ticker)
            if price:
                target_qty = int(target_value / price)
                if target_qty > 0:
                    target_positions[ticker] = {
                        'target_qty': target_qty,
                        'target_value': target_value,
                        'price': price,
                        'weight': weight
                    }
            else:
                print(f"⚠️ Skipping {ticker} - could not get price")
        
        return target_positions
    
    def submit_orders(self, target_positions, current_positions):
        """Submit orders to rebalance portfolio."""
        if not self.api:
            print("❌ No API connection - simulating orders")
            return self.simulate_orders(target_positions, current_positions)
        
        orders_submitted = []
        
        # Calculate orders needed
        for ticker, target in target_positions.items():
            current_qty = current_positions.get(ticker, {}).get('qty', 0)
            target_qty = target['target_qty']
            qty_diff = target_qty - current_qty
            
            if abs(qty_diff) > 0:  # Only trade if difference is significant
                try:
                    if qty_diff > 0:
                        # Buy order
                        order = self.api.submit_order(
                            symbol=ticker,
                            qty=qty_diff,
                            side='buy',
                            type='market',
                            time_in_force='day'
                        )
                        print(f"📈 BUY {qty_diff} shares of {ticker} at ~${target['price']:.2f}")
                        
                    else:
                        # Sell order
                        order = self.api.submit_order(
                            symbol=ticker,
                            qty=abs(qty_diff),
                            side='sell',
                            type='market',
                            time_in_force='day'
                        )
                        print(f"📉 SELL {abs(qty_diff)} shares of {ticker} at ~${target['price']:.2f}")
                    
                    orders_submitted.append({
                        'ticker': ticker,
                        'side': 'buy' if qty_diff > 0 else 'sell',
                        'qty': abs(qty_diff),
                        'order_id': order.id,
                        'submitted_at': datetime.now()
                    })
                    
                except Exception as e:
                    print(f"❌ Failed to submit order for {ticker}: {str(e)}")
        
        # Sell positions not in target portfolio
        for ticker in current_positions:
            if ticker not in target_positions and current_positions[ticker]['qty'] > 0:
                try:
                    qty = current_positions[ticker]['qty']
                    order = self.api.submit_order(
                        symbol=ticker,
                        qty=qty,
                        side='sell',
                        type='market',
                        time_in_force='day'
                    )
                    print(f"📉 SELL ALL {qty} shares of {ticker} (not in new portfolio)")
                    
                    orders_submitted.append({
                        'ticker': ticker,
                        'side': 'sell',
                        'qty': qty,
                        'order_id': order.id,
                        'submitted_at': datetime.now()
                    })
                    
                except Exception as e:
                    print(f"❌ Failed to sell {ticker}: {str(e)}")
        
        return orders_submitted
    
    def simulate_orders(self, target_positions, current_positions):
        """Simulate orders for testing without API."""
        orders_simulated = []
        
        print("🎯 SIMULATING ORDERS (No API Connection)")
        print("-" * 50)
        
        for ticker, target in target_positions.items():
            current_qty = current_positions.get(ticker, {}).get('qty', 0)
            target_qty = target['target_qty']
            qty_diff = target_qty - current_qty
            
            if abs(qty_diff) > 0:
                if qty_diff > 0:
                    print(f"📈 [SIM] BUY {qty_diff} shares of {ticker} at ${target['price']:.2f}")
                else:
                    print(f"📉 [SIM] SELL {abs(qty_diff)} shares of {ticker} at ${target['price']:.2f}")
                
                orders_simulated.append({
                    'ticker': ticker,
                    'side': 'buy' if qty_diff > 0 else 'sell',
                    'qty': abs(qty_diff),
                    'price': target['price'],
                    'simulated': True,
                    'submitted_at': datetime.now()
                })
        
        return orders_simulated
    
    def log_trading_activity(self, orders, portfolio):
        """Log trading activity to CSV file."""
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(os.path.dirname(__file__), f'07_trading_log_{today}.csv')
        
        # Create log entries
        log_entries = []
        for order in orders:
            log_entries.append({
                'timestamp': order['submitted_at'],
                'ticker': order['ticker'],
                'side': order['side'],
                'quantity': order['qty'],
                'price': order.get('price', 'Market'),
                'order_id': order.get('order_id', 'SIMULATED'),
                'status': 'SIMULATED' if order.get('simulated') else 'SUBMITTED'
            })
        
        if log_entries:
            log_df = pd.DataFrame(log_entries)
            
            # Append to existing log or create new
            if os.path.exists(log_file):
                existing_log = pd.read_csv(log_file)
                combined_log = pd.concat([existing_log, log_df], ignore_index=True)
            else:
                combined_log = log_df
            
            combined_log.to_csv(log_file, index=False)
            print(f"📝 Trading activity logged: {log_file}")
        
        # Also log portfolio composition
        portfolio_log_file = os.path.join(os.path.dirname(__file__), f'07_portfolio_snapshot_{today}.csv')
        portfolio.to_csv(portfolio_log_file, index=False)
        print(f"💼 Portfolio snapshot saved: {portfolio_log_file}")
    
    def generate_performance_report(self):
        """Generate performance tracking report."""
        if not self.api:
            print("📊 Performance tracking requires API connection")
            return
        
        try:
            account = self.api.get_account()
            positions = self.get_current_positions()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'account_status': account.status,
                'portfolio_value': float(account.portfolio_value),
                'buying_power': float(account.buying_power),
                'day_trade_buying_power': float(account.day_trade_buying_power),
                'equity': float(account.equity),
                'total_positions': len(positions),
                'positions': positions
            }
            
            # Save report
            report_file = os.path.join(os.path.dirname(__file__), 
                                     f'07_performance_report_{datetime.now().strftime("%Y-%m-%d")}.json')
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"📊 Performance report saved: {report_file}")
            
            # Print summary
            print("\n💰 CURRENT PORTFOLIO STATUS")
            print("=" * 50)
            print(f"Portfolio Value: ${float(account.portfolio_value):,.2f}")
            print(f"Equity: ${float(account.equity):,.2f}")
            print(f"Buying Power: ${float(account.buying_power):,.2f}")
            print(f"Total Positions: {len(positions)}")
            
            if positions:
                print("\n📈 CURRENT POSITIONS:")
                for ticker, pos in positions.items():
                    pnl_pct = pos['unrealized_plpc'] * 100
                    print(f"  {ticker}: {pos['qty']} shares, "
                          f"${pos['market_value']:.2f} "
                          f"({pnl_pct:+.1f}%)")
        
        except Exception as e:
            print(f"❌ Error generating performance report: {str(e)}")
    
    def execute_rebalancing(self):
        """Execute complete rebalancing process."""
        print("🔄 PAPER TRADING REBALANCING SYSTEM")
        print("=" * 60)
        
        try:
            # Load current portfolio strategy
            portfolio = self.load_current_portfolio()
            
            # Get current positions
            current_positions = self.get_current_positions()
            print(f"📊 Current positions: {len(current_positions)}")
            
            # Calculate target positions
            target_positions = self.calculate_target_positions(portfolio)
            print(f"🎯 Target positions: {len(target_positions)}")
            
            # Submit orders
            orders = self.submit_orders(target_positions, current_positions)
            print(f"📝 Orders submitted: {len(orders)}")
            
            # Log activity
            self.log_trading_activity(orders, portfolio)
            
            # Generate performance report
            self.generate_performance_report()
            
            print("\n✅ REBALANCING COMPLETED!")
            return True
            
        except Exception as e:
            print(f"❌ Rebalancing failed: {str(e)}")
            return False

def main():
    """Main execution function."""
    print("🎯 PAPER TRADING SETUP - QUALITY MOMENTUM STRATEGY")
    print("=" * 70)
    
    # Initialize paper trading manager
    manager = PaperTradingManager()
    
    # Check if properly configured
    if not manager.api and ALPACA_AVAILABLE:
        print("\n🔧 SETUP REQUIRED:")
        print("1. Check the configuration file that was created")
        print("2. Sign up for free Alpaca paper trading account")
        print("3. Add your API keys to the configuration")
        print("4. Run this script again")
        return 1
    
    # Execute rebalancing
    success = manager.execute_rebalancing()
    
    if success:
        print("\n🎉 PAPER TRADING SETUP COMPLETED!")
        print("\n📋 NEXT STEPS:")
        print("- Monitor your paper trading account at https://alpaca.markets")
        print("- Run this script monthly to rebalance")
        print("- Check performance reports in paper_trading/ folder")
        print("- Consider setting up automated scheduling")
    else:
        print("\n❌ PAPER TRADING SETUP FAILED!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 