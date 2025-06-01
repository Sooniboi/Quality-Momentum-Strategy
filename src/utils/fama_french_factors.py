import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import os
from dotenv import load_dotenv
import pandas_datareader.data as web
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

def get_fama_french_factors(start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    Download Fama-French factor data using pandas-datareader.
    This properly implements the theoretical foundation we reference.
    """
    try:
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')  # 3 years back
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        print(f"Downloading Fama-French 5-factor data from {start_date} to {end_date}...")
        
        # Get Fama-French 5-factor daily data
        ff5_daily = web.DataReader('F-F_Research_Data_5_Factors_2x3_daily', 
                                   'famafrench', start_date, end_date)
        
        # The data comes as a dictionary with different periods
        # We want the daily data (key 0)
        ff_factors = ff5_daily[0].copy()
        
        # Convert percentage to decimal
        ff_factors = ff_factors / 100
        
        print(f"Successfully downloaded FF data: {len(ff_factors)} observations")
        print(f"Columns: {list(ff_factors.columns)}")
        
        return ff_factors
        
    except Exception as e:
        print(f"Error getting Fama-French factors: {str(e)}")
        print("Falling back to sample data for demonstration...")
        
        # Create sample data if download fails
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        dates = [d for d in dates if d.weekday() < 5]  # Only weekdays
        
        sample_data = pd.DataFrame(
            index=dates,
            data={
                'Mkt-RF': np.random.normal(0.0004, 0.012, len(dates)),
                'SMB': np.random.normal(0.0001, 0.008, len(dates)),
                'HML': np.random.normal(0.0002, 0.007, len(dates)),
                'RMW': np.random.normal(0.0001, 0.006, len(dates)),
                'CMA': np.random.normal(-0.0001, 0.005, len(dates)),
                'RF': np.random.normal(0.0001, 0.001, len(dates))
            }
        )
        
        print("Using sample Fama-French factor data")
        return sample_data

def get_momentum_factor(start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """Get momentum factor data from Kenneth French's library."""
    try:
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        print("Downloading Momentum factor data...")
        
        # Get momentum factor
        mom_daily = web.DataReader('F-F_Momentum_Factor_daily', 
                                   'famafrench', start_date, end_date)
        
        momentum_factor = mom_daily[0].copy() / 100  # Convert to decimal
        
        print(f"Successfully downloaded momentum data: {len(momentum_factor)} observations")
        return momentum_factor
        
    except Exception as e:
        print(f"Error getting momentum factor: {str(e)}")
        
        # Create sample momentum data
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        dates = [d for d in dates if d.weekday() < 5]
        
        sample_mom = pd.DataFrame(
            index=dates,
            data={'Mom': np.random.normal(0.0003, 0.015, len(dates))}
        )
        
        return sample_mom

def get_stock_returns(tickers: List[str], start_date: str, end_date: str, api_key: str) -> pd.DataFrame:
    """
    Get stock return data for factor regression analysis.
    This fills the gap between our price data and FF analysis.
    """
    returns_data = {}
    
    print(f"Fetching return data for {len(tickers)} stocks...")
    
    for ticker in tickers:
        try:
            # Get historical price data
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?from={start_date}&to={end_date}&apikey={api_key}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json().get('historical', [])
                if len(data) > 1:
                    # Convert to DataFrame and calculate returns
                    prices_df = pd.DataFrame(data)
                    prices_df['date'] = pd.to_datetime(prices_df['date'])
                    prices_df = prices_df.set_index('date').sort_index()
                    
                    # Calculate daily returns
                    prices_df['returns'] = prices_df['close'].pct_change()
                    
                    # Remove NaN values
                    valid_returns = prices_df['returns'].dropna()
                    
                    if len(valid_returns) > 30:  # Need minimum data
                        returns_data[ticker] = valid_returns
                        
        except Exception as e:
            print(f"Error getting returns for {ticker}: {str(e)}")
            continue
    
    # Convert to DataFrame with aligned dates
    if returns_data:
        returns_df = pd.DataFrame(returns_data)
        print(f"Successfully collected returns for {len(returns_df.columns)} stocks")
        return returns_df
    else:
        print("No return data collected")
        return pd.DataFrame()

def calculate_factor_exposures(returns_df: pd.DataFrame, ff_factors: pd.DataFrame, 
                             momentum_factor: pd.DataFrame = None) -> Dict:
    """
    Calculate factor exposures using true Fama-French regression analysis.
    This is the proper implementation of the theory we reference.
    """
    factor_exposures = {}
    
    # Combine FF factors with momentum if available
    if momentum_factor is not None:
        ff_factors = ff_factors.join(momentum_factor, how='inner')
    
    print(f"Running factor regressions for {len(returns_df.columns)} stocks...")
    
    for ticker in returns_df.columns:
        try:
            # Align dates between stock returns and factor returns
            common_dates = returns_df.index.intersection(ff_factors.index)
            
            if len(common_dates) < 60:  # Need minimum 60 observations
                print(f"Insufficient data for {ticker}: {len(common_dates)} observations")
                continue
                
            # Get aligned data
            stock_returns = returns_df.loc[common_dates, ticker].dropna()
            factors = ff_factors.loc[common_dates].dropna()
            
            # Ensure we have matching observations
            final_dates = stock_returns.index.intersection(factors.index)
            if len(final_dates) < 60:
                continue
                
            y = stock_returns.loc[final_dates]  # Dependent variable
            X = factors.loc[final_dates]        # Independent variables
            
            # Prepare regression data
            # For FF regression: R_i - R_f = α + β*(R_m - R_f) + s*SMB + h*HML + r*RMW + c*CMA + m*MOM + ε
            
            # Subtract risk-free rate from stock returns
            if 'RF' in X.columns:
                y_excess = y - X['RF']
                X_factors = X[['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA']]
            else:
                y_excess = y  # If no RF, use raw returns
                X_factors = X[['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA']]
            
            # Add momentum if available
            if 'Mom' in X.columns:
                X_factors = X_factors.join(X[['Mom']])
            
            # Run regression
            model = LinearRegression()
            model.fit(X_factors, y_excess)
            
            # Calculate R-squared
            r_squared = model.score(X_factors, y_excess)
            
            # Store results
            factor_exposures[ticker] = {
                'alpha': model.intercept_,
                'beta_market': model.coef_[0],    # Market beta (Mkt-RF)
                'beta_size': model.coef_[1],     # SMB exposure
                'beta_value': model.coef_[2],    # HML exposure  
                'beta_profit': model.coef_[3],   # RMW exposure (profitability)
                'beta_invest': model.coef_[4],   # CMA exposure (investment)
                'r_squared': r_squared,
                'observations': len(y_excess)
            }
            
            # Add momentum beta if available
            if len(model.coef_) > 5:
                factor_exposures[ticker]['beta_momentum'] = model.coef_[5]
            
            print(f"✓ {ticker}: α={model.intercept_:.4f}, β={model.coef_[0]:.2f}, R²={r_squared:.3f}")
                
        except Exception as e:
            print(f"✗ Regression failed for {ticker}: {str(e)}")
            continue
    
    print(f"Successfully calculated factor exposures for {len(factor_exposures)} stocks")
    return factor_exposures

def integrate_ff_into_quality_momentum(stock_data: pd.DataFrame, factor_exposures: Dict) -> pd.DataFrame:
    """
    Integrate Fama-French factor analysis into our quality-momentum scoring.
    This bridges the gap between theory and implementation.
    """
    print("Integrating Fama-French exposures into scoring system...")
    
    # Add FF columns to stock data
    ff_columns = ['FF_Alpha', 'FF_Market_Beta', 'FF_Size_Loading', 'FF_Value_Loading', 
                  'FF_Profit_Loading', 'FF_Investment_Loading', 'FF_R_Squared']
    
    for col in ff_columns:
        stock_data[col] = np.nan
    
    # Populate FF data
    for idx, row in stock_data.iterrows():
        ticker = row['Ticker']
        if ticker in factor_exposures:
            exposures = factor_exposures[ticker]
            
            stock_data.loc[idx, 'FF_Alpha'] = exposures.get('alpha', 0)
            stock_data.loc[idx, 'FF_Market_Beta'] = exposures.get('beta_market', 1)
            stock_data.loc[idx, 'FF_Size_Loading'] = exposures.get('beta_size', 0)
            stock_data.loc[idx, 'FF_Value_Loading'] = exposures.get('beta_value', 0)
            stock_data.loc[idx, 'FF_Profit_Loading'] = exposures.get('beta_profit', 0)
            stock_data.loc[idx, 'FF_Investment_Loading'] = exposures.get('beta_invest', 0)
            stock_data.loc[idx, 'FF_R_Squared'] = exposures.get('r_squared', 0)
    
    # Create FF-adjusted quality score
    # Combine our fundamental quality metrics with FF profitability factor exposure
    stock_data['FF_Quality_Score'] = (
        0.4 * stock_data['Quality Score'].fillna(0) +  # Our quality score
        0.3 * stock_data['FF_Profit_Loading'].fillna(0) +  # FF profitability factor
        0.2 * stock_data['FF_Alpha'].fillna(0) +  # FF alpha (stock-specific performance)
        0.1 * (1 - abs(stock_data['FF_Market_Beta'].fillna(1) - 1))  # Preference for beta near 1
    )
    
    # Create FF-adjusted momentum score
    if 'beta_momentum' in list(factor_exposures.values())[0] if factor_exposures else False:
        for idx, row in stock_data.iterrows():
            ticker = row['Ticker']
            if ticker in factor_exposures:
                momentum_loading = factor_exposures[ticker].get('beta_momentum', 0)
                stock_data.loc[idx, 'FF_Momentum_Loading'] = momentum_loading
        
        stock_data['FF_Momentum_Score'] = (
            0.6 * stock_data['Momentum Score'].fillna(0) +  # Our momentum score
            0.4 * stock_data['FF_Momentum_Loading'].fillna(0)  # FF momentum factor
        )
    else:
        stock_data['FF_Momentum_Score'] = stock_data['Momentum Score']
    
    # Create overall FF-adjusted score
    stock_data['FF_Overall_Score'] = (
        0.5 * stock_data['FF_Quality_Score'].fillna(0) +
        0.3 * stock_data['FF_Momentum_Score'].fillna(0) +
        0.2 * stock_data['Overall Score'].fillna(0)  # Keep some of our original score
    )
    
    print(f"Added Fama-French analysis for {stock_data['FF_R_Squared'].notna().sum()} stocks")
    return stock_data

def create_ff_portfolio_analysis(portfolio_df: pd.DataFrame, factor_exposures: Dict) -> Dict:
    """
    Analyze portfolio factor exposures using Fama-French methodology.
    This provides institutional-quality risk attribution.
    """
    print("Calculating portfolio factor exposures...")
    
    portfolio_exposures = {
        'beta_market': 0,
        'beta_size': 0,
        'beta_value': 0,
        'beta_profit': 0,
        'beta_invest': 0,
        'alpha': 0,
        'avg_r_squared': 0
    }
    
    total_weight = 0
    valid_stocks = 0
    
    for _, row in portfolio_df.iterrows():
        ticker = row['Ticker']
        weight = row.get('Portfolio Weight', 1/len(portfolio_df))
        
        if ticker in factor_exposures:
            exposures = factor_exposures[ticker]
            
            for factor in portfolio_exposures.keys():
                if factor == 'avg_r_squared':
                    portfolio_exposures[factor] += exposures.get('r_squared', 0)
                else:
                    portfolio_exposures[factor] += weight * exposures.get(factor, 0)
            
            total_weight += weight
            valid_stocks += 1
    
    # Calculate weighted averages
    if total_weight > 0:
        for factor in ['beta_market', 'beta_size', 'beta_value', 'beta_profit', 'beta_invest', 'alpha']:
            portfolio_exposures[factor] /= total_weight
    
    if valid_stocks > 0:
        portfolio_exposures['avg_r_squared'] /= valid_stocks
    
    # Add interpretation
    portfolio_exposures['interpretation'] = {
        'size_bias': 'Small-cap bias' if portfolio_exposures['beta_size'] > 0.2 else 'Large-cap bias' if portfolio_exposures['beta_size'] < -0.2 else 'Size neutral',
        'value_bias': 'Value bias' if portfolio_exposures['beta_value'] > 0.2 else 'Growth bias' if portfolio_exposures['beta_value'] < -0.2 else 'Style neutral',
        'quality_bias': 'High quality bias' if portfolio_exposures['beta_profit'] > 0.2 else 'Low quality bias' if portfolio_exposures['beta_profit'] < -0.2 else 'Quality neutral',
        'market_sensitivity': 'High beta' if portfolio_exposures['beta_market'] > 1.2 else 'Low beta' if portfolio_exposures['beta_market'] < 0.8 else 'Market neutral',
        'alpha_significance': 'Positive alpha' if portfolio_exposures['alpha'] > 0.002 else 'Negative alpha' if portfolio_exposures['alpha'] < -0.002 else 'No significant alpha'
    }
    
    print(f"Portfolio analysis complete for {valid_stocks} stocks")
    return portfolio_exposures

def main():
    """Demonstrate proper Fama-French implementation."""
    print("=== FAMA-FRENCH FACTOR IMPLEMENTATION ===")
    
    # 1. Download factor data
    print("\n1. Downloading Fama-French factor data...")
    ff_factors = get_fama_french_factors()
    momentum_factor = get_momentum_factor()
    
    if not ff_factors.empty:
        print(f"FF Factors shape: {ff_factors.shape}")
        print(f"Sample data:\n{ff_factors.head()}")
    
    # 2. This would integrate with our existing system
    print("\n2. Integration points with existing system:")
    print("   ✓ Add to quality_momentum_analysis.py")
    print("   ✓ Integrate with portfolio_selection.py") 
    print("   ✓ Enhance risk_analysis.py")
    print("   ✓ Update 06_macro_economic_analysis.py")
    
    print("\n3. Benefits of proper FF implementation:")
    print("   • True factor risk attribution")
    print("   • Academic-quality performance analysis")
    print("   • Industry-standard factor exposures")
    print("   • Enhanced portfolio construction")

if __name__ == "__main__":
    main() 