import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import time

async def scrape_fedwatch_table():
    try:
        print("Starting Playwright...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-http2', '--no-sandbox']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            print("Navigating to webpage...")
            await page.goto("https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html", timeout=30000)
            
            print("Waiting for page to load...")
            await page.wait_for_timeout(10000)
            
            # Debug: Print page content
            content = await page.content()
            print("Page HTML content:")
            print(content[:1000])  # Print first 1000 characters for debugging
            
            print("\nLooking for target rates and probabilities...")
            
            # Find all elements containing the target rates (425-450)
            rate_elements = await page.query_selector_all('text="425-450"')
            print(f"Found {len(rate_elements)} rate elements")
            
            # Find all elements containing percentage values
            percentage_elements = await page.query_selector_all('text=/\\d+\\.\\d+%/')
            print(f"Found {len(percentage_elements)} percentage elements")
            
            # Extract and print all found values
            print("\nFound values:")
            for element in rate_elements:
                text = await element.text_content()
                print(f"Rate: {text}")
            
            for element in percentage_elements:
                text = await element.text_content()
                print(f"Percentage: {text}")
            
            # Take a screenshot for debugging
            await page.screenshot(path='debug_screenshot.png')
            print("\nSaved debug screenshot to debug_screenshot.png")
            
            # Close browser
            await browser.close()
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print(f"Error type: {type(e)}")
        return None

if __name__ == "__main__":
    print("Starting scraper...")
    asyncio.run(scrape_fedwatch_table())