# processor/ranker.py
import math
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import config

def parse_published_date(date_string):
    """
    RSS feeds use inconsistent date formats. Try to parse them all.
    Returns a timezone-aware datetime, or None if unparseable.
    """
    if not date_string:
        return None

    # Try RFC 822 format (most common in RSS: "Wed, 07 Oct 2026 11:00:00 GMT")
    try:
        return parsedate_to_datetime(date_string)
    except (TypeError, ValueError):
        pass

    # Try ISO 8601 format
    try:
        return datetime.fromisoformat(date_string.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        pass

    return None

def compute_recency_score(published_str, half_life_hours=None):
    """
    Exponential decay: a story from `half_life_hours` ago scores 0.5.
    A story from 2x half-life ago scores 0.25, etc.
    Returns 0.0 for very old or unparseable dates.
    """
    if half_life_hours is None:
        half_life_hours = config.RECENCY_HALF_LIFE_HOURS

    published = parse_published_date(published_str)
    if not published:
        return 0.3  # Unknown date → mild penalty but not excluded

    # Make timezone-aware comparison
    now = datetime.now(timezone.utc)
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)

    age_hours = (now - published).total_seconds() / 3600

    # If the story is from the future (clock skew), treat as brand new
    if age_hours < 0:
        age_hours = 0

    # Exponential decay formula
    score = 0.5 ** (age_hours / half_life_hours)
    return max(0.0, min(1.0, score))

def compute_interest_score(story):
    """
    Counts how many interest keywords appear in the story text.
    Uses word-boundary matching so short keywords like 'ai' don't
    false-positive on 'available', 'email', 'wait', etc.
    """
    text = (
        (story.get("clean_title", "") or story.get("title", "")) + " " +
        (story.get("clean_summary", "") or story.get("summary", ""))
    ).lower()

    if not text.strip():
        return 0.0

    matches = []
    for keyword, weight in config.INTEREST_PROFILE.items():
        # Word-boundary regex: \b keyword \b
        # Escape keyword in case it contains regex special chars
        pattern = r"\b" + re.escape(keyword) + r"\b"
        if re.search(pattern, text):
            matches.append(weight)

    if not matches:
        return 0.1

    base_score = max(matches)
    diversity_bonus = min(0.1, 0.02 * (len(matches) - 1))
    return min(1.0, base_score + diversity_bonus)

def compute_source_score(story):
    """
    Returns a 0.0–1.0 score based on the source's trust weight.
    Unknown sources get a low default.
    """
    source = story.get("source", "")
    return config.SOURCE_WEIGHTS.get(source, 0.4)

def is_junk_story(story):
    """
    Returns True if the story looks like marketing/event content
    rather than actual news.
    """
    text = (
        (story.get("clean_title", "") or story.get("title", "")) + " " +
        (story.get("clean_summary", "") or story.get("summary", ""))
    ).lower()

    for pattern in config.JUNK_PATTERNS:
        if pattern in text:
            return True
    return False

def score_story(story):
    """
    Combines all sub-scores into a single relevance score.
    """
    interest = compute_interest_score(story)
    source = compute_source_score(story)
    recency = compute_recency_score(story.get("published", ""))

    final = (
        interest * config.WEIGHT_INTEREST +
        source   * config.WEIGHT_SOURCE +
        recency  * config.WEIGHT_RECENCY
    )

    # Attach scores for debugging/transparency
    story["_scores"] = {
        "interest": round(interest, 3),
        "source": round(source, 3),
        "recency": round(recency, 3),
        "final": round(final, 3),
    }

    return final

def rank_clusters(clusters):
    """
    Scores clusters, applies junk filter, then enforces MAX_PER_SOURCE
    diversity while selecting the top N stories.
    """
    print("\n--- STEP 5: RANKING & FILTERING ---")

    if not clusters:
        print("--- No clusters to rank. ---\n")
        return []

    # Score each cluster's best story
    scored_clusters = []
    junk_filtered = 0

    for cluster in clusters:
        best_story = None
        best_score = -1.0
        for story in cluster:
            score = score_story(story)
            if score > best_score:
                best_score = score
                best_story = story

        if best_story is None:
            continue

        # Filter junk before ranking
        if is_junk_story(best_story):
            junk_filtered += 1
            continue

        scored_clusters.append((best_score, best_story))

    # Sort by score descending
    scored_clusters.sort(key=lambda x: x[0], reverse=True)

    # --- Diversity-aware selection ---
    source_counts = {}
    top_stories = []

    for score, story in scored_clusters:
        source = story.get("source", "unknown")
        current_count = source_counts.get(source, 0)

        if current_count >= config.MAX_PER_SOURCE:
            continue

        top_stories.append(story)
        source_counts[source] = current_count + 1

        if len(top_stories) >= config.MAX_STORIES:
            break

    print(f"  → Scored {len(clusters)} clusters.")
    print(f"  → Filtered {junk_filtered} junk/promo stories.")
    print(f"  → Selected top {len(top_stories)} stories.")
    if scored_clusters:
        print(f"  → Top score: {scored_clusters[0][0]:.3f}")
    print(f"  → Source distribution: {dict(source_counts)}")
    print(f"--- RANKING COMPLETE ---\n")

    return top_stories
