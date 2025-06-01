import pandas as pd
import numpy as np
import os
import glob
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
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError("No selected portfolio CSV file found.")
    return max(files, key=os.path.getctime)  # Get the most recent file

def get_latest_macro_analysis() -> pd.DataFrame:
    """Get the latest enhanced macro economic analysis CSV file."""
    print("📊 Loading enhanced macro economic analysis...")
    
    # Look for the new enhanced macro analysis files
    pattern = os.path.join(os.path.dirname(__file__), '06_enhanced_macro_analysis_*.csv')
    enhanced_files = glob.glob(pattern)
    
    if enhanced_files:
        # Use the newest enhanced macro file
        latest_file = max(enhanced_files, key=os.path.getctime)
        print(f"✅ Using enhanced macro analysis: {os.path.basename(latest_file)}")
        return pd.read_csv(latest_file)
    
    # Fallback to old macro analysis if enhanced not available
    pattern = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files', 'macro_analysis_*.csv')
    old_files = glob.glob(pattern)
    
    if old_files:
        latest_file = max(old_files, key=os.path.getctime)
        print(f"⚠️ Using fallback macro analysis: {os.path.basename(latest_file)}")
        return pd.read_csv(latest_file)
    
    print("❌ No macro analysis files found - creating minimal fallback")
    # Return minimal fallback data
    return pd.DataFrame([{
        'Date': datetime.now().strftime('%Y-%m-%d'),
        'Recession_Probability': 20.0,
        'Risk_Adjustment_Factor': 1.0,
        'Fed_Policy_Bias': 'NEUTRAL',
        'VIX': 20.0,
        'Data_Source': 'FALLBACK'
    }])

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

def analyze_macro_risk(macro_df: pd.DataFrame, portfolio_df: pd.DataFrame) -> Dict:
    """Analyze macro economic risks and their portfolio impact."""
    print("🌍 Analyzing macro economic risks...")
    
    if macro_df.empty:
        return {'error': 'No macro data available'}
    
    # Get the latest macro data
    latest_macro = macro_df.iloc[-1]
    
    # Extract key macro risk factors
    recession_prob = latest_macro.get('Recession_Probability', 20.0)
    risk_adj_factor = latest_macro.get('Risk_Adjustment_Factor', 1.0)
    fed_policy_bias = latest_macro.get('Fed_Policy_Bias', 'NEUTRAL')
    vix_level = latest_macro.get('VIX', 20.0)
    data_source = latest_macro.get('Data_Source', 'Unknown')
    
    # NY Fed model specific data (if available)
    fed_rate_direction = latest_macro.get('Fed_Rate_Direction', 'HOLD')
    yield_curve_bps = latest_macro.get('Yield_Curve_2s10s_bps', 50.0)
    
    # Classify macro risk level
    if recession_prob >= 50:
        macro_risk_level = "Very High"
        risk_impact = "Significant defensive positioning required"
    elif recession_prob >= 30:
        macro_risk_level = "High" 
        risk_impact = "Defensive tilt recommended"
    elif recession_prob >= 20:
        macro_risk_level = "Moderate"
        risk_impact = "Monitor closely, slight defensive bias"
    else:
        macro_risk_level = "Low"
        risk_impact = "Normal risk posture appropriate"
    
    # Assess sector-specific macro risks
    sector_macro_risks = analyze_sector_macro_exposure(portfolio_df, latest_macro)
    
    # Fed policy impact on portfolio
    fed_policy_impact = analyze_fed_policy_impact(portfolio_df, latest_macro)
    
    return {
        'macro_risk_level': macro_risk_level,
        'recession_probability': recession_prob,
        'risk_adjustment_factor': risk_adj_factor,
        'risk_impact': risk_impact,
        'fed_policy_bias': fed_policy_bias,
        'fed_rate_direction': fed_rate_direction,
        'yield_curve_bps': yield_curve_bps,
        'vix_level': vix_level,
        'data_source': data_source,
        'sector_macro_risks': sector_macro_risks,
        'fed_policy_impact': fed_policy_impact,
        'macro_adjusted_risk_multiplier': risk_adj_factor,
        'analysis_date': latest_macro.get('Date', datetime.now().strftime('%Y-%m-%d'))
    }

