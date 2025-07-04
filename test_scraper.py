"""
Test script for Alibaba RFQ Scraper
Tests basic functionality and validates output
"""

import os
import pandas as pd
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_csv_output(filename="alibaba_rfq_scraped_output.csv"):
    """Test if CSV output is valid"""
    try:
        if not os.path.exists(filename):
            logger.error(f"Output file {filename} not found")
            return False
        
        # Read CSV
        df = pd.read_csv(filename)
        
        # Check if file has data
        if len(df) == 0:
            logger.error("CSV file is empty")
            return False
        
        # Expected columns
        expected_columns = [
            'RFQ_ID', 'Title', 'Buyer_Name', 'Buyer_Image', 'Inquiry_Time',
            'Quotes_Left', 'Country', 'Quantity_Required', 'Email_Confirmed',
            'Experienced', 'Completed', 'Typical_Reply', 'Interactive',
            'Inquiry_URL', 'Inquiry_Date', 'Scraping_Date'
        ]
        
        # Check columns
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing columns: {missing_columns}")
            return False
        
        # Basic data validation
        logger.info(f"Total records: {len(df)}")
        logger.info(f"Records with RFQ_ID: {len(df[df['RFQ_ID'].notna()])}")
        logger.info(f"Records with Title: {len(df[df['Title'].notna() & (df['Title'] != '')])}")
        logger.info(f"Records with Buyer_Name: {len(df[df['Buyer_Name'].notna() & (df['Buyer_Name'] != '')])}")
        logger.info(f"Records with Country: {len(df[df['Country'].notna() & (df['Country'] != '')])}")
        
        # Check data quality
        if len(df[df['Title'].notna() & (df['Title'] != '')]) == 0:
            logger.warning("No records with titles found")
        
        logger.info("CSV validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Error validating CSV: {e}")
        return False

def test_requirements():
    """Test if all required packages are installed"""
    try:
        import selenium
        import pandas
        from bs4 import BeautifulSoup
        import webdriver_manager
        logger.info("All required packages are installed")
        return True
    except ImportError as e:
        logger.error(f"Missing package: {e}")
        return False

def run_basic_scraper_test():
    """Run a basic test of the scraper"""
    try:
        from simple_alibaba_scraper import SimpleAlibabaRFQScraper
        
        logger.info("Testing scraper initialization...")
        scraper = SimpleAlibabaRFQScraper()
        
        logger.info("Testing driver setup...")
        if scraper.setup_driver():
            logger.info("Driver setup successful")
            scraper.driver.quit()
            return True
        else:
            logger.error("Driver setup failed")
            return False
            
    except Exception as e:
        logger.error(f"Scraper test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting scraper tests...")
    
    # Test 1: Requirements
    logger.info("Test 1: Checking requirements...")
    if not test_requirements():
        logger.error("Requirements test failed")
        return
    
    # Test 2: Basic scraper functionality
    logger.info("Test 2: Testing scraper functionality...")
    if not run_basic_scraper_test():
        logger.error("Scraper functionality test failed")
        return
    
    # Test 3: Check if CSV exists and validate it
    logger.info("Test 3: Validating CSV output...")
    csv_exists = os.path.exists("alibaba_rfq_scraped_output.csv")
    
    if csv_exists:
        if test_csv_output():
            logger.info("All tests passed!")
        else:
            logger.error("CSV validation failed")
    else:
        logger.info("No CSV found - run the scraper first to generate output")
        logger.info("Run: python simple_alibaba_scraper.py")

if __name__ == "__main__":
    main()
