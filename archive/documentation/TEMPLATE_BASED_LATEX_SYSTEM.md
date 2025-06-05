# Template-Based LaTeX Report Generation System

## Overview

The Quality Momentum Strategy now uses a robust **template-based approach** for generating weekly LaTeX reports instead of dynamically generating LaTeX code each week. This is much more reliable, maintainable, and efficient for production use.

## How It Works

### 1. Static Template Creation
- **One-time setup**: Creates a static LaTeX template with placeholders
- **Template file**: `reports/weekly/latex/weekly_report_template.tex`
- **Placeholders**: Use `{{PLACEHOLDER_NAME}}` format for dynamic content

### 2. Weekly Data Population
- **Fresh data**: Collects current week's performance data
- **Placeholder replacement**: Automatically populates template with live data
- **Output generation**: Creates dated report file (e.g., `weekly_performance_report_2025_06_02.tex`)

## Key Advantages

### ✅ **Reliability**
- Template is validated once and reused
- No risk of LaTeX syntax errors from dynamic generation
- Consistent formatting across all reports

### ✅ **Performance** 
- Fast execution - just string replacement
- No complex LaTeX code generation logic
- Efficient memory usage

### ✅ **Maintainability**
- Easy to modify report layout in template
- Clear separation of data and presentation
- Version controlled template changes

### ✅ **Debugging**
- Template issues are caught early
- Data population errors are isolated
- Easy to test with mock data

## Template Structure

```latex
\documentclass[11pt,letterpaper]{article}
% ... preamble ...

\title{Quality Momentum Strategy \\ 
        Weekly Performance Report \\
        Week of {{WEEK_START}} to {{WEEK_END}}}

\begin{document}

\section*{Executive Summary}
\begin{itemize}
    \item \textbf{Current Market Regime:} {{CURRENT_REGIME}} ({{REGIME_CONFIDENCE}}\% confidence)
    \item \textbf{Trading Recommendation:} \textcolor{{{RECOMMENDATION_COLOR}}}{{{TRADING_RECOMMENDATION}}}
    \item \textbf{Portfolio Positions:} {{PORTFOLIO_POSITIONS}} holdings
    \item \textbf{Total Portfolio Value:} \${{PORTFOLIO_VALUE}}
\end{itemize}

% ... more sections with placeholders ...

\end{document}
```

## Available Placeholders

### Date/Time Information
- `{{WEEK_START}}` - Start date of trading week
- `{{WEEK_END}}` - End date of trading week  
- `{{REPORT_DATE}}` - Report generation timestamp
- `{{TEMPLATE_VERSION}}` - Template version number

### Market Regime Analysis
- `{{CURRENT_REGIME}}` - Current market regime name
- `{{REGIME_CONFIDENCE}}` - Confidence percentage
- `{{TRADING_RECOMMENDATION}}` - PROCEED/CAUTION/HALT
- `{{RECOMMENDATION_COLOR}}` - LaTeX color for recommendation
- `{{REGIME_DESCRIPTION}}` - Detailed regime description
- `{{REGIME_STABILITY_TEXT}}` - Stability analysis

### Portfolio Information
- `{{PORTFOLIO_POSITIONS}}` - Number of holdings
- `{{PORTFOLIO_VALUE}}` - Total portfolio value (formatted)
- `{{WEEKLY_PERFORMANCE}}` - Weekly return percentage
- `{{TOP_HOLDINGS_TABLE}}` - LaTeX table of top positions
- `{{STYLE_ALLOCATION_TEXT}}` - Style breakdown
- `{{SECTOR_ALLOCATION_TEXT}}` - Sector allocation

### Risk Management
- `{{VAR_95}}` - Value at Risk (95% confidence)
- `{{SHARPE_RATIO}}` - Portfolio Sharpe ratio
- `{{MONTE_CARLO_SUMMARY}}` - Monte Carlo analysis results

### Trading & Economic Data
- `{{RECENT_ORDERS_SUMMARY}}` - Trading activity summary
- `{{TRADING_SIGNALS_SUMMARY}}` - Signal analysis
- `{{ECONOMIC_INDICATORS_SUMMARY}}` - Key economic metrics
- `{{THIS_WEEK_EVENTS}}` - Number of economic events
- `{{UPCOMING_EVENTS_SUMMARY}}` - Next week's calendar

### Additional Sections
- `{{INVESTMENT_OPPORTUNITIES_SUMMARY}}` - Screening results
- `{{BENCHMARK_COMPARISON}}` - vs IJR performance
- `{{CHART_FIGURES}}` - LaTeX figure code for charts
- `{{NEXT_WEEK_OUTLOOK}}` - Forward-looking analysis

## Implementation Details

### Core Methods

