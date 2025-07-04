"""
Alibaba RFQ Web Scraper
Scrapes Request for Quotation data from Alibaba using Selenium and BeautifulSoup
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

class AlibabaRFQScraper:
    def __init__(self):
        """Initialize the scraper with Chrome driver"""
        self.driver = None
        self.data = []
        self.base_url = "https://sourcing.alibaba.com/rfq/rfq_search_list.htm"
        self.params = "?spm=a2700.8073608.1998677541.1.82be65aaoUUItC&country=AE&recently=Y&tracelog=newest"
        
    def setup_driver(self):
        """Setup Chrome driver with options"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Chrome driver setup successfully")
            return True
        except Exception as e:
            logger.error(f"Error setting up driver: {e}")
            return False
    
    def extract_rfq_data(self, rfq_element):
        """Extract data from a single RFQ element"""
        try:
            soup = BeautifulSoup(rfq_element.get_attribute('outerHTML'), 'html.parser')
            
            # Initialize data dictionary with default values
            rfq_data = {
                'RFQ_ID': '',
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
            
            # Extract RFQ ID from data attributes or URL
            try:
                rfq_link = soup.find('a', {'class': re.compile(r'title|link')})
                if rfq_link and rfq_link.get('href'):
                    href = rfq_link.get('href')
                    rfq_id_match = re.search(r'rfq_id[=:](\d+)', href)
                    if rfq_id_match:
                        rfq_data['RFQ_ID'] = rfq_id_match.group(1)
                    rfq_data['Inquiry_URL'] = href if href.startswith('http') else f"https://sourcing.alibaba.com{href}"
            except Exception as e:
                logger.warning(f"Error extracting RFQ ID: {e}")
            
            # Extract Title
            try:
                title_elem = soup.find('a', {'class': re.compile(r'title')}) or soup.find('h3') or soup.find('h4')
                if title_elem:
                    rfq_data['Title'] = title_elem.get_text(strip=True)
            except Exception as e:
                logger.warning(f"Error extracting title: {e}")
            
            # Extract Buyer Name
            try:
                buyer_elem = (soup.find('span', {'class': re.compile(r'buyer|name')}) or 
                             soup.find('div', {'class': re.compile(r'buyer|name')}) or
                             soup.find(text=re.compile(r'From:|By:')))
                if buyer_elem:
                    if hasattr(buyer_elem, 'get_text'):
                        rfq_data['Buyer_Name'] = buyer_elem.get_text(strip=True)
                    else:
                        parent = buyer_elem.parent if buyer_elem.parent else None
                        if parent:
                            rfq_data['Buyer_Name'] = parent.get_text(strip=True)
            except Exception as e:
                logger.warning(f"Error extracting buyer name: {e}")
            
            # Extract Buyer Image
            try:
                img_elem = soup.find('img', {'class': re.compile(r'avatar|buyer|profile')})
                if img_elem and img_elem.get('src'):
                    rfq_data['Buyer_Image'] = img_elem.get('src')
            except Exception as e:
                logger.warning(f"Error extracting buyer image: {e}")
            
            # Extract Inquiry Time
            try:
                time_patterns = [
                    re.compile(r'\d+\s*(hour|day|minute)s?\s*(ago|before)', re.I),
                    re.compile(r'(yesterday|today)', re.I)
                ]
                
                for pattern in time_patterns:
                    time_elem = soup.find(text=pattern)
                    if time_elem:
                        rfq_data['Inquiry_Time'] = time_elem.strip()
                        break
                
                if not rfq_data['Inquiry_Time']:
                    # Look for time in span or div elements
                    time_elem = soup.find('span', {'class': re.compile(r'time|date')})
                    if time_elem:
                        rfq_data['Inquiry_Time'] = time_elem.get_text(strip=True)
            except Exception as e:
                logger.warning(f"Error extracting inquiry time: {e}")
            
            # Extract Quotes Left
            try:
                quotes_text = soup.find(text=re.compile(r'\d+\s*quotes?\s*left', re.I))
                if quotes_text:
                    quotes_match = re.search(r'(\d+)', quotes_text)
                    if quotes_match:
                        rfq_data['Quotes_Left'] = quotes_match.group(1)
            except Exception as e:
                logger.warning(f"Error extracting quotes left: {e}")
            
            # Extract Country
            try:
                country_elem = (soup.find('span', {'class': re.compile(r'country|location')}) or
                               soup.find('div', {'class': re.compile(r'country|location')}))
                if country_elem:
                    rfq_data['Country'] = country_elem.get_text(strip=True)
                else:
                    # Look for country codes or names in text
                    country_text = soup.find(text=re.compile(r'\b[A-Z]{2}\b|\b(United States|China|India|Germany|UK|UAE)\b'))
                    if country_text:
                        rfq_data['Country'] = country_text.strip()
            except Exception as e:
                logger.warning(f"Error extracting country: {e}")
            
            # Extract Quantity Required
            try:
                quantity_patterns = [
                    re.compile(r'\d+[\s,]*\d*\s*(piece|box|bag|unit|kg|ton|meter|yard)s?', re.I),
                    re.compile(r'quantity[:\s]*(\d+[\s,]*\d*\s*\w+)', re.I)
                ]
                
                for pattern in quantity_patterns:
                    qty_text = soup.find(text=pattern)
                    if qty_text:
                        qty_match = pattern.search(qty_text)
                        if qty_match:
                            rfq_data['Quantity_Required'] = qty_match.group(0).strip()
                            break
            except Exception as e:
                logger.warning(f"Error extracting quantity: {e}")
            
            # Extract verification badges/flags
            try:
                badges_text = soup.get_text().lower()
                
                if any(keyword in badges_text for keyword in ['email confirmed', 'verified email', 'email verified']):
                    rfq_data['Email_Confirmed'] = 'Yes'
                
                if any(keyword in badges_text for keyword in ['experienced', 'expert', 'professional']):
                    rfq_data['Experienced'] = 'Yes'
                
                if any(keyword in badges_text for keyword in ['completed', 'finished', 'done']):
                    rfq_data['Completed'] = 'Yes'
                
                if any(keyword in badges_text for keyword in ['typical reply', 'quick reply', 'fast response']):
                    rfq_data['Typical_Reply'] = 'Yes'
                
                if any(keyword in badges_text for keyword in ['interactive', 'active', 'online']):
                    rfq_data['Interactive'] = 'Yes'
                    
            except Exception as e:
                logger.warning(f"Error extracting verification badges: {e}")
            
            return rfq_data
            
        except Exception as e:
            logger.error(f"Error extracting RFQ data: {e}")
            return None
    
    def scroll_and_load(self):
        """Scroll down to load more content"""
        try:
            # Scroll to bottom of page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Scroll to top and then gradually down
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Gradual scroll
            for i in range(3):
                self.driver.execute_script(f"window.scrollTo(0, {(i+1) * 500});")
                time.sleep(1)
                
        except Exception as e:
            logger.warning(f"Error during scrolling: {e}")
    
    def scrape_page(self, page_num=1):
        """Scrape a single page of RFQ data"""
        try:
            # Construct URL for specific page
            if page_num > 1:
                url = f"{self.base_url}{self.params}&page={page_num}"
            else:
                url = f"{self.base_url}{self.params}"
            
            logger.info(f"Scraping page {page_num}: {url}")
            
            # Navigate to page
            self.driver.get(url)
            time.sleep(5)  # Wait for page to load
            
            # Scroll to load dynamic content
            self.scroll_and_load()
            
            # Wait for RFQ elements to be present
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='rfq'], div[class*='item'], .list-item, .rfq-item"))
                )
            except TimeoutException:
                logger.warning(f"Timeout waiting for RFQ elements on page {page_num}")
            
            # Find RFQ elements using multiple selectors
            rfq_selectors = [
                "div[class*='rfq']",
                "div[class*='item']", 
                ".list-item",
                ".rfq-item",
                "div[data-rfq]",
                ".sourcing-item",
                "tr[class*='item']"
            ]
            
            rfq_elements = []
            for selector in rfq_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        rfq_elements.extend(elements)
                        logger.info(f"Found {len(elements)} elements with selector: {selector}")
                except Exception as e:
                    logger.warning(f"Error with selector {selector}: {e}")
            
            # Remove duplicates by keeping unique elements
            unique_elements = []
            seen_html = set()
            for elem in rfq_elements:
                try:
                    elem_html = elem.get_attribute('outerHTML')[:200]  # First 200 chars as identifier
                    if elem_html not in seen_html:
                        seen_html.add(elem_html)
                        unique_elements.append(elem)
                except:
                    continue
            
            rfq_elements = unique_elements
            logger.info(f"Found {len(rfq_elements)} unique RFQ elements on page {page_num}")
            
            # Extract data from each RFQ element
            page_data = []
            for i, element in enumerate(rfq_elements):
                try:
                    logger.info(f"Processing RFQ {i+1}/{len(rfq_elements)} on page {page_num}")
                    rfq_data = self.extract_rfq_data(element)
                    
                    if rfq_data and (rfq_data['Title'] or rfq_data['RFQ_ID']):
                        page_data.append(rfq_data)
                        logger.info(f"Successfully extracted data for RFQ: {rfq_data['Title'][:50]}...")
                    
                except Exception as e:
                    logger.warning(f"Error processing RFQ element {i+1}: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(page_data)} RFQ records from page {page_num}")
            return page_data
            
        except Exception as e:
            logger.error(f"Error scraping page {page_num}: {e}")
            return []
    
    def scrape_multiple_pages(self, num_pages=3):
        """Scrape multiple pages of RFQ data"""
        logger.info(f"Starting to scrape {num_pages} pages")
        
        if not self.setup_driver():
            logger.error("Failed to setup driver")
            return False
        
        try:
            all_data = []
            
            for page in range(1, num_pages + 1):
                logger.info(f"Scraping page {page} of {num_pages}")
                page_data = self.scrape_page(page)
                all_data.extend(page_data)
                
                # Wait between pages to avoid being blocked
                if page < num_pages:
                    logger.info("Waiting 5 seconds before next page...")
                    time.sleep(5)
            
            self.data = all_data
            logger.info(f"Total RFQ records scraped: {len(all_data)}")
            return True
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Driver closed")
    
    def save_to_csv(self, filename="alibaba_rfq_scraped_output.csv"):
        """Save scraped data to CSV file"""
        try:
            if not self.data:
                logger.warning("No data to save")
                return False
            
            df = pd.DataFrame(self.data)
            
            # Reorder columns to match requirements
            column_order = [
                'RFQ_ID', 'Title', 'Buyer_Name', 'Buyer_Image', 'Inquiry_Time',
                'Quotes_Left', 'Country', 'Quantity_Required', 'Email_Confirmed',
                'Experienced', 'Completed', 'Typical_Reply', 'Interactive',
                'Inquiry_URL', 'Inquiry_Date', 'Scraping_Date'
            ]
            
            # Ensure all columns exist
            for col in column_order:
                if col not in df.columns:
                    df[col] = ''
            
            df = df[column_order]
            
            # Save to CSV
            df.to_csv(filename, index=False, encoding='utf-8')
            logger.info(f"Data saved to {filename}")
            logger.info(f"Total records: {len(df)}")
            
            # Print summary statistics
            print(f"\n=== SCRAPING SUMMARY ===")
            print(f"Total RFQ records scraped: {len(df)}")
            print(f"Records with titles: {len(df[df['Title'] != ''])}")
            print(f"Records with buyer names: {len(df[df['Buyer_Name'] != ''])}")
            print(f"Records with countries: {len(df[df['Country'] != ''])}")
            print(f"Records with quantities: {len(df[df['Quantity_Required'] != ''])}")
            print(f"Email confirmed: {len(df[df['Email_Confirmed'] == 'Yes'])}")
            print(f"Output file: {filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            return False

def main():
    """Main function to run the scraper"""
    logger.info("Starting Alibaba RFQ Scraper")
    
    # Create scraper instance
    scraper = AlibabaRFQScraper()
    
    # Scrape 3 pages as requested
    if scraper.scrape_multiple_pages(num_pages=3):
        # Save data to CSV
        if scraper.save_to_csv():
            logger.info("Scraping completed successfully!")
        else:
            logger.error("Failed to save data to CSV")
    else:
        logger.error("Scraping failed")

if __name__ == "__main__":
    main()
