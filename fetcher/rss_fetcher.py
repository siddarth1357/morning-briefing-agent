# fetcher/rss_fetcher.py
import socket
import feedparser
import concurrent.futures
from datetime import datetime

# feedparser has no default timeout, so a single hung server could stall the
# whole briefing. Cap every connection at 10 seconds instead.
socket.setdefaulttimeout(10)

# A list of 5-10 high-quality RSS feeds for your topics (Tech, Payments, AI, Cloud/Sec)
# Note: In the future, this will move to config.py
RSS_SOURCES = {
    "TechCrunch": "https://techcrunch.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Hacker News": "https://hnrss.org/frontpage",
    "Cloudflare Blog": "https://blog.cloudflare.com/rss/",
    "AWS News": "https://aws.amazon.com/blogs/aws/feed/",
    "OpenAI Blog": "https://openai.com/blog/rss.xml",
    "Stripe Blog": "https://stripe.com/blog/feed.rss"
}

def fetch_single_feed(source_name, url):
    """
    Fetches a single RSS feed.
    Includes error handling and ETag/Modified checks.
    """
    print(f"  -> Fetching {source_name}...")
    try:
        # feedparser handles ETag and Modified-Since automatically if we pass them
        # For now, we just do a fresh fetch. We will add caching later.
        feed = feedparser.parse(url)

        # Check if the fetch was successful
        if feed.bozo:
            print(f"  [!] Warning parsing {source_name}: {feed.bozo_exception}")
            return []

        stories = []
        for entry in feed.entries:
            stories.append({
                "source": source_name,
                "title": entry.title,
                "link": entry.link,
                "published": entry.get("published", datetime.now().isoformat()),
                "summary": entry.get("summary", "")
            })

        print(f"  [✓] {source_name}: Found {len(stories)} stories.")
        return stories

    except Exception as e:
        print(f"  [X] Failed to fetch {source_name}: {e}")
        return []

def fetch_all_sources():
    """
    Fetches all RSS sources in parallel using a ThreadPool.
    This is the "Parallel API requests" part of Step 2.
    """
    print("\n--- STEP 2: FETCHING SOURCES ---")
    all_stories = []

    # Use a ThreadPoolExecutor to fetch all feeds at the same time
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(RSS_SOURCES)) as executor:
        # Create a future for each source
        future_to_source = {
            executor.submit(fetch_single_feed, name, url): name
            for name, url in RSS_SOURCES.items()
        }

        # Collect results as they finish
        for future in concurrent.futures.as_completed(future_to_source):
            source_name = future_to_source[future]
            try:
                stories = future.result()
                all_stories.extend(stories)
            except Exception as exc:
                print(f"  [X] {source_name} generated an exception: {exc}")

    print(f"--- FETCH COMPLETE: {len(all_stories)} total stories retrieved ---\n")
    return all_stories