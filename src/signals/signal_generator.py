#!/usr/bin/env python3
"""
Quality Momentum Strategy - Signal Generation System

This module converts portfolio analysis into actionable trading signals for live execution.
Integrates with existing portfolio construction logic to generate real-time buy/sell signals.

Key Features:
- Real-time signal generation based on portfolio weights
- Position sizing with risk controls
- Signal validation and quality checks
- Integration with monthly rebalancing schedule
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Tuple, Optional

# Add src to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, os.path.join(project_root, 'src'))

class QualityMomentumSignalGenerator:
    """
    Generates trading signals based on Quality Momentum Strategy analysis.
    """
    
    def __init__(self, config_file: str = None):
        """Initialize signal generator with configuration."""
        self.config = self._load_config(config_file)
        self.setup_logging()
        
        # Signal generation parameters
        self.portfolio_file_pattern = "04_unified_portfolio_selection_*.csv"
        self.monte_carlo_pattern = "05_monte_carlo_analysis_*.json"
        self.min_position_size = self.config.get('min_position_size', 0.01)  # 1% minimum
        self.max_position_size = self.config.get('max_position_size', 0.05)  # 5% maximum
        self.rebalance_threshold = self.config.get('rebalance_threshold', 0.02)  # 2% drift
        
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration settings."""
        default_config = {
            'min_position_size': 0.01,
            'max_position_size': 0.05,
            'rebalance_threshold': 0.02,
            'max_portfolio_size': 50,
            'risk_budget': 0.15,  # 15% annual volatility target
            'cash_buffer': 0.05   # 5% cash buffer
        }
        
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(project_root, 'logs', 'signals.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_latest_portfolio(self) -> Optional[pd.DataFrame]:
        """Load the most recent portfolio analysis."""
        try:
            # Find latest portfolio file
            portfolio_dir = os.path.join(project_root, 'data', 'processed', 'portfolios')
            if not os.path.exists(portfolio_dir):
                portfolio_dir = os.path.join(project_root, 'data', 'processed')
            
            portfolio_files = [f for f in os.listdir(portfolio_dir) 
                             if f.startswith('04_unified_portfolio_selection_') and f.endswith('.csv')]
            
            if not portfolio_files:
                self.logger.error("No portfolio CSV files found")
                return None
            
            # Get most recent file based on date in filename
            latest_file = max(portfolio_files, key=lambda x: x.split('_')[-1].replace('.csv', ''))
            portfolio_path = os.path.join(portfolio_dir, latest_file)
            
            portfolio = pd.read_csv(portfolio_path)
            self.logger.info(f"Loaded portfolio: {latest_file} with {len(portfolio)} stocks")
            
            return portfolio
            
        except Exception as e:
            self.logger.error(f"Error loading portfolio: {e}")
            return None
    
    def load_monte_carlo_risk(self) -> Optional[Dict]:
        """Load Monte Carlo risk analysis."""
        try:
            # Find latest Monte Carlo file
            mc_dir = os.path.join(project_root, 'src', 'csv_data_files', 'monte_carlo_analysis')
            
            mc_files = [f for f in os.listdir(mc_dir) 
                       if f.startswith('05_monte_carlo_analysis_')]
            
            if not mc_files:
                self.logger.warning("No Monte Carlo files found")
                return None
            
            # Get most recent file
            latest_file = max(mc_files, key=lambda x: x.split('_')[-1].replace('.json', ''))
            mc_path = os.path.join(mc_dir, latest_file)
            
            with open(mc_path, 'r') as f:
                mc_data = json.load(f)
            
            self.logger.info(f"Loaded Monte Carlo analysis: {latest_file}")
            return mc_data
            
        except Exception as e:
            self.logger.error(f"Error loading Monte Carlo data: {e}")
            return None
    
    def calculate_target_weights(self, portfolio: pd.DataFrame) -> Dict[str, float]:
        """Calculate target portfolio weights based on analysis."""
        try:
            # Use existing portfolio weights as baseline
            if 'Portfolio_Weight' in portfolio.columns:
                weights = dict(zip(portfolio['Ticker'], portfolio['Portfolio_Weight']))
            elif 'weight' in portfolio.columns:
                weights = dict(zip(portfolio['ticker'], portfolio['weight']))
            elif 'portfolio_weight' in portfolio.columns:
                weights = dict(zip(portfolio['ticker'], portfolio['portfolio_weight']))
            else:
                # Equal weight if no weights specified
                equal_weight = 1.0 / len(portfolio)
                weights = {ticker: equal_weight for ticker in portfolio['Ticker']}
            
            # Apply position size constraints
            for ticker in weights:
                weights[ticker] = max(self.min_position_size, 
                                    min(self.max_position_size, weights[ticker]))
            
            # Normalize weights to sum to 1
            total_weight = sum(weights.values())
            if total_weight > 0:
                weights = {ticker: weight / total_weight for ticker, weight in weights.items()}
            
            # Apply cash buffer
            cash_buffer = self.config['cash_buffer']
            weights = {ticker: weight * (1 - cash_buffer) for ticker, weight in weights.items()}
            
            self.logger.info(f"Calculated target weights for {len(weights)} positions")
            return weights
            
        except Exception as e:
            self.logger.error(f"Error calculating target weights: {e}")
            return {}
    
    def generate_signals(self, current_positions: Dict[str, float] = None) -> Dict[str, Dict]:
        """
        Generate trading signals based on portfolio analysis.
        
        Args:
            current_positions: Current portfolio positions {ticker: weight}
        
        Returns:
            Dictionary of signals {ticker: {action, target_weight, signal_strength}}
        """
        self.logger.info("Generating trading signals...")
        
        try:
            # Load latest portfolio analysis
            portfolio = self.load_latest_portfolio()
            if portfolio is None:
                return {}
            
            # Load risk analysis
            risk_data = self.load_monte_carlo_risk()
            
            # Calculate target weights
            target_weights = self.calculate_target_weights(portfolio)
            
            if not target_weights:
                self.logger.error("No target weights calculated")
                return {}
            
            # Generate signals based on current vs target positions
            signals = {}
            current_positions = current_positions or {}
            
            # Get all tickers (current + target)
            all_tickers = set(list(current_positions.keys()) + list(target_weights.keys()))
            
            for ticker in all_tickers:
                current_weight = current_positions.get(ticker, 0.0)
                target_weight = target_weights.get(ticker, 0.0)
                
                weight_diff = target_weight - current_weight
                
                # Determine action based on weight difference and threshold
                if abs(weight_diff) < self.rebalance_threshold:
                    action = 'HOLD'
                    signal_strength = 0.0
                elif weight_diff > 0:
                    action = 'BUY' if current_weight == 0 else 'INCREASE'
                    signal_strength = min(1.0, abs(weight_diff) / self.max_position_size)
                else:
                    action = 'SELL' if target_weight == 0 else 'REDUCE'
                    signal_strength = min(1.0, abs(weight_diff) / self.max_position_size)
                
                # Add signal quality metrics
                quality_score = self._get_quality_score(ticker, portfolio)
                momentum_score = self._get_momentum_score(ticker, portfolio)
                
                signals[ticker] = {
                    'action': action,
                    'current_weight': current_weight,
                    'target_weight': target_weight,
                    'weight_change': weight_diff,
                    'signal_strength': signal_strength,
                    'quality_score': quality_score,
                    'momentum_score': momentum_score,
                    'timestamp': datetime.now().isoformat()
                }
            
            self.logger.info(f"Generated {len(signals)} signals")
            
            # Log signal summary
            buy_signals = sum(1 for s in signals.values() if s['action'] in ['BUY', 'INCREASE'])
            sell_signals = sum(1 for s in signals.values() if s['action'] in ['SELL', 'REDUCE'])
            hold_signals = sum(1 for s in signals.values() if s['action'] == 'HOLD')
            
            self.logger.info(f"Signal summary - Buy/Increase: {buy_signals}, "
                           f"Sell/Reduce: {sell_signals}, Hold: {hold_signals}")
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")
            return {}
    
    def _get_quality_score(self, ticker: str, portfolio: pd.DataFrame) -> float:
        """Get quality score for a ticker from portfolio analysis."""
        try:
            ticker_data = portfolio[portfolio['Ticker'] == ticker]
            if len(ticker_data) == 0:
                return 0.0
            
            # Use quality metrics if available
            if 'Quality Score' in ticker_data.columns:
                return float(ticker_data['Quality Score'].iloc[0])
            elif 'quality_score' in ticker_data.columns:
                return float(ticker_data['quality_score'].iloc[0])
            elif 'ROIC' in ticker_data.columns:
                # Calculate basic quality score from ROIC
                roic = ticker_data['ROIC'].iloc[0]
                return min(1.0, max(0.0, roic / 20.0))  # Normalize ROIC to 0-1
            
            return 0.5  # Default neutral score
            
        except Exception:
            return 0.5
    
    def _get_momentum_score(self, ticker: str, portfolio: pd.DataFrame) -> float:
        """Get momentum score for a ticker from portfolio analysis."""
        try:
            ticker_data = portfolio[portfolio['Ticker'] == ticker]
            if len(ticker_data) == 0:
                return 0.0
            
            # Use momentum metrics if available
            if 'Momentum Score' in ticker_data.columns:
                return float(ticker_data['Momentum Score'].iloc[0])
            elif 'momentum_score' in ticker_data.columns:
                return float(ticker_data['momentum_score'].iloc[0])
            elif '3M Return' in ticker_data.columns:
                # Calculate basic momentum score from 3M return
                return_3m = ticker_data['3M Return'].iloc[0]
                return min(1.0, max(0.0, (return_3m + 0.5) / 2.0))  # Normalize to 0-1
            
            return 0.5  # Default neutral score
            
        except Exception:
            return 0.5
    
    def validate_signals(self, signals: Dict[str, Dict]) -> Dict[str, Dict]:
        """Validate and filter signals based on quality checks."""
        self.logger.info("Validating signals...")
        
        validated_signals = {}
        
        for ticker, signal in signals.items():
            # Skip signals with low quality scores
            if signal['quality_score'] < 0.3:
                self.logger.warning(f"Skipping {ticker} due to low quality score: {signal['quality_score']}")
                continue
            
            # Skip very small position changes
            if abs(signal['weight_change']) < 0.005:  # Less than 0.5%
                continue
            
            # Apply risk checks
            if signal['action'] in ['BUY', 'INCREASE']:
                if signal['target_weight'] > self.max_position_size:
                    self.logger.warning(f"Reducing {ticker} target weight from {signal['target_weight']:.3f} "
                                      f"to {self.max_position_size:.3f}")
                    signal['target_weight'] = self.max_position_size
                    signal['weight_change'] = signal['target_weight'] - signal['current_weight']
            
            validated_signals[ticker] = signal
        
        self.logger.info(f"Validated {len(validated_signals)} signals from {len(signals)} candidates")
        return validated_signals
    
    def save_signals(self, signals: Dict[str, Dict], output_file: str = None):
        """Save signals to file for execution."""
        try:
            if output_file is None:
                timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
                output_file = os.path.join(project_root, 'data', 'signals', f'signals_{timestamp}.json')
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Add metadata
            signal_data = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'total_signals': len(signals),
                    'config': self.config
                },
                'signals': signals
            }
            
            with open(output_file, 'w') as f:
                json.dump(signal_data, f, indent=2)
            
            self.logger.info(f"Signals saved to: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving signals: {e}")

