import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from config.settings import HTTP_HEADERS, SCRAPE_TIMEOUT, MAX_WORKERS
from src.utils import logger, resolve_google_news_url

# Gracefully import newspaper
try:
    import nltk
    # Prevent nltk from stalling the run with popups or interactive downloads
    nltk.download('punkt', quiet=True)
    from newspaper import Article
    HAS_NEWSPAPER = True
except Exception as e:
    logger.warning(f"Could not load newspaper3k or NLTK download failed: {e}. Fallback to BeautifulSoup only.")
    HAS_NEWSPAPER = False

def scrape_with_newspaper(url, html_content=None):
    """Attempt to scrape article text using newspaper3k."""
    if not HAS_NEWSPAPER:
        return None
        
    try:
        article = Article(url)
        if html_content:
            article.set_html(html_content)
        else:
            article.download()
            
        article.parse()
        
        # Extract fields
        body = article.text.strip()
        authors = ", ".join(article.authors) if article.authors else "Unknown"
        title = article.title if article.title else ""
        
        if len(body) > 100:  # If we got a decent body content
            return {
                "Title": title,
                "News_Body": body,
                "Author": authors
            }
    except Exception as e:
        logger.debug(f"Newspaper3k failed for {url}: {e}")
        
    return None

def scrape_with_beautifulsoup(url, html_content):
    """Fallback scraping method using BeautifulSoup."""
    try:
        soup = BeautifulSoup(html_content, "lxml")
        
        # 1. Try to find the title
        title_tag = soup.find("h1") or soup.find("title")
        title = title_tag.text.strip() if title_tag else ""
        
        # 2. Extract author
        author = "Unknown"
        # Try metadata tags
        author_meta = (
            soup.find("meta", attrs={"name": "author"}) or 
            soup.find("meta", attrs={"property": "article:author"})
        )
        if author_meta:
            author = author_meta.get("content", "Unknown").strip()
        else:
            # Look for common author classes/tags
            author_tag = (
                soup.find(class_=re.compile("author", re.I)) or 
                soup.find(id=re.compile("author", re.I))
            )
            if author_tag:
                author = author_tag.text.strip()
                
        # Clean author string if it's too long
        if len(author) > 100:
            author = "Unknown"
            
        # 3. Extract body text
        # Remove script, style, header, footer, nav tags
        for element in soup(["script", "style", "header", "footer", "nav", "aside", "form"]):
            element.decompose()
            
        # Try to find a main article container
        article_container = (
            soup.find("article") or 
            soup.find("main") or 
            soup.find(class_=re.compile(r"article-body|post-content|entry-content|article-content", re.I))
        )
        
        paragraphs = []
        if article_container:
            paragraphs = article_container.find_all("p")
            
        # If no container or container didn't have paragraphs, fall back to global paragraphs
        if not paragraphs:
            paragraphs = soup.find_all("p")
            
        body_text = "\n\n".join([p.text.strip() for p in paragraphs if len(p.text.strip()) > 20])
        
        return {
            "Title": title,
            "News_Body": body_text.strip(),
            "Author": author
        }
    except Exception as e:
        logger.error(f"BeautifulSoup parsing failed for {url}: {e}")
        return None

def scrape_article(article_dict):
    """
    Scrapes full content for a single article dictionary.
    Modifies article_dict in-place with scraped fields.
    """
    raw_url = article_dict.get("Article_URL", "")
    
    # 1. Resolve redirect if Google News link
    url = resolve_google_news_url(raw_url)
    article_dict["Article_URL"] = url # Update to actual URL
    
    # Set default values
    article_dict["Author"] = "Unknown"
    article_dict["News_Body"] = "Failed to scrape body content"
    article_dict["Scrape_Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Extract raw summary from RSS to use as a fallback if full scraping fails
    rss_summary = article_dict.get("Summary", "").strip()
    
    try:
        # Download HTML via requests
        response = requests.get(
            url, 
            headers=HTTP_HEADERS, 
            timeout=SCRAPE_TIMEOUT, 
            allow_redirects=True
        )
        
        # If requests failed (404, 403, 429 etc)
        if response.status_code != 200:
            logger.warning(f"Failed to download article page ({response.status_code}): {url}")
            if rss_summary:
                article_dict["News_Body"] = f"[Summary Fallback] {rss_summary}"
            return article_dict
            
        html = response.text
        
        # 1. Try newspaper3k
        scraped_data = scrape_with_newspaper(url, html_content=html)
        
        # 2. Try BeautifulSoup fallback
        if not scraped_data or not scraped_data.get("News_Body"):
            logger.debug(f"Newspaper3k failed/empty for {url}. Trying BeautifulSoup fallback...")
            scraped_data = scrape_with_beautifulsoup(url, html)
            
        if scraped_data and scraped_data.get("News_Body"):
            article_dict["News_Body"] = scraped_data["News_Body"]
            if scraped_data.get("Author"):
                article_dict["Author"] = scraped_data["Author"]
            if scraped_data.get("Title") and not article_dict.get("Title"):
                article_dict["Title"] = scraped_data["Title"]
            logger.info(f"Successfully scraped content for: {url}")
        else:
            logger.warning(f"No content extracted for: {url}")
            if rss_summary:
                article_dict["News_Body"] = f"[Summary Fallback] {rss_summary}"
            
    except Exception as e:
        logger.error(f"Error scraping article {url}: {e}")
        if rss_summary:
            article_dict["News_Body"] = f"[Summary Fallback] {rss_summary}"
        
    return article_dict

def scrape_articles_parallel(articles_list):
    """Run parallel scraper using ThreadPoolExecutor with strict batch timeout and non-blocking status checks."""
    if not articles_list:
        return []
        
    logger.info(f"Starting parallel scraping for {len(articles_list)} matched articles with {MAX_WORKERS} workers...")
    
    scraped_articles = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit tasks
        futures = {executor.submit(scrape_article, art): art for art in articles_list}
        
        # Calculate a generous timeout for the entire batch to finish
        # Minimum 5 minutes, scaling with size (average 2s per article across workers)
        total_timeout = max(300, int(len(articles_list) * 2.5 / MAX_WORKERS))
        logger.info(f"Batch timeout threshold set to {total_timeout} seconds.")
        
        import time
        completed = set()
        total = len(futures)
        pbar = tqdm(total=total, desc="Scraping articles")
        
        start_time = time.time()
        while len(completed) < total and (time.time() - start_time) < total_timeout:
            for future, art in futures.items():
                if future not in completed and future.done():
                    completed.add(future)
                    pbar.update(1)
                    try:
                        result = future.result()
                        scraped_articles.append(result)
                    except Exception as e:
                        logger.error(f"Thread execution error: {e}")
            time.sleep(0.5)
            
        pbar.close()
        
        # Identify and handle hung tasks
        hung_count = total - len(completed)
        if hung_count > 0:
            logger.warning(f"{hung_count} scraping tasks hung/timed out and will be skipped with summary fallback.")
            for future, art in futures.items():
                if future not in completed:
                    art_copy = art.copy()
                    rss_summary = art_copy.get("Summary", "").strip()
                    art_copy["News_Body"] = f"[Summary Fallback] {rss_summary}"
                    art_copy["Author"] = "Unknown"
                    art_copy["Scrape_Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    scraped_articles.append(art_copy)
                    
    return scraped_articles
