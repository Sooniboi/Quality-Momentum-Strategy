import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime

async def scrape_fed_data():
    try:
        print("Starting Playwright...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            print("Navigating to Federal Reserve website...")
            await page.goto("https://www.federalreserve.gov")
            await page.wait_for_load_state('networkidle')
            
            # Get Fed Funds Target Range using exact class name
            fed_funds_element = await page.query_selector('p._bold_1sxcz_1')
            if fed_funds_element:
                fed_funds_rate = await fed_funds_element.text_content()
                print(f"Found Fed Funds Rate: {fed_funds_rate}")
            else:
                print("Fed Funds Rate element not found")
                fed_funds_rate = "Not found"
            
            # Get PCE Inflation from card structure
            inflation_element = await page.query_selector('div.mb75.homepageBox >> text=Inflation (PCE)')
            if inflation_element:
                parent_card = await inflation_element.evaluate('element => element.closest(".card")')
                if parent_card:
                    inflation_text = await parent_card.text_content()
                    print(f"Found Inflation text: {inflation_text}")
            else:
                print("Inflation element not found")
                inflation_text = "Not found"
            
            # Get Unemployment Rate from card structure
            unemployment_element = await page.query_selector('div.mb75.homepageBox >> text=Unemployment Rate')
            if unemployment_element:
                parent_card = await unemployment_element.evaluate('element => element.closest(".card")')
                if parent_card:
                    unemployment_text = await parent_card.text_content()
                    print(f"Found Unemployment text: {unemployment_text}")
            else:
                print("Unemployment element not found")
                unemployment_text = "Not found"
            
            # Take screenshot for debugging
            await page.screenshot(path='debug_screenshot.png')
            print("\nSaved debug screenshot to debug_screenshot.png")
            
            # Print the HTML structure around the elements for debugging
            html_content = await page.content()
            print("\nRelevant HTML structure:")
            print(html_content[:1000])
            
            # Create DataFrame
            data = {
                'Metric': ['Fed Funds Target Range', 'PCE Inflation', 'Unemployment Rate'],
                'Value': [fed_funds_rate, inflation_text, unemployment_text],
                'Date Scraped': [datetime.now()] * 3
            }
            df = pd.DataFrame(data)
            
            print("\nScraped Data:")
            print("=" * 50)
            print(df)
            
            # Save to CSV
            filename = f'fed_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            df.to_csv(filename, index=False)
            print(f"\nData saved to {filename}")
            
            await browser.close()
            return df
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print(f"Error type: {type(e)}")
        print(f"Error location: {e.__traceback__.tb_lineno}")
        return None

if __name__ == "__main__":
    print("Starting Fed data scraper...")
    asyncio.run(scrape_fed_data())