#### `create_latex_template()` 
Creates the static template file with placeholders.

```python
def create_latex_template(self) -> str:
    """Create a static LaTeX template with placeholders for dynamic data."""
    template_file = self.latex_dir / "weekly_report_template.tex"
    
    if template_file.exists():
        return str(template_file)
    
    # Template content with {{PLACEHOLDERS}}
    template_content = r"""
    \documentclass[11pt,letterpaper]{article}
    % ... full template content ...
    """
    
    with open(template_file, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    return str(template_file)
```

#### `populate_latex_template()`
Populates template with fresh data.

```python
def populate_latex_template(self, template_path: str, performance_data: Dict) -> str:
    """Populate the LaTeX template with fresh data."""
    
    # Read template
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Extract data for placeholders
    placeholders = self._extract_template_data(performance_data)
    
    # Replace placeholders
    for placeholder, value in placeholders.items():
        template_content = template_content.replace(f"{{{{{placeholder}}}}}", str(value))
    
    # Write populated report
    output_file = self.latex_dir / f"weekly_performance_report_{date_str}.tex"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    return str(output_file)
```

#### `_extract_template_data()`
Extracts and formats data for all placeholders.

```python
def _extract_template_data(self, performance_data: Dict) -> Dict[str, str]:
    """Extract and format data for template placeholders."""
    
    placeholders = {
        'WEEK_START': performance_data.get('week_start', 'N/A'),
        'CURRENT_REGIME': regime_name.replace('_', '\\_'),
        'PORTFOLIO_POSITIONS': str(portfolio.get('total_positions', 0)),
        # ... extract all placeholder data ...
    }
    
    return placeholders
```

## Testing the System

Run the test script to verify the template system:

```bash
python test_template_system.py
```

### Test Output Example
```
🧪 Testing Template-Based LaTeX Report Generation System
============================================================

📝 Step 1: Creating LaTeX Template...
✅ Template created successfully: reports/weekly/latex/weekly_report_template.tex
📏 Template size: 4,856 bytes

📊 Step 2: Creating Mock Performance Data...
✅ Mock data created with 12 sections

🔄 Step 3: Populating Template with Mock Data...
✅ Template populated successfully: reports/weekly/latex/weekly_performance_report_2025_06_02.tex
📏 Populated report size: 4,923 bytes
✅ All placeholders successfully replaced

🔍 Step 4: Testing Data Extraction...
✅ Extracted 25 placeholders
   ✓ CURRENT_REGIME: HIGH\_INFLATION
   ✓ PORTFOLIO_POSITIONS: 39
   ✓ TRADING_RECOMMENDATION: PROCEED
```

## Production Workflow

### Weekly Report Generation
1. **Data Collection**: `collect_performance_data()` gathers fresh data
2. **Template Population**: `populate_latex_template()` creates report
3. **PDF Compilation**: `compile_latex_to_pdf()` generates final PDF
4. **Email Delivery**: `send_email_report()` distributes report

### Maintenance Tasks
- **Template Updates**: Modify template file as needed
- **Placeholder Addition**: Add new placeholders for enhanced data
- **Version Control**: Track template changes in git
- **Testing**: Validate template with mock data

## Migration Benefits

### Before (Dynamic Generation)
- ❌ Complex LaTeX code generation logic
- ❌ Prone to syntax errors
- ❌ Difficult to debug formatting issues
- ❌ Performance overhead from string building

### After (Template-Based)
- ✅ Simple placeholder replacement
- ✅ Template validated once
- ✅ Easy debugging and maintenance  
- ✅ Fast and reliable execution

## Error Handling

The system includes comprehensive error handling:

```python
try:
    # Template operations
    template_path = self.create_latex_template()
    populated_report = self.populate_latex_template(template_path, data)
    
except Exception as e:
    self.logger.error(f"❌ Template system error: {e}")
    # Fallback to basic report generation
```

## Future Enhancements

### Template Versioning
- Multiple template versions for different report types
- A/B testing of template layouts
- Rollback capability for template changes

### Advanced Placeholders
- Conditional sections based on data availability
- Loop constructs for dynamic table generation
- Mathematical calculations within templates

### Template Library
- Quarterly report templates
- Monthly summary templates
- Special event report templates

## Conclusion

The new template-based LaTeX system provides a robust, maintainable, and efficient approach to generating weekly performance reports. By separating data collection from presentation logic, we've created a system that's both reliable for production use and easy to maintain and enhance over time.

Key benefits:
- **Reliability**: No more LaTeX syntax errors
- **Performance**: Fast placeholder replacement
- **Maintainability**: Clear separation of concerns
- **Flexibility**: Easy template modifications
- **Testability**: Mock data validation 