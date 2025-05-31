import pandas as pd
import numpy as np
import os
from datetime import date, datetime, timedelta
import requests
from typing import Dict, List, Tuple
import time
from dotenv import load_dotenv

# Import Fama-French factor analysis for portfolio attribution
from fama_french_factors import (
    get_fama_french_factors,
    get_momentum_factor,
    get_stock_returns,
    calculate_factor_exposures
)

load_dotenv()
API_KEY = os.getenv("FMP_API_KEY")

def get_latest_portfolio_file() -> str:
    """Get the latest selected portfolio CSV file."""
    pattern = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files', '04_final_portfolio_selection_*.csv')
    import glob
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError("No selected portfolio CSV file found.")
    return max(files, key=os.path.getctime)  # Get the most recent file

def get_historical_prices(tickers: List[str], days: int = 252) -> Dict:
    """Get historical price data for correlation and volatility analysis."""
    print(f"Fetching historical price data for {len(tickers)} tickers...")
    
    price_data = {}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    for i, ticker in enumerate(tickers):
        try:
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?from={start_date.strftime('%Y-%m-%d')}&to={end_date.strftime('%Y-%m-%d')}&apikey={API_KEY}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json().get('historical', [])
                if data:
                    prices = [float(d['close']) for d in reversed(data)]  # Reverse to get chronological order
                    price_data[ticker] = prices
                else:
                    print(f"Warning: No price data for {ticker}")
            else:
                print(f"Error fetching data for {ticker}: {response.status_code}")
            
            # Rate limiting
            if i % 10 == 0 and i > 0:
                print(f"Processed {i}/{len(tickers)} tickers...")
                time.sleep(1)
                
        except Exception as e:
            print(f"Error processing {ticker}: {str(e)}")
            continue
    
    print(f"Successfully fetched data for {len(price_data)}/{len(tickers)} tickers")
    return price_data

def calculate_returns(price_data: Dict) -> pd.DataFrame:
    """Calculate daily returns from price data."""
    returns_data = {}
    
    for ticker, prices in price_data.items():
        if len(prices) > 1:
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            returns_data[ticker] = returns
    
    # Create DataFrame with aligned data
    returns_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in returns_data.items()]))
    return returns_df

def analyze_correlations(returns_df: pd.DataFrame, threshold: float = 0.8) -> Dict:
    """Analyze correlations between stocks."""
    print(f"Analyzing correlations (threshold: {threshold})...")
    
    correlation_matrix = returns_df.corr()
    
    # Find high correlations
    high_correlations = []
    for i in range(len(correlation_matrix.columns)):
        for j in range(i+1, len(correlation_matrix.columns)):
            corr = correlation_matrix.iloc[i, j]
            if abs(corr) > threshold:
                high_correlations.append({
                    'ticker1': correlation_matrix.columns[i],
                    'ticker2': correlation_matrix.columns[j],
                    'correlation': corr
                })
    
    # Calculate average correlations
    avg_correlation = correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean()
    
    return {
        'correlation_matrix': correlation_matrix,
        'high_correlations': high_correlations,
        'avg_correlation': avg_correlation,
        'max_correlation': correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].max(),
        'min_correlation': correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].min()
    }

def analyze_volatility(returns_df: pd.DataFrame) -> Dict:
    """Analyze volatility of individual stocks."""
    print("Analyzing volatility...")
    
    # Calculate annualized volatility (daily returns * sqrt(252))
    volatilities = returns_df.std() * np.sqrt(252)
    
    # Identify high volatility stocks (top 20%)
    high_vol_threshold = volatilities.quantile(0.8)
    high_vol_stocks = volatilities[volatilities > high_vol_threshold].to_dict()
    
    return {
        'volatilities': volatilities.to_dict(),
        'avg_volatility': volatilities.mean(),
        'max_volatility': volatilities.max(),
        'min_volatility': volatilities.min(),
        'high_vol_threshold': high_vol_threshold,
        'high_vol_stocks': high_vol_stocks
    }

