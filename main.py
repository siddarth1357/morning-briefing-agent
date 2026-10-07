# main.py
import sys
import time
import schedule
from datetime import datetime
import config

from fetcher.rss_fetcher import fetch_all_sources
from processor.parser import clean_stories
from processor.deduper import deduplicate_stories
from processor.ranker import rank_clusters
from memory.db import filter_unseen, mark_as_shown
from summarizer.llm import summarize_stories, fallback_template_brief
from delivery.dispatcher import deliver_brief

# Windows consoles often default to cp1252, which cannot encode emoji.
# Force UTF-8 so the briefing output prints correctly on Windows.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass

def run_briefing_agent():
    """
    The full Steps 1-7 pipeline: Trigger, Fetch, Parse & Dedupe,
    Memory Check, Rank, Summarize, Deliver + Log.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{current_time}] 🚀 Morning Briefing Agent Started!")

    # --- STEP 1: Trigger ---
    print("Executing Step 1: Cron Trigger fired successfully.")

    # --- STEP 2: Fetch ---
    stories = fetch_all_sources()

    # --- STEP 3: Parse & Dedupe ---
    cleaned_stories = clean_stories(stories)
    clusters = deduplicate_stories(cleaned_stories)

    # --- STEP 4: Memory Check ---
    new_clusters = filter_unseen(clusters)

    # --- STEP 5: Rank ---
    top_stories = rank_clusters(new_clusters)

    # --- STEP 6: Summarize ---
    brief = summarize_stories(top_stories)
    if brief is None:
        brief = fallback_template_brief(top_stories)

    # --- STEP 7: Deliver ---
    results = deliver_brief(brief)

    # --- STEP 7b: Only mark as shown if delivery succeeded ---
    if any(results.values()):
        mark_as_shown(top_stories)
        print(f"  → Marked {len(top_stories)} stories as shown.\n")
    else:
        print("  [!] Delivery failed — stories NOT marked, will retry tomorrow.\n")

def job():
    """Wrapper function for the scheduler"""
    run_briefing_agent()

if __name__ == "__main__":
    print("🤖 Morning Briefing Agent is up and running.")
    print(f"⏰ Scheduled to run daily at {config.BRIEFING_TIME}.")
    print("Press Ctrl+C to exit.\n")

    # Schedule the job
    schedule.every().day.at(config.BRIEFING_TIME).do(job)

    # Keep the script running so the scheduler can do its job
    while True:
        schedule.run_pending()
        time.sleep(1)
