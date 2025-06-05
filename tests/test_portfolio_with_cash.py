#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add the src directory to sys.path
current_dir = Path(__file__).parent.absolute()
src_dir = current_dir / 'src' / 'utils'
sys.path.insert(0, str(src_dir))

from weekly_performance_reporter import WeeklyPerformanceReporter

def test_portfolio_with_cash():
    """Test that portfolio correctly includes cash positions and totals."""
    print("🔄 Testing Portfolio with Cash Integration...")
    print("=" * 60)
    
    try:
        reporter = WeeklyPerformanceReporter()
        
        # Collect portfolio data
        print("📊 Collecting portfolio data...")
        portfolio_data = reporter.collect_real_portfolio_data()
        
        positions = portfolio_data.get('positions', [])
        total_value = portfolio_data.get('total_value', 0)
        account_info = portfolio_data.get('account_info', {})
        
        # Separate positions by type
        stock_positions = [p for p in positions if p.get('position_type') != 'cash']
        cash_positions = [p for p in positions if p.get('position_type') == 'cash']
        
        print(f"\n📋 Portfolio Breakdown:")
        print(f"  • Total Positions: {len(positions)}")
        print(f"  • Stock Positions: {len(stock_positions)}")
        print(f"  • Cash Positions: {len(cash_positions)}")
        
        # Calculate totals
        stock_value = sum(p.get('market_value', 0) for p in stock_positions)
        cash_value = sum(p.get('market_value', 0) for p in cash_positions)
        
        print(f"\n💰 Value Breakdown:")
        print(f"  • Stock Value: ${stock_value:,.2f}")
        print(f"  • Cash Value: ${cash_value:,.2f}")
        print(f"  • Total Portfolio: ${total_value:,.2f}")
        print(f"  • Alpaca Portfolio Value: ${account_info.get('portfolio_value', 0):,.2f}")
        
        # Verify totals match
        calculated_total = stock_value + cash_value
        alpaca_total = account_info.get('portfolio_value', 0)
        
        print(f"\n✅ Verification:")
        print(f"  • Calculated Total: ${calculated_total:,.2f}")
        print(f"  • Alpaca Total: ${alpaca_total:,.2f}")
        print(f"  • Match: {'✅ YES' if abs(calculated_total - alpaca_total) < 1 else '❌ NO'}")
        
        # Check cash percentage
        cash_percentage = (cash_value / total_value * 100) if total_value > 0 else 0
        print(f"  • Cash Percentage: {cash_percentage:.1f}%")
        
        # Show some sample positions
        if stock_positions:
            print(f"\n📈 Sample Stock Positions:")
            for pos in stock_positions[:5]:
                ticker = pos.get('ticker')
                value = pos.get('market_value', 0)
                weight = pos.get('weight', 0) * 100
                pl = pos.get('unrealized_pl', 0)
                print(f"  • {ticker}: ${value:,.0f} ({weight:.1f}%) | P&L: ${pl:+.0f}")
        
        if cash_positions:
            print(f"\n💵 Cash Position:")
            for pos in cash_positions:
                value = pos.get('market_value', 0)
                weight = pos.get('weight', 0) * 100
                print(f"  • CASH: ${value:,.2f} ({weight:.1f}%)")
        
        print(f"\n✅ Portfolio with cash integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_portfolio_with_cash()
    sys.exit(0 if success else 1) 