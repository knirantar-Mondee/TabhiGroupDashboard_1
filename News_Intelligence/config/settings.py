import os

# Base Directories
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CONFIG_DIR)

INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
SRC_DIR = os.path.join(BASE_DIR, "src")

# Input File Paths
RSS_FEEDS_FILE = os.path.join(INPUT_DIR, "rss_feeds.xlsx")
COMPETITORS_FILE = os.path.join(INPUT_DIR, "competitors.xlsx")
SEARCH_QUERIES_FILE = os.path.join(INPUT_DIR, "search_queries.xlsx")

# Output File Paths
DATABASE_FILE = os.path.join(OUTPUT_DIR, "raw_news_database.xlsx")

# Log File Path
LOG_FILE = os.path.join(LOGS_DIR, "scraper.log")

# Scraping Settings
SCRAPE_TIMEOUT = 15  # seconds
MAX_WORKERS = 20     # Max threads for parallel scraping

# HTTP request settings (to reduce blocking by anti-scraping walls)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HTTP_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
