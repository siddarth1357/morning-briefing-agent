# memory/db.py
import sqlite3
import hashlib
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "briefing_memory.db")

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_db():
    """Creates the table if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shown_stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_hash TEXT UNIQUE NOT NULL,
            source TEXT,
            title TEXT,
            link TEXT,
            shown_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def hash_story(story):
    """
    Creates a stable hash from the story title.
    We use the title (not the link) because different sources
    may cover the same story with different URLs.
    """
    title = story.get("clean_title", "") or story.get("title", "")
    return hashlib.sha256(title.lower().strip().encode("utf-8")).hexdigest()

def filter_unseen(clusters):
    """
    Takes the list of clusters from Step 3.
    Returns only clusters whose stories have NOT been shown in the last 30 days.
    """
    print("\n--- STEP 4: MEMORY CHECK ---")
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    # Calculate the 30-day cutoff
    cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()

    # Fetch all recently shown hashes into memory (fast lookup)
    cursor.execute(
        "SELECT story_hash FROM shown_stories WHERE shown_date >= ?",
        (cutoff_date,)
    )
    seen_hashes = {row["story_hash"] for row in cursor.fetchall()}
    conn.close()

    print(f"  → Found {len(seen_hashes)} stories shown in the last 30 days.")

    # Filter clusters: a cluster is kept if ANY of its stories is unseen
    new_clusters = []
    filtered_count = 0

    for cluster in clusters:
        # Check if this cluster has any story not in the seen_hashes
        unseen_stories = [
            s for s in cluster
            if hash_story(s) not in seen_hashes
        ]

        if unseen_stories:
            new_clusters.append(cluster)
        else:
            filtered_count += 1

    print(f"  → Filtered out {filtered_count} previously-shown clusters.")
    print(f"--- MEMORY CHECK COMPLETE: {len(new_clusters)} new clusters remain ---\n")

    return new_clusters

def mark_as_shown(stories):
    """
    Saves the stories that were actually delivered to the user.
    Called at the END of the pipeline (Step 7).
    """
    conn = get_connection()
    cursor = conn.cursor()

    inserted = 0
    for story in stories:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO shown_stories
                (story_hash, source, title, link)
                VALUES (?, ?, ?, ?)
            """, (
                hash_story(story),
                story.get("source", ""),
                story.get("clean_title", "") or story.get("title", ""),
                story.get("link", "")
            ))
            inserted += 1
        except sqlite3.Error as e:
            print(f"  [!] Failed to save story: {e}")

    conn.commit()
    conn.close()
    print(f"  → Saved {inserted} stories to memory database.")
