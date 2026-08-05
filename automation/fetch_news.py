#!/usr/bin/env python3
"""
Weekly news fetcher for KPMG audit scandal coverage.
Saves new articles to sources/new/ with date-stamped filenames.
"""
import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
SOURCES_DIR = PROJECT_ROOT / "sources" / "new"
SOURCES_DIR.mkdir(parents=True, exist_ok=True)

# Search queries for KPMG scandal
SEARCH_QUERIES = [
    "KPMG audit scandal Australia",
    "KPMG whistleblower Lendlease",
    "KPMG Andrew Yates resignation",
    "KPMG Eileen Hoggett demoted",
    "KPMG Martin Sheppard chairman",
    "KPMG FairCall whistleblower hotline",
    "KPMG ASIC investigation audit",
    "KPMG Capgemini defence unit sale",
    "Deb O'Neill KPMG parliamentary committee",
    "Barbara Pocock big four audit separation",
]

# Known article URLs to avoid duplicates (populate from original sources)
KNOWN_URLS_FILE = PROJECT_ROOT / "research" / "known_urls.json"
KNOWN_URLS_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_known_urls():
    if KNOWN_URLS_FILE.exists():
        with open(KNOWN_URLS_FILE) as f:
            return set(json.load(f))
    return set()

def save_known_urls(urls):
    with open(KNOWN_URLS_FILE, 'w') as f:
        json.dump(list(urls), f, indent=2)

def fetch_the_australian_search(query):
    """Fetch search results from The Australian (limited without subscription)."""
    # Note: The Australian has paywall. This is a placeholder for RSS/API if available.
    # For now, we'll use Google News RSS or similar free sources.
    pass

def fetch_google_news_rss(query):
    """Fetch from Google News RSS."""
    url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en-AU&gl=AU&ceid=AU:en"
    try:
        resp = requests.get(url, timeout=10)
        return resp.text
    except Exception as e:
        print(f"Error fetching Google News for '{query}': {e}")
        return None

def parse_rss_items(rss_xml, query):
    """Parse RSS feed for article items."""
    if not rss_xml:
        return []
    soup = BeautifulSoup(rss_xml, 'xml')
    items = soup.find_all('item')
    articles = []
    for item in items:
        title = item.title.text if item.title else ""
        link = item.link.text if item.link else ""
        pub_date = item.pubDate.text if item.pubDate else ""
        description = item.description.text if item.description else ""
        articles.append({
            'title': title,
            'url': link,
            'date': pub_date,
            'snippet': description[:500],
            'query': query,
            'fetched_at': datetime.now().isoformat()
        })
    return articles

def fetch_apf_hansard():
    """Check APH for new Hansard transcripts."""
    # This would check specific committee pages for new transcripts
    # Placeholder for now
    pass

def main():
    known_urls = load_known_urls()
    new_articles = []
    
    print(f"[{datetime.now()}] Starting weekly news fetch...")
    
    for query in SEARCH_QUERIES:
        print(f"  Query: {query}")
        rss = fetch_google_news_rss(query)
        articles = parse_rss_items(rss, query)
        
        for art in articles:
            url_hash = hashlib.md5(art['url'].encode()).hexdigest()
            if art['url'] not in known_urls:
                # New article - save it
                date_str = datetime.now().strftime("%Y%m%d")
                filename = f"{date_str}_{url_hash[:8]}.json"
                filepath = SOURCES_DIR / filename
                
                with open(filepath, 'w') as f:
                    json.dump(art, f, indent=2)
                
                new_articles.append(art)
                known_urls.add(art['url'])
                print(f"    NEW: {art['title'][:80]}")
    
    if new_articles:
        save_known_urls(known_urls)
        print(f"[{datetime.now()}] Saved {len(new_articles)} new articles")
        
        # Also create a summary markdown
        summary_file = SOURCES_DIR / f"{datetime.now().strftime('%Y%m%d')}_summary.md"
        with open(summary_file, 'w') as f:
            f.write(f"# Weekly News Summary - {datetime.now().strftime('%Y-%m-%d')}\n\n")
            for art in new_articles:
                f.write(f"## {art['title']}\n")
                f.write(f"- **Source**: {art['url']}\n")
                f.write(f"- **Date**: {art['date']}\n")
                f.write(f"- **Query**: {art['query']}\n")
                f.write(f"- **Snippet**: {art['snippet']}\n\n")
    else:
        print(f"[{datetime.now()}] No new articles found")

if __name__ == "__main__":
    main()