def get_beta_data(tickers: List[str]) -> Dict:
    """Get beta data for portfolio stocks."""
    print("Fetching beta data...")
    
    beta_data = {}
    
    for ticker in tickers:
        try:
            url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={API_KEY}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list):
                    beta = data[0].get('beta')
                    if beta:
                        beta_data[ticker] = float(beta)
            
            time.sleep(0.1)  # Rate limiting
            
        except Exception as e:
            print(f"Error getting beta for {ticker}: {str(e)}")
            continue
    
    return beta_data

def analyze_portfolio_risk(portfolio_df: pd.DataFrame, returns_df: pd.DataFrame) -> Dict:
    """Calculate portfolio-level risk metrics."""
    print("Calculating portfolio risk metrics...")
    
    # Equal weight assumption
    weights = np.array([1/len(portfolio_df)] * len(portfolio_df))
    
    # Portfolio returns (only for stocks we have data for)
    available_tickers = [t for t in portfolio_df['Ticker'].tolist() if t in returns_df.columns]
    portfolio_returns_df = returns_df[available_tickers]
    portfolio_weights = np.array([1/len(available_tickers)] * len(available_tickers))
    
    # Calculate portfolio returns
    portfolio_returns = (portfolio_returns_df * portfolio_weights).sum(axis=1)
    
    # Portfolio risk metrics
    portfolio_volatility = portfolio_returns.std() * np.sqrt(252)
    portfolio_return = portfolio_returns.mean() * 252
    
    # Sharpe ratio (assuming 3% risk-free rate)
    risk_free_rate = 0.03
    sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
    
    # Maximum drawdown
    cumulative_returns = (1 + portfolio_returns).cumprod()
    peak = cumulative_returns.expanding(min_periods=1).max()
    drawdown = (cumulative_returns - peak) / peak
    max_drawdown = drawdown.min()
    
    return {
        'portfolio_volatility': portfolio_volatility,
        'portfolio_return': portfolio_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'available_data_coverage': len(available_tickers) / len(portfolio_df)
    }

def analyze_concentration_risk(portfolio_df: pd.DataFrame) -> Dict:
    """Analyze concentration risks in the portfolio."""
    print("Analyzing concentration risks...")
    
    # Sector concentration
    sector_weights = portfolio_df.groupby('Sector')['Portfolio Weight'].sum()
    max_sector_weight = sector_weights.max()
    sector_hhi = (sector_weights ** 2).sum()  # Herfindahl-Hirschman Index
    
    # Style concentration
    style_weights = portfolio_df.groupby('Style')['Portfolio Weight'].sum()
    max_style_weight = style_weights.max()
    style_hhi = (style_weights ** 2).sum()
    
    # Individual position concentration
    max_position_weight = portfolio_df['Portfolio Weight'].max()
    
    return {
        'sector_concentration': {
            'max_sector_weight': max_sector_weight,
            'sector_hhi': sector_hhi,
            'sector_weights': sector_weights.to_dict()
        },
        'style_concentration': {
            'max_style_weight': max_style_weight,
            'style_hhi': style_hhi,
            'style_weights': style_weights.to_dict()
        },
        'position_concentration': {
            'max_position_weight': max_position_weight,
            'top_10_weight': portfolio_df.nlargest(10, 'Portfolio Weight')['Portfolio Weight'].sum()
        }
    }

