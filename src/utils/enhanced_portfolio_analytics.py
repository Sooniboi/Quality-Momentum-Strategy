#!/usr/bin/env python3
"""
Enhanced Portfolio Analytics with FMP Integration

Comprehensive portfolio analysis using FMP API for institutional-grade data,
Monte Carlo simulations, portfolio optimization, and advanced visualizations.
"""

import os
import json
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Load environment variables
from dotenv import load_dotenv
load_dotenv(override=True)

class EnhancedPortfolioAnalytics:
    """Comprehensive portfolio analytics using FMP API."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fmp_api_key = os.getenv('FMP_API_KEY')
        
        if not self.fmp_api_key or self.fmp_api_key == 'your_fmp_api_key_here':
            self.logger.error("❌ FMP API key not found. Please set FMP_API_KEY in .env file")
            self.fmp_api_key = None
        else:
            self.logger.info(f"✅ FMP API key loaded: {self.fmp_api_key[:10]}...")
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Create charts directory
        self.charts_dir = Path("reports/weekly/charts")
        self.charts_dir.mkdir(parents=True, exist_ok=True)
        
        # Store for portfolio comparison
        self.last_week_portfolio = self._load_last_week_portfolio()
    
    def _make_fmp_request(self, endpoint: str, params: dict = None) -> Optional[Dict]:
        """Make a request to FMP API."""
        if not self.fmp_api_key:
            return None
            
        base_url = "https://financialmodelingprep.com/api/v3"
        url = f"{base_url}/{endpoint}"
        
        if params is None:
            params = {}
        params['apikey'] = self.fmp_api_key
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.warning(f"⚠️ FMP API request failed for {endpoint}: {e}")
            return None
    
    def get_company_profile(self, symbol: str) -> Optional[Dict]:
        """Get company profile from FMP."""
        return self._make_fmp_request(f"profile/{symbol}")
    
    def get_financial_ratios(self, symbol: str) -> Optional[Dict]:
        """Get financial ratios from FMP."""
        data = self._make_fmp_request(f"ratios/{symbol}", {"limit": 1})
        return data[0] if data and len(data) > 0 else None
    
    def get_key_metrics(self, symbol: str) -> Optional[Dict]:
        """Get key metrics from FMP."""
        data = self._make_fmp_request(f"key-metrics/{symbol}", {"limit": 1})
        return data[0] if data and len(data) > 0 else None
    
    def get_stock_price_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Get historical price data from FMP."""
        data = self._make_fmp_request(f"historical-price-full/{symbol}", {"from": (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')})
        
        if not data or 'historical' not in data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data['historical'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df
    
    def get_economic_indicators(self) -> Dict:
        """Get economic indicators from FMP."""
        indicators = {}
        
        # GDP Growth
        gdp_data = self._make_fmp_request("economic", {"name": "GDP"})
        if gdp_data:
            indicators['gdp_growth'] = gdp_data[0]['value'] if gdp_data else None
        
        # Inflation
        inflation_data = self._make_fmp_request("economic", {"name": "inflationRate"})
        if inflation_data:
            indicators['inflation'] = inflation_data[0]['value'] if inflation_data else None
        
        # Unemployment
        unemployment_data = self._make_fmp_request("economic", {"name": "unemploymentRate"})
        if unemployment_data:
            indicators['unemployment'] = unemployment_data[0]['value'] if unemployment_data else None
        
        # VIX
        vix_data = self._make_fmp_request("quote/^VIX")
        if vix_data:
            indicators['vix'] = vix_data[0]['price'] if vix_data else None
        
        return indicators
    
    def analyze_portfolio_fundamentals(self, portfolio_df: pd.DataFrame) -> Dict:
        """Analyze portfolio fundamentals using FMP data."""
        self.logger.info("🔍 Analyzing portfolio fundamentals with FMP...")
        
        fundamentals_data = []
        for _, position in portfolio_df.iterrows():
            symbol = position['ticker']
            
            # Get company profile
            profile = self.get_company_profile(symbol)
            ratios = self.get_financial_ratios(symbol)
            metrics = self.get_key_metrics(symbol)
            
            if profile and len(profile) > 0:
                company_data = {
                    'ticker': symbol,
                    'company_name': profile[0].get('companyName', symbol),
                    'sector': profile[0].get('sector', 'Unknown'),
                    'industry': profile[0].get('industry', 'Unknown'),
                    'market_cap': profile[0].get('mktCap', 0),
                    'pe_ratio': ratios.get('priceEarningsRatio') if ratios else None,
                    'roe': ratios.get('returnOnEquity') if ratios else None,
                    'debt_to_equity': ratios.get('debtEquityRatio') if ratios else None,
                    'current_ratio': ratios.get('currentRatio') if ratios else None,
                    'revenue_growth': metrics.get('revenueGrowth') if metrics else None,
                    'eps_growth': metrics.get('epsgrowth') if metrics else None,
                    'free_cash_flow': metrics.get('freeCashFlow') if metrics else None,
                    'weight': position.get('weight', 0)
                }
                fundamentals_data.append(company_data)
        
        fundamentals_df = pd.DataFrame(fundamentals_data)
        self.logger.info(f"✅ Analyzed fundamentals for {len(fundamentals_df)} holdings")
        
        # Calculate portfolio-level metrics
        portfolio_metrics = self._calculate_portfolio_fundamentals(fundamentals_df)
        
        return {
            'holdings_fundamentals': fundamentals_df,
            'portfolio_metrics': portfolio_metrics
        }
    
    def _calculate_portfolio_fundamentals(self, fundamentals_df: pd.DataFrame) -> Dict:
        """Calculate weighted portfolio fundamental metrics."""
        if fundamentals_df.empty:
            return {}
        
        # Weight-adjusted metrics
        valid_pe = fundamentals_df.dropna(subset=['pe_ratio', 'weight'])
        portfolio_pe = (valid_pe['pe_ratio'] * valid_pe['weight']).sum() / valid_pe['weight'].sum() if not valid_pe.empty else None
        
        valid_roe = fundamentals_df.dropna(subset=['roe', 'weight'])
        portfolio_roe = (valid_roe['roe'] * valid_roe['weight']).sum() / valid_roe['weight'].sum() if not valid_roe.empty else None
        
        # Sector allocation
        sector_allocation = fundamentals_df.groupby('sector')['weight'].sum().to_dict()
        
        # Quality score (0-100)
        quality_scores = []
        for _, row in fundamentals_df.iterrows():
            score = 0
            if pd.notna(row['roe']) and row['roe'] > 0.15:
                score += 25
            if pd.notna(row['debt_to_equity']) and row['debt_to_equity'] < 0.5:
                score += 25
            if pd.notna(row['current_ratio']) and row['current_ratio'] > 1.5:
                score += 25
            if pd.notna(row['revenue_growth']) and row['revenue_growth'] > 0.1:
                score += 25
            quality_scores.append(score)
        
        avg_quality_score = np.mean(quality_scores) if quality_scores else 0
        
        return {
            'portfolio_pe': portfolio_pe,
            'portfolio_roe': portfolio_roe,
            'sector_allocation': sector_allocation,
            'avg_quality_score': avg_quality_score,
            'num_holdings': len(fundamentals_df)
        }
    
    def run_monte_carlo_simulation(self, portfolio_df: pd.DataFrame, days: int = 30, simulations: int = 1000) -> Dict:
        """Run Monte Carlo simulation for portfolio."""
        self.logger.info(f"🎯 Running Monte Carlo simulation ({simulations} scenarios)...")
        
        # Get historical returns for each holding
        returns_data = []
        weights = []
        
        for _, position in portfolio_df.iterrows():
            symbol = position['ticker']
            weight = position.get('weight', 0)
            
            price_data = self.get_stock_price_data(symbol, days=90)  # 3 months for volatility
            if not price_data.empty:
                price_data['returns'] = price_data['close'].pct_change().dropna()
                if len(price_data['returns']) > 10:
                    returns_data.append(price_data['returns'].values)
                    weights.append(weight)
        
        if not returns_data:
            return {'error': 'No historical data available for simulation'}
        
        # Convert to numpy arrays
        returns_matrix = np.array([returns[:min(len(r) for r in returns_data)] for returns in returns_data]).T
        weights_array = np.array(weights)
        weights_array = weights_array / weights_array.sum()  # Normalize weights
        
        # Calculate portfolio returns
        portfolio_returns = np.dot(returns_matrix, weights_array)
        
        # Simulation parameters
        mean_return = np.mean(portfolio_returns)
        volatility = np.std(portfolio_returns)
        
        # Run simulations
        simulated_returns = []
        for _ in range(simulations):
            random_returns = np.random.normal(mean_return, volatility, days)
            cumulative_return = np.prod(1 + random_returns) - 1
            simulated_returns.append(cumulative_return)
        
        simulated_returns = np.array(simulated_returns)
        
        # Calculate statistics
        results = {
            'simulations': simulations,
            'days': days,
            'expected_return': np.mean(simulated_returns),
            'volatility': np.std(simulated_returns),
            'var_95': np.percentile(simulated_returns, 5),
            'var_99': np.percentile(simulated_returns, 1),
            'best_case': np.percentile(simulated_returns, 95),
            'worst_case': np.percentile(simulated_returns, 5),
            'probability_positive': np.sum(simulated_returns > 0) / simulations,
            'all_returns': simulated_returns
        }
        
        self.logger.info(f"✅ Monte Carlo complete: {results['probability_positive']:.1%} chance of positive returns")
        return results
    
    def analyze_portfolio_changes(self, current_portfolio: pd.DataFrame) -> Dict:
        """Analyze changes from last week's portfolio."""
        self.logger.info("🔄 Analyzing portfolio changes...")
        
        changes = {
            'new_positions': [],
            'closed_positions': [],
            'increased_positions': [],
            'decreased_positions': [],
            'sector_changes': {}
        }
        
        if self.last_week_portfolio is None or self.last_week_portfolio.empty:
            self.logger.warning("⚠️ No previous portfolio data for comparison")
            return changes
        
        # Find new and closed positions
        current_tickers = set(current_portfolio['ticker'])
        last_week_tickers = set(self.last_week_portfolio['ticker'])
        
        changes['new_positions'] = list(current_tickers - last_week_tickers)
        changes['closed_positions'] = list(last_week_tickers - current_tickers)
        
        # Find position size changes
        for ticker in current_tickers.intersection(last_week_tickers):
            current_weight = current_portfolio[current_portfolio['ticker'] == ticker]['weight'].iloc[0]
            last_weight = self.last_week_portfolio[self.last_week_portfolio['ticker'] == ticker]['weight'].iloc[0]
            
            weight_change = current_weight - last_weight
            if abs(weight_change) > 0.01:  # 1% threshold
                if weight_change > 0:
                    changes['increased_positions'].append({
                        'ticker': ticker,
                        'change': weight_change,
                        'current_weight': current_weight
                    })
                else:
                    changes['decreased_positions'].append({
                        'ticker': ticker,
                        'change': weight_change,
                        'current_weight': current_weight
                    })
        
        # Save current portfolio for next week
        self._save_current_portfolio(current_portfolio)
        
        return changes
    
    def screen_investment_opportunities(self, num_candidates: int = 15) -> pd.DataFrame:
        """Screen for quality momentum investment opportunities using FMP."""
        self.logger.info(f"👀 Screening for {num_candidates} investment opportunities...")
        
        # Get list of S&P 500 stocks for screening
        sp500_data = self._make_fmp_request("sp500_constituent")
        if not sp500_data:
            self.logger.warning("⚠️ Could not fetch S&P 500 list, using fallback symbols")
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B', 'UNH', 'JNJ']
        else:
            symbols = [stock['symbol'] for stock in sp500_data[:100]]  # Screen top 100 for speed
        
        candidates = []
        
        for symbol in symbols:
            try:
                profile = self.get_company_profile(symbol)
                ratios = self.get_financial_ratios(symbol)
                metrics = self.get_key_metrics(symbol)
                price_data = self.get_stock_price_data(symbol, days=30)
                
                if profile and ratios and metrics and not price_data.empty:
                    # Calculate momentum (30-day return)
                    momentum = (price_data['close'].iloc[-1] / price_data['close'].iloc[0] - 1) if len(price_data) >= 30 else 0
                    
                    # Quality filters
                    roe = ratios.get('returnOnEquity', 0)
                    debt_equity = ratios.get('debtEquityRatio', float('inf'))
                    current_ratio = ratios.get('currentRatio', 0)
                    revenue_growth = metrics.get('revenueGrowth', 0)
                    
                    # Quality score
                    quality_score = 0
                    if roe > 0.15:
                        quality_score += 25
                    if debt_equity < 0.5:
                        quality_score += 25
                    if current_ratio > 1.5:
                        quality_score += 25
                    if revenue_growth > 0.1:
                        quality_score += 25
                    
                    # Momentum score
                    momentum_score = min(100, max(0, (momentum + 0.1) * 500))  # Scale to 0-100
                    
                    # Combined score
                    combined_score = (quality_score * 0.6) + (momentum_score * 0.4)
                    
                    candidates.append({
                        'ticker': symbol,
                        'company_name': profile[0].get('companyName', symbol),
                        'sector': profile[0].get('sector', 'Unknown'),
                        'market_cap': profile[0].get('mktCap', 0),
                        'roe': roe,
                        'debt_equity': debt_equity,
                        'current_ratio': current_ratio,
                        'revenue_growth': revenue_growth,
                        'momentum_30d': momentum,
                        'quality_score': quality_score,
                        'momentum_score': momentum_score,
                        'combined_score': combined_score,
                        'pe_ratio': ratios.get('priceEarningsRatio'),
                        'price': price_data['close'].iloc[-1] if not price_data.empty else None
                    })
                
            except Exception as e:
                self.logger.debug(f"Skipping {symbol}: {e}")
                continue
        
        candidates_df = pd.DataFrame(candidates)
        
        if not candidates_df.empty:
            # Sort by combined score and return top candidates
            candidates_df = candidates_df.sort_values('combined_score', ascending=False).head(num_candidates)
            self.logger.info(f"✅ Found {len(candidates_df)} quality momentum candidates")
        
        return candidates_df
    
    def _load_last_week_portfolio(self) -> Optional[pd.DataFrame]:
        """Load last week's portfolio for comparison."""
        portfolio_file = Path("data/last_week_portfolio.csv")
        if portfolio_file.exists():
            try:
                return pd.read_csv(portfolio_file)
            except Exception as e:
                self.logger.warning(f"⚠️ Could not load last week's portfolio: {e}")
        return None
    
    def _save_current_portfolio(self, portfolio_df: pd.DataFrame):
        """Save current portfolio for next week's comparison."""
        portfolio_file = Path("data/last_week_portfolio.csv")
        portfolio_file.parent.mkdir(parents=True, exist_ok=True)
        portfolio_df.to_csv(portfolio_file, index=False)
        self.logger.info("💾 Saved current portfolio for next week's comparison")
    
    def create_portfolio_visualizations(self, portfolio_data: Dict) -> Dict[str, str]:
        """Create comprehensive portfolio visualizations."""
        self.logger.info("📊 Creating portfolio visualizations...")
        
        chart_files = {}
        
        # 1. Portfolio Performance Chart
        if 'portfolio_history' in portfolio_data:
            chart_files['performance'] = self._create_performance_chart(portfolio_data['portfolio_history'])
        
        # 2. Sector Allocation Charts
        if 'fundamentals' in portfolio_data:
            chart_files['sector_allocation'] = self._create_sector_allocation_chart(portfolio_data['fundamentals']['holdings_fundamentals'])
        
        # 3. Monte Carlo Results
        if 'monte_carlo' in portfolio_data:
            chart_files['monte_carlo'] = self._create_monte_carlo_chart(portfolio_data['monte_carlo'])
        
        # 4. Portfolio Changes
        if 'portfolio_changes' in portfolio_data:
            chart_files['portfolio_changes'] = self._create_portfolio_changes_chart(portfolio_data['portfolio_changes'])
        
        # 5. Quality vs Momentum Scatter
        if 'investment_opportunities' in portfolio_data and not portfolio_data['investment_opportunities'].empty:
            chart_files['opportunities'] = self._create_opportunities_chart(portfolio_data['investment_opportunities'])
        
        # 6. Risk Analysis
        chart_files['risk_analysis'] = self._create_risk_analysis_chart(portfolio_data)
        
        self.logger.info(f"✅ Created {len(chart_files)} visualization charts")
        return chart_files
    
    def _create_performance_chart(self, history_df: pd.DataFrame) -> str:
        """Create portfolio performance chart."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Portfolio value over time
        ax1.plot(history_df.index, history_df['equity'], linewidth=3, color='#2E86AB', label='Portfolio Value')
        ax1.set_title('Portfolio Performance', fontsize=18, fontweight='bold', pad=20)
        ax1.set_ylabel('Portfolio Value ($)', fontsize=14)
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=12)
        ax1.tick_params(axis='both', which='major', labelsize=12)
        
        # Daily returns
        daily_returns = history_df['equity'].pct_change().dropna() * 100
        ax2.plot(daily_returns.index, daily_returns, alpha=0.8, color='#A23B72', linewidth=2)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax2.set_title('Daily Returns (%)', fontsize=16, fontweight='bold', pad=15)
        ax2.set_ylabel('Return (%)', fontsize=14)
        ax2.set_xlabel('Date', fontsize=14)
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='both', which='major', labelsize=12)
        
        plt.tight_layout(pad=2.0)
        filename = self.charts_dir / 'portfolio_performance.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close()
        
        return str(filename)
    
    def _create_sector_allocation_chart(self, fundamentals_df: pd.DataFrame) -> str:
        """Create sector allocation visualization."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Pie chart
        sector_weights = fundamentals_df.groupby('sector')['weight'].sum()
        colors = plt.cm.Set3(np.linspace(0, 1, len(sector_weights)))
        
        wedges, texts, autotexts = ax1.pie(sector_weights.values, labels=sector_weights.index, 
                                          autopct='%1.1f%%', colors=colors, startangle=90,
                                          textprops={'fontsize': 12})
        ax1.set_title('Sector Allocation', fontsize=18, fontweight='bold', pad=20)
        
        # Improve text formatting
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(11)
        
        # Bar chart with quality scores (handle missing columns gracefully)
        # Only use columns that exist
        agg_dict = {'weight': 'sum'}
        if 'roe' in fundamentals_df.columns:
            agg_dict['roe'] = 'mean'
        if 'pe_ratio' in fundamentals_df.columns:
            agg_dict['pe_ratio'] = 'mean'
        
        sector_quality = fundamentals_df.groupby('sector').agg(agg_dict).fillna(0)
        
        x = range(len(sector_quality))
        bars = ax2.bar(x, sector_quality['weight'] * 100, alpha=0.8, color=colors[:len(sector_quality)])
        ax2.set_title('Sector Weights', fontsize=18, fontweight='bold', pad=20)
        ax2.set_ylabel('Weight (%)', fontsize=14)
        ax2.set_xlabel('Sector', fontsize=14)
        ax2.set_xticks(x)
        ax2.set_xticklabels(sector_quality.index, rotation=45, ha='right', fontsize=12)
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.tick_params(axis='both', which='major', labelsize=12)
        
        # Add value labels on bars
        for bar, weight in zip(bars, sector_quality['weight']):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{weight:.1%}', ha='center', va='bottom', fontweight='bold', fontsize=10)
        
        plt.tight_layout(pad=2.0)
        filename = self.charts_dir / 'sector_allocation.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close()
        
        return str(filename)
    
    def _create_monte_carlo_chart(self, monte_carlo_results: Dict) -> str:
        """Create Monte Carlo simulation visualization."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        returns = monte_carlo_results['all_returns'] * 100
        
        # Handle NaN values
        if np.isnan(returns).any() or len(returns) == 0:
            # Create placeholder chart
            ax1.text(0.5, 0.5, 'Monte Carlo Data\nContains Invalid Values', ha='center', va='center', 
                    transform=ax1.transAxes, fontsize=14, bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
            ax1.set_title('Monte Carlo Results', fontsize=16, fontweight='bold', pad=15)
            
            ax2.text(0.5, 0.5, 'Invalid Data\nCannot Generate\nProbability Curve', ha='center', va='center', 
                    transform=ax2.transAxes, fontsize=14, bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
            ax2.set_title('Cumulative Probability', fontsize=16, fontweight='bold', pad=15)
            
            plt.tight_layout(pad=2.0)
            filename = self.charts_dir / 'monte_carlo_analysis.png'
            plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
            plt.close()
            return str(filename)
        
        # Filter out NaN values
        valid_returns = returns[~np.isnan(returns)]
        if len(valid_returns) == 0:
            valid_returns = np.array([0.0])  # Fallback to zero
        
        simulations = monte_carlo_results.get('simulations', len(valid_returns))
        expected_return = monte_carlo_results.get('expected_return', 0)
        var_95 = monte_carlo_results.get('var_95', np.percentile(valid_returns/100, 5))
        volatility = monte_carlo_results.get('volatility', np.std(valid_returns/100))
        probability_positive = monte_carlo_results.get('probability_positive', np.sum(valid_returns > 0) / len(valid_returns))
        
        # Handle NaN in statistics
        if np.isnan(expected_return):
            expected_return = 0
        if np.isnan(var_95):
            var_95 = -0.05
        if np.isnan(volatility):
            volatility = 0.1
        if np.isnan(probability_positive):
            probability_positive = 0.5
        
        # Histogram of returns
        ax1.hist(valid_returns, bins=30, alpha=0.8, color='#2E86AB', edgecolor='black', linewidth=0.5)
        ax1.axvline(expected_return * 100, color='red', linestyle='--', linewidth=2,
                   label=f"Expected: {expected_return*100:.1f}%")
        ax1.axvline(var_95 * 100, color='orange', linestyle='--', linewidth=2,
                   label=f"95% VaR: {var_95*100:.1f}%")
        ax1.set_title(f'Monte Carlo Results ({simulations} simulations)', 
                     fontsize=16, fontweight='bold', pad=15)
        ax1.set_xlabel('Return (%)', fontsize=14)
        ax1.set_ylabel('Frequency', fontsize=14)
        ax1.legend(fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='both', which='major', labelsize=12)
        
        # Probability curve
        sorted_returns = np.sort(valid_returns)
        probabilities = np.arange(1, len(sorted_returns) + 1) / len(sorted_returns)
        ax2.plot(sorted_returns, probabilities, linewidth=3, color='#A23B72')
        ax2.axvline(0, color='black', linestyle='-', alpha=0.5, linewidth=1)
        ax2.set_title('Cumulative Probability', fontsize=16, fontweight='bold', pad=15)
        ax2.set_xlabel('Return (%)', fontsize=14)
        ax2.set_ylabel('Probability', fontsize=14)
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='both', which='major', labelsize=12)
        
        # Add text box with key stats
        stats_text = f"""Key Statistics:
Expected Return: {expected_return*100:.1f}%
Volatility: {volatility*100:.1f}%
95% VaR: {var_95*100:.1f}%
Prob. Positive: {probability_positive:.1%}"""
        
        ax2.text(0.05, 0.95, stats_text, transform=ax2.transAxes, fontsize=11,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9, pad=0.8))
        
        plt.tight_layout(pad=2.0)
        filename = self.charts_dir / 'monte_carlo_analysis.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close()
        
        return str(filename)
    
    def _create_portfolio_changes_chart(self, changes: Dict) -> str:
        """Create portfolio changes visualization."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # New positions
        if changes['new_positions']:
            bars1 = ax1.bar(range(len(changes['new_positions'])), [1] * len(changes['new_positions']), 
                           color='green', alpha=0.8)
            ax1.set_title('New Positions', fontsize=16, fontweight='bold', pad=15)
            ax1.set_xticks(range(len(changes['new_positions'])))
            ax1.set_xticklabels(changes['new_positions'], rotation=45, ha='right', fontsize=11)
            ax1.set_ylabel('Count', fontsize=12)
        else:
            ax1.text(0.5, 0.5, 'No new positions', ha='center', va='center', 
                    transform=ax1.transAxes, fontsize=14, bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
            ax1.set_title('New Positions', fontsize=16, fontweight='bold', pad=15)
        ax1.tick_params(axis='both', which='major', labelsize=11)
        
        # Closed positions
        if changes['closed_positions']:
            bars2 = ax2.bar(range(len(changes['closed_positions'])), [1] * len(changes['closed_positions']), 
                           color='red', alpha=0.8)
            ax2.set_title('Closed Positions', fontsize=16, fontweight='bold', pad=15)
            ax2.set_xticks(range(len(changes['closed_positions'])))
            ax2.set_xticklabels(changes['closed_positions'], rotation=45, ha='right', fontsize=11)
            ax2.set_ylabel('Count', fontsize=12)
        else:
            ax2.text(0.5, 0.5, 'No closed positions', ha='center', va='center', 
                    transform=ax2.transAxes, fontsize=14, bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
            ax2.set_title('Closed Positions', fontsize=16, fontweight='bold', pad=15)
        ax2.tick_params(axis='both', which='major', labelsize=11)
        
        # Increased positions
        if changes['increased_positions']:
            tickers = [pos['ticker'] for pos in changes['increased_positions']]
            changes_vals = [pos['change'] * 100 for pos in changes['increased_positions']]
            bars3 = ax3.bar(range(len(tickers)), changes_vals, color='lightgreen', alpha=0.8)
            ax3.set_title('Increased Positions', fontsize=16, fontweight='bold', pad=15)
            ax3.set_ylabel('Weight Change (%)', fontsize=12)
            ax3.set_xticks(range(len(tickers)))
            ax3.set_xticklabels(tickers, rotation=45, ha='right', fontsize=11)
            ax3.grid(True, alpha=0.3, axis='y')
        else:
            ax3.text(0.5, 0.5, 'No increased positions', ha='center', va='center', 
                    transform=ax3.transAxes, fontsize=14, bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
            ax3.set_title('Increased Positions', fontsize=16, fontweight='bold', pad=15)
        ax3.tick_params(axis='both', which='major', labelsize=11)
        
        # Decreased positions
        if changes['decreased_positions']:
            tickers = [pos['ticker'] for pos in changes['decreased_positions']]
            changes_vals = [pos['change'] * 100 for pos in changes['decreased_positions']]
            bars4 = ax4.bar(range(len(tickers)), changes_vals, color='lightcoral', alpha=0.8)
            ax4.set_title('Decreased Positions', fontsize=16, fontweight='bold', pad=15)
            ax4.set_ylabel('Weight Change (%)', fontsize=12)
            ax4.set_xticks(range(len(tickers)))
            ax4.set_xticklabels(tickers, rotation=45, ha='right', fontsize=11)
            ax4.grid(True, alpha=0.3, axis='y')
        else:
            ax4.text(0.5, 0.5, 'No decreased positions', ha='center', va='center', 
                    transform=ax4.transAxes, fontsize=14, bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
            ax4.set_title('Decreased Positions', fontsize=16, fontweight='bold', pad=15)
        ax4.tick_params(axis='both', which='major', labelsize=11)
        
        plt.tight_layout(pad=2.0)
        filename = self.charts_dir / 'portfolio_changes.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close()
        
        return str(filename)
    
    def _create_opportunities_chart(self, opportunities_df: pd.DataFrame) -> str:
        """Create investment opportunities scatter plot."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Quality vs Momentum scatter
        # Normalize market cap for better sizing
        sizes = (opportunities_df['market_cap'] / 1e9).clip(upper=100) * 50 + 20  # Min size 20, max ~5020
        scatter = ax1.scatter(opportunities_df['quality_score'], opportunities_df['momentum_score'], 
                             s=sizes, alpha=0.7, c=opportunities_df['combined_score'], 
                             cmap='RdYlGn', edgecolors='black', linewidth=0.5)
        ax1.set_xlabel('Quality Score', fontsize=14)
        ax1.set_ylabel('Momentum Score', fontsize=14)
        ax1.set_title('Investment Opportunities: Quality vs Momentum', fontsize=16, fontweight='bold', pad=15)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='both', which='major', labelsize=12)
        
        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax1)
        cbar.set_label('Combined Score', rotation=270, labelpad=20, fontsize=12)
        cbar.ax.tick_params(labelsize=11)
        
        # Top opportunities bar chart
        top_10 = opportunities_df.head(10)
        bars = ax2.barh(range(len(top_10)), top_10['combined_score'], alpha=0.8, 
                       color='lightblue', edgecolor='darkblue', linewidth=0.5)
        ax2.set_title('Top 10 Investment Opportunities', fontsize=16, fontweight='bold', pad=15)
        ax2.set_xlabel('Combined Score', fontsize=14)
        ax2.set_yticks(range(len(top_10)))
        ax2.set_yticklabels(top_10['ticker'], fontsize=12)
        ax2.grid(True, alpha=0.3, axis='x')
        ax2.tick_params(axis='both', which='major', labelsize=12)
        
        # Add value labels on bars
        for i, (bar, score) in enumerate(zip(bars, top_10['combined_score'])):
            ax2.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                    f'{score:.1f}', va='center', fontweight='bold', fontsize=10)
        
        plt.tight_layout(pad=2.0)
        filename = self.charts_dir / 'investment_opportunities.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close()
        
        return str(filename)
    
    def _create_risk_analysis_chart(self, portfolio_data: Dict) -> str:
        """Create risk analysis visualization."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Risk gauge (VaR)
        if 'monte_carlo' in portfolio_data:
            var_95 = abs(portfolio_data['monte_carlo']['var_95'] * 100)
            remaining = max(0, 20 - var_95)  # Show up to 20% risk scale
            colors = ['red' if var_95 > 10 else 'orange' if var_95 > 5 else 'yellow', 'lightgreen']
            sizes = [var_95, remaining] if remaining > 0 else [var_95]
            labels = [f'VaR 95%: {var_95:.1f}%', f'Low Risk Zone: {remaining:.1f}%'] if remaining > 0 else [f'VaR 95%: {var_95:.1f}%']
            
            wedges, texts, autotexts = ax1.pie(sizes, labels=labels, colors=colors[:len(sizes)], 
                                              startangle=90, counterclock=False, autopct='%1.1f%%',
                                              textprops={'fontsize': 11})
            ax1.set_title(f'Value at Risk (95%)', fontsize=16, fontweight='bold', pad=15)
            
            for autotext in autotexts:
                autotext.set_fontweight('bold')
        else:
            ax1.text(0.5, 0.5, 'Monte Carlo\nData Not Available', ha='center', va='center', 
                    transform=ax1.transAxes, fontsize=14, bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
            ax1.set_title('Value at Risk (95%)', fontsize=16, fontweight='bold', pad=15)
        
        # Sector concentration
        if 'fundamentals' in portfolio_data:
            fundamentals_df = portfolio_data['fundamentals']['holdings_fundamentals']
            sector_weights = fundamentals_df.groupby('sector')['weight'].sum().sort_values(ascending=True)
            bars = ax2.barh(range(len(sector_weights)), sector_weights * 100, alpha=0.8, color='steelblue')
            ax2.set_title('Sector Concentration Risk', fontsize=16, fontweight='bold', pad=15)
            ax2.set_xlabel('Weight (%)', fontsize=14)
            ax2.set_yticks(range(len(sector_weights)))
            ax2.set_yticklabels(sector_weights.index, fontsize=12)
            ax2.grid(True, alpha=0.3, axis='x')
            ax2.tick_params(axis='both', which='major', labelsize=12)
            
            # Add value labels
            for i, (bar, weight) in enumerate(zip(bars, sector_weights)):
                ax2.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                        f'{weight:.1%}', va='center', fontweight='bold', fontsize=10)
        else:
            ax2.text(0.5, 0.5, 'Fundamentals\nData Not Available', ha='center', va='center', 
                    transform=ax2.transAxes, fontsize=14, bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
            ax2.set_title('Sector Concentration Risk', fontsize=16, fontweight='bold', pad=15)
        
        # Volatility distribution
        if 'monte_carlo' in portfolio_data:
            returns = portfolio_data['monte_carlo']['all_returns'] * 100
            
            # Handle NaN values
            if np.isnan(returns).any() or len(returns) == 0:
                ax3.text(0.5, 0.5, 'Monte Carlo Data\nContains Invalid Values', ha='center', va='center', 
                        transform=ax3.transAxes, fontsize=14, bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
                ax3.set_title('Return Distribution', fontsize=16, fontweight='bold', pad=15)
            else:
                # Filter out NaN values
                valid_returns = returns[~np.isnan(returns)]
                if len(valid_returns) == 0:
                    valid_returns = np.array([0.0])  # Fallback
                
                n, bins, patches = ax3.hist(valid_returns, bins=30, alpha=0.8, color='orange', edgecolor='black', linewidth=0.5)
                ax3.set_title('Return Distribution', fontsize=16, fontweight='bold', pad=15)
                ax3.set_xlabel('Return (%)', fontsize=14)
                ax3.set_ylabel('Frequency', fontsize=14)
                ax3.grid(True, alpha=0.3)
                ax3.tick_params(axis='both', which='major', labelsize=12)
                
                # Add mean line
                mean_return = np.mean(valid_returns)
                if not np.isnan(mean_return):
                    ax3.axvline(mean_return, color='red', linestyle='--', linewidth=2, 
                               label=f'Mean: {mean_return:.1f}%')
                    ax3.legend(fontsize=12)
        else:
            ax3.text(0.5, 0.5, 'Monte Carlo\nData Not Available', ha='center', va='center', 
                    transform=ax3.transAxes, fontsize=14, bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
            ax3.set_title('Return Distribution', fontsize=16, fontweight='bold', pad=15)
        
        # Risk metrics summary
        risk_metrics = []
        if 'monte_carlo' in portfolio_data:
            mc = portfolio_data['monte_carlo']
            risk_metrics = [
                f"Expected Return: {mc.get('expected_return', 0)*100:.1f}%",
                f"Volatility: {mc.get('volatility', 0)*100:.1f}%", 
                f"95% VaR: {mc.get('var_95', 0)*100:.1f}%",
                f"99% VaR: {mc.get('var_99', mc.get('var_95', 0))*100:.1f}%",
                f"Prob. Positive: {mc.get('probability_positive', 0):.1%}",
                f"Best Case: {mc.get('best_case', 0)*100:.1f}%",
                f"Worst Case: {mc.get('worst_case', 0)*100:.1f}%"
            ]
        else:
            risk_metrics = ["Monte Carlo analysis", "data not available"]
        
        ax4.text(0.1, 0.9, '\n'.join(risk_metrics), transform=ax4.transAxes, fontsize=12,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8, pad=1.0))
        ax4.set_title('Risk Summary', fontsize=16, fontweight='bold', pad=15)
        ax4.axis('off')
        
        plt.tight_layout(pad=2.0)
        filename = self.charts_dir / 'risk_analysis.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close()
        
        return str(filename)

def main():
    """Test enhanced portfolio analytics."""
    logging.basicConfig(level=logging.INFO)
    
    analytics = EnhancedPortfolioAnalytics()
    
    # Test with mock data
    positions_df = pd.DataFrame([
        {'ticker': 'AAPL', 'shares': 100, 'current_price': 150, 'weight': 0.4},
        {'ticker': 'MSFT', 'shares': 75, 'current_price': 160, 'weight': 0.6}
    ])
    
    print("🚀 Testing enhanced portfolio analytics...")
    
    # Test fundamentals analysis
    print("🔍 Testing fundamentals analysis...")
    fundamentals_result = analytics.analyze_portfolio_fundamentals(positions_df)
    print(f"✅ Analyzed fundamentals for {len(fundamentals_result.get('holdings_fundamentals', []))} holdings")
    
    # Test Monte Carlo simulation
    print("🎯 Testing Monte Carlo simulation...")
    monte_carlo_result = analytics.run_monte_carlo_simulation(positions_df, days=30, simulations=100)
    if 'error' not in monte_carlo_result:
        print(f"✅ Monte Carlo complete: Expected return {monte_carlo_result.get('expected_return', 0)*100:.1f}%")
    else:
        print(f"⚠️ Monte Carlo simulation: {monte_carlo_result['error']}")
    
    # Test investment opportunities screening
    print("👀 Testing investment screening...")
    opportunities = analytics.screen_investment_opportunities(num_candidates=5)
    print(f"✅ Found {len(opportunities)} investment opportunities")
    
    # Test visualization creation
    print("📊 Testing chart generation...")
    test_data = {
        'fundamentals': fundamentals_result,
        'monte_carlo': monte_carlo_result if 'error' not in monte_carlo_result else None,
        'investment_opportunities': opportunities,
        'portfolio_changes': {
            'new_positions': ['TEST1', 'TEST2'],
            'closed_positions': ['OLD1'],
            'increased_positions': [{'ticker': 'AAPL', 'change': 0.05, 'current_weight': 0.45}],
            'decreased_positions': [{'ticker': 'MSFT', 'change': -0.03, 'current_weight': 0.57}]
        }
    }
    
    charts = analytics.create_portfolio_visualizations(test_data)
    print(f"✅ Created {len(charts)} visualization charts with improved proportions")
    
    print("🎉 Enhanced analytics test completed successfully!")
    print("\n📊 Charts generated:")
    for chart_type, file_path in charts.items():
        print(f"   • {chart_type}: {Path(file_path).name}")
    
    return True

if __name__ == "__main__":
    main() 