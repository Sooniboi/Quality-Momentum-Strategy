import pandas as pd
import numpy as np
import os
import glob
from datetime import date, datetime
from typing import Dict, List, Optional
import json

class UnifiedPortfolioConstructor:
    """
    Unified Portfolio Construction System
    
    Integrates:
    - Sector Scoring → Company Selection
    - Risk Analysis → Weight Optimization 
    - Macro Economics → Market Regime Adjustments
    - All feeding into ONE portfolio construction process
    """
    
    def __init__(self, target_size: int = 50):
        self.target_size = target_size
        self.market_regime = None
        self.macro_data = None
        self.risk_metrics = {}
        
    def construct_portfolio(self) -> pd.DataFrame:
        """Main unified portfolio construction process."""
        print("🚀 UNIFIED PORTFOLIO CONSTRUCTION SYSTEM")
        print("=" * 80)
        
        # Step 1: Load all data sources
        sector_data, macro_data, risk_data = self._load_all_data()
        
        # Store risk data for use in other methods
        self.risk_data = risk_data
        
        # Step 2: Integrate macro conditions into scoring
        enhanced_data = self._integrate_macro_conditions(sector_data, macro_data)
        
        # Step 3: Apply risk-aware filtering
        filtered_data = self._apply_risk_filtering(enhanced_data, risk_data)
        
        # Step 4: Select companies using integrated scoring
        selected_companies = self._select_companies(filtered_data)
        
        # Step 5: Optimize weights using risk metrics
        portfolio = self._optimize_weights(selected_companies, risk_data)
        
        # Step 6: Final validation and reporting
        portfolio = self._finalize_portfolio(portfolio)
        
        return portfolio
    
    def _load_all_data(self) -> tuple:
        """Load sector scoring, macro, and risk data."""
        print("\n📊 LOADING DATA SOURCES")
        print("-" * 40)
        
        base_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files')
        
        # 1. Sector scored companies (main data) - look in main folder first for latest data
        sector_pattern = os.path.join(base_dir, '03_sector_scored_companies_*.csv')
        sector_files = glob.glob(sector_pattern)
        if not sector_files:
            # Fallback to fundamental_data folder
            sector_pattern = os.path.join(base_dir, 'fundamental_data', '03_sector_scored_companies_*.csv')
            sector_files = glob.glob(sector_pattern)
        
        if not sector_files:
            raise FileNotFoundError("No sector scored data found")
        
        sector_file = max(sector_files, key=os.path.getctime)
        sector_data = pd.read_csv(sector_file)
        print(f"✅ Loaded sector data: {len(sector_data)} companies from {os.path.basename(sector_file)}")
        
        # 2. Macro economic data - look in macro_analysis folder
        macro_pattern = os.path.join(base_dir, 'macro_analysis', '*macro*.csv')
        macro_files = glob.glob(macro_pattern)
        if not macro_files:
            # Fallback to main folder
            macro_pattern = os.path.join(base_dir, '*macro*.csv')
            macro_files = glob.glob(macro_pattern)
        
        if macro_files:
            macro_file = max(macro_files, key=os.path.getctime)
            macro_data = pd.read_csv(macro_file)
            print(f"✅ Loaded macro data from {os.path.basename(macro_file)}")
        else:
            print("⚠️ No macro data found, using defaults")
            macro_data = pd.DataFrame([{
                'Recession_Probability': 20.0,
                'Fed_Policy_Bias': 'NEUTRAL',
                'VIX': 20.0
            }])
        
        # 3. Risk analysis data (including comprehensive macro risk analysis)
        risk_pattern = os.path.join(base_dir, 'risk_analysis', '*.csv')
        risk_files = glob.glob(risk_pattern)
        
        risk_data = {}
        if risk_files:
            for risk_file in risk_files:
                if 'correlations' in risk_file:
                    risk_data['correlations'] = pd.read_csv(risk_file, index_col=0)
                elif 'risk_metrics' in risk_file:
                    risk_data['metrics'] = pd.read_csv(risk_file)
            print(f"✅ Loaded risk analysis data")
        
        # 4. Load comprehensive macro risk analysis from risk_analysis folder
        macro_risk_file = os.path.join(base_dir, 'risk_analysis', 'macro_risk_analysis_latest.json')
        fed_policy_file = os.path.join(base_dir, 'risk_analysis', 'fed_policy_analysis_latest.json')
        fred_data_file = os.path.join(base_dir, 'risk_analysis', 'fred_economic_data_latest.json')
        
        try:
            if os.path.exists(macro_risk_file):
                with open(macro_risk_file, 'r') as f:
                    risk_data['macro_risk'] = json.load(f)
                print(f"✅ Loaded comprehensive macro risk analysis")
            
            if os.path.exists(fed_policy_file):
                with open(fed_policy_file, 'r') as f:
                    risk_data['fed_policy'] = json.load(f)
                print(f"✅ Loaded Fed policy analysis")
                
            if os.path.exists(fred_data_file):
                with open(fred_data_file, 'r') as f:
                    risk_data['fred_data'] = json.load(f)
                print(f"✅ Loaded FRED economic data")
                
        except Exception as e:
            print(f"⚠️ Could not load enhanced risk data: {e}")
            risk_data = risk_data or {}
        
        return sector_data, macro_data, risk_data
    
    def _integrate_macro_conditions(self, sector_data: pd.DataFrame, macro_data: pd.DataFrame) -> pd.DataFrame:
        """Integrate macro economic conditions into company scoring."""
        print("\n🌍 INTEGRATING MACRO CONDITIONS")
        print("-" * 40)
        
        df = sector_data.copy()
        
        # Determine market regime from enhanced macro risk analysis if available
        if hasattr(self, 'risk_data') and 'macro_risk' in self.risk_data:
            macro_risk = self.risk_data['macro_risk']
            recession_prob = macro_risk.get('recession_analysis', {}).get('probability', 20)
            fed_policy_bias = self.risk_data.get('fed_policy', {}).get('overall_assessment', {}).get('policy_bias', 'NEUTRAL')
            
            print(f"Enhanced data source: Comprehensive macro risk analysis")
            print(f"Fed Policy Bias: {fed_policy_bias}")
            print(f"Recession Probability: {recession_prob:.1f}%")
            
        elif 'Recession_Probability' in macro_data.columns:
            recession_prob = macro_data['Recession_Probability'].iloc[-1]
            fed_policy_bias = macro_data.get('Fed_Policy_Bias', pd.Series(['NEUTRAL'])).iloc[-1]
            print(f"Standard data source: Basic macro analysis")
            
        else:
            recession_prob = 20.0
            fed_policy_bias = 'NEUTRAL'
            print(f"Fallback data source: Default values")
        
        # Enhanced market regime logic incorporating Fed policy
        if recession_prob > 40 or fed_policy_bias == 'STRONGLY_DOVISH':
            self.market_regime = 'DEFENSIVE'
        elif recession_prob > 25 or fed_policy_bias in ['DOVISH', 'STRONGLY_HAWKISH']:
            self.market_regime = 'CAUTIOUS'  
        else:
            self.market_regime = 'NORMAL'
        
        print(f"Market Regime: {self.market_regime} (Recession: {recession_prob:.1f}%, Fed: {fed_policy_bias})")
        
        # Enhanced sector adjustments incorporating Fed policy stance
        base_adjustments = {
            'DEFENSIVE': {
                'Healthcare': 1.15,
                'Consumer Defensive': 1.10,
                'Utilities': 1.05,
                'Technology': 0.90,
                'Real Estate': 0.85,
                'Energy': 0.80
            },
            'CAUTIOUS': {
                'Healthcare': 1.05,
                'Consumer Defensive': 1.03,
                'Technology': 0.95,
                'Energy': 0.90
            },
            'NORMAL': {},  # No adjustments
        }
        
        # Fed policy overlay adjustments
        fed_adjustments = {}
        if fed_policy_bias in ['HAWKISH', 'STRONGLY_HAWKISH']:
            fed_adjustments.update({
                'Financial Services': 1.10,  # Banks benefit from higher rates
                'Real Estate': 0.85,         # REITs hurt by higher rates
                'Utilities': 0.90            # Interest-sensitive sectors hurt
            })
        elif fed_policy_bias in ['DOVISH', 'STRONGLY_DOVISH']:
            fed_adjustments.update({
                'Technology': 1.10,          # Growth stocks benefit from lower rates
                'Real Estate': 1.05,         # REITs benefit from lower rates
                'Financial Services': 0.90   # Banks hurt by lower rates
            })
        
        # Combine base and Fed policy adjustments
        adjustments = base_adjustments.get(self.market_regime, {}).copy()
        for sector, adj in fed_adjustments.items():
            if sector in adjustments:
                adjustments[sector] = (adjustments[sector] + adj) / 2  # Average the adjustments
            else:
                adjustments[sector] = adj
        
        if adjustments:
            print("Applying enhanced sector adjustments:")
            for sector, adjustment in adjustments.items():
                mask = df['Sector'] == sector
                df.loc[mask, 'Quality Score'] *= adjustment
                df.loc[mask, 'Momentum Score'] *= adjustment
                df.loc[mask, 'Overall Score'] *= adjustment
                source = "Fed+Regime" if sector in fed_adjustments else "Regime"
                print(f"  {sector}: {adjustment:.2f}x ({source})")
        
        # Create macro-adjusted composite score
        df['Macro_Adjusted_Score'] = (
            df['Quality Score'] * 0.4 +
            df['Momentum Score'] * 0.3 +
            df['Overall Score'] * 0.3
        )
        
        return df
    
    def _apply_risk_filtering(self, df: pd.DataFrame, risk_data: Dict) -> pd.DataFrame:
        """Apply risk-based filtering and add risk metrics."""
        print("\n⚠️ APPLYING RISK FILTERING")
        print("-" * 40)
        
        initial_count = len(df)
        
        # Basic financial health filters
        df = df[
            (df['Style'] != 'Weak') &
            (df['Quality Score'] > -0.5) &
            (df['Momentum Score'] > -1.0) &
            (df['ROIC'] > 0) &
            (df['Operating Margin'] > 0) &
            (df['FCF'] > 0) &
            (df['Net Debt to EBITDA'] < 5.0) &
            (df['marketCap'] > 100_000_000)  # $100M minimum
        ].copy()
        
        print(f"Basic filtering: {initial_count} → {len(df)} companies")
        
        # Add estimated risk metrics
        df = self._add_risk_metrics(df, risk_data)
        
        # Apply risk-based filters
        df = df[
            (df['Est_Volatility'] <= 0.40) &  # Max 40% volatility
            (df['Est_Beta'] >= 0.5) &
            (df['Est_Beta'] <= 1.8)
        ]
        
        print(f"Risk filtering: {initial_count} → {len(df)} companies")
        
        return df
    
    def _add_risk_metrics(self, df: pd.DataFrame, risk_data: Dict) -> pd.DataFrame:
        """Add risk metrics to companies."""
        
        # Sector-based volatility estimates
        sector_volatilities = {
            'Technology': 0.28,
            'Healthcare': 0.22,
            'Financial Services': 0.25,
            'Consumer Cyclical': 0.30,
            'Consumer Defensive': 0.18,
            'Industrials': 0.24,
            'Energy': 0.35,
            'Basic Materials': 0.30,
            'Real Estate': 0.22,
            'Utilities': 0.16,
            'Communication Services': 0.24
        }
        
        # Sector-based beta estimates
        sector_betas = {
            'Technology': 1.2,
            'Healthcare': 0.9,
            'Financial Services': 1.1,
            'Consumer Cyclical': 1.3,
            'Consumer Defensive': 0.8,
            'Industrials': 1.1,
            'Energy': 1.4,
            'Basic Materials': 1.2,
            'Real Estate': 0.9,
            'Utilities': 0.7,
            'Communication Services': 1.0
        }
        
        # Estimate volatility and beta
        df['Est_Volatility'] = df['Sector'].map(sector_volatilities).fillna(0.25)
        df['Est_Beta'] = df['Sector'].map(sector_betas).fillna(1.0)
        
        # Adjust based on momentum (higher momentum = higher vol/beta)
        df['Est_Volatility'] *= (1 + abs(df['Momentum Score']) * 0.1)
        df['Est_Beta'] *= (1 + df['Momentum Score'] * 0.1)
        
        # Cap values
        df['Est_Volatility'] = np.clip(df['Est_Volatility'], 0.10, 0.50)
        df['Est_Beta'] = np.clip(df['Est_Beta'], 0.3, 2.5)
        
        # Risk-adjusted scores
        df['Risk_Adj_Quality'] = df['Quality Score'] / np.sqrt(df['Est_Volatility'])
        df['Risk_Adj_Momentum'] = df['Momentum Score'] / df['Est_Beta']
        
        # Sharpe-like ratio
        df['Sharpe_Score'] = df['6M Return'] / (df['Est_Volatility'] + 0.01) if '6M Return' in df.columns else 0
        
        return df
    
    def _select_companies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Select companies using integrated scoring approach."""
        print("\n🎯 SELECTING COMPANIES")
        print("-" * 40)
        
        # Adjust style targets based on market regime
        if self.market_regime == 'DEFENSIVE':
            style_targets = {'Quality': 30, 'Value': 12, 'Growth': 5, 'Blend': 3}
        elif self.market_regime == 'CAUTIOUS':
            style_targets = {'Quality': 25, 'Value': 15, 'Growth': 8, 'Blend': 2}
        else:  # NORMAL
            style_targets = {'Quality': 20, 'Growth': 15, 'Value': 10, 'Blend': 5}
        
        print(f"Style targets for {self.market_regime} market:")
        for style, target in style_targets.items():
            print(f"  {style}: {target} companies")
        
        # Create final integrated score
        df['Final_Score'] = (
            df['Macro_Adjusted_Score'] * 0.5 +
            df['Risk_Adj_Quality'] * 0.25 +
            df['Risk_Adj_Momentum'] * 0.15 +
            df['Sharpe_Score'] * 0.10
        )
        
        # Select companies by style
        selected = pd.DataFrame()
        
        for style, target_count in style_targets.items():
            style_companies = df[df['Style'] == style].copy()
            
            if len(style_companies) == 0:
                print(f"⚠️ No {style} companies available")
                continue
            
            # Sort by final score
            style_companies = style_companies.sort_values('Final_Score', ascending=False)
            
            # Select top companies
            selected_count = min(target_count, len(style_companies))
            style_selected = style_companies.head(selected_count)
            
            selected = pd.concat([selected, style_selected])
            print(f"✅ Selected {selected_count}/{target_count} {style} companies")
        
        print(f"\nTotal selected: {len(selected)} companies")
        return selected
    
    def _optimize_weights(self, df: pd.DataFrame, risk_data: Dict) -> pd.DataFrame:
        """Optimize portfolio weights using risk considerations."""
        print("\n⚖️ OPTIMIZING WEIGHTS")
        print("-" * 40)
        
        # Risk-based weighting methods
        if len(df) == 0:
            return df
        
        # Method 1: Inverse volatility weighting
        inv_vol_weights = (1 / df['Est_Volatility']) / (1 / df['Est_Volatility']).sum()
        
        # Method 2: Score-based weighting
        score_weights = (df['Final_Score'] - df['Final_Score'].min() + 0.1)
        score_weights = score_weights / score_weights.sum()
        
        # Method 3: Equal weighting
        equal_weights = np.ones(len(df)) / len(df)
        
        # Combine methods (60% score, 30% risk-parity, 10% equal)
        df['Portfolio_Weight'] = (
            score_weights * 0.60 +
            inv_vol_weights * 0.30 +
            equal_weights * 0.10
        )
        
        # Apply constraints
        max_single_weight = 0.05  # 5% max per stock
        max_sector_weight = 0.25  # 25% max per sector
        
        # Cap individual weights
        df['Portfolio_Weight'] = np.minimum(df['Portfolio_Weight'], max_single_weight)
        df['Portfolio_Weight'] = df['Portfolio_Weight'] / df['Portfolio_Weight'].sum()
        
        # Check sector concentration
        sector_weights = df.groupby('Sector')['Portfolio_Weight'].sum()
        max_sector = sector_weights.max()
        
        if max_sector > max_sector_weight:
            print(f"⚠️ Adjusting sector concentration (max was {max_sector:.1%})")
            # Proportionally reduce overweight sectors
            for sector in sector_weights.index:
                if sector_weights[sector] > max_sector_weight:
                    sector_mask = df['Sector'] == sector
                    adjustment = max_sector_weight / sector_weights[sector]
                    df.loc[sector_mask, 'Portfolio_Weight'] *= adjustment
            
            # Renormalize
            df['Portfolio_Weight'] = df['Portfolio_Weight'] / df['Portfolio_Weight'].sum()
        
        print(f"Weight optimization complete:")
        print(f"  Max single stock: {df['Portfolio_Weight'].max():.2%}")
        print(f"  Max sector: {df.groupby('Sector')['Portfolio_Weight'].sum().max():.2%}")
        
        return df
    
    def _finalize_portfolio(self, df: pd.DataFrame) -> pd.DataFrame:
        """Final validation and portfolio metrics calculation."""
        print("\n📋 FINALIZING PORTFOLIO")
        print("-" * 40)
        
        if len(df) == 0:
            print("❌ No companies in final portfolio!")
            return df
        
        # Calculate portfolio-level metrics
        portfolio_quality = (df['Quality Score'] * df['Portfolio_Weight']).sum()
        portfolio_momentum = (df['Momentum Score'] * df['Portfolio_Weight']).sum()
        portfolio_volatility = np.sqrt((df['Est_Volatility'] ** 2 * df['Portfolio_Weight'] ** 2).sum())
        portfolio_beta = (df['Est_Beta'] * df['Portfolio_Weight']).sum()
        
        # Style and sector distributions
        style_dist = df.groupby('Style')['Portfolio_Weight'].sum()
        sector_dist = df.groupby('Sector')['Portfolio_Weight'].sum()
        
        # Generate report
        print(f"\n🎯 PORTFOLIO SUMMARY")
        print("=" * 50)
        print(f"Companies: {len(df)}")
        print(f"Sectors: {df['Sector'].nunique()}")
        print(f"Market Regime: {self.market_regime}")
        
        print(f"\nPortfolio Metrics:")
        print(f"  Quality Score: {portfolio_quality:.2f}")
        print(f"  Momentum Score: {portfolio_momentum:.2f}")
        print(f"  Est. Volatility: {portfolio_volatility:.1%}")
        print(f"  Est. Beta: {portfolio_beta:.2f}")
        
        print(f"\nStyle Allocation:")
        for style, weight in style_dist.items():
            print(f"  {style}: {weight:.1%}")
        
        print(f"\nTop Holdings:")
        top_holdings = df.nlargest(10, 'Portfolio_Weight')
        for _, row in top_holdings.iterrows():
            print(f"  {row['Ticker']} ({row['Sector']}) - {row['Style']} - {row['Portfolio_Weight']:.2%}")
        
        # Save portfolio
        self._save_portfolio(df, {
            'portfolio_quality': portfolio_quality,
            'portfolio_momentum': portfolio_momentum,
            'portfolio_volatility': portfolio_volatility,
            'portfolio_beta': portfolio_beta,
            'style_distribution': style_dist.to_dict(),
            'sector_distribution': sector_dist.to_dict(),
            'market_regime': self.market_regime
        })
        
        return df
    
    def _save_portfolio(self, portfolio: pd.DataFrame, metrics: Dict) -> str:
        """Save the unified portfolio."""
        today = date.today().strftime('%Y-%m-%d')
        filename = f"04_unified_portfolio_selection_{today}.csv"
        
        # Create organized directory structure
        base_output_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files')
        portfolios_dir = os.path.join(base_output_dir, 'portfolios')
        os.makedirs(portfolios_dir, exist_ok=True)
        
        output_path = os.path.join(portfolios_dir, filename)
        
        # Select output columns
        output_columns = [
            'Ticker', 'Sector', 'Style', 'Portfolio_Weight',
            'Final_Score', 'Macro_Adjusted_Score', 'Quality Score', 'Momentum Score',
            'Risk_Adj_Quality', 'Risk_Adj_Momentum', 'Sharpe_Score',
            'Est_Volatility', 'Est_Beta',
            'ROIC', 'Operating Margin', 'Revenue Growth', 'FCF', 'Net Debt to EBITDA',
            '3M Return', '6M Return', 'marketCap'
        ]
        
        available_columns = [col for col in output_columns if col in portfolio.columns]
        portfolio[available_columns].to_csv(output_path, index=False)
        
        # Save metadata to portfolios folder
        metadata = {
            'construction_date': datetime.now().isoformat(),
            'system_type': 'unified_portfolio_construction',
            'market_regime': self.market_regime,
            'target_size': self.target_size,
            'actual_size': len(portfolio),
            'metrics': metrics
        }
        
        metadata_path = output_path.replace('.csv', '_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n💾 Portfolio saved to: {output_path}")
        print(f"💾 Metadata saved to: {metadata_path}")
        return output_path

def main():
    """Run the unified portfolio construction system."""
    try:
        constructor = UnifiedPortfolioConstructor(target_size=50)
        portfolio = constructor.construct_portfolio()
        
        print(f"\n✅ UNIFIED PORTFOLIO CONSTRUCTION COMPLETED!")
        print(f"Final portfolio: {len(portfolio)} companies")
        
        return portfolio
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    portfolio = main() 