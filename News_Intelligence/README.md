# Competitor News Intelligence Pipeline

A Python-based, business-user-configurable News Intelligence Pipeline designed to read RSS feeds and tracking criteria from Excel sheets, scrape matching competitor news, deduplicate articles, and compile a structured news database.

This project serves as a foundation for a full Market Intelligence & Competitive Context (MICC) platform.

---

## Folder Structure

```text
News_Intelligence/
│
├── config/
│   └── settings.py              # Central settings (timeouts, headers, workers)
│
├── input/
│   ├── competitors.xlsx         # Business classification of tracked competitors
│   ├── rss_feeds.xlsx           # List of active RSS feeds
│   └── search_queries.xlsx      # Structured keywords/operators for matching
│
├── logs/
│   └── scraper.log              # Run history, processing metrics, errors
│
├── output/
│   └── raw_news_database.xlsx   # Deduplicated historical news database
│
├── src/
│   ├── main.py                  # Main pipeline orchestrator
│   ├── rss_reader.py            # RSS parser using feedparser + requests
│   ├── article_scraper.py       # Concurrent scraper (newspaper3k + BeautifulSoup)
│   ├── keyword_matcher.py       # Keyword match engine with boundary matching
│   ├── excel_handler.py         # Reading inputs / memory-efficient appending
│   ├── deduplicator.py          # Stripped URL normalization & deduplication
│   ├── utils.py                 # Time parsers, log setup, Google News resolver
│   └── ai_placeholders.py       # Topic classifier, sentiment placeholders
│
├── README.md                    # Setup and execution guide
└── requirements.txt             # Dependency declarations
```

---

## Configuration Guide

Business users configure the system by modifying the files inside the `input/` directory:

### 1. `rss_feeds.xlsx` (Sheet: `RSS_Feeds`)
Add or remove RSS sources.
- **Active = Yes**: Feeds with `Yes` in the `Active` column will be checked.
- **Active = No**: Feeds with `No` (or any other text) will be ignored.

### 2. `competitors.xlsx` (Sheet: `Competitors`)
List the competitor names under the `Competitor` column and classify them by business line (e.g. `Travel`).

### 3. `search_queries.xlsx` (Sheet: `Search_Queries`)
Define the keywords used to detect competitor activity. Multiple terms are compiled dynamically for each competitor.
- **Query_Type**: Classify terms into `Brand`, `Product`, `Executive`, `Technology`, etc.
- **Search_Query**: The exact keyword phrase to look for (e.g. `Prasad Gundumogula` or `Navan Connect`).

---

## Features

1. **Robust Keyword Matching**: Uses regex word boundaries (`\bterm\b`) to prevent false-positives (e.g. "Ramp" won't match "Trampoline").
2. **Multi-Competitor Tracking**: If an article discusses two competitors (e.g. "Navan partners with Ramp"), the database records both: `Competitor = Navan, Ramp`.
3. **URL Normalization**: Normalizes URLs by removing tracking/ref parameters (e.g. `?utm_source=...`) to ensure deduplication catches duplicate articles.
4. **Google News Resolving**: Automatically follows redirects for Google News URLs (`news.google.com/articles/...`) to scrape from the original news publisher.
5. **Robust Scraper**: Combines the power of `newspaper3k` (for structured text extraction) with a customized `BeautifulSoup` fallback scraper.
6. **Concurrent Scraping**: Runs requests across multiple threads (`ThreadPoolExecutor`) to dramatically speed up processing for large batches of news.

---

## Setup and Installation

### 1. Prerequisite
Ensure you have Python 3.8+ installed on your system.

### 2. Install Dependencies
Open terminal/powershell and run:
```bash
pip install -r requirements.txt
```

---

## How to Run

1. **Bootstrap Templates**: Run the pipeline once. It will automatically detect if the input Excel files are missing and generate default templates containing sample data.
   ```bash
   python src/main.py
   ```
2. **Configure Criteria**: Open the generated files in `input/` and modify them to track your targets.
3. **Run Pipeline**: Run `python src/main.py` again to fetch, match, scrape, and record news.
4. **Verify Database**: View the compiled database under `output/raw_news_database.xlsx`.
5. **Inspect Logs**: Check `logs/scraper.log` to view processing details or debug issues.