def analyze_sector_macro_exposure(portfolio_df: pd.DataFrame, macro_data: pd.Series) -> Dict:
    """Analyze how different portfolio sectors are exposed to macro risks."""
    
    recession_prob = macro_data.get('Recession_Probability', 20.0)
    fed_bias = macro_data.get('Fed_Policy_Bias', 'NEUTRAL')
    
    # Sector sensitivity to macro conditions
    sector_sensitivities = {
        'Technology': {
            'recession_sensitivity': 'High',
            'fed_policy_sensitivity': 'High',
            'risk_in_recession': 'Very High',
            'risk_with_hawkish_fed': 'High'
        },
        'Financial Services': {
            'recession_sensitivity': 'Very High', 
            'fed_policy_sensitivity': 'Very High',
            'risk_in_recession': 'Very High',
            'risk_with_hawkish_fed': 'Low'  # Benefits from higher rates
        },
        'Healthcare': {
            'recession_sensitivity': 'Low',
            'fed_policy_sensitivity': 'Low',
            'risk_in_recession': 'Low',
            'risk_with_hawkish_fed': 'Low'
        },
        'Consumer Defensive': {
            'recession_sensitivity': 'Low',
            'fed_policy_sensitivity': 'Low',
            'risk_in_recession': 'Low',
            'risk_with_hawkish_fed': 'Low'
        },
        'Consumer Cyclical': {
            'recession_sensitivity': 'Very High',
            'fed_policy_sensitivity': 'High',
            'risk_in_recession': 'Very High',
            'risk_with_hawkish_fed': 'High'
        },
        'Industrials': {
            'recession_sensitivity': 'High',
            'fed_policy_sensitivity': 'Moderate',
            'risk_in_recession': 'High',
            'risk_with_hawkish_fed': 'Moderate'
        },
        'Energy': {
            'recession_sensitivity': 'High',
            'fed_policy_sensitivity': 'Moderate',
            'risk_in_recession': 'High',
            'risk_with_hawkish_fed': 'Moderate'
        },
        'Real Estate': {
            'recession_sensitivity': 'Very High',
            'fed_policy_sensitivity': 'Very High',
            'risk_in_recession': 'Very High',
            'risk_with_hawkish_fed': 'Very High'
        },
        'Utilities': {
            'recession_sensitivity': 'Low',
            'fed_policy_sensitivity': 'Moderate',
            'risk_in_recession': 'Low',
            'risk_with_hawkish_fed': 'Moderate'
        },
        'Basic Materials': {
            'recession_sensitivity': 'Very High',
            'fed_policy_sensitivity': 'Moderate',
            'risk_in_recession': 'Very High',
            'risk_with_hawkish_fed': 'Moderate'
        },
        'Communication Services': {
            'recession_sensitivity': 'High',
            'fed_policy_sensitivity': 'High',
            'risk_in_recession': 'High',
            'risk_with_hawkish_fed': 'High'
        }
    }
    
    # Calculate sector risk scores
    sector_risks = {}
    portfolio_sectors = portfolio_df['Sector'].value_counts()
    
    for sector, count in portfolio_sectors.items():
        weight = count / len(portfolio_df)
        sensitivity = sector_sensitivities.get(sector, {
            'recession_sensitivity': 'Moderate',
            'fed_policy_sensitivity': 'Moderate',
            'risk_in_recession': 'Moderate',
            'risk_with_hawkish_fed': 'Moderate'
        })
        
        # Calculate risk score based on current macro conditions
        risk_score = 1.0  # Base risk
        
        # Adjust for recession risk
        if recession_prob >= 40:
            if sensitivity['risk_in_recession'] == 'Very High':
                risk_score *= 1.4
            elif sensitivity['risk_in_recession'] == 'High':
                risk_score *= 1.2
            elif sensitivity['risk_in_recession'] == 'Low':
                risk_score *= 0.9
        
        # Adjust for Fed policy
        if 'HAWKISH' in fed_bias:
            if sensitivity['risk_with_hawkish_fed'] == 'Very High':
                risk_score *= 1.3
            elif sensitivity['risk_with_hawkish_fed'] == 'High':
                risk_score *= 1.15
            elif sensitivity['risk_with_hawkish_fed'] == 'Low':
                risk_score *= 0.85
        
        sector_risks[sector] = {
            'portfolio_weight': weight,
            'stock_count': count,
            'macro_risk_score': risk_score,
            'sensitivity_profile': sensitivity,
            'risk_level': 'High' if risk_score > 1.2 else 'Moderate' if risk_score > 0.9 else 'Low'
        }
    
    return sector_risks

