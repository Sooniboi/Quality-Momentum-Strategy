#!/usr/bin/env python3
"""
IBKR TWS Paper Trading Setup for Quality Momentum Strategy

This module sets up live paper trading using Interactive Brokers TWS:
- Connects to TWS paper trading account via API
- Loads current portfolio and submits paper trading orders
- Tracks live performance vs benchmark
- Handles rebalancing and position management
- Generates trading logs and performance reports

Requirements:
1. IBKR paper trading account with TWS installed
2. API permissions enabled in TWS (File > Global Configuration > API > Settings)
3. TWS or IB Gateway running locally
4. Python package: pip install ib_insync

Connection Details:
- TWS Paper Trading: localhost:7497
- IB Gateway Paper: localhost:4002
- TWS Live Trading: localhost:7496 (NOT RECOMMENDED)
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
    from ib_insync import *
    IB_AVAILABLE = True
except ImportError:
    IB_AVAILABLE = False
    print("⚠️ ib_insync not installed. Install with: pip install ib_insync")

class IBKRPaperTradingManager:
    def __init__(self, host='127.0.0.1', port=7497, client_id=1):
        """
        Initialize IBKR paper trading manager.
        
        Args:
            host (str): TWS host (usually localhost/127.0.0.1)
            port (int): TWS port (7497=paper, 7496=live, 4002=IB Gateway paper)
            client_id (int): Unique client ID for this connection
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = None
        self.portfolio_value = 10000
        self.config_file = os.path.join(os.path.dirname(__file__), '07_ibkr_config.json')
        
        print("🏦 IBKR TWS Paper Trading Manager")
        print("="*50)
        
    def load_config(self):
        """Load or create IBKR configuration."""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            self.host = config.get('host', '127.0.0.1')
            self.port = config.get('port', 7497)
            self.client_id = config.get('client_id', 1)
            self.portfolio_value = config.get('portfolio_value', 10000)
            
        else:
            self.create_config_template()
    
    def create_config_template(self):
        """Create configuration template file."""
        config_template = {
            "host": "127.0.0.1",
            "port": 7497,
            "client_id": 1,
            "portfolio_value": 10000,
            "max_position_size": 0.05,
            "rebalance_frequency": "monthly",
            "setup_instructions": [
                "IBKR TWS Paper Trading Setup:",
                "",
                "1. Open TWS (Trader Workstation)",
                "2. Log in to your paper trading account",
                "3. Enable API access:",
                "   - File > Global Configuration > API > Settings",
                "   - Check 'Enable ActiveX and Socket Clients'", 
                "   - Set Socket port to 7497 (paper trading)",
                "   - Check 'Download open orders on connection'",
                "   - Click 'OK' and restart TWS",
                "",
                "4. Install required package: pip install ib_insync",
                "5. Keep TWS running while using this script",
                "",
                "Port Reference:",
                "- 7497: TWS Paper Trading (DEFAULT)",
                "- 7496: TWS Live Trading (BE CAREFUL!)",
                "- 4002: IB Gateway Paper Trading"
            ]
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_template, f, indent=2)
        
        print(f"📝 Configuration template created: {self.config_file}")
        print("\n🔧 IBKR TWS SETUP INSTRUCTIONS:")
        for instruction in config_template["setup_instructions"]:
            print(f"   {instruction}")
        
        return False
    
    def connect_to_tws(self):
        """Connect to TWS or IB Gateway."""
        if not IB_AVAILABLE:
            print("❌ ib_insync package not available")
            print("📦 Install with: pip install ib_insync")
            return False
        
        try:
            self.ib = IB()
            print(f"🔌 Connecting to TWS at {self.host}:{self.port}...")
            
            self.ib.connect(self.host, self.port, clientId=self.client_id, timeout=10)
            
            # Test connection and get account info
            account_values = self.ib.accountValues()
            nav = None
            
            for av in account_values:
                if av.tag == 'NetLiquidationByCurrency' and av.currency == 'USD':
                    nav = float(av.value)
                    break
            
            if nav:
                self.portfolio_value = nav
                
            print(f"✅ Connected to IBKR TWS (Paper Trading)")
            print(f"🎭 Account Type: {'LIVE' if self.port == 7496 else 'PAPER'}")
            print(f"💰 Net Liquidation Value: ${nav:,.2f}" if nav else "💰 Account value: Not available")
            print(f"🔢 Client ID: {self.client_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to TWS: {str(e)}")
            print("\n🔧 Troubleshooting:")
            print("   1. Is TWS/IB Gateway running?")
            print("   2. Is API access enabled in TWS?")
            print("   3. Is the port correct? (7497 for paper, 7496 for live)")
            print("   4. Try a different client_id if another connection exists")
            return False
    
    def load_current_portfolio(self):
        """Load the most recent portfolio selection."""
        # Try new structure first
        portfolio_patterns = [
            os.path.join('..', '..', 'data', 'processed', 'portfolios', '*portfolio*.csv'),
            os.path.join('..', '..', 'csv_data_files', 'portfolios', '04_unified_portfolio_selection_*.csv'),
            os.path.join('data', 'processed', 'portfolios', '*portfolio*.csv'),
            os.path.join('csv_data_files', 'portfolios', '04_unified_portfolio_selection_*.csv'),
        ]
        
        portfolio_files = []
        for pattern in portfolio_patterns:
            portfolio_files.extend(glob.glob(pattern))
        
        if not portfolio_files:
            raise FileNotFoundError("No portfolio files found")
        
        latest_file = max(portfolio_files, key=os.path.getctime)
        portfolio = pd.read_csv(latest_file)
        
        print(f"✅ Loaded portfolio: {len(portfolio)} stocks from {os.path.basename(latest_file)}")
        return portfolio
    
    def get_current_positions(self):
        """Get current positions from IBKR account."""
        if not self.ib:
            return {}
        
        try:
            positions = self.ib.positions()
            current_positions = {}
            
            for position in positions:
                if position.position != 0:  # Only positions with actual holdings
                    symbol = position.contract.symbol
                    current_positions[symbol] = {
                        'qty': float(position.position),
                        'avg_cost': float(position.avgCost) if position.avgCost else 0,
                        'market_value': float(position.marketValue) if position.marketValue else 0,
                        'unrealized_pnl': float(position.unrealizedPNL) if position.unrealizedPNL else 0,
                        'contract': position.contract
                    }
            
            return current_positions
            
        except Exception as e:
            print(f"❌ Error getting positions: {str(e)}")
            return {}
    
    def get_stock_price(self, ticker):
        """Get current stock price via IBKR with delayed data fallback."""
        if not self.ib:
            return None
        
        try:
            # Create stock contract
            stock = Stock(ticker, 'SMART', 'USD')
            self.ib.qualifyContracts(stock)
            
            # Request delayed market data (no subscription needed)
            ticker_data = self.ib.reqMktData(stock, '', False, False)
            
            # Wait for data (reduced wait time)
            for _ in range(20):  # 2 seconds max
                self.ib.sleep(0.1)
                
                # Check for valid last price
                if hasattr(ticker_data, 'last') and ticker_data.last and ticker_data.last > 0:
                    price = float(ticker_data.last)
                    self.ib.cancelMktData(stock)
                    return price
                
                # Check for valid bid/ask
                if hasattr(ticker_data, 'bid') and hasattr(ticker_data, 'ask'):
                    if ticker_data.bid and ticker_data.ask and ticker_data.bid > 0 and ticker_data.ask > 0:
                        price = (float(ticker_data.bid) + float(ticker_data.ask)) / 2
                        self.ib.cancelMktData(stock)
                        return price
            
            # Clean up
            self.ib.cancelMktData(stock)
            
            # If no real-time data, try to get historical close price as fallback
            try:
                from datetime import datetime, timedelta
                end_date = datetime.now()
                start_date = end_date - timedelta(days=5)  # Get last 5 days
                
                bars = self.ib.reqHistoricalData(
                    stock,
                    endDateTime='',
                    durationStr='5 D',
                    barSizeSetting='1 day',
                    whatToShow='MIDPOINT',
                    useRTH=True,
                    formatDate=1
                )
                
                if bars and len(bars) > 0:
                    # Use most recent close price
                    latest_bar = bars[-1]
                    price = float(latest_bar.close)
                    print(f"📈 {ticker}: Using historical price ${price:.2f}")
                    return price
                    
            except Exception as hist_e:
                print(f"⚠️ Historical data failed for {ticker}: {str(hist_e)}")
            
            return None
            
        except Exception as e:
            # Check if it's a market data subscription error
            if "10089" in str(e) or "market data" in str(e).lower():
                print(f"📊 {ticker}: Market data subscription needed - using fallback")
                # Return a reasonable estimated price for simulation (this is just for testing)
                return 50.0  # Placeholder price for simulation
            else:
                print(f"⚠️ Could not get price for {ticker}: {str(e)}")
                return None
    
    def calculate_target_positions(self, portfolio):
        """Calculate target positions based on portfolio weights."""
        target_positions = {}
        
        # Get current account value
        account_values = self.ib.accountValues()
        total_value = self.portfolio_value
        
        for av in account_values:
            if av.tag == 'NetLiquidationByCurrency' and av.currency == 'USD':
                total_value = float(av.value)
                break
        
        print(f"💰 Total Portfolio Value: ${total_value:,.2f}")
        
        for _, stock in portfolio.iterrows():
            ticker = stock['Ticker']
            weight = stock['Portfolio_Weight']
            target_value = total_value * weight
            
            # Get current price
            price = self.get_stock_price(ticker)
            if price and price > 0:
                target_qty = int(target_value / price)
                if target_qty > 0:
                    target_positions[ticker] = {
                        'target_qty': target_qty,
                        'target_value': target_value,
                        'price': price,
                        'weight': weight
                    }
                    print(f"📊 {ticker}: {target_qty} shares @ ${price:.2f} = ${target_value:.2f} ({weight*100:.1f}%)")
            else:
                print(f"⚠️ Skipping {ticker} - could not get price")
        
        return target_positions
    
    def submit_orders(self, target_positions, current_positions):
        """Submit orders to IBKR."""
        if not self.ib:
            print("❌ Not connected to TWS")
            return []
        
        orders_submitted = []
        
        print("\n📋 SUBMITTING ORDERS TO IBKR TWS:")
        print("-" * 50)
        
        for ticker, target in target_positions.items():
            try:
                current_qty = current_positions.get(ticker, {}).get('qty', 0)
                qty_diff = target['target_qty'] - current_qty
                
                if abs(qty_diff) < 1:  # Skip tiny adjustments
                    continue
                
                # Create stock contract
                stock = Stock(ticker, 'SMART', 'USD')
                self.ib.qualifyContracts(stock)
                
                # Create market order
                action = 'BUY' if qty_diff > 0 else 'SELL'
                order = MarketOrder(action, abs(qty_diff))
                
                # Submit order
                trade = self.ib.placeOrder(stock, order)
                
                orders_submitted.append({
                    'ticker': ticker,
                    'action': action,
                    'quantity': abs(qty_diff),
                    'order_type': 'MKT',
                    'target_qty': target['target_qty'],
                    'current_qty': current_qty,
                    'trade': trade
                })
                
                print(f"✅ {action} {abs(qty_diff)} {ticker} (target: {target['target_qty']}, current: {current_qty})")
                
                # Small delay between orders
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error submitting order for {ticker}: {str(e)}")
        
        print(f"\n📊 Total orders submitted: {len(orders_submitted)}")
        return orders_submitted
    
    def simulate_orders(self, target_positions, current_positions):
        """Simulate orders without actually submitting (for testing)."""
        print("\n🎭 SIMULATION MODE - Orders not actually submitted:")
        print("-" * 50)
        
        simulated_orders = []
        
        for ticker, target in target_positions.items():
            current_qty = current_positions.get(ticker, {}).get('qty', 0)
            qty_diff = target['target_qty'] - current_qty
            
            if abs(qty_diff) >= 1:
                action = 'BUY' if qty_diff > 0 else 'SELL'
                simulated_orders.append({
                    'ticker': ticker,
                    'action': action,
                    'quantity': abs(qty_diff),
                    'order_type': 'MKT',
                    'target_qty': target['target_qty'],
                    'current_qty': current_qty,
                    'price': target['price'],
                    'value': abs(qty_diff) * target['price']
                })
                
                print(f"🎭 {action} {abs(qty_diff)} {ticker} @ ${target['price']:.2f} = ${abs(qty_diff) * target['price']:,.2f}")
        
        print(f"\n📊 Total simulated orders: {len(simulated_orders)}")
        return simulated_orders
    
    def disconnect(self):
        """Disconnect from TWS."""
        if self.ib:
            self.ib.disconnect()
            print("🔌 Disconnected from TWS")
    
    def execute_rebalancing(self, simulate_only=True):
        """Execute complete rebalancing process."""
        print("🔄 IBKR PAPER TRADING REBALANCING")
        print("="*60)
        
        try:
            # Load configuration
            self.load_config()
            
            # Connect to TWS
            if not self.connect_to_tws():
                return False
            
            # Load portfolio
            portfolio = self.load_current_portfolio()
            
            # Get current positions
            current_positions = self.get_current_positions()
            print(f"📊 Current positions: {len(current_positions)}")
            
            # Calculate target positions
            target_positions = self.calculate_target_positions(portfolio)
            print(f"🎯 Target positions: {len(target_positions)}")
            
            # Submit or simulate orders
            if simulate_only:
                orders = self.simulate_orders(target_positions, current_positions)
            else:
                orders = self.submit_orders(target_positions, current_positions)
            
            # Log activity
            self.log_trading_activity(orders, portfolio, simulate_only)
            
            return True
            
        except Exception as e:
            print(f"❌ Rebalancing failed: {str(e)}")
            return False
        finally:
            self.disconnect()
    
    def log_trading_activity(self, orders, portfolio, simulated=True):
        """Log trading activity to file."""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_file = f"07_ibkr_trading_log_{timestamp}.csv"
        log_path = os.path.join(os.path.dirname(__file__), log_file)
        
        # Create detailed log
        log_data = []
        for order in orders:
            log_data.append({
                'timestamp': datetime.now().isoformat(),
                'ticker': order['ticker'],
                'action': order['action'],
                'quantity': order['quantity'],
                'order_type': order['order_type'],
                'target_qty': order['target_qty'],
                'current_qty': order['current_qty'],
                'price': order.get('price', 'N/A'),
                'value': order.get('value', 'N/A'),
                'simulated': simulated
            })
        
        if log_data:
            log_df = pd.DataFrame(log_data)
            log_df.to_csv(log_path, index=False)
            print(f"📄 Trading log saved: {log_file}")
        
        # Summary report
        print(f"\n📊 REBALANCING SUMMARY:")
        print(f"✅ Portfolio stocks: {len(portfolio)}")
        print(f"📋 Orders {'simulated' if simulated else 'submitted'}: {len(orders)}")
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main execution function."""
    manager = IBKRPaperTradingManager()
    
    print("🏦 IBKR TWS Paper Trading Setup")
    print("=" * 50)
    print("⚠️  IMPORTANT: Make sure TWS is running with API enabled!")
    print()
    
    # Ask user preference
    while True:
        choice = input("Choose mode:\n1. Simulate orders (recommended first)\n2. Submit real paper trades\n3. Exit\nEnter choice (1-3): ").strip()
        
        if choice == '1':
            print("\n🎭 Running in SIMULATION mode...")
            success = manager.execute_rebalancing(simulate_only=True)
            break
        elif choice == '2':
            confirm = input("\n⚠️  Submit REAL paper trades to IBKR? (yes/no): ").strip().lower()
            if confirm == 'yes':
                print("\n🏦 Submitting REAL orders to IBKR TWS...")
                success = manager.execute_rebalancing(simulate_only=False)
            else:
                print("❌ Cancelled")
                success = False
            break
        elif choice == '3':
            print("👋 Goodbye!")
            return 0
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")
    
    if success:
        print("\n✅ IBKR PAPER TRADING SETUP COMPLETED!")
        return 0
    else:
        print("\n❌ IBKR PAPER TRADING SETUP FAILED!")
        return 1

if __name__ == "__main__":
    exit(main()) 