#!/usr/bin/env python3
"""
Historical Backtesting System for Quality Momentum Strategy

This module performs comprehensive backtesting using historical data:
- Downloads historical price data for portfolio holdings via FMP API
- Simulates monthly rebalancing
- Calculates performance metrics vs benchmarks
- Generates detailed performance reports and charts

Uses Financial Modeling Prep (FMP) API for consistent data source.
"""

import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import glob
import os
import json
import time
import warnings
warnings.filterwarnings('ignore')

class HistoricalBacktester:
    def __init__(self, years=3, rebalance_freq='M', api_key=None):
        """
        Initialize backtester.
        
        Args:
            years (int): Number of years to backtest
            rebalance_freq (str): Rebalancing frequency ('M'=monthly, 'Q'=quarterly)
            api_key (str): FMP API key (optional, will try to load from config)
        """
        self.years = years
        self.rebalance_freq = rebalance_freq
        self.start_date = (datetime.now() - timedelta(days=365 * years)).strftime('%Y-%m-%d')
        self.end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Load API key
        self.api_key = api_key or self.load_api_key()
        
    def load_api_key(self):
        """Load FMP API key from config files."""
        config_paths = [
            'config/api_keys.json',
            '../config/api_keys.json',
            '../../config/api_keys.json'
        ]
        
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        return config.get('financial_modeling_prep', config.get('fmp_api_key'))
                except:
                    continue
        
        # Try environment variable
        api_key = os.getenv('FMP_API_KEY')
        if api_key:
            return api_key
            
        print("⚠️ No FMP API key found. Using demo/limited data.")
        return None
        
    def load_current_portfolio(self):
        """Load the most recent portfolio selection."""
        # Try new structure first
        portfolio_patterns = [
            os.path.join('data', 'processed', 'portfolios', '*portfolio*.csv'),
            os.path.join('..', 'data', 'processed', 'portfolios', '*portfolio*.csv'),
            os.path.join('..', '..', 'data', 'processed', 'portfolios', '*portfolio*.csv'),
            # Fallback to old structure
            os.path.join('csv_data_files', 'portfolios', '04_unified_portfolio_selection_*.csv'),
            os.path.join('..', 'csv_data_files', 'portfolios', '04_unified_portfolio_selection_*.csv'),
            os.path.join('..', '..', 'csv_data_files', 'portfolios', '04_unified_portfolio_selection_*.csv'),
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
    
    def download_fmp_historical_data(self, ticker, retries=3):
        """
        Download historical data for a single ticker from FMP.
        
        Args:
            ticker (str): Stock ticker symbol
            retries (int): Number of retry attempts
        """
        if not self.api_key:
            return None
            
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}"
        params = {
            'from': self.start_date,
            'to': self.end_date,
            'apikey': self.api_key
        }
        
        for attempt in range(retries):
            try:
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'historical' in data and data['historical']:
                        df = pd.DataFrame(data['historical'])
                        df['date'] = pd.to_datetime(df['date'])
                        df.set_index('date', inplace=True)
                        df.sort_index(inplace=True)
                        
                        # Return adjusted close prices
                        return df[['adjClose']].rename(columns={'adjClose': ticker})
                    else:
                        print(f"⚠️ No historical data found for {ticker}")
                        return None
                        
                elif response.status_code == 429:  # Rate limit exceeded
                    wait_time = min(60, 2 ** attempt)  # Cap at 60 seconds
                    print(f"⏱️ Rate limit hit for {ticker}, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                elif response.status_code == 403:  # API key issue
                    print(f"❌ API key error for {ticker}: Check your FMP API key")
                    return None
                else:
                    print(f"❌ API error for {ticker}: {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"❌ Error downloading {ticker}: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(1)
                    continue
                return None
        
        return None
    
    def download_historical_data(self, tickers, benchmark='IJR'):
        """
        Download historical price data for portfolio and benchmark using FMP.
        
        FMP Rate Limit: 300 calls/minute (5 calls/second)
        Optimized with 0.2s delay between calls for safety.
        
        Args:
            tickers (list): List of ticker symbols
            benchmark (str): Benchmark ticker (IJR = S&P 600 ETF)
        """
        print(f"📊 Downloading historical data from FMP ({self.start_date} to {self.end_date})...")
        print(f"⚡ FMP Rate Limit: 300 calls/minute (5 calls/second)")
        
        all_tickers = list(tickers) + [benchmark]
        price_data = {}
        valid_tickers = []
        
        # Estimate time for downloads
        estimated_time = len(all_tickers) * 0.2  # 0.2 seconds per call
        print(f"📈 Downloading {len(all_tickers)} tickers (estimated time: {estimated_time:.1f}s)")
        
        # Download data for each ticker with progress tracking
        start_time = time.time()
        for i, ticker in enumerate(all_tickers):
            # Progress indicator
            progress = (i + 1) / len(all_tickers) * 100
            elapsed = time.time() - start_time
            
            print(f"📈 [{progress:5.1f}%] Downloading {ticker} ({i+1}/{len(all_tickers)}) - {elapsed:.1f}s elapsed")
            
            ticker_data = self.download_fmp_historical_data(ticker)
            
            if ticker_data is not None and len(ticker_data) > 0:
                price_data[ticker] = ticker_data[ticker]
                if ticker != benchmark:
                    valid_tickers.append(ticker)
                print(f"    ✅ {ticker}: {len(ticker_data)} data points")
            else:
                print(f"    ❌ Failed to download {ticker}")
            
            # Rate limiting: 0.2s delay for 5 calls/second (300/minute limit)
            if i < len(all_tickers) - 1:
                time.sleep(0.2)
        
        total_time = time.time() - start_time
        print(f"📊 Download completed in {total_time:.1f}s (avg: {total_time/len(all_tickers):.2f}s per ticker)")
        
        if not price_data:
            print("❌ No price data downloaded!")
            return None, []
        
        # Combine all price data
        print("🔄 Combining and validating price data...")
        combined_data = pd.DataFrame(price_data)
        
        # Filter for minimum data availability (require 80% data coverage)
        min_data_points = len(combined_data) * 0.8
        sufficient_data_tickers = []
        
        for ticker in valid_tickers:
            if ticker in combined_data.columns:
                data_coverage = combined_data[ticker].count() / len(combined_data)
                if combined_data[ticker].count() >= min_data_points:
                    sufficient_data_tickers.append(ticker)
                    print(f"    ✅ {ticker}: {data_coverage:.1%} data coverage")
                else:
                    print(f"    ❌ {ticker}: {data_coverage:.1%} data coverage (insufficient)")
        
        # Include benchmark if it has sufficient data
        final_columns = sufficient_data_tickers.copy()
        if benchmark in combined_data.columns:
            benchmark_coverage = combined_data[benchmark].count() / len(combined_data)
            if combined_data[benchmark].count() >= min_data_points:
                final_columns.append(benchmark)
                print(f"    ✅ {benchmark} (benchmark): {benchmark_coverage:.1%} data coverage")
            else:
                print(f"    ❌ {benchmark} (benchmark): {benchmark_coverage:.1%} data coverage")
        
        if not final_columns:
            print("❌ No tickers have sufficient data!")
            return None, []
        
        # Clean and prepare final dataset
        final_data = combined_data[final_columns].dropna()
        
        print(f"\n📊 DATA DOWNLOAD SUMMARY:")
        print(f"✅ Successfully downloaded: {len(sufficient_data_tickers)}/{len(tickers)} portfolio stocks")
        print(f"✅ Benchmark data: {benchmark}")
        print(f"📅 Date range: {final_data.index[0].strftime('%Y-%m-%d')} to {final_data.index[-1].strftime('%Y-%m-%d')}")
        print(f"📈 Trading days: {len(final_data)}")
        print(f"⏱️  Total download time: {total_time:.1f}s")
        print(f"🔄 API calls made: {len(all_tickers)}")
        
        return final_data, sufficient_data_tickers
    
    def calculate_returns(self, prices):
        """Calculate daily returns."""
        return prices.pct_change().dropna()
    
    def simulate_strategy(self, portfolio, prices, benchmark='IJR'):
        """
        Simulate the strategy with monthly rebalancing.
        
        Args:
            portfolio (pd.DataFrame): Portfolio with weights
            prices (pd.DataFrame): Historical price data
            benchmark (str): Benchmark ticker
        """
        print(f"🎯 Simulating strategy with {self.rebalance_freq} rebalancing...")
        
        # Get valid tickers that have price data
        valid_tickers = [t for t in portfolio['Ticker'].tolist() if t in prices.columns]
        portfolio_subset = portfolio[portfolio['Ticker'].isin(valid_tickers)].copy()
        
        if len(portfolio_subset) == 0:
            raise ValueError("No portfolio stocks have historical price data!")
        
        # Normalize weights for valid tickers only
        total_weight = portfolio_subset['Portfolio_Weight'].sum()
        portfolio_subset['Normalized_Weight'] = portfolio_subset['Portfolio_Weight'] / total_weight
        
        print(f"📊 Simulating with {len(portfolio_subset)} stocks")
        
        # Calculate returns
        returns = self.calculate_returns(prices)
        
        # Create rebalancing dates
        rebalancing_dates = pd.date_range(start=self.start_date, end=self.end_date, 
                                        freq='MS' if self.rebalance_freq == 'M' else 'QS')
        rebalancing_dates = rebalancing_dates[rebalancing_dates <= returns.index[-1]]
        
        # Initialize portfolio value tracking
        portfolio_values = []
        benchmark_values = []
        
        initial_value = 10000  # Start with $10,000
        current_value = initial_value
        benchmark_value = initial_value
        
        # Track holdings
        holdings = {}
        for _, stock in portfolio_subset.iterrows():
            holdings[stock['Ticker']] = stock['Normalized_Weight'] * initial_value
        
        # Simulate day by day
        prev_rebalance_date = None
        
        for date in returns.index:
            # Check if rebalancing date
            if date in rebalancing_dates or prev_rebalance_date is None:
                # Rebalance portfolio
                current_value = sum(holdings.values())
                for _, stock in portfolio_subset.iterrows():
                    holdings[stock['Ticker']] = stock['Normalized_Weight'] * current_value
                prev_rebalance_date = date
            
            # Calculate daily changes
            daily_portfolio_return = 0
            total_portfolio_value = sum(holdings.values())
            
            for ticker in holdings.keys():
                if ticker in returns.columns and not pd.isna(returns.loc[date, ticker]):
                    weight = holdings[ticker] / total_portfolio_value if total_portfolio_value > 0 else 0
                    daily_portfolio_return += weight * returns.loc[date, ticker]
                    holdings[ticker] *= (1 + returns.loc[date, ticker])
            
            # Update portfolio value
            current_value = sum(holdings.values())
            portfolio_values.append(current_value)
            
            # Update benchmark
            if benchmark in returns.columns and not pd.isna(returns.loc[date, benchmark]):
                benchmark_value *= (1 + returns.loc[date, benchmark])
            benchmark_values.append(benchmark_value)
        
        # Create results DataFrame
        results = pd.DataFrame({
            'Date': returns.index,
            'Portfolio_Value': portfolio_values,
            'Benchmark_Value': benchmark_values
        }).set_index('Date')
        
        # Calculate cumulative returns
        results['Portfolio_Return'] = (results['Portfolio_Value'] / initial_value - 1) * 100
        results['Benchmark_Return'] = (results['Benchmark_Value'] / initial_value - 1) * 100
        results['Excess_Return'] = results['Portfolio_Return'] - results['Benchmark_Return']
        
        return results
    
    def calculate_metrics(self, results):
        """Calculate comprehensive performance metrics."""
        portfolio_returns = results['Portfolio_Value'].pct_change().dropna()
        benchmark_returns = results['Benchmark_Value'].pct_change().dropna()
        
        # Annualized metrics
        trading_days = 252
        portfolio_annual_return = (1 + portfolio_returns.mean()) ** trading_days - 1
        benchmark_annual_return = (1 + benchmark_returns.mean()) ** trading_days - 1
        
        portfolio_volatility = portfolio_returns.std() * np.sqrt(trading_days)
        benchmark_volatility = benchmark_returns.std() * np.sqrt(trading_days)
        
        # Sharpe ratio (assuming risk-free rate of 3%)
        risk_free_rate = 0.03
        portfolio_sharpe = (portfolio_annual_return - risk_free_rate) / portfolio_volatility
        benchmark_sharpe = (benchmark_annual_return - risk_free_rate) / benchmark_volatility
        
        # Maximum drawdown
        portfolio_cumulative = (1 + portfolio_returns).cumprod()
        portfolio_rolling_max = portfolio_cumulative.expanding().max()
        portfolio_drawdown = (portfolio_cumulative - portfolio_rolling_max) / portfolio_rolling_max
        portfolio_max_drawdown = portfolio_drawdown.min()
        
        benchmark_cumulative = (1 + benchmark_returns).cumprod()
        benchmark_rolling_max = benchmark_cumulative.expanding().max()
        benchmark_drawdown = (benchmark_cumulative - benchmark_rolling_max) / benchmark_rolling_max
        benchmark_max_drawdown = benchmark_drawdown.min()
        
        # Win rate (days outperforming benchmark)
        excess_returns = portfolio_returns - benchmark_returns
        win_rate = (excess_returns > 0).mean()
        
        # Beta and correlation
        correlation = portfolio_returns.corr(benchmark_returns)
        beta = portfolio_returns.cov(benchmark_returns) / benchmark_returns.var()
        
        # Information ratio
        excess_return_annual = portfolio_annual_return - benchmark_annual_return
        tracking_error = excess_returns.std() * np.sqrt(trading_days)
        information_ratio = excess_return_annual / tracking_error if tracking_error > 0 else 0
        
        # Calmar ratio
        calmar_ratio = portfolio_annual_return / abs(portfolio_max_drawdown) if portfolio_max_drawdown < 0 else 0
        
        # Final values
        final_portfolio_value = results['Portfolio_Value'].iloc[-1]
        final_benchmark_value = results['Benchmark_Value'].iloc[-1]
        
        metrics = {
            'Total Return': {
                'Portfolio': (final_portfolio_value / 10000 - 1) * 100,
                'Benchmark': (final_benchmark_value / 10000 - 1) * 100
            },
            'Annualized Return': {
                'Portfolio': portfolio_annual_return * 100,
                'Benchmark': benchmark_annual_return * 100
            },
            'Volatility': {
                'Portfolio': portfolio_volatility * 100,
                'Benchmark': benchmark_volatility * 100
            },
            'Sharpe Ratio': {
                'Portfolio': portfolio_sharpe,
                'Benchmark': benchmark_sharpe
            },
            'Maximum Drawdown': {
                'Portfolio': portfolio_max_drawdown * 100,
                'Benchmark': benchmark_max_drawdown * 100
            },
            'Win Rate': win_rate * 100,
            'Beta': beta,
            'Correlation': correlation,
            'Information Ratio': information_ratio,
            'Calmar Ratio': calmar_ratio,
            'Tracking Error': tracking_error * 100,
            'Excess Return': excess_return_annual * 100
        }
        
        return metrics
    
    def create_performance_chart(self, results, metrics, save_path):
        """Create comprehensive performance visualization."""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Quality Momentum Strategy - Backtesting Results', fontsize=16, fontweight='bold')
        
        # 1. Cumulative Returns
        axes[0, 0].plot(results.index, results['Portfolio_Return'], label='Strategy', linewidth=2, color='blue')
        axes[0, 0].plot(results.index, results['Benchmark_Return'], label='S&P 600 (IJR)', linewidth=2, color='red')
        axes[0, 0].set_title('Cumulative Returns (%)')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].set_ylabel('Return (%)')
        
        # 2. Excess Returns
        axes[0, 1].plot(results.index, results['Excess_Return'], label='Excess Return', linewidth=2, color='green')
        axes[0, 1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        axes[0, 1].set_title('Excess Returns vs Benchmark (%)')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].set_ylabel('Excess Return (%)')
        
        # 3. Rolling Sharpe Ratio (6-month window)
        portfolio_returns = results['Portfolio_Value'].pct_change().dropna()
        rolling_sharpe = portfolio_returns.rolling(126).mean() / portfolio_returns.rolling(126).std() * np.sqrt(252)
        axes[1, 0].plot(rolling_sharpe.index, rolling_sharpe, label='6M Rolling Sharpe', linewidth=2, color='purple')
        axes[1, 0].axhline(y=1.0, color='black', linestyle='--', alpha=0.5, label='Sharpe = 1.0')
        axes[1, 0].set_title('Rolling Sharpe Ratio (6M)')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].set_ylabel('Sharpe Ratio')
        
        # 4. Drawdown
        portfolio_cumulative = (1 + portfolio_returns).cumprod()
        drawdown = (portfolio_cumulative / portfolio_cumulative.cummax() - 1) * 100
        axes[1, 1].fill_between(drawdown.index, drawdown, 0, alpha=0.3, color='red')
        axes[1, 1].plot(drawdown.index, drawdown, linewidth=1, color='darkred')
        axes[1, 1].set_title('Portfolio Drawdown (%)')
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].set_ylabel('Drawdown (%)')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Performance chart saved: {save_path}")
    
    def generate_report(self, results, metrics, portfolio, save_path):
        """Generate comprehensive HTML report."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Quality Momentum Strategy - Backtesting Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; min-width: 200px; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .summary {{ background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Quality Momentum Strategy - Backtesting Report</h1>
                <p><strong>Period:</strong> {self.start_date} to {self.end_date} ({self.years} years)</p>
                <p><strong>Rebalancing:</strong> {self.rebalance_freq}onthly</p>
                <p><strong>Portfolio Size:</strong> {len(portfolio)} stocks</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="summary">
                <h2>📊 Performance Summary</h2>
                <p><strong>Total Return:</strong> 
                   <span class="{'positive' if metrics['Total Return']['Portfolio'] > 0 else 'negative'}">
                   {metrics['Total Return']['Portfolio']:.1f}%</span> vs 
                   <span class="{'positive' if metrics['Total Return']['Benchmark'] > 0 else 'negative'}">
                   {metrics['Total Return']['Benchmark']:.1f}%</span> (benchmark)
                </p>
                <p><strong>Excess Return:</strong> 
                   <span class="{'positive' if metrics['Excess Return'] > 0 else 'negative'}">
                   {metrics['Excess Return']:.1f}%</span>
                </p>
                <p><strong>Annual Return:</strong> 
                   <span class="{'positive' if metrics['Annualized Return']['Portfolio'] > 0 else 'negative'}">
                   {metrics['Annualized Return']['Portfolio']:.1f}%</span>
                </p>
                <p><strong>Sharpe Ratio:</strong> {metrics['Sharpe Ratio']['Portfolio']:.2f}</p>
                <p><strong>Max Drawdown:</strong> 
                   <span class="negative">{metrics['Maximum Drawdown']['Portfolio']:.1f}%</span>
                </p>
            </div>
            
            <h2>📈 Detailed Metrics</h2>
            <table>
                <tr><th>Metric</th><th>Strategy</th><th>Benchmark</th><th>Difference</th></tr>
                <tr>
                    <td>Total Return</td>
                    <td>{metrics['Total Return']['Portfolio']:.1f}%</td>
                    <td>{metrics['Total Return']['Benchmark']:.1f}%</td>
                    <td class="{'positive' if metrics['Excess Return'] > 0 else 'negative'}">
                        {metrics['Excess Return']:.1f}%</td>
                </tr>
                <tr>
                    <td>Annualized Return</td>
                    <td>{metrics['Annualized Return']['Portfolio']:.1f}%</td>
                    <td>{metrics['Annualized Return']['Benchmark']:.1f}%</td>
                    <td class="{'positive' if metrics['Annualized Return']['Portfolio'] - metrics['Annualized Return']['Benchmark'] > 0 else 'negative'}">
                        {metrics['Annualized Return']['Portfolio'] - metrics['Annualized Return']['Benchmark']:.1f}%</td>
                </tr>
                <tr>
                    <td>Volatility</td>
                    <td>{metrics['Volatility']['Portfolio']:.1f}%</td>
                    <td>{metrics['Volatility']['Benchmark']:.1f}%</td>
                    <td>{metrics['Volatility']['Portfolio'] - metrics['Volatility']['Benchmark']:.1f}%</td>
                </tr>
                <tr>
                    <td>Sharpe Ratio</td>
                    <td>{metrics['Sharpe Ratio']['Portfolio']:.2f}</td>
                    <td>{metrics['Sharpe Ratio']['Benchmark']:.2f}</td>
                    <td class="{'positive' if metrics['Sharpe Ratio']['Portfolio'] - metrics['Sharpe Ratio']['Benchmark'] > 0 else 'negative'}">
                        {metrics['Sharpe Ratio']['Portfolio'] - metrics['Sharpe Ratio']['Benchmark']:.2f}</td>
                </tr>
            </table>
            
            <h2>🔍 Risk Metrics</h2>
            <div class="metric">
                <strong>Beta:</strong> {metrics['Beta']:.2f}<br>
                <small>Market sensitivity</small>
            </div>
            <div class="metric">
                <strong>Information Ratio:</strong> {metrics['Information Ratio']:.2f}<br>
                <small>Risk-adjusted excess return</small>
            </div>
            <div class="metric">
                <strong>Tracking Error:</strong> {metrics['Tracking Error']:.1f}%<br>
                <small>Volatility of excess returns</small>
            </div>
            <div class="metric">
                <strong>Win Rate:</strong> {metrics['Win Rate']:.1f}%<br>
                <small>Days outperforming benchmark</small>
            </div>
            <div class="metric">
                <strong>Calmar Ratio:</strong> {metrics['Calmar Ratio']:.2f}<br>
                <small>Return / Max Drawdown</small>
            </div>
            
            <h2>💼 Portfolio Composition</h2>
            <table>
                <tr><th>Ticker</th><th>Sector</th><th>Style</th><th>Weight</th></tr>
        """
        
        # Add portfolio holdings
        for _, stock in portfolio.head(10).iterrows():  # Top 10 holdings
            html_content += f"""
                <tr>
                    <td>{stock['Ticker']}</td>
                    <td>{stock.get('Sector', 'N/A')}</td>
                    <td>{stock.get('Style', 'N/A')}</td>
                    <td>{stock.get('Portfolio_Weight', 0)*100:.1f}%</td>
                </tr>
            """
        
        html_content += """
            </table>
            
            <h2>💡 Key Insights</h2>
            <ul>
        """
        
        # Add insights based on performance
        if metrics['Excess Return'] > 0:
            html_content += f"<li>✅ Strategy outperformed benchmark by {metrics['Excess Return']:.1f}%</li>"
        else:
            html_content += f"<li>⚠️ Strategy underperformed benchmark by {abs(metrics['Excess Return']):.1f}%</li>"
            
        if metrics['Sharpe Ratio']['Portfolio'] > metrics['Sharpe Ratio']['Benchmark']:
            html_content += "<li>✅ Better risk-adjusted returns than benchmark</li>"
        else:
            html_content += "<li>⚠️ Lower risk-adjusted returns than benchmark</li>"
            
        if metrics['Maximum Drawdown']['Portfolio'] > -20:
            html_content += "<li>✅ Reasonable maximum drawdown</li>"
        else:
            html_content += "<li>⚠️ High maximum drawdown - consider risk management</li>"
            
        if metrics['Win Rate'] > 50:
            html_content += f"<li>✅ Positive win rate of {metrics['Win Rate']:.1f}%</li>"
        else:
            html_content += f"<li>⚠️ Low win rate of {metrics['Win Rate']:.1f}%</li>"
        
        html_content += """
            </ul>
            
            <p><strong>Note:</strong> Past performance does not guarantee future results. 
            This backtesting analysis is for informational purposes only.</p>
        </body>
        </html>
        """
        
        with open(save_path, 'w') as f:
            f.write(html_content)
        
        print(f"📄 HTML report saved: {save_path}")
    
    def run_backtest(self):
        """Execute complete backtesting process."""
        print("🚀 HISTORICAL BACKTESTING SYSTEM")
        print("="*60)
        print(f"📅 Period: {self.start_date} to {self.end_date}")
        print(f"⏰ Rebalancing: {self.rebalance_freq}onthly")
        
        try:
            # Load portfolio
            portfolio = self.load_current_portfolio()
            tickers = portfolio['Ticker'].tolist()
            
            # Download historical data
            prices, valid_tickers = self.download_historical_data(tickers)
            
            if prices is None or len(valid_tickers) == 0:
                raise ValueError("No historical data available")
            
            # Simulate strategy
            results = self.simulate_strategy(portfolio, prices)
            
            # Calculate metrics
            metrics = self.calculate_metrics(results)
            
            # Save results
            today = datetime.now().strftime('%Y-%m-%d')
            output_dir = os.path.dirname(__file__)
            
            # CSV results
            results_path = os.path.join(output_dir, f'06_backtest_results_{today}.csv')
            results.to_csv(results_path)
            
            # Performance chart
            chart_path = os.path.join(output_dir, f'06_performance_charts_{today}.png')
            self.create_performance_chart(results, metrics, chart_path)
            
            # HTML report
            report_path = os.path.join(output_dir, f'06_backtest_report_{today}.html')
            self.generate_report(results, metrics, portfolio, report_path)
            
            # Print summary
            print("\n📊 BACKTESTING RESULTS SUMMARY")
            print("="*60)
            print(f"Total Return: {metrics['Total Return']['Portfolio']:.1f}% vs {metrics['Total Return']['Benchmark']:.1f}% (benchmark)")
            print(f"Excess Return: {metrics['Excess Return']:.1f}%")
            print(f"Annual Return: {metrics['Annualized Return']['Portfolio']:.1f}%")
            print(f"Sharpe Ratio: {metrics['Sharpe Ratio']['Portfolio']:.2f}")
            print(f"Max Drawdown: {metrics['Maximum Drawdown']['Portfolio']:.1f}%")
            print(f"Win Rate: {metrics['Win Rate']:.1f}%")
            
            print(f"\n💾 RESULTS SAVED:")
            print(f"  📊 Data: {results_path}")
            print(f"  📈 Chart: {chart_path}")
            print(f"  📄 Report: {report_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Backtesting failed: {str(e)}")
            return False

def main():
    """Main execution function."""
    backtester = HistoricalBacktester(years=3, rebalance_freq='M')
    success = backtester.run_backtest()
    
    if success:
        print("\n✅ BACKTESTING COMPLETED SUCCESSFULLY!")
    else:
        print("\n❌ BACKTESTING FAILED!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 