def analyze_portfolio_factor_attribution(portfolio_df: pd.DataFrame, returns_df: pd.DataFrame) -> Dict:
    """Analyze portfolio factor exposures using Fama-French methodology."""
    print("\n=== FAMA-FRENCH PORTFOLIO FACTOR ATTRIBUTION ===")
    
    try:
        # Get Fama-French factor data (2 years)
        print("1. Downloading Fama-French factor data...")
        start_date = (datetime.now() - timedelta(days=365*2)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        ff_factors = get_fama_french_factors(start_date, end_date)
        momentum_factor = get_momentum_factor(start_date, end_date)
        
        if ff_factors.empty:
            print("⚠️  No FF factor data available")
            return {}
        
        print(f"✓ Downloaded {len(ff_factors)} days of factor data")
        
        # Calculate portfolio returns (equal weighted)
        available_tickers = [t for t in portfolio_df['Ticker'].tolist() if t in returns_df.columns]
        if len(available_tickers) < 5:
            print("⚠️  Insufficient return data for factor analysis")
            return {}
        
        portfolio_weights = np.array([1/len(available_tickers)] * len(available_tickers))
        portfolio_returns = (returns_df[available_tickers] * portfolio_weights).sum(axis=1)
        
        # Align dates between portfolio returns and factor data
        portfolio_returns_series = pd.Series(portfolio_returns.values, 
                                           index=pd.date_range(end=datetime.now().date(), 
                                                             periods=len(portfolio_returns), freq='D'))
        
        # Get overlapping dates
        common_dates = portfolio_returns_series.index.intersection(ff_factors.index)
        if len(common_dates) < 100:  # Need at least 100 observations
            print("⚠️  Insufficient overlapping data for regression")
            return {}
        
        # Align data
        portfolio_aligned = portfolio_returns_series.loc[common_dates]
        factors_aligned = ff_factors.loc[common_dates]
        
        print(f"✓ Aligned data: {len(common_dates)} observations")
        
        # Perform factor regression: R_p = α + β_mkt*MKT + β_smb*SMB + β_hml*HML + β_rmw*RMW + β_cma*CMA + ε
        from sklearn.linear_model import LinearRegression
        
        X = factors_aligned[['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA']].values
        y = (portfolio_aligned.values - factors_aligned['RF'].values)  # Excess returns
        
        # Fit regression
        model = LinearRegression().fit(X, y)
        r_squared = model.score(X, y)
        
        # Extract factor loadings
        factor_exposures = {
            'Market_Beta': model.coef_[0],
            'Size_Beta': model.coef_[1],      # SMB
            'Value_Beta': model.coef_[2],     # HML  
            'Quality_Beta': model.coef_[3],   # RMW
            'Investment_Beta': model.coef_[4], # CMA
            'Alpha': model.intercept_,
            'R_Squared': r_squared
        }
        
        # Add momentum factor if available
        if not momentum_factor.empty:
            momentum_aligned = momentum_factor.loc[common_dates]
            if len(momentum_aligned) == len(y):
                X_with_mom = np.column_stack([X, momentum_aligned['Mom'].values])
                model_mom = LinearRegression().fit(X_with_mom, y)
                factor_exposures.update({
                    'Momentum_Beta': model_mom.coef_[5],
                    'R_Squared_with_Mom': model_mom.score(X_with_mom, y)
                })
        
        # Calculate factor contributions to portfolio return
        avg_factor_returns = factors_aligned.mean()
        factor_contributions = {
            'Market_Contribution': factor_exposures['Market_Beta'] * avg_factor_returns['Mkt-RF'],
            'Size_Contribution': factor_exposures['Size_Beta'] * avg_factor_returns['SMB'],
            'Value_Contribution': factor_exposures['Value_Beta'] * avg_factor_returns['HML'],
            'Quality_Contribution': factor_exposures['Quality_Beta'] * avg_factor_returns['RMW'],
            'Investment_Contribution': factor_exposures['Investment_Beta'] * avg_factor_returns['CMA']
        }
        
        if 'Momentum_Beta' in factor_exposures:
            momentum_contrib = factor_exposures['Momentum_Beta'] * momentum_aligned.mean()['Mom']
            factor_contributions['Momentum_Contribution'] = momentum_contrib
        
        # Portfolio style classification based on factor loadings
        style_characteristics = classify_portfolio_style(factor_exposures)
        
        print("✓ Factor regression complete!")
        print(f"  Portfolio R²: {r_squared:.3f}")
        print(f"  Market Beta: {factor_exposures['Market_Beta']:.3f}")
        print(f"  Size Tilt: {factor_exposures['Size_Beta']:.3f} ({'Small-cap' if factor_exposures['Size_Beta'] > 0 else 'Large-cap'} bias)")
        print(f"  Value Tilt: {factor_exposures['Value_Beta']:.3f} ({'Value' if factor_exposures['Value_Beta'] > 0 else 'Growth'} bias)")
        print(f"  Quality Tilt: {factor_exposures['Quality_Beta']:.3f} ({'High' if factor_exposures['Quality_Beta'] > 0 else 'Low'} quality)")
        
        return {
            'factor_exposures': factor_exposures,
            'factor_contributions': factor_contributions,
            'style_characteristics': style_characteristics,
            'regression_stats': {
                'observations': len(common_dates),
                'start_date': common_dates.min().strftime('%Y-%m-%d'),
                'end_date': common_dates.max().strftime('%Y-%m-%d')
            }
        }
        
    except Exception as e:
        print(f"⚠️  Factor attribution failed: {str(e)}")
        return {}

def classify_portfolio_style(factor_exposures: Dict) -> Dict:
    """Classify portfolio style based on factor exposures."""
    style = {}
    
    # Market exposure
    beta = factor_exposures.get('Market_Beta', 1.0)
    if beta > 1.2:
        style['market_exposure'] = 'High Beta (Aggressive)'
    elif beta < 0.8:
        style['market_exposure'] = 'Low Beta (Defensive)'
    else:
        style['market_exposure'] = 'Market Beta (Neutral)'
    
    # Size bias
    size_beta = factor_exposures.get('Size_Beta', 0)
    if size_beta > 0.3:
        style['size_bias'] = 'Strong Small-Cap Bias'
    elif size_beta > 0.1:
        style['size_bias'] = 'Moderate Small-Cap Bias'
    elif size_beta < -0.1:
        style['size_bias'] = 'Large-Cap Bias'
    else:
        style['size_bias'] = 'Size Neutral'
    
    # Value vs Growth
    value_beta = factor_exposures.get('Value_Beta', 0)
    if value_beta > 0.2:
        style['value_growth'] = 'Strong Value Bias'
    elif value_beta > 0.05:
        style['value_growth'] = 'Moderate Value Bias'
    elif value_beta < -0.05:
        style['value_growth'] = 'Growth Bias'
    else:
        style['value_growth'] = 'Value-Growth Neutral'
    
    # Quality bias
    quality_beta = factor_exposures.get('Quality_Beta', 0)
    if quality_beta > 0.2:
        style['quality_bias'] = 'High Quality Focus'
    elif quality_beta < -0.1:
        style['quality_bias'] = 'Low Quality/Junk'
    else:
        style['quality_bias'] = 'Quality Neutral'
    
    # Investment/Profitability
    investment_beta = factor_exposures.get('Investment_Beta', 0)
    if investment_beta > 0.1:
        style['investment_style'] = 'Conservative Investment'
    elif investment_beta < -0.1:
        style['investment_style'] = 'Aggressive Investment'
    else:
        style['investment_style'] = 'Investment Neutral'
    
    # Momentum
    if 'Momentum_Beta' in factor_exposures:
        mom_beta = factor_exposures['Momentum_Beta']
        if mom_beta > 0.1:
            style['momentum_bias'] = 'Momentum Following'
        elif mom_beta < -0.1:
            style['momentum_bias'] = 'Contrarian'
        else:
            style['momentum_bias'] = 'Momentum Neutral'
    
    return style

def generate_risk_report(portfolio_df: pd.DataFrame, risk_metrics: Dict) -> None:
    """Generate comprehensive risk report."""
    print("\n" + "="*80)
    print("COMPREHENSIVE RISK ANALYSIS REPORT")
    print("="*80)
    
    print(f"\nPortfolio Overview:")
    print(f"Total Holdings: {len(portfolio_df)}")
    print(f"Sectors: {portfolio_df['Sector'].nunique()}")
    print(f"Styles: {portfolio_df['Style'].nunique()}")
    
    # Portfolio-level risks
    if 'portfolio_risk' in risk_metrics:
        pr = risk_metrics['portfolio_risk']
        print(f"\nPortfolio Risk Metrics:")
        print(f"  Annual Volatility: {pr['portfolio_volatility']:.2%}")
        print(f"  Expected Return: {pr['portfolio_return']:.2%}")
        print(f"  Sharpe Ratio: {pr['sharpe_ratio']:.2f}")
        print(f"  Maximum Drawdown: {pr['max_drawdown']:.2%}")
        print(f"  Data Coverage: {pr['available_data_coverage']:.1%}")
    
    # Correlation risks
    if 'correlations' in risk_metrics:
        corr = risk_metrics['correlations']
        print(f"\nCorrelation Analysis:")
        print(f"  Average Correlation: {corr['avg_correlation']:.3f}")
        print(f"  Max Correlation: {corr['max_correlation']:.3f}")
        print(f"  High Correlations (>0.8): {len(corr['high_correlations'])}")
        
        if corr['high_correlations']:
            print(f"  Warning: Highly correlated pairs found:")
            for pair in corr['high_correlations'][:5]:  # Show top 5
                print(f"    {pair['ticker1']} - {pair['ticker2']}: {pair['correlation']:.3f}")
    
    # Volatility risks
    if 'volatility' in risk_metrics:
        vol = risk_metrics['volatility']
        print(f"\nVolatility Analysis:")
        print(f"  Average Stock Volatility: {vol['avg_volatility']:.2%}")
        print(f"  Max Stock Volatility: {vol['max_volatility']:.2%}")
        print(f"  High Volatility Stocks: {len(vol['high_vol_stocks'])}")
        
        if vol['high_vol_stocks']:
            print(f"  Warning: High volatility stocks:")
            for ticker, volatility in list(vol['high_vol_stocks'].items())[:5]:
                print(f"    {ticker}: {volatility:.2%}")
    
    # Concentration risks
    if 'concentration' in risk_metrics:
        conc = risk_metrics['concentration']
        print(f"\nConcentration Analysis:")
        
        # Sector concentration
        sc = conc['sector_concentration']
        print(f"  Max Sector Weight: {sc['max_sector_weight']:.1%}")
        print(f"  Sector HHI: {sc['sector_hhi']:.3f} ({'Concentrated' if sc['sector_hhi'] > 0.25 else 'Diversified'})")
        
        # Style concentration
        st = conc['style_concentration']
        print(f"  Max Style Weight: {st['max_style_weight']:.1%}")
        print(f"  Style HHI: {st['style_hhi']:.3f}")
        
        # Position concentration
        pc = conc['position_concentration']
        print(f"  Max Position Weight: {pc['max_position_weight']:.1%}")
        print(f"  Top 10 Holdings Weight: {pc['top_10_weight']:.1%}")
    
    # Fama-French Factor Attribution
    if 'factor_attribution' in risk_metrics and risk_metrics['factor_attribution']:
        fa = risk_metrics['factor_attribution']
        print(f"\nFama-French Factor Attribution:")
        
        if 'factor_exposures' in fa:
            fe = fa['factor_exposures']
            print(f"  Model R²: {fe.get('R_Squared', 0):.3f} ({fe.get('R_Squared', 0)*100:.1f}% explained)")
            print(f"  Portfolio Alpha: {fe.get('Alpha', 0)*252:.2%} (annualized)")
            print(f"  Market Beta: {fe.get('Market_Beta', 0):.3f}")
            print(f"  Size Factor (SMB): {fe.get('Size_Beta', 0):+.3f}")
            print(f"  Value Factor (HML): {fe.get('Value_Beta', 0):+.3f}")
            print(f"  Quality Factor (RMW): {fe.get('Quality_Beta', 0):+.3f}")
            print(f"  Investment Factor (CMA): {fe.get('Investment_Beta', 0):+.3f}")
            
            if 'Momentum_Beta' in fe:
                print(f"  Momentum Factor: {fe.get('Momentum_Beta', 0):+.3f}")
                print(f"  R² with Momentum: {fe.get('R_Squared_with_Mom', 0):.3f}")
        
        if 'style_characteristics' in fa:
            sc = fa['style_characteristics']
            print(f"\nPortfolio Style Characteristics:")
            for category, style in sc.items():
                print(f"  {category.replace('_', ' ').title()}: {style}")
        
        if 'factor_contributions' in fa:
            fc = fa['factor_contributions']
            print(f"\nFactor Return Contributions (annualized):")
            for factor, contrib in fc.items():
                print(f"  {factor.replace('_', ' ')}: {contrib*252:+.2%}")
        
        if 'regression_stats' in fa:
            rs = fa['regression_stats']
            print(f"\nRegression Statistics:")
            print(f"  Observations: {rs.get('observations', 0)}")
            print(f"  Period: {rs.get('start_date', 'N/A')} to {rs.get('end_date', 'N/A')}")
    
    # Risk warnings
    print(f"\nRisk Warnings:")
    warnings = []
    
    if 'correlations' in risk_metrics and len(risk_metrics['correlations']['high_correlations']) > 5:
        warnings.append(f"High correlation risk: {len(risk_metrics['correlations']['high_correlations'])} pairs >0.8 correlation")
    
    if 'concentration' in risk_metrics:
        if risk_metrics['concentration']['sector_concentration']['max_sector_weight'] > 0.3:
            warnings.append(f"Sector concentration risk: {risk_metrics['concentration']['sector_concentration']['max_sector_weight']:.1%} in single sector")
        
        if risk_metrics['concentration']['position_concentration']['top_10_weight'] > 0.5:
            warnings.append(f"Position concentration risk: Top 10 holdings = {risk_metrics['concentration']['position_concentration']['top_10_weight']:.1%}")
    
    if 'volatility' in risk_metrics and len(risk_metrics['volatility']['high_vol_stocks']) > 10:
        warnings.append(f"Volatility risk: {len(risk_metrics['volatility']['high_vol_stocks'])} high volatility stocks")
    
    if warnings:
        for warning in warnings:
            print(f"  ⚠️  {warning}")
    else:
        print(f"  ✅ No major risk warnings detected")

def main():
    try:
        # Read the latest portfolio
        portfolio_path = get_latest_portfolio_file()
        print(f"Reading portfolio from: {portfolio_path}")
        
        portfolio_df = pd.read_csv(portfolio_path)
        tickers = portfolio_df['Ticker'].tolist()
        
        print(f"Analyzing risks for {len(tickers)} holdings...")
        
        # Get historical price data
        price_data = get_historical_prices(tickers, days=252)  # 1 year of data
        
        # Calculate returns
        returns_df = calculate_returns(price_data)
        
        risk_metrics = {}
        
        # Analyze correlations
        if len(returns_df.columns) > 1:
            risk_metrics['correlations'] = analyze_correlations(returns_df)
        
        # Analyze volatility
        if len(returns_df.columns) > 0:
            risk_metrics['volatility'] = analyze_volatility(returns_df)
        
        # Portfolio-level risk
        if len(returns_df.columns) > 5:  # Need reasonable number of stocks
            risk_metrics['portfolio_risk'] = analyze_portfolio_risk(portfolio_df, returns_df)
        
        # Concentration analysis (doesn't need price data)
        risk_metrics['concentration'] = analyze_concentration_risk(portfolio_df)
        
        # Analyze portfolio factor attribution
        risk_metrics['factor_attribution'] = analyze_portfolio_factor_attribution(portfolio_df, returns_df)
        
        # Generate risk report
        generate_risk_report(portfolio_df, risk_metrics)
        
        # Save risk metrics
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files', 'risk_analysis')
        today = date.today().strftime('%Y-%m-%d')
        
        # Save correlation matrix if available
        if 'correlations' in risk_metrics:
            corr_path = os.path.join(output_dir, f"portfolio_correlations_{today}.csv")
            risk_metrics['correlations']['correlation_matrix'].to_csv(corr_path)
            print(f"\nCorrelation matrix saved to: {corr_path}")
        
        # Save risk summary
        risk_summary = {
            'ticker': tickers,
            'volatility': [risk_metrics['volatility']['volatilities'].get(t, np.nan) for t in tickers] if 'volatility' in risk_metrics else [np.nan] * len(tickers)
        }
        
        risk_summary_df = pd.DataFrame(risk_summary)
        risk_summary_path = os.path.join(output_dir, f"portfolio_risk_metrics_{today}.csv")
        risk_summary_df.to_csv(risk_summary_path, index=False)
        print(f"Risk summary saved to: {risk_summary_path}")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main() 