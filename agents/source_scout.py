"""
AI-powered source scouting using SerpAPI and RSS feed discovery for Clearfeed.
"""
import os
from typing import List, Dict

try:
    from serpapi import GoogleSearch
except ImportError:
    raise ImportError("google-search-results package not installed. Please install with 'pip install google-search-results'.")

try:
    from feedfinder2 import find_feeds
except ImportError:
    def find_feeds(url):
        return []  # fallback if feedfinder2 is not installed

SERPAPI_KEY = os.environ.get('SERPAPI_KEY')

def scout_sources_for_topic(topic: str, max_results: int = 10) -> List[str]:
    """
    Search for candidate news sources using SerpAPI for a given topic.
    Returns a list of URLs. Prints progress for debugging.
    """
    if not SERPAPI_KEY:
        raise EnvironmentError("SERPAPI_KEY environment variable not set.")
    print(f"[DEBUG] Starting SerpApi search for topic: {topic}")
    params = {
        "engine": "google",
        "q": f"{topic} news rss feed",
        "num": max_results,
        "api_key": SERPAPI_KEY,
    }
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        print(f"[DEBUG] SerpApi search completed. Results: {results.get('search_information', {})}")
    except Exception as e:
        print(f"[SerpAPI Error] {e}")
        return []
    urls = []
    for idx, res in enumerate(results.get('organic_results', [])):
        link = res.get('link')
        if link:
            print(f"[DEBUG] Found URL {idx+1}: {link}")
            urls.append(link)
        if len(urls) >= max_results:
            break
    print(f"[DEBUG] Total URLs to process: {len(urls)}")
    return urls

import concurrent.futures

def discover_feeds(urls: List[str], max_feeds: int = 10, timeout: int = 20, max_feeds_per_site: int = 10) -> List[str]:
    """
    Discover RSS feeds from a list of URLs using feedfinder2. Prints progress. Skips URLs that take too long.
    Limits number of feeds per site to max_feeds_per_site.
    """
    feeds = []
    skipped_non_http = []
    skipped_errors = []
    skipped_timeouts = []
    for idx, url in enumerate(urls):
        if not url.startswith(('http://', 'https://')):
            print(f"[DEBUG] Skipping non-HTTP URL: {url}")
            skipped_non_http.append(url)
            continue
        print(f"[DEBUG] Discovering feeds for URL {idx+1}/{len(urls)}: {url}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(find_feeds, url)
            try:
                found = future.result(timeout=timeout)[:max_feeds_per_site]
                print(f"[DEBUG] Feeds found (limited to {max_feeds_per_site}): {found}")
                feeds.extend(found)
            except concurrent.futures.TimeoutError:
                print(f"[WARN] Feed discovery timed out for {url} (>{timeout}s). Skipping.")
                skipped_timeouts.append(url)
                continue
            except Exception as e:
                err_str = str(e)
                if any(x in err_str for x in ["CERTIFICATE_VERIFY_FAILED", "No connection adapters were found", "NameResolutionError", "TLSV1_ALERT_INTERNAL_ERROR", "Max retries exceeded", "Failed to resolve", "SSLError", "HTTPSConnectionPool"]):
                    print(f"[WARN] Connection/SSL error for {url}: {e}")
                else:
                    print(f"[Feed Discovery Error] {url}: {e}")
                skipped_errors.append(url)
                continue
        if len(feeds) >= max_feeds:
            break
    print(f"[DEBUG] Total feeds discovered: {len(feeds)} (before deduplication)")
    print(f"[SUMMARY] URLs processed: {len(urls)} | Feeds found: {len(feeds)} | Skipped non-HTTP: {len(skipped_non_http)} | Skipped errors: {len(skipped_errors)} | Skipped timeouts: {len(skipped_timeouts)}")
    return feeds[:max_feeds]

def vet_and_format_feeds(feeds: List[str], topic: str) -> List[Dict]:
    """
    Deduplicate and format feed URLs into source dicts.
    Deduplicate by both domain and feed URL.
    """
    vetted = []
    seen_domains = set()
    seen_urls = set()
    for feed_url in feeds:
        try:
            domain = feed_url.split('/')[2]
        except Exception:
            domain = feed_url
        if feed_url in seen_urls or domain in seen_domains:
            print(f"[DEBUG] Skipping duplicate feed or domain: {feed_url}")
            continue
        vetted.append({
            'name': domain,
            'url': feed_url,
            'category': topic,
            'trust_score': 7.0  # Placeholder for trust scoring
        })
        seen_urls.add(feed_url)
        seen_domains.add(domain)
    print(f"[DEBUG] Total vetted sources after deduplication: {len(vetted)}")
    return vetted

def scout_and_vet_sources(topic: str, group: str = None) -> List[Dict]:
    # Try specific-topic feeds first
    candidate_urls = scout_sources_for_topic(topic, max_results=10)
    feeds = discover_feeds(candidate_urls, max_feeds=10, timeout=20, max_feeds_per_site=10) if candidate_urls else []
    if feeds:
        sources = vet_and_format_feeds(feeds, topic)
        return sources
    # Fallback: try general/group feeds and mark for filtering
    if group:
        print(f"[HYBRID] No specific feeds for '{topic}'. Trying general '{group}' feeds and will filter articles.")
        gen_urls = scout_sources_for_topic(group, max_results=3)
        gen_feeds = discover_feeds(gen_urls, max_feeds=3, timeout=10, max_feeds_per_site=3) if gen_urls else []
        sources = vet_and_format_feeds(gen_feeds, group)
        # Mark sources for filtering by topic
        for s in sources:
            s['filter_topic'] = topic
        return sources
    print(f"[HYBRID] No feeds found for '{topic}' and no group fallback.")
    return []
    """
    Main entry: scouts and vets sources for a topic.
    Returns a list of vetted source dicts.
    """
    candidate_urls = scout_sources_for_topic(topic)
    if not candidate_urls:
        print("No candidate URLs found for topic.")
        return []
    feeds = discover_feeds(candidate_urls)
    if not feeds:
        print("No RSS feeds discovered from candidate URLs.")
        return []
    sources = vet_and_format_feeds(feeds, topic)
    return sources
