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
                    
                    # Extract buyer information - improved extraction with Alibaba-specific structure
                    buyer_name = ''
                    
                    # Try to find buyer name in specific Alibaba elements first
                    buyer_candidates = [
                        # Primary: Look for the specific Alibaba username div with class "text"
                        element.find('div', class_='text'),
                        element.find('div', class_=re.compile(r'^text$', re.I)),
                        # Secondary: Look for other buyer-related elements
                        element.find('span', class_=re.compile(r'buyer|company|name|contact|supplier|vendor', re.I)),
                        element.find('div', class_=re.compile(r'buyer|company|name|contact|supplier|vendor', re.I)),
                        element.find('a', class_=re.compile(r'buyer|company|name|contact|supplier|vendor', re.I)),
                        element.find('p', class_=re.compile(r'buyer|company|name|contact|supplier|vendor', re.I)),
                        element.find('strong'),
                        element.find('b')
                    ]
                    
                    for buyer_elem in buyer_candidates:
                        if buyer_elem:
                            buyer_text = self.safe_extract_text(buyer_elem)
                            # Clean and validate buyer name
                            if len(buyer_text) > 2 and len(buyer_text) < 100:
                                # Remove common prefixes
                                buyer_text = re.sub(r'^(from|buyer|company|contact|supplier|vendor)[:\s]*', '', buyer_text, flags=re.I)
                                buyer_text = buyer_text.strip()
                                
                                # For div with class="text", accept names more liberally (likely usernames)
                                if buyer_elem.get('class') and 'text' in buyer_elem.get('class', []):
                                    # This is likely a username div, be more permissive
                                    if (buyer_text and 
                                        not buyer_text.lower() in ['quote', 'request', 'inquiry', 'rfq', 'alibaba', 'sourcing'] and
                                        not buyer_text.isdigit() and
                                        not re.match(r'^\d+\s*(piece|unit|kg|ton|hour|day|minute)', buyer_text, re.I) and
                                        re.search(r'[A-Za-z]{2,}', buyer_text)):  # Must contain at least 2 letters
                                        buyer_name = buyer_text
                                        break
                                else:
                                    # Standard validation for other elements
                                    if (buyer_text and 
                                        not buyer_text.lower() in ['quote', 'request', 'inquiry', 'rfq', 'alibaba', 'sourcing', 'buyer', 'supplier'] and
                                        not buyer_text.isdigit() and
                                        not re.match(r'^\d+\s*(piece|unit|kg|ton)', buyer_text, re.I)):
                                        buyer_name = buyer_text
                                        break
                    
                    # If no buyer found in specific elements, try regex patterns on the full text
                    if not buyer_name:
                        buyer_patterns = [
                            r'from[:\s]+([A-Za-z][A-Za-z0-9\s&.,\-]{2,80}?)(?:\s*(?:,|\n|$|UAE|AE|China|India|USA|UK|Germany))',
                            r'buyer[:\s]+([A-Za-z][A-Za-z0-9\s&.,\-]{2,80}?)(?:\s*(?:,|\n|$|UAE|AE|China|India|USA|UK|Germany))',
                            r'company[:\s]+([A-Za-z][A-Za-z0-9\s&.,\-]{2,80}?)(?:\s*(?:,|\n|$|UAE|AE|China|India|USA|UK|Germany))',
                            r'contact[:\s]+([A-Za-z][A-Za-z0-9\s&.,\-]{2,80}?)(?:\s*(?:,|\n|$|UAE|AE|China|India|USA|UK|Germany))',
                            r'supplier[:\s]+([A-Za-z][A-Za-z0-9\s&.,\-]{2,80}?)(?:\s*(?:,|\n|$|UAE|AE|China|India|USA|UK|Germany))',
                            r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:LLC|Ltd|Inc|Corp|Co\.)',
                            r'([A-Z][A-Z\s&.,\-]{5,50})\s*(?:TRADING|COMPANY|CORP|LLC|LTD|INC|CO\.)',
                            r'([A-Za-z][A-Za-z0-9\s&.,\-]{3,50})\s+(?:Trading|Company|Corp|LLC|Ltd|Inc)',
                            r'([A-Z][A-Z\s]{10,50})',  # All caps company names
                            r'by\s+([A-Za-z][A-Za-z0-9\s&.,\-]{2,50})',  # "by Company Name"
                            r'posted\s+by\s+([A-Za-z][A-Za-z0-9\s&.,\-]{2,50})',  # "posted by Company Name"
                        ]
                        
                        for pattern in buyer_patterns:
                            match = re.search(pattern, element_text, re.I)
                            if match:
                                potential_buyer = match.group(1).strip()
                                # Filter out common false positives
                                if (potential_buyer and 
                                    not potential_buyer.lower() in ['quote', 'request', 'inquiry', 'rfq', 'alibaba', 'sourcing', 'buyer', 'supplier', 'trading', 'company'] and
                                    len(potential_buyer) > 2 and 
                                    not potential_buyer.isdigit() and
                                    not re.match(r'^\d+\s*(piece|unit|kg|ton)', potential_buyer, re.I)):
                                    buyer_name = potential_buyer
                                    break
                    
                    # Try to extract from commonly structured text patterns
                    if not buyer_name:
                        # Look for patterns like "Company Name - Country" or "Company Name, Country"
                        text_lines = element_text.split('\n')
                        for line in text_lines:
                            line = line.strip()
                            if len(line) > 5 and len(line) < 100:
                                # Check if line contains a company-like name
                                if (any(word in line.lower() for word in ['trading', 'company', 'corp', 'ltd', 'llc', 'inc', 'co.']) or
                                    re.search(r'[A-Z][A-Z\s]{5,}', line) or  # All caps names
                                    re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+', line)):  # Title case names
                                    
                                    # Clean the line
                                    clean_line = re.sub(r'(from|buyer|company|contact)[:\s]*', '', line, flags=re.I)
                                    clean_line = re.sub(r'\s*[-,]\s*(UAE|AE|China|India|USA|UK|Germany).*', '', clean_line, flags=re.I)
                                    clean_line = clean_line.strip()
                                    
                                    if (clean_line and len(clean_line) > 3 and
                                        not clean_line.lower() in ['quote', 'request', 'inquiry', 'rfq', 'alibaba', 'sourcing']):
                                        buyer_name = clean_line
                                        break
                    
                    if buyer_name:
                        rfq_data['Buyer_Name'] = buyer_name[:100]
                    
                    # Extract country - using simplified pattern from alternative scraper
                    country_name = ''
                    
                    # Try to find country in specific Alibaba RFQ elements first
                    country_candidates = [
                        # Primary: Look for the specific Alibaba RFQ country div
                        element.find('div', class_=re.compile(r'brh-rfq-item__country', re.I)),
                        element.find('div', class_=re.compile(r'rfq.*country', re.I)),
                        element.find('div', class_=re.compile(r'country', re.I)),
                        # Secondary: Look for flag images with country info
                        element.find('img', class_=re.compile(r'country.*flag|flag.*country', re.I)),
                        element.find('img', {'title': re.compile(r'United Arab Emirates|China|India|USA|UK|Germany|France|Canada|Australia|Brazil|Japan', re.I)}),
                        element.find('img', {'alt': re.compile(r'United Arab Emirates|China|India|USA|UK|Germany|France|Canada|Australia|Brazil|Japan', re.I)}),
                    ]
                    
                    for country_elem in country_candidates:
                        if country_elem:
                            # Handle different element types
                            if country_elem.name == 'img':
                                # Extract from image alt or title attributes
                                alt_text = self.safe_extract_attribute(country_elem, 'alt')
                                title_text = self.safe_extract_attribute(country_elem, 'title')
                                country_text = title_text or alt_text
                                if country_text:
                                    country_name = country_text.strip()
                                    break
                            else:
                                # Extract text from div/span elements
                                country_text = self.safe_extract_text(country_elem)
                                if country_text:
                                    # Clean up the text (remove "Posted in:" and other labels)
                                    clean_text = re.sub(r'posted\s+in\s*:?\s*', '', country_text, flags=re.I)
                                    clean_text = re.sub(r'country\s*:?\s*', '', clean_text, flags=re.I)
                                    clean_text = re.sub(r'location\s*:?\s*', '', clean_text, flags=re.I)
                                    clean_text = clean_text.strip()
                                    
                                    # If cleaned text looks like a country, use it
                                    if len(clean_text) > 2 and len(clean_text) < 50 and not re.search(r'\d', clean_text):
                                        country_name = clean_text
                                        break
                    
                    # If no country found in specific elements, use simplified pattern matching
                    if not country_name:
                        # Simplified country pattern from alternative scraper
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
                                country_name = country_mapping.get(country_found, country_found)
                                break
                    
                    if country_name:
                        rfq_data['Country'] = country_name
                    
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
                    
                    # Extract quotes left - improved extraction for Alibaba RFQ structure
                    quotes_left = ''
                    
                    # Try to find quotes in specific Alibaba RFQ elements first
                    quotes_candidates = [
                        # Primary: Look for the specific Alibaba RFQ quotes div
                        element.find('div', class_=re.compile(r'brh-rfq-item__quote-left', re.I)),
                        element.find('div', class_=re.compile(r'quote.*left|quotes.*left', re.I)),
                        element.find('span', class_=re.compile(r'quote.*left|quotes.*left', re.I)),
                        # Secondary: Look for elements containing "quotes left" text
                        element.find('div', string=re.compile(r'quotes?\s+left', re.I)),
                        element.find('span', string=re.compile(r'quotes?\s+left', re.I))
                    ]
                    
                    for quotes_elem in quotes_candidates:
                        if quotes_elem:
                            quotes_text = self.safe_extract_text(quotes_elem)
                            if quotes_text:
                                # Extract number from "Quotes Left 9" or similar patterns
                                quotes_match = re.search(r'quotes?\s+left\s+(\d+)', quotes_text, re.I)
                                if not quotes_match:
                                    # Try to find number in nested span
                                    span_elem = quotes_elem.find('span')
                                    if span_elem:
                                        span_text = self.safe_extract_text(span_elem)
                                        if span_text and span_text.isdigit():
                                            quotes_left = span_text
                                            break
                                    # Try to extract just the number from the text
                                    number_match = re.search(r'(\d+)', quotes_text)
                                    if number_match:
                                        quotes_left = number_match.group(1)
                                        break
                                else:
                                    quotes_left = quotes_match.group(1)
                                    break
                    
                    # If no quotes found in specific elements, use regex on full text
                    if not quotes_left:
                        quotes_match = re.search(r'quotes?\s+left\s+(\d+)', element_text, re.I)
                        if not quotes_match:
                            quotes_match = re.search(r'(\d+)\s*quotes?\s*left', element_text, re.I)
                        if quotes_match:
                            quotes_left = quotes_match.group(1)
                    
                    if quotes_left:
                        rfq_data['Quotes_Left'] = quotes_left
                    
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
                        
                        # Debug logging for extracted data
                        logger.debug(f"Extracted RFQ {i+1}: Title='{rfq_data['Title'][:30]}...', Buyer='{rfq_data['Buyer_Name']}', Country='{rfq_data['Country']}', Quantity='{rfq_data['Quantity_Required']}'")
                        
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
            print(f"Records with quotes left: {len(df[df['Quotes_Left'] != ''])}")
            print(f"Output saved to: {filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            return False

def main():
    """Main function"""
    logger.info("Starting Simple Alibaba RFQ Scraper")
    
    # Enable debug logging for more detailed output
    # Uncomment the line below to see detailed extraction logs
    # logging.getLogger().setLevel(logging.DEBUG)
    
    scraper = SimpleAlibabaRFQScraper()
    
    if scraper.scrape_multiple_pages(num_pages=3):
        scraper.save_to_csv()
        logger.info("Scraping completed successfully!")
    else:
        logger.error("Scraping failed")

if __name__ == "__main__":
    main()
