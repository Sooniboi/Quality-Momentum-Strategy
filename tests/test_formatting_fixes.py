#!/usr/bin/env python3

import sys
import os
from pathlib import Path

def test_formatting_fixes():
    """Test that all formatting issues have been resolved."""
    print("🔄 Testing LaTeX Formatting Fixes...")
    print("=" * 60)
    
    try:
        # Check the latest generated LaTeX file
        latex_file = Path("reports/weekly/latex/weekly_performance_report_2025_06_04.tex")
        
        if not latex_file.exists():
            print("❌ LaTeX file not found")
            return False
        
        with open(latex_file, 'r') as f:
            content = f.read()
        
        # Test 1: Check for proper sector mapping (no "Unknown")
        unknown_count = content.count('Unknown')
        print(f"📊 Test 1 - Sector Mapping:")
        print(f"  • 'Unknown' sectors found: {unknown_count}")
        print(f"  • Result: {'✅ PASS' if unknown_count == 0 else '❌ FAIL'}")
        
        # Test 2: Check for scientific notation (e+ or E+)
        scientific_notation = 'e+' in content.lower() or 'e-' in content.lower()
        print(f"\n🔬 Test 2 - Scientific Notation:")
        print(f"  • Scientific notation found: {scientific_notation}")
        print(f"  • Result: {'✅ PASS' if not scientific_notation else '❌ FAIL'}")
        
        # Test 3: Check for proper portfolio value
        portfolio_value_correct = "99,855" in content
        print(f"\n💰 Test 3 - Portfolio Value:")
        print(f"  • Correct portfolio value (99,855): {portfolio_value_correct}")
        print(f"  • Result: {'✅ PASS' if portfolio_value_correct else '❌ FAIL'}")
        
        # Test 4: Check for cash position inclusion
        cash_position = "CASH" in content and "24,379" in content
        print(f"\n💵 Test 4 - Cash Position:")
        print(f"  • Cash position included: {cash_position}")
        print(f"  • Result: {'✅ PASS' if cash_position else '❌ FAIL'}")
        
        # Test 5: Check for sector variety (not all same sector)
        sectors = ['Industrials', 'Healthcare', 'Technology', 'Financials', 'Energy', 'Consumer']
        sector_count = sum(1 for sector in sectors if sector in content)
        print(f"\n🏭 Test 5 - Sector Diversity:")
        print(f"  • Different sectors found: {sector_count}/6")
        print(f"  • Result: {'✅ PASS' if sector_count >= 4 else '❌ FAIL'}")
        
        # Test 6: Check coordinate formatting (no decimals with lots of zeros)
        bad_coordinates = content.count('.000') > 5  # Some decimals are OK, but not many .000
        print(f"\n📈 Test 6 - Chart Coordinates:")
        print(f"  • Excessive .000 decimals: {bad_coordinates}")
        print(f"  • Result: {'✅ PASS' if not bad_coordinates else '❌ FAIL'}")
        
        # Overall result
        all_tests = [
            unknown_count == 0,
            not scientific_notation,
            portfolio_value_correct,
            cash_position,
            sector_count >= 4,
            not bad_coordinates
        ]
        
        passed_tests = sum(all_tests)
        print(f"\n🎯 Overall Results:")
        print(f"  • Tests Passed: {passed_tests}/6")
        print(f"  • Overall: {'✅ ALL TESTS PASSED!' if all(all_tests) else '⚠️ SOME ISSUES REMAIN'}")
        
        return all(all_tests)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_formatting_fixes()
    sys.exit(0 if success else 1) 