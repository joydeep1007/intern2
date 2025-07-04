"""
Configuration file for Alibaba RFQ Scraper
"""

# Scraping Configuration
SCRAPING_CONFIG = {
    'num_pages': 3,
    'base_url': 'https://sourcing.alibaba.com/rfq/rfq_search_list.htm',
    'params': '?spm=a2700.8073608.1998677541.1.82be65aaoUUItC&country=AE&recently=Y&tracelog=newest',
    'output_filename': 'alibaba_rfq_scraped_output.csv',
    'page_load_delay': 5,  # seconds
    'between_pages_delay': 5,  # seconds
    'scroll_delay': 3  # seconds
}

# Chrome Driver Options
CHROME_OPTIONS = [
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-blink-features=AutomationControlled',
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
]

# CSS Selectors for RFQ elements (in order of preference)
RFQ_SELECTORS = [
    "div[class*='rfq']",
    "div[class*='item']", 
    ".list-item",
    ".rfq-item",
    "div[data-rfq]",
    ".sourcing-item",
    "tr[class*='item']"
]

# Data extraction patterns
EXTRACTION_PATTERNS = {
    'time_patterns': [
        r'\d+\s*(hour|day|minute)s?\s*(ago|before)',
        r'(yesterday|today)'
    ],
    'quantity_patterns': [
        r'\d+[\s,]*\d*\s*(piece|box|bag|unit|kg|ton|meter|yard)s?',
        r'quantity[:\s]*(\d+[\s,]*\d*\s*\w+)'
    ],
    'rfq_id_pattern': r'rfq_id[=:](\d+)',
    'quotes_pattern': r'(\d+)\s*quotes?\s*left'
}

# Verification keywords
VERIFICATION_KEYWORDS = {
    'email_confirmed': ['email confirmed', 'verified email', 'email verified'],
    'experienced': ['experienced', 'expert', 'professional'],
    'completed': ['completed', 'finished', 'done'],
    'typical_reply': ['typical reply', 'quick reply', 'fast response'],
    'interactive': ['interactive', 'active', 'online']
}
