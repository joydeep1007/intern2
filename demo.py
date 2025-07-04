"""
Demo script for Alibaba RFQ Scraper
Shows how to use the scraper with different configurations
"""

import time
import logging
from simple_alibaba_scraper import SimpleAlibabaRFQScraper

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_demo_scraping():
    """Run a demo scraping session"""
    logger.info("=" * 50)
    logger.info("ALIBABA RFQ SCRAPER DEMO")
    logger.info("=" * 50)
    
    # Create scraper instance
    scraper = SimpleAlibabaRFQScraper()
    
    logger.info("Starting demo scraping session...")
    logger.info("Target: Alibaba RFQ listings from UAE")
    logger.info("Pages to scrape: 3")
    logger.info("Expected time: 2-3 minutes")
    
    # Start scraping
    start_time = time.time()
    
    if scraper.scrape_multiple_pages(num_pages=3):
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        
        logger.info(f"Scraping completed in {duration} seconds")
        
        # Save results
        if scraper.save_to_csv("demo_alibaba_rfq_output.csv"):
            logger.info("Demo completed successfully!")
            logger.info("Check 'demo_alibaba_rfq_output.csv' for results")
            
            # Show sample data
            if scraper.data:
                logger.info("\n" + "=" * 50)
                logger.info("SAMPLE SCRAPED DATA")
                logger.info("=" * 50)
                
                for i, record in enumerate(scraper.data[:3]):  # Show first 3 records
                    logger.info(f"\nRecord {i+1}:")
                    logger.info(f"  Title: {record['Title'][:80]}...")
                    logger.info(f"  Buyer: {record['Buyer_Name']}")
                    logger.info(f"  Country: {record['Country']}")
                    logger.info(f"  Quantity: {record['Quantity_Required']}")
                    logger.info(f"  Time: {record['Inquiry_Time']}")
        else:
            logger.error("Failed to save results")
    else:
        logger.error("Demo scraping failed")

def show_usage_examples():
    """Show different ways to use the scraper"""
    print("\n" + "=" * 60)
    print("USAGE EXAMPLES")
    print("=" * 60)
    
    print("\n1. Basic usage (scrape 3 pages):")
    print("   python simple_alibaba_scraper.py")
    
    print("\n2. Custom usage (modify in script):")
    print("   scraper = SimpleAlibabaRFQScraper()")
    print("   scraper.scrape_multiple_pages(num_pages=5)")
    print("   scraper.save_to_csv('custom_output.csv')")
    
    print("\n3. Test the scraper:")
    print("   python test_scraper.py")
    
    print("\n4. Run this demo:")
    print("   python demo.py")

if __name__ == "__main__":
    # Show usage examples first
    show_usage_examples()
    
    # Ask user if they want to run demo
    response = input("\nDo you want to run the demo scraping? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        run_demo_scraping()
    else:
        print("Demo cancelled. You can run the scraper manually using the examples above.")
