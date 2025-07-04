# Alibaba RFQ Web Scraper

This project scrapes Request for Quotation (RFQ) data from Alibaba using Selenium and BeautifulSoup.

## Features

- Scrapes RFQ data from Alibaba sourcing pages
- Extracts 16 different data fields per RFQ
- Handles multiple pages (configurable)
- Anti-detection measures for web scraping
- Exports data to CSV format
- Comprehensive error handling and logging

## Data Fields Extracted

1. **RFQ_ID** - Unique identifier for each RFQ
2. **Title** - RFQ title/description
3. **Buyer_Name** - Name of the buyer
4. **Buyer_Image** - Buyer's profile image URL
5. **Inquiry_Time** - When the inquiry was posted
6. **Quotes_Left** - Number of quotes remaining
7. **Country** - Buyer's country
8. **Quantity_Required** - Quantity needed (e.g., "4000 Piece")
9. **Email_Confirmed** - Whether buyer's email is verified
10. **Experienced** - Whether buyer is experienced
11. **Completed** - Whether buyer has completed orders
12. **Typical_Reply** - Whether buyer typically replies
13. **Interactive** - Whether buyer is interactive
14. **Inquiry_URL** - Link to the RFQ page
15. **Inquiry_Date** - Formatted inquiry date
16. **Scraping_Date** - Timestamp when data was scraped

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. The script will automatically download ChromeDriver using webdriver-manager.

## Usage

### Option 1: Use the comprehensive scraper
```bash
python alibaba_rfq_scraper.py
```

### Option 2: Use the simplified scraper (recommended for beginners)
```bash
python simple_alibaba_scraper.py
```

## Configuration

You can modify the following in the scripts:

- **Number of pages**: Change `num_pages` parameter (default: 3)
- **Target URL**: Modify the base URL and parameters
- **Output filename**: Change the CSV output filename
- **Delays**: Adjust sleep times between requests

## Files

- `alibaba_rfq_scraper.py` - Main comprehensive scraper
- `simple_alibaba_scraper.py` - Simplified version with robust extraction
- `config.py` - Configuration settings
- `requirements.txt` - Python dependencies
- `test_scraper.py` - Test script for validation

## Output

The scraper generates a CSV file named `alibaba_rfq_scraped_output.csv` with all extracted data.

## Important Notes

1. **Respect robots.txt**: Always check the website's robots.txt before scraping
2. **Rate limiting**: The script includes delays to avoid overwhelming the server
3. **Legal compliance**: Ensure your scraping complies with the website's terms of service
4. **Dynamic content**: Some data might be loaded dynamically and may require additional waiting time

## Troubleshooting

1. **Chrome driver issues**: The script automatically manages ChromeDriver, but ensure Chrome browser is installed
2. **Access blocked**: If you get blocked, try:
   - Increasing delays between requests
   - Using different user agents
   - Using proxies (not implemented in this version)
3. **No data extracted**: Check if the website structure has changed and update selectors accordingly

## Sample Output

```csv
RFQ_ID,Title,Buyer_Name,Country,Quantity_Required,Scraping_Date
RFQ_123,Organic Cotton T-shirts,ABC Trading,UAE,5000 Piece,2024-01-15 10:30:00
```

## Legal Disclaimer

This tool is for educational purposes. Users are responsible for complying with website terms of service and applicable laws regarding web scraping.
