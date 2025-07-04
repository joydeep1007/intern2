"""
Simplified and Robust Alibaba RFQ Scraper
Focuses on extracting available data from Alibaba RFQ listings
"""

import time
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleAlibabaRFQScraper:
    def __init__(self):
        """Initialize the scraper"""
        self.driver = None
        self.data = []
        self.base_url = "https://sourcing.alibaba.com/rfq/rfq_search_list.htm"
        
    def setup_driver(self):
        """Setup Chrome driver with anti-detection options"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Chrome driver setup successfully")
            return True
        except Exception as e:
            logger.error(f"Error setting up driver: {e}")
            return False
    
    def safe_extract_text(self, element, default=""):
        """Safely extract text from an element"""
        try:
            return element.get_text(strip=True) if element else default
        except:
            return default
    
    def safe_extract_attribute(self, element, attr, default=""):
        """Safely extract attribute from an element"""
        try:
            return element.get(attr, default) if element else default
        except:
            return default
    
    def extract_data_from_page_source(self):
        """Extract RFQ data from current page source"""
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            rfq_data_list = []
            
            # Try different selectors to find RFQ containers
            possible_containers = [
                soup.find_all('div', class_=re.compile(r'item|rfq|list', re.I)),
                soup.find_all('tr'),
                soup.find_all('li', class_=re.compile(r'item|rfq', re.I)),
                soup.find_all('div', {'data-tracelog': True}),
                soup.find_all('a', href=re.compile(r'rfq', re.I))
            ]
            
            all_elements = []
            for container_list in possible_containers:
                all_elements.extend(container_list)
            
            logger.info(f"Found {len(all_elements)} potential RFQ elements")
            
            for i, element in enumerate(all_elements):
                try:
                    # Extract any text that looks like an RFQ
                    element_text = self.safe_extract_text(element)
                    
                    # Skip if element is too small or doesn't look like an RFQ
                    if len(element_text) < 20:
                        continue
                    
                    # Initialize data structure
                    rfq_data = {
                        'RFQ_ID': f"RFQ_{i+1}_{int(time.time())}",  # Generate unique ID
                        'Title': '',
                        'Buyer_Name': '',
                        'Buyer_Image': '',
                        'Inquiry_Time': '',
                        'Quotes_Left': '',
                        'Country': '',
                        'Quantity_Required': '',
                        'Email_Confirmed': 'No',
                        'Experienced': 'No',
                        'Completed': 'No',
                        'Typical_Reply': 'No',
                        'Interactive': 'No',
                        'Inquiry_URL': '',
                        'Inquiry_Date': '',
                        'Scraping_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Extract title (look for prominent text or links)
                    title_candidates = [
                        element.find('a', href=re.compile(r'rfq', re.I)),
                        element.find('h1'), element.find('h2'), element.find('h3'), element.find('h4'),
                        element.find('div', class_=re.compile(r'title', re.I)),
                        element.find('span', class_=re.compile(r'title', re.I))
                    ]
                    
                    for title_elem in title_candidates:
                        if title_elem:
                            title_text = self.safe_extract_text(title_elem)
                            if len(title_text) > 5:  # Reasonable title length
                                rfq_data['Title'] = title_text[:200]  # Limit length
                                
                                # If it's a link, extract URL
                                if title_elem.name == 'a':
                                    href = self.safe_extract_attribute(title_elem, 'href')
                                    if href:
                                        if href.startswith('http'):
                                            rfq_data['Inquiry_URL'] = href
                                        elif href.startswith('/'):
                                            rfq_data['Inquiry_URL'] = f"https://sourcing.alibaba.com{href}"
                                break
                    
                    # Extract buyer information
                    buyer_patterns = [
                        r'from[:\s]*([^,\n]+)',
                        r'buyer[:\s]*([^,\n]+)',
                        r'company[:\s]*([^,\n]+)'
                    ]
                    
                    for pattern in buyer_patterns:
                        match = re.search(pattern, element_text, re.I)
                        if match:
                            rfq_data['Buyer_Name'] = match.group(1).strip()[:100]
                            break
                    
                    # Extract country
                    country_pattern = r'\b([A-Z]{2,3}|United States|China|India|Germany|France|UK|UAE|Australia|Canada|Brazil|Japan|South Korea)\b'
                    country_match = re.search(country_pattern, element_text)
                    if country_match:
                        rfq_data['Country'] = country_match.group(1)
                    
                    # Extract quantity
                    quantity_patterns = [
                        r'(\d+[\s,]*\d*)\s*(pieces?|units?|boxes?|bags?|kgs?|tons?|meters?|yards?)',
                        r'quantity[:\s]*(\d+[\s,]*\d*\s*\w+)',
                        r'need[:\s]*(\d+[\s,]*\d*\s*\w+)'
                    ]
                    
                    for pattern in quantity_patterns:
                        match = re.search(pattern, element_text, re.I)
                        if match:
                            rfq_data['Quantity_Required'] = match.group(0).strip()[:50]
                            break
                    
                    # Extract time information
                    time_patterns = [
                        r'(\d+)\s*(hours?|days?|minutes?)\s*(ago|before)',
                        r'(yesterday|today|last week)',
                        r'(\d{1,2}\/\d{1,2}\/\d{2,4})'
                    ]
                    
                    for pattern in time_patterns:
                        match = re.search(pattern, element_text, re.I)
                        if match:
                            rfq_data['Inquiry_Time'] = match.group(0).strip()
                            break
                    
                    # Extract quotes left
                    quotes_match = re.search(r'(\d+)\s*quotes?\s*left', element_text, re.I)
                    if quotes_match:
                        rfq_data['Quotes_Left'] = quotes_match.group(1)
                    
                    # Look for verification badges
                    element_text_lower = element_text.lower()
                    if any(keyword in element_text_lower for keyword in ['verified', 'confirmed', 'email']):
                        rfq_data['Email_Confirmed'] = 'Yes'
                    
                    if any(keyword in element_text_lower for keyword in ['experienced', 'expert', '+ years']):
                        rfq_data['Experienced'] = 'Yes'
                    
                    # Only add if we found meaningful data
                    if rfq_data['Title'] or len(element_text) > 50:
                        # If no title found, use first 100 chars of text as title
                        if not rfq_data['Title']:
                            rfq_data['Title'] = element_text[:100].replace('\n', ' ').strip()
                        
                        rfq_data_list.append(rfq_data)
                        logger.info(f"Extracted RFQ: {rfq_data['Title'][:50]}...")
                
                except Exception as e:
                    logger.warning(f"Error processing element {i}: {e}")
                    continue
            
            # Remove duplicates based on title similarity
            unique_rfqs = []
            seen_titles = set()
            
            for rfq in rfq_data_list:
                title_key = rfq['Title'][:50].lower().strip()
                if title_key not in seen_titles and len(title_key) > 10:
                    seen_titles.add(title_key)
                    unique_rfqs.append(rfq)
            
            logger.info(f"Extracted {len(unique_rfqs)} unique RFQ records from page")
            return unique_rfqs
            
        except Exception as e:
            logger.error(f"Error extracting data from page: {e}")
            return []
    
    def scrape_page(self, page_num=1):
        """Scrape a single page"""
        try:
            # Build URL
            params = {
                'spm': 'a2700.8073608.1998677541.1.82be65aaoUUItC',
                'country': 'AE',
                'recently': 'Y',
                'tracelog': 'newest'
            }
            
            if page_num > 1:
                params['page'] = str(page_num)
            
            param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            url = f"{self.base_url}?{param_string}"
            
            logger.info(f"Scraping page {page_num}: {url}")
            
            # Navigate to page
            self.driver.get(url)
            time.sleep(8)  # Wait for page to load
            
            # Scroll to load content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(3)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Extract data
            page_data = self.extract_data_from_page_source()
            return page_data
            
        except Exception as e:
            logger.error(f"Error scraping page {page_num}: {e}")
            return []
    
    def scrape_multiple_pages(self, num_pages=3):
        """Scrape multiple pages"""
        if not self.setup_driver():
            return False
        
        try:
            all_data = []
            
            for page in range(1, num_pages + 1):
                logger.info(f"Scraping page {page} of {num_pages}")
                page_data = self.scrape_page(page)
                all_data.extend(page_data)
                
                if page < num_pages:
                    logger.info("Waiting before next page...")
                    time.sleep(5)
            
            self.data = all_data
            logger.info(f"Total records scraped: {len(all_data)}")
            return True
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_to_csv(self, filename="alibaba_rfq_scraped_output.csv"):
        """Save data to CSV"""
        try:
            if not self.data:
                logger.warning("No data to save")
                return False
            
            df = pd.DataFrame(self.data)
            df.to_csv(filename, index=False, encoding='utf-8')
            
            logger.info(f"Data saved to {filename}")
            print(f"\n=== SCRAPING SUMMARY ===")
            print(f"Total records: {len(df)}")
            print(f"Records with titles: {len(df[df['Title'] != ''])}")
            print(f"Records with buyer names: {len(df[df['Buyer_Name'] != ''])}")
            print(f"Records with countries: {len(df[df['Country'] != ''])}")
            print(f"Records with quantities: {len(df[df['Quantity_Required'] != ''])}")
            print(f"Output saved to: {filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            return False

def main():
    """Main function"""
    logger.info("Starting Simple Alibaba RFQ Scraper")
    
    scraper = SimpleAlibabaRFQScraper()
    
    if scraper.scrape_multiple_pages(num_pages=3):
        scraper.save_to_csv()
        logger.info("Scraping completed successfully!")
    else:
        logger.error("Scraping failed")

if __name__ == "__main__":
    main()
