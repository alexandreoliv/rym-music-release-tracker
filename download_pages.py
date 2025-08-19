from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urljoin

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

def get_next_page_url(driver, current_url):
    """Extract the next page URL from the navigation if it exists"""
    try:
        # Wait for page to load and find navigation
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Look for the navigation div with id="nav_bottom"
        nav_div = driver.find_element(By.ID, "nav_bottom")
        
        # Find the "next" link with class "navlinknext"
        next_link = nav_div.find_element(By.CLASS_NAME, "navlinknext")
        next_url = next_link.get_attribute("href")
        
        if next_url:
            # Convert relative URL to absolute if needed
            return urljoin(current_url, next_url)
        
    except (TimeoutException, NoSuchElementException):
        # No next page found
        pass
    
    return None

def download_single_page(driver, url, page_counter, save_dir):
    """Download a single page and save it"""
    try:
        print(f"Downloading page {page_counter}: {url}")
        
        # Load the page
        driver.get(url)
        
        # Wait for page to load (adjust timeout if needed)
        time.sleep(random.uniform(3, 5))
        
        # Generate a filename based on the URL and counter
        filename = f"page_{page_counter}_{int(time.time())}.mhtml"
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
        
        return True
        
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def process_list_url(driver, base_url, page_counter, save_dir):
    """Process a list URL and all its pagination pages"""
    current_url = base_url
    pages_downloaded = 0
    
    while current_url:
        # Download current page
        success = download_single_page(driver, current_url, page_counter, save_dir)
        if success:
            pages_downloaded += 1
            page_counter += 1
        
        # Look for next page
        next_url = get_next_page_url(driver, current_url)
        
        if next_url and next_url != current_url:
            current_url = next_url
            print(f"Found next page: {next_url}")
        else:
            print(f"No more pages found for {base_url}")
            break
    
    return page_counter, pages_downloaded

def download_pages():
    """Download all pages from the URLs list"""
    # Create saved_pages directory if it doesn't exist
    save_dir = Path("/home/alex/Code/python/rym-release-tracker/saved_pages")
    save_dir.mkdir(exist_ok=True)
    
    driver = setup_brave()
    page_counter = 1
    total_pages_downloaded = 0
    
    try:
        # Add authentication cookies
        add_cookies(driver)
        
        # Download each URL
        for i, url in enumerate(URLS, 1):
            try:
                print(f"\n=== Processing URL {i} of {len(URLS)} ===")
                
                if "/list/" in url:
                    # Handle list URL with pagination
                    print(f"Detected list URL, will process all pages: {url}")
                    page_counter, pages_downloaded = process_list_url(driver, url, page_counter, save_dir)
                    total_pages_downloaded += pages_downloaded
                    print(f"Downloaded {pages_downloaded} pages for list: {url}")
                else:
                    # Handle single page URL
                    success = download_single_page(driver, url, page_counter, save_dir)
                    if success:
                        total_pages_downloaded += 1
                        page_counter += 1
                
            except Exception as e:
                print(f"Error processing {url}: {e}")
                continue
        
        print("\n=== Download Complete ===")
        print(f"Total pages downloaded: {total_pages_downloaded}")
                
    finally:
        driver.quit()

if __name__ == "__main__":
    download_pages() 