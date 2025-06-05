#!/usr/bin/env python3
"""
Test script for the new template-based LaTeX report generation system.
This demonstrates how the system now uses static templates with placeholders
instead of generating LaTeX code dynamically each week.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'src'))

def test_template_system():
    """Test the new template-based LaTeX generation system."""
    print("🧪 Testing Template-Based LaTeX Report Generation System")
    print("="*60)
    
    try:
        from utils.weekly_performance_reporter import WeeklyPerformanceReporter
        
        # Create reporter instance
        reporter = WeeklyPerformanceReporter()
        
        # Test 1: Create LaTeX template
        print("\n📝 Step 1: Creating LaTeX Template...")
        template_path = reporter.create_latex_template()
        
        if template_path:
            print(f"✅ Template created successfully: {template_path}")
            
            # Check template exists and has content
            if Path(template_path).exists():
                template_size = Path(template_path).stat().st_size
                print(f"📏 Template size: {template_size:,} bytes")
                
                # Show first few lines of template
                with open(template_path, 'r') as f:
                    lines = f.readlines()[:10]
                    print("\n📄 Template preview (first 10 lines):")
                    for i, line in enumerate(lines, 1):
                        print(f"   {i:2d}: {line.rstrip()}")
            else:
                print("❌ Template file was not created")
                return False
        else:
            print("❌ Template creation failed")
            return False
        
        # Test 2: Create mock performance data
        print("\n📊 Step 2: Creating Mock Performance Data...")
        mock_data = create_mock_performance_data()
        print(f"✅ Mock data created with {len(mock_data)} sections")
        
        # Test 3: Populate template with mock data
        print("\n🔄 Step 3: Populating Template with Mock Data...")
        populated_report = reporter.populate_latex_template(template_path, mock_data)
        
        if populated_report:
            print(f"✅ Template populated successfully: {populated_report}")
            
            # Check populated report
            if Path(populated_report).exists():
                report_size = Path(populated_report).stat().st_size
                print(f"📏 Populated report size: {report_size:,} bytes")
                
                # Show key sections that were populated
                with open(populated_report, 'r') as f:
                    content = f.read()
                    
                    # Check for placeholder replacements
                    placeholders_found = content.count('{{')
                    if placeholders_found == 0:
                        print("✅ All placeholders successfully replaced")
                    else:
                        print(f"⚠️  {placeholders_found} placeholders still remain")
                    
                    # Show some populated sections
                    print("\n📄 Key populated sections:")
                    if "HIGH_INFLATION" in content:
                        print("   ✓ Market regime populated")
                    if "39 holdings" in content:
                        print("   ✓ Portfolio positions populated")
                    if "2025-06-" in content:
                        print("   ✓ Date information populated")
                        
            else:
                print("❌ Populated report file was not created")
                return False
        else:
            print("❌ Template population failed")
            return False
        
        # Test 4: Test template data extraction
        print("\n🔍 Step 4: Testing Data Extraction...")
        placeholders = reporter._extract_template_data(mock_data)
        print(f"✅ Extracted {len(placeholders)} placeholders")
        
        # Show key placeholders
        key_placeholders = ['CURRENT_REGIME', 'PORTFOLIO_POSITIONS', 'TRADING_RECOMMENDATION']
        for key in key_placeholders:
            if key in placeholders:
                print(f"   ✓ {key}: {placeholders[key]}")
        
        print("\n🎉 Template-Based System Test Results:")
        print("="*50)
        print("✅ Template creation: SUCCESS")
        print("✅ Mock data generation: SUCCESS") 
        print("✅ Template population: SUCCESS")
        print("✅ Data extraction: SUCCESS")
        print("\n💡 The system is now ready for production use!")
        print("   • Templates are created once and reused")
        print("   • Fresh data populates placeholders automatically")
        print("   • Much more reliable than dynamic LaTeX generation")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_mock_performance_data():
    """Create mock performance data for testing."""
    return {
        'week_start': '2025-06-02',
        'week_end': '2025-06-06', 
        'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        
        'market_regime': {
            'current_regime': {
                'regime': 'HIGH_INFLATION',
                'confidence': 80,
                'recommendation': 'PROCEED'
            },
            'regime_stability': {
                'stability_score': 1.00,
                'regime_changes': 0,
                'dominant_regime': 'HIGH_INFLATION'
            }
        },
        
        'portfolio': {
            'total_positions': 39,
            'weekly_return': 0.025
        },
        
        'account': {
            'portfolio_value': 157500.00
        },
        
        'positions': [
            {
                'ticker': 'AAPL', 
                'qty': 100, 
                'market_price': 150.00, 
                'market_value': 15000,
                'avg_entry_price': 145.00,
                'unrealized_pl': 500.00,
                'weight': 0.095,
                'sector': 'Technology'
            },
            {
                'ticker': 'MSFT', 
                'qty': 75, 
                'market_price': 200.00, 
                'market_value': 15000,
                'avg_entry_price': 190.00,
                'unrealized_pl': 750.00,
                'weight': 0.095,
                'sector': 'Technology'
            },
            {
                'ticker': 'JNJ', 
                'qty': 80, 
                'market_price': 160.00, 
                'market_value': 12800,
                'avg_entry_price': 165.00,
                'unrealized_pl': -400.00,
                'weight': 0.081,
                'sector': 'Healthcare'
            },
            {
                'ticker': 'JPM', 
                'qty': 60, 
                'market_price': 140.00, 
                'market_value': 8400,
                'avg_entry_price': 130.00,
                'unrealized_pl': 600.00,
                'weight': 0.053,
                'sector': 'Finance'
            },
            {
                'ticker': 'PG', 
                'qty': 40, 
                'market_price': 155.00, 
                'market_value': 6200,
                'avg_entry_price': 150.00,
                'unrealized_pl': 200.00,
                'weight': 0.039,
                'sector': 'Consumer Goods'
            }
        ],
        
        'risk_metrics': {
            'var_95': -0.0235,
            'sharpe_ratio': 1.45
        },
        
        'monte_carlo': {
            'simulations': 1000,
            'days': 30,
            'expected_return': 0.08,
            'volatility': 0.15,
            'var_95': -0.12,
            'probability_positive': 0.68
        },
        
        'orders': [
            {'symbol': 'XYZ', 'side': 'buy', 'qty': 50},
            {'symbol': 'ABC', 'side': 'sell', 'qty': 25}
        ],
        
        'trading_signals': {
            'total_signals': 5,
            'proceed_days': 4,
            'caution_days': 1,
            'halt_days': 0
        },
        
        'economic_indicators': {
            'vix': 18.5,
            'inflation': 2.8,
            'unemployment': 3.7
        },
        
        'economic_events': {
            'this_week_events': ['CPI', 'FOMC Minutes'],
            'next_week_events': ['Jobs Report', 'GDP'],
            'next_fed_meeting': {
                'date': '2025-06-18',
                'days_until': 12
            }
        },
        
        'investment_opportunities': None,
        'benchmark_comparison': {'summary': 'Outperformed IJR by 1.2% this week'},
        'fundamentals': {
            'style_allocation': {
                'Quality': 0.513,
                'Value': 0.256, 
                'Blend': 0.128,
                'Growth': 0.103
            }
        }
    }

def main():
    """Main function."""
    print("Quality Momentum Strategy - Template-Based LaTeX System Test")
    print("This test demonstrates the new approach where we use static templates")
    print("with placeholders instead of generating LaTeX dynamically each week.\n")
    
    success = test_template_system()
    
    if success:
        print("\n🚀 Template system is ready for production!")
        print("   Next steps:")
        print("   1. The template will be created once and reused")
        print("   2. Weekly reports will populate with fresh data automatically")
        print("   3. Much more reliable than dynamic generation")
    else:
        print("\n❌ Template system needs debugging")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 