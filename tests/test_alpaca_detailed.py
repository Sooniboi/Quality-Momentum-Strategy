#!/usr/bin/env python3

import logging
import sys
from src.utils.alpaca_portfolio_data import AlpacaPortfolioData

# Setup detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_alpaca_connection():
    logger.info("🚀 Starting detailed Alpaca connection test...")
    
    # Initialize Alpaca data provider
    data_provider = AlpacaPortfolioData()
    
    if data_provider.alpaca is None:
        logger.error("❌ Alpaca connection failed")
        return False
    
    logger.info("✅ Alpaca connection successful")
    
    # Test getting positions
    logger.info("📊 Testing portfolio positions...")
    positions = data_provider.get_portfolio_positions()
    logger.info(f"📊 Retrieved {len(positions)} positions")
    
    if not positions.empty:
        logger.info("Top 5 positions:")
        for _, pos in positions.head().iterrows():
            logger.info(f"  {pos['ticker']}: {pos['shares']} shares @ ${pos['current_price']:.2f}")
    
    # Test account info
    logger.info("💰 Testing account information...")
    account_info = data_provider.get_account_info()
    logger.info(f"💰 Portfolio value: ${account_info['portfolio_value']:,.2f}")
    
    return True

if __name__ == "__main__":
    success = test_alpaca_connection()
    sys.exit(0 if success else 1) 