"""
Test script to verify country and buyer name extraction improvements
"""

import logging
from simple_alibaba_scraper import SimpleAlibabaRFQScraper

# Enable debug logging to see detailed extraction
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_country_extraction():
    print("Testing improved country and buyer name extraction...")
    print("This will scrape 1 page to test the fixes.")
    
    scraper = SimpleAlibabaRFQScraper()
    
    # Test with just 1 page
    if scraper.scrape_multiple_pages(num_pages=1):
        # Save with a test filename
        if scraper.save_to_csv("test_country_extraction.csv"):
            print("\nTest completed! Check the summary above to see if countries and buyer names are now being extracted.")
            
            # Analyze results
            if scraper.data:
                print(f"\n=== DETAILED ANALYSIS ===")
                print(f"Total records extracted: {len(scraper.data)}")
                
                # Count records with each field
                records_with_buyers = sum(1 for record in scraper.data if record['Buyer_Name'])
                records_with_countries = sum(1 for record in scraper.data if record['Country'])
                records_with_quantities = sum(1 for record in scraper.data if record['Quantity_Required'])
                records_with_times = sum(1 for record in scraper.data if record['Inquiry_Time'])
                
                print(f"Records with buyer names: {records_with_buyers}")
                print(f"Records with countries: {records_with_countries}")
                print(f"Records with quantities: {records_with_quantities}")
                print(f"Records with inquiry times: {records_with_times}")
                
                # Show unique countries and buyers found
                unique_countries = set(record['Country'] for record in scraper.data if record['Country'])
                unique_buyers = set(record['Buyer_Name'] for record in scraper.data if record['Buyer_Name'])
                
                if unique_countries:
                    print(f"\nCountries found: {', '.join(sorted(unique_countries))}")
                else:
                    print("\nNo countries found - extraction still needs improvement")
                
                if unique_buyers:
                    print(f"\nBuyer names found: {', '.join(list(unique_buyers)[:5])}")
                    if len(unique_buyers) > 5:
                        print(f"... and {len(unique_buyers) - 5} more")
                else:
                    print("\nNo buyer names found - extraction still needs improvement")
                
                # Show sample records
                print(f"\n=== SAMPLE RECORDS ===")
                for i, record in enumerate(scraper.data[:3]):
                    print(f"\n--- Record {i+1} ---")
                    print(f"Title: {record['Title'][:60]}...")
                    print(f"Buyer: '{record['Buyer_Name']}'")
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
    test_country_extraction()
