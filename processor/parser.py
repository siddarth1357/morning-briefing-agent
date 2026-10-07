# processor/parser.py
from bs4 import BeautifulSoup

def clean_html(raw_html):
    """
    Strips HTML tags, scripts, and styles from the raw RSS summary.
    Returns clean, readable text.
    """
    if not raw_html:
        return ""

    # Parse with BeautifulSoup
    soup = BeautifulSoup(raw_html, "html.parser")

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Get text and clean up whitespace
    text = soup.get_text(separator=" ")
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    clean_text = " ".join(chunk for chunk in chunks if chunk)

    return clean_text

def clean_stories(stories):
    """
    Takes the raw list of stories from Step 2 and cleans each one.
    """
    print("\n--- STEP 3a: PARSING & CLEANING HTML ---")
    cleaned_count = 0

    for story in stories:
        original_summary = story.get("summary", "")
        story["clean_summary"] = clean_html(original_summary)

        # Also clean the title just in case it has HTML entities
        story["clean_title"] = clean_html(story.get("title", ""))

        if len(story["clean_summary"]) > 0:
            cleaned_count += 1

    print(f"--- PARSED: {cleaned_count}/{len(stories)} stories have clean text ---\n")
    return stories
