#!/usr/bin/env python3

import os
from dotenv import load_dotenv
import alpaca_trade_api as api

# Clear any existing environment variables first
for key in ['ALPACA_API_KEY', 'ALPACA_SECRET_KEY', 'ALPACA_BASE_URL']:
    if key in os.environ:
        del os.environ[key]

# Load environment variables from .env file
load_dotenv(override=True)

api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_SECRET_KEY') 
base_url = os.getenv('ALPACA_BASE_URL')

print(f'API Key: {api_key[:10] if api_key else "NOT FOUND"}...')
print(f'Base URL: {base_url}')

if not api_key or api_key == 'your_alpaca_api_key_here':
    print('❌ API key not set or still using placeholder')
    exit(1)

if not secret_key or secret_key == 'your_alpaca_secret_key_here':
    print('❌ Secret key not set or still using placeholder')
    exit(1)

try:
    alpaca = api.REST(api_key, secret_key, base_url, api_version='v2')
    account = alpaca.get_account()
    print(f'✅ Connection successful!')
    print(f'Account Status: {account.status}')
    print(f'Portfolio Value: ${float(account.portfolio_value):,.2f}')
    print(f'Buying Power: ${float(account.buying_power):,.2f}')
    
    # Test getting positions
    positions = alpaca.list_positions()
    print(f'Number of positions: {len(positions)}')
    
    if positions:
        print("\nCurrent Positions:")
        for pos in positions[:5]:  # Show first 5 positions
            print(f"  {pos.symbol}: {pos.qty} shares @ ${float(pos.market_value):,.2f}")
    else:
        print("No positions found")
        
except Exception as e:
    print(f'❌ Connection failed: {e}')
    print(f'Error type: {type(e).__name__}') 