from selenium import webdriver
import time
import random
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load URLs from environment variable (handles multiline format with backslashes)
urls_raw = os.getenv('URLS', '')
if urls_raw:
    # Split by whitespace and filter out empty strings and backslashes
    URLS = [url.strip() for url in urls_raw.split() if url.strip() and url.strip() != '\\']
else:
    URLS = []

# Load authentication cookies from environment variables
COOKIES = {
    "cf_clearance": os.getenv('COOKIE_CF_CLEARANCE'),
    "sec_bs": os.getenv('COOKIE_SEC_BS'),
    "sec_id": os.getenv('COOKIE_SEC_ID'),
    "sec_ts": os.getenv('COOKIE_SEC_TS')
}

def setup_brave():
    """Setup Brave browser with Selenium"""
    # Set up Brave browser options
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/brave-browser"  # Adjust this path if needed
    
    # Add any additional options if needed
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Create the driver
    driver = webdriver.Chrome(options=options)
    return driver

def add_cookies(driver):
    """Add authentication cookies to the browser"""
    # First visit the site to set domain for cookies
    driver.get("https://rateyourmusic.com")
    time.sleep(2)  # Wait for page to load
    
    # Add each cookie
    for name, value in COOKIES.items():
        cookie = {
            'name': name,
            'value': value,
            'domain': '.rateyourmusic.com'
        }
        driver.add_cookie(cookie)

def download_pages():
    """Download all pages from the URLs list"""
    # Create saved_pages directory if it doesn't exist
    save_dir = Path("/home/alex/Code/python/rym-release-tracker/saved_pages")
    save_dir.mkdir(exist_ok=True)
    
    driver = setup_brave()
    try:
        # Add authentication cookies
        add_cookies(driver)
        
        # Download each page
        for i, url in enumerate(URLS, 1):
            try:
                print(f"Downloading page {i} of {len(URLS)}: {url}")
                
                # Load the page
                driver.get(url)
                
                # Wait for page to load (adjust timeout if needed)
                time.sleep(random.uniform(3, 5))
                
                # Generate a filename based on the URL
                filename = f"page_{i}_{int(time.time())}.mhtml"
                filepath = save_dir / filename
                
                # Save page as MHTML
                # This requires Chrome DevTools Protocol
                cdp = driver.execute_cdp_cmd('Page.captureSnapshot', {})
                
                # Save the MHTML content
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(cdp['data'])
                
                print(f"Saved to {filepath}")
                
                # Random delay between requests
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"Error downloading {url}: {e}")
                continue
                
    finally:
        driver.quit()

if __name__ == "__main__":
    download_pages() 