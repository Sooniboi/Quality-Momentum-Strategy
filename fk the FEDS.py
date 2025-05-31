import requests
from bs4 import BeautifulSoup

# URL of the Federal Reserve website (assuming this is the homepage or a relevant page)
url = "https://www.federalreserve.gov"

# Send a GET request to the website
try:
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for bad status codes
except requests.RequestException as e:
    print(f"Error fetching URL: {e}")
    exit()

# Parse the HTML content
soup = BeautifulSoup(response.text, "html.parser")

# Dictionary to store scraped data
data = {
    "Policy Rate": None,
    "Fed Funds Target Range": None,
    "Inflation (PCE)": None,
    "Unemployment Rate": None
}

# Scrape Fed Funds Target Range
fed_funds_element = soup.find("p", class_="_bold_1sxcz_1")
if fed_funds_element:
    data["Fed Funds Target Range"] = fed_funds_element.text.strip()
    # Check if this is under "Policy Rate" header
    parent_h3 = fed_funds_element.find_previous("h3", class_="homepageHeader")
    if parent_h3 and "Policy Rate" in parent_h3.text:
        data["Policy Rate"] = data["Fed Funds Target Range"]

# Scrape other values (Inflation (PCE), Unemployment Rate) by looking for similar homepageBox structures
homepage_boxes = soup.find_all("div", class_="homepageBox")
for box in homepage_boxes:
    header = box.find("h3", class_="homepageHeader")
    if header:
        header_text = header.text.strip()
        # Look for Inflation (PCE)
        if "Inflation (PCE)" in header_text:
            value = box.find("p", class_="_bold_1sxcz_1")
            if value:
                data["Inflation (PCE)"] = value.text.strip()
        # Look for Unemployment Rate
        if "Unemployment Rate" in header_text:
            value = box.find("p", class_="_bold_1sxcz_1")
            if value:
                data["Unemployment Rate"] = value.text.strip()

# Print the scraped data
for key, value in data.items():
    print(f"{key}: {value if value else 'Not found'}")