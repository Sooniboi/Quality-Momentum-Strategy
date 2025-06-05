#!/usr/bin/env python3

import sys
import os
import logging
from pathlib import Path

# Add the trading/paper_trading directory to sys.path
current_dir = Path(__file__).parent.absolute()
trading_dir = current_dir / 'trading' / 'paper_trading'
sys.path.insert(0, str(trading_dir))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_get_current_positions():
    """Test the get_current_positions method from AlpacaPaperTrader."""
    print("🔄 Testing get_current_positions() method...")
    print("=" * 60)
    
    try:
        from alpaca_connector import AlpacaPaperTrader
        
        # Initialize the trader
        print("🔌 Initializing AlpacaPaperTrader...")
        trader = AlpacaPaperTrader()
        
        # Get account info first
        print("\n💰 Getting account information...")
        account_info = trader.get_account_info()
        print(f"Portfolio Value: ${account_info.get('portfolio_value', 0):,.2f}")
        print(f"Buying Power: ${account_info.get('buying_power', 0):,.2f}")
        print(f"Cash: ${account_info.get('cash', 0):,.2f}")
        
        # Test get_current_positions method
        print("\n📊 Testing get_current_positions()...")
        positions = trader.get_current_positions()
        
        print(f"✅ Retrieved {len(positions)} positions")
        
        if positions:
            print("\n📋 Current Positions:")
            print("-" * 80)
            print(f"{'Symbol':<8} {'Shares':<10} {'Price':<12} {'Value':<12} {'Weight':<8} {'P&L':<12}")
            print("-" * 80)
            
            total_value = sum(pos['market_value'] for pos in positions.values())
            
            # Sort by market value (largest first)
            sorted_positions = sorted(positions.items(), 
                                    key=lambda x: x[1]['market_value'], 
                                    reverse=True)
            
            for symbol, pos in sorted_positions:
                print(f"{symbol:<8} {pos['shares']:<10} "
                      f"${pos['current_price']:<11.2f} "
                      f"${pos['market_value']:<11.2f} "
                      f"{pos['weight']:<7.2%} "
                      f"${pos['unrealized_pl']:<11.2f}")
            
            print("-" * 80)
            print(f"{'TOTAL':<8} {'':<10} {'':<12} ${total_value:<11.2f} {'100.0%':<8} {'':<12}")
            
            # Show summary stats
            print(f"\n📊 Summary:")
            print(f"  • Total Positions: {len(positions)}")
            print(f"  • Total Market Value: ${total_value:,.2f}")
            print(f"  • Largest Position: {sorted_positions[0][0]} (${sorted_positions[0][1]['market_value']:,.2f})")
            print(f"  • Smallest Position: {sorted_positions[-1][0]} (${sorted_positions[-1][1]['market_value']:,.2f})")
            
            # Calculate total P&L
            total_pl = sum(pos['unrealized_pl'] for pos in positions.values())
            total_pl_pct = (total_pl / (total_value - total_pl)) * 100 if total_value > total_pl else 0
            print(f"  • Total Unrealized P&L: ${total_pl:,.2f} ({total_pl_pct:.2f}%)")
            
        else:
            print("⚠️ No positions found in account")
            
        print(f"\n✅ get_current_positions() test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure Alpaca Trade API is installed: pip install alpaca-trade-api")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_get_current_positions()
    sys.exit(0 if success else 1) 