def main():
    """Main function for testing signal generation."""
    print("🔄 Quality Momentum Strategy - Signal Generation")
    print("=" * 60)
    
    # Initialize signal generator
    generator = QualityMomentumSignalGenerator()
    
    # Example current positions (empty for initial run)
    current_positions = {}
    
    # Generate signals
    signals = generator.generate_signals(current_positions)
    
    if signals:
        # Validate signals
        validated_signals = generator.validate_signals(signals)
        
        # Save signals
        generator.save_signals(validated_signals)
        
        # Display summary
        print(f"\n📊 Signal Generation Summary:")
        print(f"Total signals generated: {len(signals)}")
        print(f"Validated signals: {len(validated_signals)}")
        
        # Show top signals
        buy_signals = {k: v for k, v in validated_signals.items() 
                      if v['action'] in ['BUY', 'INCREASE']}
        sell_signals = {k: v for k, v in validated_signals.items() 
                       if v['action'] in ['SELL', 'REDUCE']}
        
        print(f"\n🟢 Buy/Increase signals: {len(buy_signals)}")
        for ticker, signal in sorted(buy_signals.items(), 
                                   key=lambda x: x[1]['signal_strength'], reverse=True)[:5]:
            print(f"  {ticker}: {signal['action']} (Target: {signal['target_weight']:.3f}, "
                  f"Strength: {signal['signal_strength']:.2f})")
        
        print(f"\n🔴 Sell/Reduce signals: {len(sell_signals)}")
        for ticker, signal in sorted(sell_signals.items(), 
                                   key=lambda x: x[1]['signal_strength'], reverse=True)[:5]:
            print(f"  {ticker}: {signal['action']} (Target: {signal['target_weight']:.3f}, "
                  f"Strength: {signal['signal_strength']:.2f})")
        
        print(f"\n✅ Signals ready for execution!")
    else:
        print("❌ No signals generated")

if __name__ == "__main__":
    main() 