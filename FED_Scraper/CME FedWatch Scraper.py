import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime

def parse_date(date_str):
    if not date_str:
        return None
    try:
        # Convert "April 2025" to datetime
        return pd.to_datetime(date_str, format="%B %Y")
    except:
        return None

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
            
            # Get PCE Inflation with exact class combination
            inflation_element = await page.query_selector('span._bold_1sxcz_1._smaller_1sxcz_11')
            if inflation_element:
                inflation_rate = await inflation_element.text_content()
                # Get the date which is in the next span
                date_element = await page.query_selector('span._date_1sxcz_17')
                if date_element:
                    inflation_date = await date_element.text_content()
                else:
                    inflation_date = None
                print(f"Found Inflation: {inflation_rate} ({inflation_date})")
            else:
                print("Inflation element not found")
                inflation_rate = "Not found"
                inflation_date = None
            
            # Get Unemployment Rate with exact class combination (same structure as PCE)
            unemployment_element = await page.query_selector('div.homepageBox:has-text("Unemployment Rate") span._bold_1sxcz_1._smaller_1sxcz_11')
            if unemployment_element:
                unemployment_rate = await unemployment_element.text_content()
                # Get the date which is in the next span
                date_element = await page.query_selector('div.homepageBox:has-text("Unemployment Rate") span._date_1sxcz_17')
                if date_element:
                    unemployment_date = await date_element.text_content()
                else:
                    unemployment_date = None
                print(f"Found Unemployment: {unemployment_rate} ({unemployment_date})")
            else:
                print("Unemployment element not found")
                unemployment_rate = "Not found"
                unemployment_date = None
            
            # Create DataFrame with separate value and date columns
            data = {
                'Metric': ['Fed Funds Target Range', 'PCE Inflation', 'Unemployment Rate'],
                'Value': [fed_funds_rate, inflation_rate, unemployment_rate],
                'Forecast Date': [None, inflation_date, unemployment_date],  # Fed Funds has no forecast date
                'Scrape Timestamp': [datetime.now()] * 3
            }
            df = pd.DataFrame(data)
            
            # Convert the Forecast Date column to datetime
            df['Forecast Date'] = df['Forecast Date'].apply(parse_date)
            
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