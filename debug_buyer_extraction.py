"""
Debug script to analyze buyer name extraction issues
This will show the actual text content being processed
"""

import logging
import time
from simple_alibaba_scraper import SimpleAlibabaRFQScraper

# Enable debug logging to see all details
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DebugAlibabaRFQScraper(SimpleAlibabaRFQScraper):
    """Extended scraper with debug capabilities"""
    
    def debug_single_page(self):
        """Debug a single page to see what's being extracted"""
        if not self.setup_driver():
            return False
        
        try:
            # Navigate to first page
            url = f"{self.base_url}?spm=a2700.8073608.1998677541.1.82be65aaoUUItC&country=AE&recently=Y&tracelog=newest"
            print(f"Navigating to: {url}")
            
            self.driver.get(url)
            time.sleep(10)  # Wait longer for page to load
            
            # Scroll to load content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(3)
            
            # Save page source for analysis
            with open('debug_page_source.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            print("Page source saved to debug_page_source.html")
            
            # Extract data with debug info
            page_data = self.extract_data_from_page_source()
            
            # Show detailed analysis
            print(f"\n{'='*60}")
            print("DETAILED EXTRACTION ANALYSIS")
            print(f"{'='*60}")
            
            if page_data:
                print(f"Total elements processed: {len(page_data)}")
                
                for i, record in enumerate(page_data[:3]):  # Show first 3 in detail
                    print(f"\n--- RECORD {i+1} DETAILS ---")
                    print(f"RFQ ID: {record['RFQ_ID']}")
                    print(f"Title: {record['Title']}")
                    print(f"Buyer Name: '{record['Buyer_Name']}'")
                    print(f"Country: '{record['Country']}'")
                    print(f"Quantity: '{record['Quantity_Required']}'")
                    print(f"Time: '{record['Inquiry_Time']}'")
                    print(f"URL: {record['Inquiry_URL']}")
                    
                # Save debug data
                import pandas as pd
                df = pd.DataFrame(page_data)
                df.to_csv('debug_extraction_results.csv', index=False)
                print(f"\nDebug results saved to debug_extraction_results.csv")
                
            else:
                print("No data extracted! This indicates a problem with the selectors.")
                
            return True
            
        except Exception as e:
            print(f"Debug failed: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

def main():
    print("Starting DEBUG session for buyer name extraction...")
    print("This will:")
    print("1. Navigate to Alibaba RFQ page")
    print("2. Extract data with detailed logging")
    print("3. Save page source and results for analysis")
    print("4. Show detailed breakdown of extracted data")
    
    scraper = DebugAlibabaRFQScraper()
    scraper.debug_single_page()

if __name__ == "__main__":
    main()
