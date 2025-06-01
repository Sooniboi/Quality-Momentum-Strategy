#!/usr/bin/env python3

"""
Monte Carlo Portfolio Simulation System
Loads unified portfolio construction output and runs comprehensive simulations.
"""

import pandas as pd
import numpy as np
import os
import glob
import json
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class MonteCarloPortfolioSimulator:
    """
    Monte Carlo simulation system for portfolio analysis.
    
    Features:
    - Portfolio return simulations
    - Risk metrics (VaR, CVaR, Maximum Drawdown)
    - Scenario analysis
    - Stress testing
    - Performance forecasting
    """
    
    def __init__(self, num_simulations: int = 10000, time_horizon_days: int = 252):
        self.num_simulations = num_simulations
        self.time_horizon_days = time_horizon_days  # 1 year default
        self.portfolio_data = None
        self.metadata = None
        self.correlation_matrix = None
        self.simulation_results = None
        
    def load_portfolio_data(self) -> bool:
        """Load the latest unified portfolio data."""
        print("📊 LOADING PORTFOLIO DATA FOR MONTE CARLO")
        print("=" * 60)
        
        # Find latest portfolio file
        base_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files', 'portfolios')
        portfolio_pattern = os.path.join(base_dir, '04_unified_portfolio_selection_*.csv')
        portfolio_files = glob.glob(portfolio_pattern)
        
        if not portfolio_files:
            print("❌ No portfolio files found!")
            return False
        
        # Get latest file
        latest_portfolio_file = max(portfolio_files, key=os.path.getctime)
        self.portfolio_data = pd.read_csv(latest_portfolio_file)
        
        # Load metadata
        metadata_file = latest_portfolio_file.replace('.csv', '_metadata.json')
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                self.metadata = json.load(f)
        
        print(f"✅ Loaded portfolio: {len(self.portfolio_data)} stocks")
        print(f"   File: {os.path.basename(latest_portfolio_file)}")
        print(f"   Portfolio Beta: {self.metadata['metrics']['portfolio_beta']:.2f}")
        print(f"   Portfolio Volatility: {self.metadata['metrics']['portfolio_volatility']:.1%}")
        print(f"   Market Regime: {self.metadata['market_regime']}")
        
        return True
    
    def estimate_correlation_matrix(self) -> np.ndarray:
        """Estimate correlation matrix using sector-based correlations."""
        print("\n🔗 ESTIMATING CORRELATION MATRIX")
        print("-" * 40)
        
        num_stocks = len(self.portfolio_data)
        correlation_matrix = np.eye(num_stocks)
        
        # Sector-based correlation estimates
        sector_correlations = {
            'Technology': 0.65,
            'Healthcare': 0.45,
            'Financial Services': 0.70,
            'Consumer Cyclical': 0.60,
            'Consumer Defensive': 0.40,
            'Industrials': 0.55,
            'Energy': 0.75,
            'Basic Materials': 0.70,
            'Real Estate': 0.65,
            'Utilities': 0.50,
            'Communication Services': 0.60
        }
        
        # Create correlation matrix
        sectors = self.portfolio_data['Sector'].values
        
        for i in range(num_stocks):
            for j in range(i+1, num_stocks):
                if sectors[i] == sectors[j]:
                    # Same sector - higher correlation
                    correlation = sector_correlations.get(sectors[i], 0.50)
                else:
                    # Different sectors - lower correlation
                    correlation = 0.15 + np.random.normal(0, 0.05)  # Base market correlation
                
                # Ensure correlation is within bounds
                correlation = np.clip(correlation, -0.95, 0.95)
                correlation_matrix[i, j] = correlation
                correlation_matrix[j, i] = correlation
        
        # Ensure positive semi-definite
        eigenvals = np.linalg.eigvals(correlation_matrix)
        if np.min(eigenvals) < 0:
            # Adjust negative eigenvalues
            correlation_matrix += np.eye(num_stocks) * (abs(np.min(eigenvals)) + 0.01)
            # Re-normalize diagonal
            for i in range(num_stocks):
                correlation_matrix[i, i] = 1.0
        
        self.correlation_matrix = correlation_matrix
        
        avg_correlation = np.mean(correlation_matrix[np.triu_indices_from(correlation_matrix, k=1)])
        print(f"✅ Correlation matrix created: {num_stocks}x{num_stocks}")
        print(f"   Average correlation: {avg_correlation:.3f}")
        
        return correlation_matrix
    
    def run_monte_carlo_simulation(self) -> Dict:
        """Run Monte Carlo simulation for portfolio returns."""
        print(f"\n🎲 RUNNING MONTE CARLO SIMULATION")
        print("-" * 40)
        print(f"Simulations: {self.num_simulations:,}")
        print(f"Time Horizon: {self.time_horizon_days} days")
        
        # Portfolio parameters
        weights = self.portfolio_data['Portfolio_Weight'].values
        volatilities = self.portfolio_data['Est_Volatility'].values
        
        # Convert annual volatilities to daily
        daily_volatilities = volatilities / np.sqrt(252)
        
        # Expected returns (estimate from momentum and quality scores)
        expected_annual_returns = (
            self.portfolio_data['Quality Score'] * 0.02 +  # Quality premium
            self.portfolio_data['Momentum Score'] * 0.03 + # Momentum premium  
            0.05  # Risk-free rate baseline
        ).values
        
        daily_expected_returns = expected_annual_returns / 252
        
        # Monte Carlo simulation
        portfolio_returns = np.zeros((self.num_simulations, self.time_horizon_days))
        
        print("Running simulations...")
        for sim in range(self.num_simulations):
            if sim % 1000 == 0:
                print(f"  Simulation {sim:,}/{self.num_simulations:,}")
            
            # Generate correlated random returns
            random_returns = np.random.multivariate_normal(
                mean=daily_expected_returns,
                cov=np.outer(daily_volatilities, daily_volatilities) * self.correlation_matrix,
                size=self.time_horizon_days
            )
            
            # Calculate portfolio returns
            daily_portfolio_returns = np.dot(random_returns, weights)
            portfolio_returns[sim, :] = daily_portfolio_returns
        
        # Calculate cumulative returns
        cumulative_returns = np.cumprod(1 + portfolio_returns, axis=1) - 1
        final_returns = cumulative_returns[:, -1]
        
        # Store results
        self.simulation_results = {
            'daily_returns': portfolio_returns,
            'cumulative_returns': cumulative_returns,
            'final_returns': final_returns,
            'weights': weights,
            'volatilities': volatilities,
            'expected_returns': expected_annual_returns
        }
        
        print(f"✅ Simulation complete!")
        
        return self.simulation_results
    
    def calculate_risk_metrics(self) -> Dict:
        """Calculate comprehensive risk metrics from simulation results."""
        print(f"\n⚠️ CALCULATING RISK METRICS")
        print("-" * 40)
        
        if self.simulation_results is None:
            print("❌ No simulation results available!")
            return {}
        
        final_returns = self.simulation_results['final_returns']
        daily_returns = self.simulation_results['daily_returns']
        cumulative_returns = self.simulation_results['cumulative_returns']
        
        # Basic statistics
        mean_return = np.mean(final_returns)
        std_return = np.std(final_returns)
        
        # Value at Risk (VaR)
        var_95 = np.percentile(final_returns, 5)
        var_99 = np.percentile(final_returns, 1)
        
        # Conditional Value at Risk (Expected Shortfall)
        cvar_95 = np.mean(final_returns[final_returns <= var_95])
        cvar_99 = np.mean(final_returns[final_returns <= var_99])
        
        # Maximum Drawdown
        max_drawdowns = []
        for sim in range(self.num_simulations):
            cum_returns = cumulative_returns[sim, :]
            running_max = np.maximum.accumulate(cum_returns)
            drawdowns = (cum_returns - running_max) / (1 + running_max)
            max_drawdowns.append(np.min(drawdowns))
        
        max_drawdown_95 = np.percentile(max_drawdowns, 95)
        max_drawdown_mean = np.mean(max_drawdowns)
        
        # Sharpe Ratio (approximate)
        risk_free_rate = 0.05  # 5% annual
        sharpe_ratio = (mean_return - risk_free_rate) / std_return
        
        # Probability of positive returns
        prob_positive = np.sum(final_returns > 0) / len(final_returns)
        
        # Probability of beating market (assume 8% annual return)
        market_return = 0.08
        prob_beat_market = np.sum(final_returns > market_return) / len(final_returns)
        
        risk_metrics = {
            'expected_return': mean_return,
            'volatility': std_return,
            'sharpe_ratio': sharpe_ratio,
            'var_95': var_95,
            'var_99': var_99,
            'cvar_95': cvar_95,
            'cvar_99': cvar_99,
            'max_drawdown_mean': max_drawdown_mean,
            'max_drawdown_95': max_drawdown_95,
            'prob_positive': prob_positive,
            'prob_beat_market': prob_beat_market,
            'percentile_10': np.percentile(final_returns, 10),
            'percentile_25': np.percentile(final_returns, 25),
            'percentile_75': np.percentile(final_returns, 75),
            'percentile_90': np.percentile(final_returns, 90)
        }
        
        # Display results
        print(f"Expected Return: {mean_return:.1%}")
        print(f"Volatility: {std_return:.1%}")
        print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
        print(f"VaR (95%): {var_95:.1%}")
        print(f"VaR (99%): {var_99:.1%}")
        print(f"Max Drawdown (95%): {max_drawdown_95:.1%}")
        print(f"Prob. Positive: {prob_positive:.1%}")
        print(f"Prob. Beat Market: {prob_beat_market:.1%}")
        
        return risk_metrics
    
    def run_stress_tests(self) -> Dict:
        """Run stress test scenarios."""
        print(f"\n🔥 RUNNING STRESS TESTS")
        print("-" * 40)
        
        if self.portfolio_data is None:
            print("❌ No portfolio data available!")
            return {}
        
        weights = self.portfolio_data['Portfolio_Weight'].values
        volatilities = self.portfolio_data['Est_Volatility'].values
        
        stress_scenarios = {
            'market_crash': {
                'description': '2008-style market crash (-40% market)',
                'market_return': -0.40,
                'volatility_multiplier': 2.0
            },
            'recession': {
                'description': 'Economic recession (-25% market)', 
                'market_return': -0.25,
                'volatility_multiplier': 1.5
            },
            'inflation_shock': {
                'description': 'Inflation shock (high rates)',
                'market_return': -0.15,
                'volatility_multiplier': 1.3
            },
            'sector_rotation': {
                'description': 'Major sector rotation',
                'market_return': -0.05,
                'volatility_multiplier': 1.2
            }
        }
        
        stress_results = {}
        
        for scenario_name, scenario in stress_scenarios.items():
            # Adjust returns and volatilities for stress scenario
            market_beta = self.metadata['metrics']['portfolio_beta']
            
            # Portfolio return under stress
            portfolio_return = scenario['market_return'] * market_beta
            
            # Adjust for sector exposures under stress
            sector_stress_adjustments = {
                'Technology': 1.2,  # More volatile in stress
                'Financial Services': 1.5,
                'Energy': 1.3,
                'Consumer Cyclical': 1.4,
                'Healthcare': 0.8,  # Defensive
                'Consumer Defensive': 0.7,
                'Utilities': 0.6
            }
            
            # Calculate sector-adjusted stress return
            sector_adjusted_return = 0
            for _, stock in self.portfolio_data.iterrows():
                sector = stock['Sector']
                weight = stock['Portfolio_Weight']
                stress_multiplier = sector_stress_adjustments.get(sector, 1.0)
                sector_adjusted_return += weight * portfolio_return * stress_multiplier
            
            stress_results[scenario_name] = {
                'description': scenario['description'],
                'portfolio_return': sector_adjusted_return,
                'market_return': scenario['market_return'],
                'relative_performance': sector_adjusted_return - scenario['market_return']
            }
            
            print(f"{scenario_name}: {sector_adjusted_return:.1%} "
                  f"(vs market {scenario['market_return']:.1%})")
        
        return stress_results
    
    def generate_report(self, risk_metrics: Dict, stress_results: Dict) -> str:
        """Generate comprehensive Monte Carlo analysis report."""
        print(f"\n📋 GENERATING MONTE CARLO REPORT")
        print("-" * 40)
        
        # Create report
        report_lines = [
            "MONTE CARLO PORTFOLIO ANALYSIS REPORT",
            "=" * 60,
            f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Portfolio: {len(self.portfolio_data)} stocks",
            f"Simulations: {self.num_simulations:,}",
            f"Time Horizon: {self.time_horizon_days} days",
            f"Market Regime: {self.metadata.get('market_regime', 'N/A')}",
            "",
            "PORTFOLIO COMPOSITION:",
            f"Quality Allocation: {self.metadata['metrics']['style_distribution'].get('Quality', 0):.1%}",
            f"Growth Allocation: {self.metadata['metrics']['style_distribution'].get('Growth', 0):.1%}",
            f"Value Allocation: {self.metadata['metrics']['style_distribution'].get('Value', 0):.1%}",
            f"Blend Allocation: {self.metadata['metrics']['style_distribution'].get('Blend', 0):.1%}",
            "",
            "RISK METRICS:",
            f"Expected Return: {risk_metrics['expected_return']:.1%}",
            f"Volatility: {risk_metrics['volatility']:.1%}",
            f"Sharpe Ratio: {risk_metrics['sharpe_ratio']:.2f}",
            "",
            "VALUE AT RISK:",
            f"VaR (95%): {risk_metrics['var_95']:.1%}",
            f"VaR (99%): {risk_metrics['var_99']:.1%}",
            f"CVaR (95%): {risk_metrics['cvar_95']:.1%}",
            f"CVaR (99%): {risk_metrics['cvar_99']:.1%}",
            "",
            "DRAWDOWN ANALYSIS:",
            f"Average Max Drawdown: {risk_metrics['max_drawdown_mean']:.1%}",
            f"95th Percentile Max Drawdown: {risk_metrics['max_drawdown_95']:.1%}",
            "",
            "RETURN DISTRIBUTION:",
            f"10th Percentile: {risk_metrics['percentile_10']:.1%}",
            f"25th Percentile: {risk_metrics['percentile_25']:.1%}",
            f"75th Percentile: {risk_metrics['percentile_75']:.1%}",
            f"90th Percentile: {risk_metrics['percentile_90']:.1%}",
            "",
            "PROBABILITIES:",
            f"Probability of Positive Return: {risk_metrics['prob_positive']:.1%}",
            f"Probability of Beating Market: {risk_metrics['prob_beat_market']:.1%}",
            "",
            "STRESS TEST RESULTS:",
        ]
        
        for scenario_name, results in stress_results.items():
            report_lines.extend([
                f"{scenario_name.upper()}:",
                f"  {results['description']}",
                f"  Portfolio Return: {results['portfolio_return']:.1%}",
                f"  Relative to Market: {results['relative_performance']:+.1%}",
                ""
            ])
        
        report_lines.extend([
            "TOP HOLDINGS ANALYSIS:",
        ])
        
        # Top 10 holdings
        top_holdings = self.portfolio_data.nlargest(10, 'Portfolio_Weight')
        for _, stock in top_holdings.iterrows():
            report_lines.append(
                f"  {stock['Ticker']} ({stock['Sector']}) - "
                f"{stock['Portfolio_Weight']:.1%} - {stock['Style']}"
            )
        
        report_lines.extend([
            "",
            "RISK WARNINGS:",
        ])
        
        # Generate risk warnings
        warnings = []
        if risk_metrics['var_95'] < -0.20:
            warnings.append("⚠️ High downside risk: 95% VaR exceeds -20%")
        if risk_metrics['max_drawdown_95'] < -0.30:
            warnings.append("⚠️ Severe drawdown risk: 95th percentile exceeds -30%")
        if risk_metrics['prob_positive'] < 0.60:
            warnings.append("⚠️ Low probability of positive returns")
        if self.metadata['metrics']['portfolio_volatility'] > 0.25:
            warnings.append("⚠️ High portfolio volatility exceeds 25%")
        
        concentration_risk = self.portfolio_data['Portfolio_Weight'].max()
        if concentration_risk > 0.10:
            warnings.append(f"⚠️ High concentration risk: largest position {concentration_risk:.1%}")
        
        if not warnings:
            warnings.append("✅ No major risk warnings identified")
        
        report_lines.extend(warnings)
        
        # Join and print report
        report = "\n".join(report_lines)
        print(report)
        
        return report
    
    def save_results(self, risk_metrics: Dict, stress_results: Dict, report: str) -> str:
        """Save Monte Carlo analysis results."""
        print(f"\n💾 SAVING MONTE CARLO RESULTS")
        print("-" * 40)
        
        timestamp = date.today().strftime('%Y-%m-%d')
        
        # Create outputs directory
        base_output_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data_files')
        mc_dir = os.path.join(base_output_dir, 'monte_carlo_analysis')
        os.makedirs(mc_dir, exist_ok=True)
        
        # Save detailed results
        results_data = {
            'analysis_date': datetime.now().isoformat(),
            'simulation_parameters': {
                'num_simulations': self.num_simulations,
                'time_horizon_days': self.time_horizon_days,
                'portfolio_size': len(self.portfolio_data)
            },
            'risk_metrics': risk_metrics,
            'stress_test_results': stress_results,
            'portfolio_metadata': self.metadata
        }
        
        # Save JSON results
        json_path = os.path.join(mc_dir, f"05_monte_carlo_analysis_{timestamp}.json")
        with open(json_path, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        # Save summary CSV
        summary_data = [{
            'Analysis_Date': timestamp,
            'Portfolio_Size': len(self.portfolio_data),
            'Simulations': self.num_simulations,
            'Time_Horizon_Days': self.time_horizon_days,
            'Expected_Return': risk_metrics['expected_return'],
            'Volatility': risk_metrics['volatility'],
            'Sharpe_Ratio': risk_metrics['sharpe_ratio'],
            'VaR_95': risk_metrics['var_95'],
            'VaR_99': risk_metrics['var_99'],
            'Max_Drawdown_95': risk_metrics['max_drawdown_95'],
            'Prob_Positive': risk_metrics['prob_positive'],
            'Prob_Beat_Market': risk_metrics['prob_beat_market'],
            'Market_Regime': self.metadata.get('market_regime', 'N/A')
        }]
        
        csv_path = os.path.join(mc_dir, f"05_monte_carlo_summary_{timestamp}.csv")
        pd.DataFrame(summary_data).to_csv(csv_path, index=False)
        
        # Save report
        report_path = os.path.join(mc_dir, f"05_monte_carlo_report_{timestamp}.txt")
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"✅ Results saved:")
        print(f"   JSON: {os.path.basename(json_path)}")
        print(f"   CSV: {os.path.basename(csv_path)}")
        print(f"   Report: {os.path.basename(report_path)}")
        
        return mc_dir

def main():
    """Run Monte Carlo portfolio simulation."""
    try:
        print("🎲 MONTE CARLO PORTFOLIO SIMULATION")
        print("=" * 80)
        
        # Initialize simulator
        simulator = MonteCarloPortfolioSimulator(
            num_simulations=10000,
            time_horizon_days=252  # 1 year
        )
        
        # Load portfolio data
        if not simulator.load_portfolio_data():
            return False
        
        # Estimate correlations
        simulator.estimate_correlation_matrix()
        
        # Run Monte Carlo simulation
        simulation_results = simulator.run_monte_carlo_simulation()
        
        # Calculate risk metrics
        risk_metrics = simulator.calculate_risk_metrics()
        
        # Run stress tests
        stress_results = simulator.run_stress_tests()
        
        # Generate report
        report = simulator.generate_report(risk_metrics, stress_results)
        
        # Save results
        output_dir = simulator.save_results(risk_metrics, stress_results, report)
        
        print(f"\n✅ MONTE CARLO ANALYSIS COMPLETE!")
        print(f"📁 Results saved to: {os.path.basename(output_dir)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in Monte Carlo simulation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main() 