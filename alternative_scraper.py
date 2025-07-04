"""
Alternative Alibaba RFQ Scraper with different extraction strategy
Focuses on actual page structure analysis
"""

import time
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AlternativeAlibabaRFQScraper:
    def __init__(self):
        self.driver = None
        self.data = []
        self.base_url = "https://sourcing.alibaba.com/rfq/rfq_search_list.htm"
        
    def setup_driver(self):
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
    
    def extract_using_selenium_elements(self):
        """Use Selenium to find elements directly instead of BeautifulSoup"""
        try:
            # Wait for page to load
            time.sleep(5)
            
            # Try different selectors to find RFQ items
            possible_selectors = [
                "[class*='item']",
                "[class*='rfq']", 
                "[class*='list']",
                "tr",
                "li",
                ".J_rfq_item",
                "[data-tracelog]",
                ".sourcing-item"
            ]
            
            all_elements = []
            for selector in possible_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"Found {len(elements)} elements with selector: {selector}")
                        all_elements.extend(elements)
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
            
            # Remove duplicates
            unique_elements = list(set(all_elements))
            logger.info(f"Total unique elements found: {len(unique_elements)}")
            
            rfq_data_list = []
            
            for i, element in enumerate(unique_elements):
                try:
                    # Get text content
                    element_text = element.text
                    element_html = element.get_attribute('outerHTML')
                    
                    # Skip if too small
                    if len(element_text) < 30:
                        continue
                    
                    # Initialize data
                    rfq_data = {
                        'RFQ_ID': f"ALT_RFQ_{i+1}_{int(time.time())}",
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
                    
                    # Extract title from links
                    try:
                        title_links = element.find_elements(By.TAG_NAME, "a")
                        for link in title_links:
                            href = link.get_attribute('href')
                            link_text = link.text.strip()
                            if href and 'rfq' in href and len(link_text) > 5:
                                rfq_data['Title'] = link_text[:200]
                                rfq_data['Inquiry_URL'] = href
                                break
                    except:
                        pass
                    
                    # If no title from links, use the first substantial text
                    if not rfq_data['Title']:
                        text_lines = element_text.split('\n')
                        for line in text_lines:
                            line = line.strip()
                            if len(line) > 10 and not re.match(r'^\d+\s*(hour|day|minute)', line, re.I):
                                rfq_data['Title'] = line[:200]
                                break
                    
                    # Extract buyer name using multiple strategies
                    buyer_found = False
                    
                    # Strategy 1: Look for specific text patterns
                    text_lines = element_text.split('\n')
                    for line in text_lines:
                        line = line.strip()
                        if not buyer_found and len(line) > 3 and len(line) < 80:
                            # Check if line looks like a company/buyer name
                            if (not re.search(r'\b(hour|day|minute|ago|quote|left|piece|unit|box|rfq|request)\b', line, re.I) and
                                not line.isdigit() and
                                (re.search(r'\b(trading|company|corp|ltd|inc|llc|co\.|group|industries)\b', line, re.I) or
                                 re.search(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+', line) or
                                 (len(line) > 8 and re.search(r'[A-Z]', line)))):
                                rfq_data['Buyer_Name'] = line
                                buyer_found = True
                                break
                    
                    # Strategy 2: Look in specific child elements
                    if not buyer_found:
                        try:
                            child_elements = element.find_elements(By.CSS_SELECTOR, "span, div, p, td")
                            for child in child_elements:
                                child_text = child.text.strip()
                                if (len(child_text) > 5 and len(child_text) < 60 and
                                    not re.search(r'\b(hour|day|minute|ago|quote|left|piece|unit|box)\b', child_text, re.I) and
                                    not child_text.isdigit() and
                                    re.search(r'[A-Za-z]{3,}', child_text)):
                                    # Additional validation for company-like names
                                    if (re.search(r'\b(trading|company|corp|ltd|inc|llc|co\.|group)\b', child_text, re.I) or
                                        re.search(r'^[A-Z][a-z]+\s+[A-Z]', child_text) or
                                        len([c for c in child_text if c.isupper()]) >= 2):
                                        rfq_data['Buyer_Name'] = child_text
                                        buyer_found = True
                                        break
                        except:
                            pass
                    
                    # Extract country
                    country_patterns = [
                        r'\b(UAE|AE|United Arab Emirates|China|CN|India|IN|USA|US|UK|Germany|DE|France|FR|Canada|CA|Australia|AU|Brazil|BR|Japan|JP|South Korea|KR|Italy|IT|Spain|ES|Netherlands|NL|Turkey|TR|Russia|RU|Saudi Arabia|SA|Egypt|EG|Pakistan|PK|Bangladesh|BD|Thailand|TH|Vietnam|VN|Malaysia|MY|Singapore|SG|Indonesia|ID|Philippines|PH|Taiwan|TW|Hong Kong|HK)\b'
                    ]
                    
                    for pattern in country_patterns:
                        match = re.search(pattern, element_text, re.I)
                        if match:
                            country_found = match.group(1).upper()
                            country_mapping = {
                                'AE': 'UAE', 'CN': 'China', 'IN': 'India', 'US': 'USA', 
                                'GB': 'UK', 'DE': 'Germany', 'FR': 'France', 'CA': 'Canada',
                                'AU': 'Australia', 'BR': 'Brazil', 'JP': 'Japan', 'KR': 'South Korea',
                                'IT': 'Italy', 'ES': 'Spain', 'NL': 'Netherlands', 'TR': 'Turkey',
                                'RU': 'Russia', 'SA': 'Saudi Arabia', 'EG': 'Egypt', 'PK': 'Pakistan',
                                'BD': 'Bangladesh', 'TH': 'Thailand', 'VN': 'Vietnam', 'MY': 'Malaysia',
                                'SG': 'Singapore', 'ID': 'Indonesia', 'PH': 'Philippines', 'TW': 'Taiwan',
                                'HK': 'Hong Kong'
                            }
                            rfq_data['Country'] = country_mapping.get(country_found, country_found)
                            break
                    
                    # Extract quantity
                    qty_match = re.search(r'(\d+[\s,]*\d*)\s*(pieces?|units?|boxes?|bags?|kgs?|tons?)', element_text, re.I)
                    if qty_match:
                        rfq_data['Quantity_Required'] = qty_match.group(0).strip()
                    
                    # Extract time
                    time_match = re.search(r'(\d+)\s*(hours?|days?|minutes?)\s*(ago|before)', element_text, re.I)
                    if time_match:
                        rfq_data['Inquiry_Time'] = time_match.group(0).strip()
                    
                    # Extract quotes left
                    quotes_match = re.search(r'(\d+)\s*quotes?\s*left', element_text, re.I)
                    if quotes_match:
                        rfq_data['Quotes_Left'] = quotes_match.group(1)
                    
                    # Only add if we have meaningful data
                    if rfq_data['Title'] or len(element_text) > 50:
                        if not rfq_data['Title']:
                            rfq_data['Title'] = element_text[:100].replace('\n', ' ').strip()
                        
                        rfq_data_list.append(rfq_data)
                        logger.info(f"Extracted RFQ {len(rfq_data_list)}: Title='{rfq_data['Title'][:40]}...', Buyer='{rfq_data['Buyer_Name']}', Country='{rfq_data['Country']}'")
                
                except Exception as e:
                    logger.warning(f"Error processing element {i}: {e}")
                    continue
            
            logger.info(f"Total RFQ records extracted: {len(rfq_data_list)}")
            return rfq_data_list
            
        except Exception as e:
            logger.error(f"Error in selenium extraction: {e}")
            return []
    
    def scrape_single_page(self):
        """Scrape a single page using alternative method"""
        if not self.setup_driver():
            return False
        
        try:
            url = f"{self.base_url}?spm=a2700.8073608.1998677541.1.82be65aaoUUItC&country=AE&recently=Y&tracelog=newest"
            logger.info(f"Navigating to: {url}")
            
            self.driver.get(url)
            time.sleep(10)  # Wait for page to load
            
            # Scroll to load content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(3)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Extract data
            self.data = self.extract_using_selenium_elements()
            return True
            
        except Exception as e:
            logger.error(f"Error scraping: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_to_csv(self, filename="alternative_alibaba_rfq_output.csv"):
        """Save data to CSV"""
        if not self.data:
            logger.warning("No data to save")
            return False
        
        try:
            df = pd.DataFrame(self.data)
            df.to_csv(filename, index=False, encoding='utf-8')
            
            print(f"\n=== ALTERNATIVE SCRAPER RESULTS ===")
            print(f"Total records: {len(df)}")
            print(f"Records with titles: {len(df[df['Title'] != ''])}")
            print(f"Records with buyer names: {len(df[df['Buyer_Name'] != ''])}")
            print(f"Records with countries: {len(df[df['Country'] != ''])}")
            print(f"Records with quantities: {len(df[df['Quantity_Required'] != ''])}")
            
            # Show sample data
            if len(df) > 0:
                print(f"\nSample extracted data:")
                for i, row in df.head(3).iterrows():
                    print(f"Record {i+1}:")
                    print(f"  Title: {row['Title'][:60]}...")
                    print(f"  Buyer: '{row['Buyer_Name']}'")
                    print(f"  Country: '{row['Country']}'")
                    print(f"  Quantity: '{row['Quantity_Required']}'")
            
            print(f"Output saved to: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
            return False

def main():
    logger.info("Starting Alternative Alibaba RFQ Scraper")
    scraper = AlternativeAlibabaRFQScraper()
    
    if scraper.scrape_single_page():
        scraper.save_to_csv()
        logger.info("Alternative scraping completed!")
    else:
        logger.error("Alternative scraping failed")

if __name__ == "__main__":
    main()
