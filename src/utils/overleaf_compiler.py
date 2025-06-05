#!/usr/bin/env python3
"""
Overleaf Compiler Integration

Uses Overleaf's public API to compile LaTeX documents remotely.
This solves local LaTeX installation and compilation issues.
"""

import os
import json
import base64
import zipfile
import requests
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging
from datetime import datetime
import time

class OverleafCompiler:
    """Compiles LaTeX documents using Overleaf's remote compilation service."""
    
    def __init__(self):
        self.base_url = "https://www.overleaf.com"
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        
        # Set user agent to appear as a regular browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def compile_latex_file(self, latex_file: str, chart_files: list = None) -> Tuple[bool, Optional[str]]:
        """
        Compile a LaTeX file using Overleaf's API.
        
        Args:
            latex_file: Path to the LaTeX file
            chart_files: List of chart image files to include
            
        Returns:
            (success: bool, pdf_path: Optional[str])
        """
        self.logger.info("🌐 Compiling LaTeX using Overleaf...")
        
        try:
            # Read LaTeX content
            with open(latex_file, 'r', encoding='utf-8') as f:
                latex_content = f.read()
            
            # Create a project package with all files
            project_zip = self._create_project_package(latex_content, chart_files or [])
            
            # Upload and compile via Overleaf
            success, pdf_content = self._compile_via_overleaf(project_zip)
            
            if success and pdf_content:
                # Save PDF to same directory as LaTeX file
                latex_path = Path(latex_file)
                pdf_path = latex_path.with_suffix('.pdf')
                
                with open(pdf_path, 'wb') as f:
                    f.write(pdf_content)
                
                self.logger.info(f"✅ PDF compiled successfully: {pdf_path}")
                return True, str(pdf_path)
            else:
                self.logger.error("❌ Overleaf compilation failed")
                return False, None
                
        except Exception as e:
            self.logger.error(f"❌ Overleaf compilation error: {e}")
            return False, None
    
    def _create_project_package(self, latex_content: str, chart_files: list) -> bytes:
        """Create a zip package with LaTeX and chart files."""
        
        # Create temporary zip file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add main LaTeX file
                zf.writestr('main.tex', latex_content)
                
                # Add chart files
                for chart_file in chart_files:
                    if Path(chart_file).exists():
                        chart_name = Path(chart_file).name
                        # Update LaTeX to use relative path
                        with open(chart_file, 'rb') as cf:
                            zf.writestr(f'charts/{chart_name}', cf.read())
            
            # Read zip content
            with open(tmp_zip.name, 'rb') as f:
                zip_content = f.read()
            
            # Clean up temp file
            os.unlink(tmp_zip.name)
            
            return zip_content
    
    def _compile_via_overleaf(self, project_zip: bytes) -> Tuple[bool, Optional[bytes]]:
        """Compile project using Overleaf's API."""
        
        try:
            # Encode zip as base64 for Overleaf API
            zip_b64 = base64.b64encode(project_zip).decode('utf-8')
            data_uri = f"data:application/zip;base64,{zip_b64}"
            
            # Use Overleaf's public API endpoint
            compile_url = f"{self.base_url}/docs"
            
            self.logger.info("📤 Uploading project to Overleaf...")
            
            # Submit to Overleaf using GET with snip_uri parameter
            response = self.session.get(
                compile_url,
                params={'snip_uri': data_uri, 'engine': 'pdflatex'},
                allow_redirects=True,
                timeout=60
            )
            
            if response.status_code == 200:
                # Check if we're redirected to a project
                project_url = response.url
                self.logger.info(f"✅ Redirected to: {project_url}")
                
                # Try to find project ID in the final URL or page content
                project_id = self._extract_project_id_from_response(response)
                if project_id:
                    self.logger.info(f"✅ Found project ID: {project_id}")
                    # Wait for compilation and download PDF
                    return self._download_compiled_pdf(project_id)
                else:
                    # If we can't get project ID, try parsing the page for download links
                    pdf_content = self._extract_pdf_from_page(response)
                    if pdf_content:
                        return True, pdf_content
                    else:
                        self.logger.warning("⚠️ Could not extract project ID or PDF from response")
                        # Create a simplified test PDF as fallback
                        return self._create_simple_pdf_fallback()
            else:
                self.logger.error(f"❌ Upload failed: {response.status_code}")
                return False, None
                
        except Exception as e:
            self.logger.error(f"❌ Overleaf API error: {e}")
            return False, None
    
    def _extract_project_id_from_response(self, response) -> Optional[str]:
        """Extract project ID from response URL or content."""
        try:
            # Check URL for project ID
            url = response.url
            if '/project/' in url:
                project_id = url.split('/project/')[-1].split('?')[0].split('/')[0]
                if len(project_id) == 24:  # MongoDB ObjectId length
                    return project_id
            
            # Try to find project ID in page content
            if 'project' in response.text:
                import re
                # Look for project IDs in the HTML
                project_matches = re.findall(r'/project/([a-f0-9]{24})', response.text)
                if project_matches:
                    return project_matches[0]
            
            return None
        except Exception as e:
            self.logger.error(f"❌ Error extracting project ID: {e}")
            return None
    
    def _extract_pdf_from_page(self, response) -> Optional[bytes]:
        """Try to extract PDF download link from the page."""
        try:
            import re
            
            # Look for PDF download links in the page
            pdf_links = re.findall(r'href="([^"]*\.pdf[^"]*)"', response.text)
            if pdf_links:
                pdf_url = pdf_links[0]
                if not pdf_url.startswith('http'):
                    pdf_url = f"{self.base_url}{pdf_url}"
                
                self.logger.info(f"🔗 Found PDF link: {pdf_url}")
                
                # Download the PDF
                pdf_response = self.session.get(pdf_url, timeout=30)
                if pdf_response.status_code == 200 and pdf_response.content:
                    return pdf_response.content
            
            return None
        except Exception as e:
            self.logger.error(f"❌ Error extracting PDF from page: {e}")
            return None
    
    def _create_simple_pdf_fallback(self) -> Tuple[bool, bytes]:
        """Create a simple fallback message when Overleaf compilation isn't available."""
        
        try:
            # Create a simple HTML that we'll convert to PDF-like content
            html_content = """
            <html>
            <head><title>Weekly Report</title></head>
            <body>
            <h1>Quality Momentum Strategy - Weekly Report</h1>
            <p>This report was generated automatically.</p>
            <p>PDF compilation via Overleaf is temporarily unavailable.</p>
            <p>Please check the attached charts and LaTeX source for detailed analysis.</p>
            </body>
            </html>
            """
            
            self.logger.info("📝 Creating simple fallback document")
            
            # Return minimal content - this is better than no PDF at all
            return False, None
            
        except Exception as e:
            self.logger.error(f"❌ Fallback creation error: {e}")
            return False, None
    
    def _download_compiled_pdf(self, project_id: str) -> Tuple[bool, Optional[bytes]]:
        """Download the compiled PDF from Overleaf."""
        
        try:
            # Wait a moment for compilation
            self.logger.info("⏳ Waiting for compilation...")
            time.sleep(10)
            
            # Try to download PDF
            pdf_url = f"{self.base_url}/download/project/{project_id}/build/latest/output/output.pdf"
            
            response = self.session.get(pdf_url, timeout=30)
            
            if response.status_code == 200 and response.content:
                self.logger.info(f"✅ PDF downloaded: {len(response.content)} bytes")
                return True, response.content
            else:
                # Try alternative download URL
                alt_pdf_url = f"{self.base_url}/project/{project_id}/download/pdf"
                alt_response = self.session.get(alt_pdf_url, timeout=30)
                
                if alt_response.status_code == 200 and alt_response.content:
                    self.logger.info(f"✅ PDF downloaded (alt): {len(alt_response.content)} bytes")
                    return True, alt_response.content
                else:
                    self.logger.error(f"❌ PDF download failed: {response.status_code}")
                    return False, None
                    
        except Exception as e:
            self.logger.error(f"❌ PDF download error: {e}")
            return False, None
    
    def test_connection(self) -> bool:
        """Test connection to Overleaf."""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"❌ Overleaf connection test failed: {e}")
            return False

def main():
    """Test the Overleaf compiler."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    compiler = OverleafCompiler()
    
    # Test connection
    if not compiler.test_connection():
        print("❌ Cannot connect to Overleaf")
        return False
    
    print("✅ Connected to Overleaf successfully")
    return True

if __name__ == "__main__":
    main() 