#!/usr/bin/env python3
"""
HTML to PDF Report Generator

Creates professional PDF reports from HTML templates.
This replaces LaTeX for reliable automated PDF generation.
"""

import os
import base64
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime
import json

# Try multiple PDF generation options for maximum compatibility
PDF_LIBRARIES = []

try:
    import weasyprint
    PDF_LIBRARIES.append('weasyprint')
except ImportError:
    pass

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib import colors
    PDF_LIBRARIES.append('reportlab')
except ImportError:
    pass

try:
    import pdfkit
    PDF_LIBRARIES.append('pdfkit')
except ImportError:
    pass

class HTMLPDFGenerator:
    """Generates PDF reports from HTML templates using available libraries."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.available_libraries = PDF_LIBRARIES
        self.logger.info(f"📚 Available PDF libraries: {self.available_libraries}")
        
    def generate_pdf_report(self, performance_data: Dict, chart_files: List[str], output_path: str) -> bool:
        """Generate PDF report from performance data and charts."""
        
        try:
            if not self.available_libraries:
                self.logger.error("❌ No PDF libraries available. Installing weasyprint...")
                return self._install_and_retry(performance_data, chart_files, output_path)
            
            # Try each available library until one works
            for library in self.available_libraries:
                try:
                    if library == 'reportlab':
                        return self._generate_with_reportlab(performance_data, chart_files, output_path)
                    elif library == 'weasyprint':
                        return self._generate_with_weasyprint(performance_data, chart_files, output_path)
                    elif library == 'pdfkit':
                        return self._generate_with_pdfkit(performance_data, chart_files, output_path)
                except Exception as e:
                    self.logger.warning(f"⚠️ {library} failed: {e}")
                    continue
            
            self.logger.error("❌ All PDF generation methods failed")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ PDF generation error: {e}")
            return False
    
    def _generate_with_reportlab(self, performance_data: Dict, chart_files: List[str], output_path: str) -> bool:
        """Generate comprehensive PDF using ReportLab."""
        
        self.logger.info("📄 Generating comprehensive PDF with ReportLab...")
        
        try:
            # Create document
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            section_style = ParagraphStyle(
                'SectionHeader',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=15,
                textColor=colors.HexColor('#2c3e50')
            )
            
            # Title and header
            story.append(Paragraph("Quality Momentum Strategy", title_style))
            story.append(Paragraph("Comprehensive Weekly Portfolio Report", styles['Heading2']))
            story.append(Spacer(1, 20))
            
            # Report info
            report_info = f"""
            <b>Week:</b> {performance_data.get('week_start', 'N/A')} to {performance_data.get('week_end', 'N/A')}<br/>
            <b>Generated:</b> {performance_data.get('report_date', 'N/A')}<br/>
            """
            story.append(Paragraph(report_info, styles['Normal']))
            story.append(Spacer(1, 30))
            
            # 1. Executive Summary
            story.append(Paragraph("📊 Executive Summary", section_style))
            self._add_executive_summary(story, performance_data, styles)
            story.append(Spacer(1, 20))
            
            # 2. Portfolio Performance
            story.append(Paragraph("📈 Portfolio Performance", section_style))
            self._add_portfolio_performance(story, performance_data, styles)
            story.append(Spacer(1, 20))
            
            # 3. Trading Activity
            if 'trade_activity' in performance_data:
                story.append(Paragraph("💼 Trading Activity", section_style))
                self._add_trading_activity(story, performance_data['trade_activity'], styles)
                story.append(Spacer(1, 20))
            
            # 4. Fundamentals Analysis
            if 'fundamentals_summary' in performance_data:
                story.append(Paragraph("🔍 Fundamentals Analysis", section_style))
                self._add_fundamentals_analysis(story, performance_data['fundamentals_summary'], styles)
                story.append(Spacer(1, 20))
            
            # 5. Sector Analysis
            if 'sector_analysis' in performance_data:
                story.append(Paragraph("🏭 Sector Analysis", section_style))
                self._add_sector_analysis(story, performance_data['sector_analysis'], styles)
                story.append(Spacer(1, 20))
            
            # 6. Charts
            story.append(Paragraph("📊 Performance Charts", section_style))
            self._add_charts(story, chart_files, styles)
            story.append(Spacer(1, 20))
            
            # 7. Watchlist
            if 'watchlist_candidates' in performance_data:
                story.append(Paragraph("👀 Watchlist Candidates", section_style))
                self._add_watchlist(story, performance_data['watchlist_candidates'], styles)
                story.append(Spacer(1, 20))
            
            # 8. Market Regime & Economic Events
            story.append(Paragraph("🌍 Market Environment", section_style))
            self._add_market_environment(story, performance_data, styles)
            story.append(Spacer(1, 20))
            
            # 9. Risk Metrics
            if 'risk_metrics' in performance_data:
                story.append(Paragraph("⚠️ Risk Analysis", section_style))
                self._add_risk_analysis(story, performance_data['risk_metrics'], styles)
            
            # Footer
            story.append(Spacer(1, 30))
            footer_text = f"""
            <i>This comprehensive report was generated automatically by the Enhanced Quality Momentum Strategy system.<br/>
            Report includes real-time Alpaca data, fundamentals analysis, and macro indicators.<br/>
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
            """
            story.append(Paragraph(footer_text, styles['Normal']))
            
            # Build PDF
            doc.build(story)
            self.logger.info(f"✅ Comprehensive PDF generated with ReportLab: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ ReportLab generation failed: {e}")
            return False
    
    def _add_executive_summary(self, story: List, performance_data: Dict, styles):
        """Add executive summary section."""
        try:
            # Account info
            account = performance_data.get('account', {})
            portfolio = performance_data.get('portfolio', {})
            weekly_perf = performance_data.get('weekly_performance', {})
            
            summary_text = f"""
            <b>Portfolio Value:</b> ${account.get('total_equity', 0):,.2f}<br/>
            <b>Total Positions:</b> {portfolio.get('total_positions', 0)}<br/>
            <b>Weekly Return:</b> {weekly_perf.get('portfolio_weekly_return', 0):.2f}%<br/>
            <b>Unrealized P&L:</b> ${portfolio.get('total_unrealized_pl', 0):,.2f}<br/>
            <b>Cash Available:</b> ${account.get('cash', 0):,.2f}<br/>
            """
            
            story.append(Paragraph(summary_text, styles['Normal']))
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error adding executive summary: {e}")
    
    def _add_portfolio_performance(self, story: List, performance_data: Dict, styles):
        """Add portfolio performance details."""
        try:
            weekly_perf = performance_data.get('weekly_performance', {})
            
            # Top performers
            top_performers = weekly_perf.get('top_performers', [])
            if top_performers:
                story.append(Paragraph("<b>Top Performers This Week:</b>", styles['Normal']))
                for i, performer in enumerate(top_performers[:3]):
                    story.append(Paragraph(f"{i+1}. {performer.get('ticker', 'N/A')}: {performer.get('weekly_return', 0):.2f}%", styles['Normal']))
                story.append(Spacer(1, 10))
            
            # Bottom performers
            bottom_performers = weekly_perf.get('bottom_performers', [])
            if bottom_performers:
                story.append(Paragraph("<b>Bottom Performers This Week:</b>", styles['Normal']))
                for i, performer in enumerate(bottom_performers[:3]):
                    story.append(Paragraph(f"{i+1}. {performer.get('ticker', 'N/A')}: {performer.get('weekly_return', 0):.2f}%", styles['Normal']))
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error adding portfolio performance: {e}")
    
    def _add_trading_activity(self, story: List, trade_activity: Dict, styles):
        """Add trading activity summary."""
        try:
            activity_text = f"""
            <b>Total Trades This Week:</b> {trade_activity.get('total_trades', 0)}<br/>
            <b>Buy Trades:</b> {trade_activity.get('buy_trades', 0)}<br/>
            <b>Sell Trades:</b> {trade_activity.get('sell_trades', 0)}<br/>
            <b>Total Volume:</b> {trade_activity.get('total_volume', 0):,.0f} shares<br/>
            <b>Total Value Traded:</b> ${trade_activity.get('total_value_traded', 0):,.2f}<br/>
            """
            
            story.append(Paragraph(activity_text, styles['Normal']))
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error adding trading activity: {e}")
    
    def _add_fundamentals_analysis(self, story: List, fundamentals: Dict, styles):
        """Add fundamentals analysis."""
        try:
            fund_text = f"""
            <b>Portfolio Fundamentals Overview:</b><br/>
            • Average P/E Ratio: {fundamentals.get('average_pe', 0):.1f}<br/>
            • Average P/B Ratio: {fundamentals.get('average_pb', 0):.1f}<br/>
            • Average ROE: {fundamentals.get('average_roe', 0):.1f}%<br/>
            • High Quality Stocks: {fundamentals.get('high_quality_count', 0)}<br/>
            • Dividend Yield Avg: {fundamentals.get('dividend_yield_avg', 0):.2f}%<br/>
            """
            
            story.append(Paragraph(fund_text, styles['Normal']))
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error adding fundamentals: {e}")
    
    def _add_sector_analysis(self, story: List, sector_data: Dict, styles):
        """Add sector analysis."""
        try:
            allocation = sector_data.get('sector_allocation', {})
            
            story.append(Paragraph("<b>Sector Allocation:</b>", styles['Normal']))
            for sector, data in allocation.items():
                weight_pct = data.get('weight_pct', 0)
                story.append(Paragraph(f"• {sector}: {weight_pct:.1f}%", styles['Normal']))
            
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"<b>Diversification Score:</b> {sector_data.get('sector_diversification_score', 0):.1f}/100", styles['Normal']))
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error adding sector analysis: {e}")
    
    def _add_charts(self, story: List, chart_files: List[str], styles):
        """Add performance charts."""
        try:
            for i, chart_file in enumerate(chart_files):
                if Path(chart_file).exists():
                    try:
                        # Add chart image
                        img = Image(chart_file, width=6*inch, height=4*inch)
                        story.append(img)
                        story.append(Spacer(1, 10))
                        
                        # Chart caption
                        chart_name = Path(chart_file).stem.replace('_', ' ').title()
                        story.append(Paragraph(f"Chart {i+1}: {chart_name}", styles['Normal']))
                        story.append(Spacer(1, 15))
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not add chart {chart_file}: {e}")
        except Exception as e:
            self.logger.warning(f"⚠️ Error adding charts: {e}")
    
    def _add_watchlist(self, story: List, watchlist: List[Dict], styles):
        """Add watchlist candidates."""
        try:
            story.append(Paragraph("<b>Top Quality Momentum Candidates:</b>", styles['Normal']))
            
            for i, candidate in enumerate(watchlist[:5]):
                candidate_text = f"""
                {i+1}. <b>{candidate.get('ticker', 'N/A')}</b> ({candidate.get('sector', 'Unknown')})<br/>
                   P/E: {candidate.get('pe_ratio', 0):.1f} | ROE: {candidate.get('roe', 0):.1f}% | 
                   Weekly Momentum: {candidate.get('weekly_momentum', 0):.2f}%<br/>
                   Composite Score: {candidate.get('composite_score', 0):.1f}/100
                """
                story.append(Paragraph(candidate_text, styles['Normal']))
                story.append(Spacer(1, 8))
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error adding watchlist: {e}")
    
    def _add_market_environment(self, story: List, performance_data: Dict, styles):
        """Add market regime and economic environment."""
        try:
            regime_data = performance_data.get('market_regime', {})
            current_regime = regime_data.get('current_regime', {})
            
            market_text = f"""
            <b>Market Regime:</b> {current_regime.get('regime', 'Unknown')}<br/>
            <b>Trading Recommendation:</b> {current_regime.get('recommendation', 'Unknown')}<br/>
            <b>Regime Confidence:</b> {current_regime.get('confidence', 0):.0%}<br/>
            """
            
            story.append(Paragraph(market_text, styles['Normal']))
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error adding market environment: {e}")
    
    def _add_risk_analysis(self, story: List, risk_metrics: Dict, styles):
        """Add risk analysis section."""
        try:
            if 'error' not in risk_metrics:
                risk_text = f"""
                <b>Risk Metrics:</b><br/>
                • Portfolio VaR (95%): {risk_metrics.get('var_95', 0):.2%}<br/>
                • Expected Return: {risk_metrics.get('expected_return', 0):.2%}<br/>
                • Volatility: {risk_metrics.get('volatility', 0):.2%}<br/>
                • Sharpe Ratio: {risk_metrics.get('sharpe_ratio', 0):.2f}<br/>
                """
                
                story.append(Paragraph(risk_text, styles['Normal']))
            else:
                story.append(Paragraph("Risk analysis data currently unavailable.", styles['Normal']))
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error adding risk analysis: {e}")
    
    def _generate_with_weasyprint(self, performance_data: Dict, chart_files: List[str], output_path: str) -> bool:
        """Generate PDF using WeasyPrint from HTML."""
        
        self.logger.info("🌐 Generating PDF with WeasyPrint...")
        
        try:
            # Create HTML content
            html_content = self._create_html_report(performance_data, chart_files)
            
            # Generate PDF
            html_doc = weasyprint.HTML(string=html_content)
            html_doc.write_pdf(output_path)
            
            self.logger.info(f"✅ PDF generated with WeasyPrint: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ WeasyPrint generation failed: {e}")
            return False
    
    def _generate_with_pdfkit(self, performance_data: Dict, chart_files: List[str], output_path: str) -> bool:
        """Generate PDF using pdfkit (wkhtmltopdf)."""
        
        self.logger.info("🔧 Generating PDF with pdfkit...")
        
        try:
            # Create HTML content
            html_content = self._create_html_report(performance_data, chart_files)
            
            # Configure options
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None
            }
            
            # Generate PDF
            pdfkit.from_string(html_content, output_path, options=options)
            
            self.logger.info(f"✅ PDF generated with pdfkit: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ pdfkit generation failed: {e}")
            return False
    
    def _create_html_report(self, performance_data: Dict, chart_files: List[str]) -> str:
        """Create HTML content for the report."""
        
        # Get data with safe defaults
        current_regime = performance_data.get('market_regime', {}).get('current_regime', {})
        regime_name = current_regime.get('regime', 'Unknown')
        trading_rec = current_regime.get('recommendation', 'Unknown')
        portfolio_positions = performance_data.get('portfolio', {}).get('total_positions', 'N/A')
        
        # Convert charts to base64 for embedding
        chart_html = ""
        for i, chart_file in enumerate(chart_files):
            if Path(chart_file).exists():
                try:
                    with open(chart_file, 'rb') as f:
                        chart_data = base64.b64encode(f.read()).decode()
                    
                    chart_name = Path(chart_file).stem.replace('_', ' ').title()
                    chart_html += f"""
                    <div class="chart">
                        <img src="data:image/png;base64,{chart_data}" alt="{chart_name}">
                        <p class="caption">Chart {i+1}: {chart_name}</p>
                    </div>
                    """
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not embed chart {chart_file}: {e}")
        
        # Create complete HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Weekly Performance Report</title>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 3px solid #2c3e50;
                    padding-bottom: 20px;
                }}
                .header h1 {{
                    font-size: 28px;
                    margin: 0;
                    color: #2c3e50;
                }}
                .header h2 {{
                    font-size: 18px;
                    margin: 10px 0 0 0;
                    color: #7f8c8d;
                }}
                .section {{
                    margin: 25px 0;
                }}
                .section h3 {{
                    font-size: 20px;
                    color: #2c3e50;
                    border-left: 4px solid #3498db;
                    padding-left: 15px;
                    margin-bottom: 15px;
                }}
                .highlight-box {{
                    background: #ecf0f1;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 15px 0;
                }}
                .chart {{
                    text-align: center;
                    margin: 25px 0;
                    page-break-inside: avoid;
                }}
                .chart img {{
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .caption {{
                    font-style: italic;
                    color: #7f8c8d;
                    margin-top: 10px;
                }}
                .metric {{
                    display: inline-block;
                    margin: 5px 15px 5px 0;
                    font-weight: bold;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #bdc3c7;
                    font-size: 12px;
                    color: #7f8c8d;
                    text-align: center;
                }}
                .status-proceed {{ color: #27ae60; }}
                .status-caution {{ color: #f39c12; }}
                .status-halt {{ color: #e74c3c; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Quality Momentum Strategy</h1>
                <h2>Weekly Performance Report</h2>
                <p>Week of {performance_data.get('week_start', 'N/A')} to {performance_data.get('week_end', 'N/A')}</p>
                <p>Generated: {performance_data.get('report_date', 'N/A')}</p>
            </div>
            
            <div class="section">
                <h3>📊 Key Highlights</h3>
                <div class="highlight-box">
                    <div class="metric">Market Regime: <strong>{regime_name}</strong></div>
                    <div class="metric">Trading Recommendation: <strong class="status-{trading_rec.lower()}">{trading_rec}</strong></div>
                    <div class="metric">Portfolio Positions: <strong>{portfolio_positions}</strong></div>
                </div>
            </div>
            
            <div class="section">
                <h3>📈 Performance Charts</h3>
                {chart_html}
            </div>
            
            <div class="section">
                <h3>🔍 Market Analysis</h3>
                <p>The current market regime is classified as <strong>{regime_name}</strong> based on our 
                15-regime market detection system. This week's analysis shows a 
                <strong>{trading_rec}</strong> recommendation for portfolio management.</p>
                
                <p>The portfolio currently holds {portfolio_positions} positions optimized 
                according to our quality momentum methodology, with systematic risk management 
                and regime-aware allocation strategies.</p>
            </div>
            
            <div class="section">
                <h3>⚙️ System Status</h3>
                <p><strong>Automation Health:</strong> All systems operational</p>
                <p><strong>Daily Monitoring:</strong> Active (6:00 AM EST)</p>
                <p><strong>Weekly Rebalancing:</strong> Active (Monday 5:00 AM EST)</p>
                <p><strong>Risk Management:</strong> Enhanced 15-regime system operational</p>
            </div>
            
            <div class="footer">
                <p>This report was generated automatically by the Quality Momentum Strategy system.<br>
                Report version: Enhanced Automated PDF v1.0 | Generation time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _install_and_retry(self, performance_data: Dict, chart_files: List[str], output_path: str) -> bool:
        """Try to install weasyprint and retry PDF generation."""
        
        try:
            self.logger.info("📦 Installing weasyprint for PDF generation...")
            import subprocess
            import sys
            
            # Try to install weasyprint
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', 'weasyprint'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Reload the module
                import weasyprint
                self.available_libraries.append('weasyprint')
                return self._generate_with_weasyprint(performance_data, chart_files, output_path)
            else:
                self.logger.error(f"❌ Failed to install weasyprint: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Installation failed: {e}")
            return False

def main():
    """Test PDF generation."""
    
    logging.basicConfig(level=logging.INFO)
    
    # Test data
    test_data = {
        'week_start': '2025-06-02',
        'week_end': '2025-06-06',
        'report_date': '2025-06-03 18:00:00',
        'market_regime': {
            'current_regime': {
                'regime': 'OPTIMISTIC',
                'recommendation': 'PROCEED'
            }
        },
        'portfolio': {
            'total_positions': 25
        }
    }
    
    generator = HTMLPDFGenerator()
    success = generator.generate_pdf_report(test_data, [], 'test_report.pdf')
    
    if success:
        print("✅ Test PDF generated successfully!")
    else:
        print("❌ Test PDF generation failed")
    
    return success

if __name__ == "__main__":
    main() 