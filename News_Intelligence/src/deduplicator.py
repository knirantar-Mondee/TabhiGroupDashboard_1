import urllib.parse
from src.utils import logger

class Deduplicator:
    def __init__(self, existing_urls):
        """
        existing_urls: A set of URL strings already present in the database.
        """
        self.existing_normalized = {self.normalize_url(url) for url in existing_urls if url}
        logger.info(f"Initialized Deduplicator with {len(self.existing_normalized)} unique normalized URLs.")

    @staticmethod
    def normalize_url(url):
        """Normalize URL by stripping query parameters, fragments, and trailing slashes."""
        if not url:
            return ""
        try:
            parsed = urllib.parse.urlparse(url.strip())
            # Reconstruct URL ignoring queries and fragments
            normalized = f"{parsed.scheme}://{parsed.netloc.lower()}{parsed.path}"
            # Strip trailing slash
            if normalized.endswith("/"):
                normalized = normalized[:-1]
            return normalized
        except Exception:
            # Fallback to simple strip in case of parsing failures
            return url.strip().lower()

    def is_duplicate(self, url):
        """Check if a URL has already been scraped."""
        normalized = self.normalize_url(url)
        return normalized in self.existing_normalized

    def filter_new_articles(self, articles_list):
        """
        Filters a list of articles, returning only the ones that are not duplicates.
        Logs the number of skipped duplicates.
        """
        new_articles = []
        duplicate_count = 0
        
        # Track URLs in the current run as well to avoid duplicates within the same batch
        seen_in_run = set()
        
        for article in articles_list:
            url = article.get("Article_URL", "")
            normalized = self.normalize_url(url)
            
            if not url:
                continue
                
            if normalized in self.existing_normalized or normalized in seen_in_run:
                duplicate_count += 1
            else:
                new_articles.append(article)
                seen_in_run.add(normalized)
                
        if duplicate_count > 0:
            logger.info(f"Filtered out {duplicate_count} duplicate articles from this run.")
            
        return new_articles