def analyze_fed_policy_impact(portfolio_df: pd.DataFrame, macro_data: pd.Series) -> Dict:
    """Analyze Federal Reserve policy impact on portfolio sectors."""
    
    fed_bias = macro_data.get('Fed_Policy_Bias', 'NEUTRAL')
    fed_direction = macro_data.get('Fed_Rate_Direction', 'HOLD')
    yield_curve_bps = macro_data.get('Yield_Curve_2s10s_bps', 50.0)
    
    # Fed policy impact on different sectors
    fed_impacts = {
        'rate_sensitive_sectors': {
            'positive_from_hikes': ['Financial Services'],  # Banks benefit from higher rates
            'negative_from_hikes': ['Real Estate', 'Utilities', 'Technology']  # High duration/growth sensitive
        },
        'yield_curve_sensitive': {
            'benefit_from_steepening': ['Financial Services'],  # Banks need spread
            'hurt_by_inversion': ['Financial Services', 'Real Estate']
        }
    }
    
    # Calculate Fed policy risk/opportunity for portfolio
    portfolio_sectors = portfolio_df['Sector'].value_counts()
    fed_policy_analysis = {}
    
    for sector, count in portfolio_sectors.items():
        weight = count / len(portfolio_df)
        
        impact_score = 0  # Neutral impact
        impact_factors = []
        
        # Rate direction impact
        if fed_direction == 'UP' or 'HAWKISH' in fed_bias:
            if sector in fed_impacts['rate_sensitive_sectors']['positive_from_hikes']:
                impact_score += 0.2
                impact_factors.append("Benefits from rising rates")
            elif sector in fed_impacts['rate_sensitive_sectors']['negative_from_hikes']:
                impact_score -= 0.3
                impact_factors.append("Pressure from rising rates")
        elif fed_direction == 'DOWN' or 'DOVISH' in fed_bias:
            if sector in fed_impacts['rate_sensitive_sectors']['negative_from_hikes']:
                impact_score += 0.2
                impact_factors.append("Benefits from falling rates")
            elif sector in fed_impacts['rate_sensitive_sectors']['positive_from_hikes']:
                impact_score -= 0.15
                impact_factors.append("Reduced spread income from falling rates")
        
        # Yield curve impact
        if yield_curve_bps < 0:  # Inverted curve
            if sector in fed_impacts['yield_curve_sensitive']['hurt_by_inversion']:
                impact_score -= 0.2
                impact_factors.append("Pressured by inverted yield curve")
        elif yield_curve_bps > 100:  # Steep curve
            if sector in fed_impacts['yield_curve_sensitive']['benefit_from_steepening']:
                impact_score += 0.15
                impact_factors.append("Benefits from steep yield curve")
        
        fed_policy_analysis[sector] = {
            'portfolio_weight': weight,
            'fed_impact_score': impact_score,
            'impact_factors': impact_factors,
            'overall_impact': 'Positive' if impact_score > 0.1 else 'Negative' if impact_score < -0.1 else 'Neutral'
        }
    
    return {
        'fed_policy_bias': fed_bias,
        'fed_rate_direction': fed_direction,
        'yield_curve_bps': yield_curve_bps,
        'sector_impacts': fed_policy_analysis,
        'overall_portfolio_fed_impact': sum(analysis['fed_impact_score'] * analysis['portfolio_weight'] 
                                          for analysis in fed_policy_analysis.values())
    }

