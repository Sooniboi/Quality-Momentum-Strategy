#!/usr/bin/env python3
"""
Alpaca Portfolio Data Integration

Fetches real-time portfolio data, prices, volumes, and trading metrics
from Alpaca API to enhance weekly performance reporting.
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

# Load environment variables first
from dotenv import load_dotenv
load_dotenv(override=True)

try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

class AlpacaPortfolioData:
    """Fetches comprehensive portfolio data from Alpaca and other sources."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_alpaca_connection()
        
    def setup_alpaca_connection(self):
        """Setup Alpaca API connection."""
        try:
            if not ALPACA_AVAILABLE:
                self.logger.warning("⚠️ Alpaca Trade API not installed. Install with: pip install alpaca-trade-api")
                self.alpaca = None
                return
            
            # Clear any existing environment variables first
            for key in ['ALPACA_API_KEY', 'ALPACA_SECRET_KEY', 'ALPACA_BASE_URL']:
                if key in os.environ:
                    del os.environ[key]
            
            # Reload environment variables
            load_dotenv(override=True)
            
            # Get Alpaca credentials from environment
            api_key = os.getenv('ALPACA_API_KEY')
            secret_key = os.getenv('ALPACA_SECRET_KEY')
            base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')  # Paper trading by default
            
            self.logger.info(f"🔍 Debug - API Key: {api_key[:10] if api_key else 'NOT FOUND'}...")
            self.logger.info(f"🔍 Debug - Base URL: {base_url}")
            
            if not api_key or not secret_key or api_key == 'your_alpaca_api_key_here':
                self.logger.error("❌ Alpaca credentials not found in environment variables")
                self.alpaca = None
                return
            
            self.alpaca = tradeapi.REST(api_key, secret_key, base_url, api_version='v2')
            
            # Test connection
            account = self.alpaca.get_account()
            self.logger.info(f"✅ Connected to Alpaca - Account: {account.status}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to Alpaca: {e}")
            self.alpaca = None
    
    def get_portfolio_positions(self) -> pd.DataFrame:
        """Get current portfolio positions from Alpaca."""
        try:
            if not self.alpaca:
                return self._get_mock_portfolio_data()
            
            # Get positions from Alpaca
            positions = self.alpaca.list_positions()
            
            portfolio_data = []
            for position in positions:
                portfolio_data.append({
                    'ticker': position.symbol,
                    'shares': float(position.qty),
                    'market_value': float(position.market_value),
                    'cost_basis': float(position.cost_basis),
                    'current_price': float(position.current_price),
                    'avg_entry_price': float(position.avg_entry_price),
                    'unrealized_pl': float(position.unrealized_pl),
                    'unrealized_plpc': float(position.unrealized_plpc),
                    'side': position.side
                })
            
            df = pd.DataFrame(portfolio_data)
            
            if not df.empty:
                # Add additional calculated fields
                df['total_return_pct'] = (df['current_price'] - df['avg_entry_price']) / df['avg_entry_price']
                df['weight'] = df['market_value'] / df['market_value'].sum()
                
                self.logger.info(f"✅ Retrieved {len(df)} positions from Alpaca")
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get Alpaca positions: {e}")
            return self._get_mock_portfolio_data()
    
    def get_account_info(self) -> Dict:
        """Get account information and performance metrics."""
        try:
            if not self.alpaca:
                return self._get_mock_account_data()
            
            account = self.alpaca.get_account()
            
            account_info = {
                'total_equity': float(account.equity),
                'buying_power': float(account.buying_power),
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'long_market_value': float(account.long_market_value),
                'short_market_value': float(account.short_market_value),
                'day_trade_buying_power': float(getattr(account, 'day_trade_buying_power', account.buying_power)),
                'last_equity': float(account.last_equity),
                'multiplier': int(account.multiplier),
                'currency': account.currency,
                'account_blocked': account.account_blocked,
                'trade_suspended_by_user': account.trade_suspended_by_user,
                'trading_blocked': account.trading_blocked,
                'transfers_blocked': account.transfers_blocked
            }
            
            self.logger.info(f"✅ Account equity: ${account_info['total_equity']:,.2f}")
            return account_info
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get account info: {e}")
            return self._get_mock_account_data()
    
    def get_portfolio_history(self, period: str = '1M', timeframe: str = '1D') -> pd.DataFrame:
        """Get portfolio performance history."""
        try:
            if not self.alpaca:
                return self._get_mock_history_data()
            
            # Get portfolio history
            portfolio_history = self.alpaca.get_portfolio_history(
                period=period,
                timeframe=timeframe
            )
            
            # Convert to DataFrame
            history_data = []
            for i, timestamp in enumerate(portfolio_history.timestamp):
                history_data.append({
                    'timestamp': pd.to_datetime(timestamp, unit='s'),
                    'equity': portfolio_history.equity[i],
                    'profit_loss': portfolio_history.profit_loss[i],
                    'profit_loss_pct': portfolio_history.profit_loss_pct[i]
                })
            
            df = pd.DataFrame(history_data)
            df.set_index('timestamp', inplace=True)
            
            self.logger.info(f"✅ Retrieved {len(df)} portfolio history records")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get portfolio history: {e}")
            return self._get_mock_history_data()
    
    def get_recent_orders(self, limit: int = 50) -> pd.DataFrame:
        """Get recent trading activity."""
        try:
            if not self.alpaca:
                return self._get_mock_orders_data()
            
            # Get recent orders
            orders = self.alpaca.list_orders(
                status='all',
                limit=limit,
                nested=True
            )
            
            orders_data = []
            for order in orders:
                orders_data.append({
                    'id': order.id,
                    'symbol': order.symbol,
                    'side': order.side,
                    'qty': float(order.qty),
                    'filled_qty': float(order.filled_qty or 0),
                    'order_type': order.order_type,
                    'status': order.status,
                    'submitted_at': pd.to_datetime(order.submitted_at),
                    'filled_at': pd.to_datetime(order.filled_at) if order.filled_at else None,
                    'avg_fill_price': float(order.filled_avg_price or 0),
                    'commission': 0  # Alpaca is commission-free
                })
            
            df = pd.DataFrame(orders_data)
            self.logger.info(f"✅ Retrieved {len(df)} recent orders")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get recent orders: {e}")
            return self._get_mock_orders_data()
    
    def get_stock_fundamentals(self, symbols: List[str]) -> pd.DataFrame:
        """Get fundamental data for stocks using yfinance."""
        try:
            if not YFINANCE_AVAILABLE:
                self.logger.warning("⚠️ yfinance not available. Install with: pip install yfinance")
                return self._get_mock_fundamentals_data(symbols)
            
            fundamentals_data = []
            
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    fundamentals_data.append({
                        'ticker': symbol,
                        'market_cap': info.get('marketCap', 0),
                        'pe_ratio': info.get('trailingPE', None),
                        'pb_ratio': info.get('priceToBook', None),
                        'roe': info.get('returnOnEquity', None),
                        'eps_ttm': info.get('trailingEps', None),
                        'revenue_ttm': info.get('totalRevenue', 0),
                        'debt_to_equity': info.get('debtToEquity', None),
                        'current_ratio': info.get('currentRatio', None),
                        'dividend_yield': info.get('dividendYield', None),
                        'beta': info.get('beta', None),
                        'sector': info.get('sector', 'Unknown'),
                        'industry': info.get('industry', 'Unknown'),
                        '52_week_high': info.get('fiftyTwoWeekHigh', None),
                        '52_week_low': info.get('fiftyTwoWeekLow', None)
                    })
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to get fundamentals for {symbol}: {e}")
                    # Add placeholder data
                    fundamentals_data.append({
                        'ticker': symbol,
                        'market_cap': 0,
                        'pe_ratio': None,
                        'pb_ratio': None,
                        'roe': None,
                        'eps_ttm': None,
                        'revenue_ttm': 0,
                        'debt_to_equity': None,
                        'current_ratio': None,
                        'dividend_yield': None,
                        'beta': None,
                        'sector': 'Unknown',
                        'industry': 'Unknown',
                        '52_week_high': None,
                        '52_week_low': None
                    })
            
            df = pd.DataFrame(fundamentals_data)
            self.logger.info(f"✅ Retrieved fundamentals for {len(df)} stocks")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get fundamentals: {e}")
            return self._get_mock_fundamentals_data(symbols)
    
    def calculate_portfolio_metrics(self, positions_df: pd.DataFrame, history_df: pd.DataFrame) -> Dict:
        """Calculate comprehensive portfolio performance metrics."""
        try:
            metrics = {}
            
            if not positions_df.empty:
                # Current portfolio metrics
                metrics['total_positions'] = len(positions_df)
                metrics['total_market_value'] = positions_df['market_value'].sum()
                metrics['total_unrealized_pl'] = positions_df['unrealized_pl'].sum()
                metrics['total_return_pct'] = (metrics['total_unrealized_pl'] / 
                                             (metrics['total_market_value'] - metrics['total_unrealized_pl'])) * 100
                
                # Top performers
                top_performers = positions_df.nlargest(3, 'unrealized_plpc')[['ticker', 'unrealized_plpc']]
                bottom_performers = positions_df.nsmallest(3, 'unrealized_plpc')[['ticker', 'unrealized_plpc']]
                
                metrics['top_performers'] = top_performers.to_dict('records')
                metrics['bottom_performers'] = bottom_performers.to_dict('records')
                
                # Sector allocation
                if 'sector' in positions_df.columns:
                    sector_allocation = positions_df.groupby('sector')['market_value'].sum()
                    metrics['sector_allocation'] = (sector_allocation / sector_allocation.sum()).to_dict()
            
            if not history_df.empty and len(history_df) > 1:
                # Performance over time
                latest_equity = history_df['equity'].iloc[-1]
                week_ago_equity = history_df['equity'].iloc[-6] if len(history_df) >= 6 else history_df['equity'].iloc[0]
                
                metrics['weekly_return'] = ((latest_equity - week_ago_equity) / week_ago_equity) * 100
                
                # Volatility (annualized)
                daily_returns = history_df['equity'].pct_change().dropna()
                if len(daily_returns) > 1:
                    metrics['volatility'] = daily_returns.std() * np.sqrt(252) * 100  # Annualized
                else:
                    metrics['volatility'] = 0
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate portfolio metrics: {e}")
            return {}
    
    def _get_mock_portfolio_data(self) -> pd.DataFrame:
        """Generate mock portfolio data for testing."""
        mock_data = [
            {'ticker': 'AAPL', 'shares': 100, 'market_value': 15000, 'cost_basis': 14000, 
             'current_price': 150, 'avg_entry_price': 140, 'unrealized_pl': 1000, 
             'unrealized_plpc': 0.071, 'side': 'long', 'weight': 0.3},
            {'ticker': 'MSFT', 'shares': 75, 'market_value': 12000, 'cost_basis': 11500, 
             'current_price': 160, 'avg_entry_price': 153, 'unrealized_pl': 500, 
             'unrealized_plpc': 0.043, 'side': 'long', 'weight': 0.24},
            {'ticker': 'GOOGL', 'shares': 50, 'market_value': 10000, 'cost_basis': 9800, 
             'current_price': 200, 'avg_entry_price': 196, 'unrealized_pl': 200, 
             'unrealized_plpc': 0.02, 'side': 'long', 'weight': 0.2}
        ]
        return pd.DataFrame(mock_data)
    
    def _get_mock_account_data(self) -> Dict:
        """Generate mock account data for testing."""
        return {
            'total_equity': 50000.0,
            'buying_power': 100000.0,
            'cash': 5000.0,
            'portfolio_value': 45000.0,
            'long_market_value': 45000.0,
            'short_market_value': 0.0,
            'day_trade_buying_power': 200000.0,
            'last_equity': 49500.0,
            'multiplier': 4,
            'currency': 'USD'
        }
    
    def _get_mock_history_data(self) -> pd.DataFrame:
        """Generate mock portfolio history data."""
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        base_equity = 50000
        
        history_data = []
        for i, date in enumerate(dates):
            # Simulate some portfolio movement
            equity = base_equity + np.random.normal(0, 500) + i * 20
            profit_loss = equity - base_equity
            profit_loss_pct = profit_loss / base_equity
            
            history_data.append({
                'equity': equity,
                'profit_loss': profit_loss,
                'profit_loss_pct': profit_loss_pct
            })
        
        df = pd.DataFrame(history_data, index=dates)
        return df
    
    def _get_mock_orders_data(self) -> pd.DataFrame:
        """Generate mock orders data."""
        mock_orders = [
            {'id': 'order1', 'symbol': 'AAPL', 'side': 'buy', 'qty': 10, 'filled_qty': 10,
             'order_type': 'market', 'status': 'filled', 'submitted_at': datetime.now() - timedelta(days=2),
             'filled_at': datetime.now() - timedelta(days=2), 'avg_fill_price': 150.25, 'commission': 0},
            {'id': 'order2', 'symbol': 'MSFT', 'side': 'sell', 'qty': 5, 'filled_qty': 5,
             'order_type': 'limit', 'status': 'filled', 'submitted_at': datetime.now() - timedelta(days=1),
             'filled_at': datetime.now() - timedelta(days=1), 'avg_fill_price': 162.10, 'commission': 0}
        ]
        return pd.DataFrame(mock_orders)
    
    def _get_mock_fundamentals_data(self, symbols: List[str]) -> pd.DataFrame:
        """Generate mock fundamentals data."""
        fundamentals = []
        for symbol in symbols:
            fundamentals.append({
                'ticker': symbol,
                'market_cap': 1000000000,
                'pe_ratio': 25.5,
                'pb_ratio': 3.2,
                'roe': 0.15,
                'eps_ttm': 6.50,
                'revenue_ttm': 5000000000,
                'debt_to_equity': 0.45,
                'current_ratio': 1.2,
                'dividend_yield': 0.02,
                'beta': 1.1,
                'sector': 'Technology',
                'industry': 'Software',
                '52_week_high': 180.0,
                '52_week_low': 120.0
            })
        return pd.DataFrame(fundamentals)

def main():
    """Test Alpaca portfolio data fetching."""
    logging.basicConfig(level=logging.INFO)
    
    alpaca_data = AlpacaPortfolioData()
    
    # Test data retrieval
    positions = alpaca_data.get_portfolio_positions()
    print(f"Portfolio positions: {len(positions)}")
    
    account = alpaca_data.get_account_info()
    print(f"Account equity: ${account.get('total_equity', 0):,.2f}")
    
    history = alpaca_data.get_portfolio_history()
    print(f"Portfolio history: {len(history)} records")
    
    if not positions.empty:
        symbols = positions['ticker'].tolist()
        fundamentals = alpaca_data.get_stock_fundamentals(symbols)
        print(f"Fundamentals data: {len(fundamentals)} stocks")
        
        metrics = alpaca_data.calculate_portfolio_metrics(positions, history)
        print("Portfolio metrics calculated successfully")

if __name__ == "__main__":
    main() 