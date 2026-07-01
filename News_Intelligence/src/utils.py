import os
import re
import logging
from datetime import datetime
import requests
import urllib.parse
from config.settings import LOG_FILE, HTTP_HEADERS, SCRAPE_TIMEOUT

# Setup Logger
def setup_logging():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    logger = logging.getLogger("news_scraper")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup is called multiple times
    if not logger.handlers:
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
    return logger

logger = setup_logging()

def initialize_directories(base_dir):
    """Create project directories if they don't exist."""
    dirs = ["input", "output", "logs", "config", "src"]
    for d in dirs:
        path = os.path.join(base_dir, d)
        if not os.path.exists(path):
            os.makedirs(path)
            logger.info(f"Created directory: {path}")

def clean_text(text):
    """Normalize text for consistent keyword matching."""
    if not text:
        return ""
    # Lowercase, replace non-breaking spaces, strip whitespace
    text = text.lower()
    text = text.replace('\xa0', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_date(date_val):
    """Safely convert date string or object to standardized string format YYYY-MM-DD HH:MM:SS."""
    if date_val is None:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    if isinstance(date_val, datetime):
        return date_val.strftime("%Y-%m-%d %H:%M:%S")
        
    date_str = str(date_val).strip()
    
    # Try various date formats
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
        "%d %b %Y",
    ):
        try:
            # Strip timezones if they cause issues
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
            
    # Return string representation of current time as fallback
    logger.debug(f"Failed to parse date: {date_str}, using current time instead.")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def resolve_google_news_url(url):
    """Resolve Google News redirect links to get the actual article URL."""
    if not url:
        return ""
        
    if "news.google.com" not in url:
        return url
        
    # 1. Try googlenewsdecoder package
    try:
        import googlenewsdecoder
        decoded = googlenewsdecoder.gnewsdecoder(url)
        if isinstance(decoded, dict) and decoded.get("status") and decoded.get("decoded_url"):
            resolved_url = decoded.get("decoded_url")
            logger.info(f"Resolved Google News redirect via decoder: {url} -> {resolved_url}")
            return resolved_url
    except Exception as e:
        logger.warning(f"googlenewsdecoder failed for {url}: {e}. Falling back to network request...")

    # 2. Network request fallback (HEAD/GET redirects)
    try:
        response = requests.head(
            url, 
            headers=HTTP_HEADERS, 
            timeout=SCRAPE_TIMEOUT, 
            allow_redirects=True
        )
        if response.status_code == 200:
            resolved_url = response.url
            logger.info(f"Resolved Google News redirect via HEAD: {url} -> {resolved_url}")
            return resolved_url
        else:
            response = requests.get(
                url, 
                headers=HTTP_HEADERS, 
                timeout=SCRAPE_TIMEOUT, 
                allow_redirects=True
            )
            resolved_url = response.url
            logger.info(f"Resolved Google News redirect via GET: {url} -> {resolved_url}")
            return resolved_url
    except Exception as e:
        logger.warning(f"Failed to resolve Google News redirect via network for {url}: {e}. Using original URL.")
        return url

def is_within_past_months(date_str, months=6):
    """Check if a date string in YYYY-MM-DD HH:MM:SS format is within the past N months (N * 30 days)."""
    if not date_str:
        return False
    try:
        from datetime import timedelta
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        cutoff = datetime.now() - timedelta(days=months * 30)
        return dt >= cutoff
    except Exception:
        # Fallback: if we can't parse it, treat it as true so we don't accidentally drop valid entries
        return True