def generate_risk_report(portfolio_df: pd.DataFrame, risk_metrics: Dict) -> None:
    """Generate comprehensive risk report including macro economic risks."""
    print("\n" + "="*80)
    print("COMPREHENSIVE RISK ANALYSIS REPORT")
    print("="*80)
    
    print(f"\nPortfolio Overview:")
    print(f"Total Holdings: {len(portfolio_df)}")
    print(f"Sectors: {portfolio_df['Sector'].nunique()}")
    print(f"Styles: {portfolio_df['Style'].nunique()}")
    
    # =================================================================
    # MACRO ECONOMIC RISK ANALYSIS (NEW - HIGHEST PRIORITY)
    # =================================================================
    if 'macro_risk' in risk_metrics:
        macro = risk_metrics['macro_risk']
        if 'error' not in macro:
            print(f"\n🌍 MACRO ECONOMIC RISK ANALYSIS:")
            print(f"Analysis Date: {macro.get('analysis_date', 'N/A')}")
            print(f"Data Source: {macro.get('data_source', 'N/A')}")
            print(f"Macro Risk Level: {macro.get('macro_risk_level', 'N/A')}")
            print(f"Recession Probability: {macro.get('recession_probability', 0):.1f}%")
            print(f"Risk Adjustment Factor: {macro.get('risk_adjustment_factor', 1.0):.2f}x")
            print(f"Risk Impact: {macro.get('risk_impact', 'N/A')}")
            
            print(f"\n📊 Fed Policy Assessment:")
            print(f"Policy Bias: {macro.get('fed_policy_bias', 'N/A')}")
            print(f"Rate Direction: {macro.get('fed_rate_direction', 'N/A')}")
            print(f"Yield Curve: {macro.get('yield_curve_bps', 0):+.0f} bps")
            print(f"VIX Level: {macro.get('vix_level', 0):.1f}")
            
            # Sector-specific macro risks
            if 'sector_macro_risks' in macro:
                print(f"\n📈 Sector Macro Risk Assessment:")
                for sector, risk_data in macro['sector_macro_risks'].items():
                    risk_score = risk_data.get('macro_risk_score', 1.0)
                    risk_level = risk_data.get('risk_level', 'Moderate')
                    weight = risk_data.get('portfolio_weight', 0)
                    
                    emoji = "🚨" if risk_level == "High" else "⚠️" if risk_level == "Moderate" else "✅"
                    print(f"    {emoji} {sector}: {risk_level} Risk (Score: {risk_score:.2f}, Weight: {weight:.1%})")
            
            # Fed policy impact
            if 'fed_policy_impact' in macro:
                fed_impact = macro['fed_policy_impact']
                overall_impact = fed_impact.get('overall_portfolio_fed_impact', 0)
                
                print(f"\n🏛️ Fed Policy Portfolio Impact:")
                print(f"Overall Portfolio Impact: {overall_impact:+.2f} (Fed {fed_impact.get('fed_rate_direction', 'N/A')})")
                
                print(f"Sector-Specific Fed Impacts:")
                for sector, impact_data in fed_impact.get('sector_impacts', {}).items():
                    impact = impact_data.get('overall_impact', 'Neutral')
                    factors = impact_data.get('impact_factors', [])
                    
                    emoji = "🟢" if impact == "Positive" else "🔴" if impact == "Negative" else "🟡"
                    print(f"    {emoji} {sector}: {impact}")
                    for factor in factors[:2]:  # Show top 2 factors
                        print(f"        • {factor}")
    
    # Portfolio-level risks
    if 'portfolio_risk' in risk_metrics:
        pr = risk_metrics['portfolio_risk']
        print(f"\n📊 Portfolio Risk Metrics:")
        print(f"  Annual Volatility: {pr['portfolio_volatility']:.2%}")
        print(f"  Expected Return: {pr['portfolio_return']:.2%}")
        print(f"  Sharpe Ratio: {pr['sharpe_ratio']:.2f}")
        print(f"  Maximum Drawdown: {pr['max_drawdown']:.2%}")
        print(f"  Data Coverage: {pr['available_data_coverage']:.1%}")
        
        # Apply macro risk adjustment
        if 'macro_risk' in risk_metrics and 'error' not in risk_metrics['macro_risk']:
            macro_multiplier = risk_metrics['macro_risk'].get('macro_adjusted_risk_multiplier', 1.0)
            adjusted_vol = pr['portfolio_volatility'] * macro_multiplier
            print(f"  Macro-Adjusted Volatility: {adjusted_vol:.2%} ({macro_multiplier:.2f}x multiplier)")
    
    # Correlation risks
    if 'correlations' in risk_metrics:
        corr = risk_metrics['correlations']
        print(f"\n🔗 Correlation Analysis:")
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
        print(f"\n📈 Volatility Analysis:")
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
        print(f"\n🎯 Concentration Analysis:")
        
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
        print(f"\n📊 Fama-French Factor Attribution:")
        
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
    
    # =================================================================
    # COMPREHENSIVE RISK WARNINGS (UPDATED WITH MACRO)
    # =================================================================
    print(f"\n⚠️ Risk Warnings:")
    warnings = []
    
    # Macro risk warnings (highest priority)
    if 'macro_risk' in risk_metrics and 'error' not in risk_metrics['macro_risk']:
        macro = risk_metrics['macro_risk']
        recession_prob = macro.get('recession_probability', 0)
        
        if recession_prob >= 50:
            warnings.append(f"🚨 CRITICAL MACRO RISK: {recession_prob:.1f}% recession probability - implement defensive strategies immediately")
        elif recession_prob >= 30:
            warnings.append(f"⚠️ HIGH MACRO RISK: {recession_prob:.1f}% recession probability - consider defensive positioning")
        elif recession_prob >= 20:
            warnings.append(f"⚠️ Elevated macro risk: {recession_prob:.1f}% recession probability - monitor closely")
        
        # Fed policy warnings
        fed_bias = macro.get('fed_policy_bias', 'NEUTRAL')
        if 'STRONGLY' in fed_bias:
            warnings.append(f"⚠️ Strong Fed policy shift: {fed_bias} - expect significant rate changes")
        
        # Yield curve warnings
        yield_curve = macro.get('yield_curve_bps', 0)
        if yield_curve < -50:
            warnings.append(f"🚨 DEEPLY INVERTED YIELD CURVE: {yield_curve:.0f} bps - recession risk very high")
        elif yield_curve < 0:
            warnings.append(f"⚠️ Inverted yield curve: {yield_curve:.0f} bps - recession indicator triggered")
        
        # VIX warnings
        vix = macro.get('vix_level', 0)
        if vix > 35:
            warnings.append(f"🚨 CRISIS VOLATILITY: VIX {vix:.1f} - market panic conditions")
        elif vix > 30:
            warnings.append(f"⚠️ High market volatility: VIX {vix:.1f} - heightened uncertainty")
    
    # Traditional risk warnings
    if 'correlations' in risk_metrics and len(risk_metrics['correlations']['high_correlations']) > 5:
        warnings.append(f"⚠️ High correlation risk: {len(risk_metrics['correlations']['high_correlations'])} pairs >0.8 correlation")
    
    if 'concentration' in risk_metrics:
        if risk_metrics['concentration']['sector_concentration']['max_sector_weight'] > 0.3:
            warnings.append(f"⚠️ Sector concentration risk: {risk_metrics['concentration']['sector_concentration']['max_sector_weight']:.1%} in single sector")
        
        if risk_metrics['concentration']['position_concentration']['top_10_weight'] > 0.5:
            warnings.append(f"⚠️ Position concentration risk: Top 10 holdings = {risk_metrics['concentration']['position_concentration']['top_10_weight']:.1%}")
    
    if 'volatility' in risk_metrics and len(risk_metrics['volatility']['high_vol_stocks']) > 10:
        warnings.append(f"⚠️ Volatility risk: {len(risk_metrics['volatility']['high_vol_stocks'])} high volatility stocks")
    
    if warnings:
        for warning in warnings:
            print(f"  {warning}")
    else:
        print(f"  ✅ No major risk warnings detected")
    
    # =================================================================
    # RISK MANAGEMENT RECOMMENDATIONS (NEW)
    # =================================================================
    print(f"\n💡 Risk Management Recommendations:")
    
    if 'macro_risk' in risk_metrics and 'error' not in risk_metrics['macro_risk']:
        macro = risk_metrics['macro_risk']
        recession_prob = macro.get('recession_probability', 0)
        risk_impact = macro.get('risk_impact', '')
        
        print(f"  📊 Macro Strategy: {risk_impact}")
        
        if recession_prob >= 40:
            print(f"  🛡️ Defensive Actions:")
            print(f"    • Reduce overall portfolio risk by 20-40%")
            print(f"    • Overweight defensive sectors (Healthcare, Consumer Defensive, Utilities)")
            print(f"    • Increase quality allocation, reduce growth exposure")
            print(f"    • Consider increasing cash buffer")
        elif recession_prob >= 20:
            print(f"  ⚖️ Balanced Actions:")
            print(f"    • Maintain current risk level with slight defensive bias")
            print(f"    • Monitor recession indicators weekly")
            print(f"    • Prepare defensive positioning plan")
        else:
            print(f"  📈 Growth Actions:")
            print(f"    • Consider slightly increasing portfolio risk")
            print(f"    • Overweight cyclical sectors if appropriate")
            print(f"    • Normal growth/value balance")
    
    if 'correlations' in risk_metrics and len(risk_metrics['correlations']['high_correlations']) > 3:
        print(f"  🔗 Correlation Management: Reduce positions in highly correlated stocks")
    
    if 'concentration' in risk_metrics:
        conc = risk_metrics['concentration']
        if conc['sector_concentration']['max_sector_weight'] > 0.25:
            print(f"  🎯 Diversification: Reduce sector concentration below 25%")


