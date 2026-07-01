import feedparser
import requests
from config.settings import HTTP_HEADERS, SCRAPE_TIMEOUT
from src.utils import logger, parse_date

def fetch_rss_feed(feed_dict):
    """
    Fetch and parse articles from a single RSS feed dictionary.
    Returns a list of parsed article dicts.
    """
    feed_name = feed_dict.get("Feed_Name", "Unknown Source")
    rss_url = feed_dict.get("RSS_URL", "")
    
    if not rss_url:
        logger.warning(f"No URL found for feed: {feed_name}")
        return []
        
    logger.info(f"Fetching RSS feed: {feed_name} ({rss_url})")
    
    try:
        # Fetch RSS XML content using requests to support headers and timeouts
        response = requests.get(
            rss_url, 
            headers=HTTP_HEADERS, 
            timeout=SCRAPE_TIMEOUT
        )
        response.raise_for_status()
        
        # Parse XML with feedparser
        feed_data = feedparser.parse(response.content)
        
        # Check for parse errors
        if feed_data.bozo:
            # Bozo is set to 1 if the XML is not well-formed, but it might still parse some entries
            logger.debug(f"Feed parser reported non-well-formed XML for feed: {feed_name}")
            
        articles = []
        for entry in feed_data.entries:
            # Extract fields with safe fallbacks
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            
            # Summary/Description parsing
            summary = entry.get("summary", "")
            if not summary and "description" in entry:
                summary = entry.get("description", "")
            summary = summary.strip()
            
            # Published Date
            pub_date_raw = entry.get("published", entry.get("updated", None))
            pub_date = parse_date(pub_date_raw)
            
            if not title or not link:
                continue
                
            articles.append({
                "Title": title,
                "Summary": summary,
                "Article_URL": link,
                "Published_Date": pub_date,
                "RSS_Source": feed_name,
                "RSS_URL": rss_url
            })
            
        logger.info(f"Successfully fetched {len(articles)} articles from {feed_name}")
        return articles
        
    except requests.exceptions.RequestException as re_err:
        logger.error(f"Network error fetching feed {feed_name}: {re_err}")
    except Exception as e:
        logger.error(f"Unexpected error parsing feed {feed_name}: {e}")
        
    return []

def aggregate_all_feeds(feeds_list):
    """Fetch articles from multiple feeds and return a combined list with safety delays."""
    import time
    all_articles = []
    for idx, feed in enumerate(feeds_list):
        if idx > 0:
            # Sleep 1.5 seconds to prevent rate-limiting by Google News or target site
            time.sleep(1.5)
        feed_articles = fetch_rss_feed(feed)
        all_articles.extend(feed_articles)
    logger.info(f"Total articles aggregated across all feeds: {len(all_articles)}")
    return all_articles
