"""
Quick test to verify improved buyer name and country extraction
"""

import logging
from simple_alibaba_scraper import SimpleAlibabaRFQScraper

# Enable debug logging to see detailed extraction
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_improved_extraction():
    print("Testing improved buyer name and country extraction...")
    print("This will scrape 1 page to test the fixes.")
    
    scraper = SimpleAlibabaRFQScraper()
    
    # Test with just 1 page
    if scraper.scrape_multiple_pages(num_pages=1):
        # Save with a test filename
        if scraper.save_to_csv("test_improved_extraction.csv"):
            print("\nTest completed! Check the summary above to see if buyer names and countries are now being extracted.")
            
            # Show detailed results
            if scraper.data:
                print(f"\nDetailed results from {len(scraper.data)} records:")
                for i, record in enumerate(scraper.data[:5]):  # Show first 5
                    print(f"\n--- Record {i+1} ---")
                    print(f"Title: {record['Title'][:80]}...")
                    print(f"Buyer Name: '{record['Buyer_Name']}'")
                    print(f"Country: '{record['Country']}'")
                    print(f"Quantity: '{record['Quantity_Required']}'")
                    print(f"Time: '{record['Inquiry_Time']}'")
                    
            return True
        else:
            print("Failed to save test results")
            return False
    else:
        print("Test scraping failed")
        return False

if __name__ == "__main__":
    test_improved_extraction()