def main():
    try:
        # Read the latest portfolio
        portfolio_path = get_latest_portfolio_file()
        print(f"Reading portfolio from: {portfolio_path}")
        
        portfolio_df = pd.read_csv(portfolio_path)
        tickers = portfolio_df['Ticker'].tolist()
        
        print(f"Analyzing risks for {len(tickers)} holdings...")
        
        # =================================================================
        # ENHANCED: Load macro economic analysis (NEW)
        # =================================================================
        macro_df = get_latest_macro_analysis()
        
        # Get historical price data
        price_data = get_historical_prices(tickers, days=252)  # 1 year of data
        
        # Calculate returns
        returns_df = calculate_returns(price_data)
        
        risk_metrics = {}
        
        # =================================================================
        # ENHANCED: Analyze macro economic risks (NEW - HIGHEST PRIORITY)
        # =================================================================
        risk_metrics['macro_risk'] = analyze_macro_risk(macro_df, portfolio_df)
        
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
        
        # Generate enhanced risk report with macro analysis
        generate_risk_report(portfolio_df, risk_metrics)
        
        # =================================================================
        # ENHANCED: Save enhanced risk metrics with macro data
        # =================================================================
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files', 'risk_analysis')
        today = date.today().strftime('%Y-%m-%d')
        
        # Save correlation matrix if available
        if 'correlations' in risk_metrics:
            corr_path = os.path.join(output_dir, f"portfolio_correlations_{today}.csv")
            risk_metrics['correlations']['correlation_matrix'].to_csv(corr_path)
            print(f"\n💾 Correlation matrix saved to: {corr_path}")
        
        # Save enhanced risk summary with macro data
        risk_summary = {
            'ticker': tickers,
            'volatility': [risk_metrics['volatility']['volatilities'].get(t, np.nan) for t in tickers] if 'volatility' in risk_metrics else [np.nan] * len(tickers)
        }
        
        # Add macro risk data to summary
        if 'macro_risk' in risk_metrics and 'error' not in risk_metrics['macro_risk']:
            macro = risk_metrics['macro_risk']
            
            # Add portfolio-level macro data
            for ticker in tickers:
                risk_summary.setdefault('recession_probability', []).append(macro.get('recession_probability', np.nan))
                risk_summary.setdefault('macro_risk_level', []).append(macro.get('macro_risk_level', 'Unknown'))
                risk_summary.setdefault('risk_adjustment_factor', []).append(macro.get('risk_adjustment_factor', np.nan))
                risk_summary.setdefault('fed_policy_bias', []).append(macro.get('fed_policy_bias', 'Unknown'))
        
        risk_summary_df = pd.DataFrame(risk_summary)
        risk_summary_path = os.path.join(output_dir, f"portfolio_risk_metrics_{today}.csv")
        risk_summary_df.to_csv(risk_summary_path, index=False)
        print(f"💾 Enhanced risk summary saved to: {risk_summary_path}")
        
        # Save macro risk analysis separately for detailed review
        if 'macro_risk' in risk_metrics and 'error' not in risk_metrics['macro_risk']:
            import json
            macro_risk_path = os.path.join(output_dir, f"macro_risk_analysis_{today}.json")
            with open(macro_risk_path, 'w') as f:
                json.dump(risk_metrics['macro_risk'], f, indent=2, default=str)
            print(f"💾 Macro risk analysis saved to: {macro_risk_path}")
        
        print(f"\n✅ Enhanced risk analysis complete with macro economic integration!")
        
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main() 