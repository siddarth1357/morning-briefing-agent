# summarizer/llm.py
from openai import OpenAI
import config

_client = None

def get_client():
    """Lazily create the OpenAI SDK client pointed at OpenRouter."""
    global _client
    if _client is None:
        if not config.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not set in .env")
        # Only this part changes: we tell the OpenAI client to
        # talk to OpenRouter instead of OpenAI directly.
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.OPENROUTER_API_KEY,
            timeout=90,
        )
    return _client

def build_prompt(top_stories):
    """
    Builds the system + user messages for the briefing generation call.
    Returns (system_prompt, user_prompt).
    """
    story_lines = []
    for i, story in enumerate(top_stories, 1):
        story_lines.append(
            f"{i}. Source: {story.get('source', '')}\n"
            f"   Title: {story.get('clean_title', '')}\n"
            f"   Link: {story.get('link', '')}\n"
            f"   Published: {story.get('published', '')}\n"
            f"   Summary: {(story.get('clean_summary', '') or '')[:500]}"
        )
    stories_block = "\n".join(story_lines)

    system_prompt = (
        "You are a morning briefing assistant. You produce concise, "
        "accurate, linked news briefs in Markdown. You never invent "
        "links or facts — you only use the story data provided."
    )

    user_prompt = f"""Generate a concise, linked 2-minute brief (~{config.BRIEFING_TARGET_WORDS} words), personalized for {config.USER_PROFILE_DESCRIPTION}.

Requirements:
- Start with a one-line greeting, then a 2-3 sentence "Top story" callout.
- Group the remaining stories under 2-4 short category headings (e.g., AI, Cloud & Security, Payments).
- Each item must be a linked headline: [Title](exact-url-from-story-data) — followed by 1-2 sentences summarizing WHY it matters.
- Use ONLY the links provided below. Never invent or modify a URL.
- Personalize emphasis and ordering toward the user's profile.
- Output Markdown only, no code fences, no preamble, no numbering of the raw data.

Stories:
{stories_block}
"""
    return system_prompt, user_prompt

def summarize_stories(top_stories):
    """
    Calls the LLM to generate the final brief.
    Falls back to a plain template if the LLM call fails.
    """
    print("\n--- STEP 6: SUMMARIZE (LLM) ---")

    if not top_stories:
        print("--- No stories to summarize. ---\n")
        return ""

    system_prompt, user_prompt = build_prompt(top_stories)

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            # Nemotron is a reasoning model: without this flag it burns the
            # whole completion budget (900 tokens on the free tier) on hidden
            # reasoning and returns EMPTY content (finish=length). Disabling
            # reasoning sends all tokens straight to the brief.
            max_tokens=2500,
            extra_body={"reasoning": {"enabled": False}},
        )
        brief = (response.choices[0].message.content or "").strip()
        if not brief:
            raise ValueError("Empty response from LLM")
        print("--- LLM brief generated successfully ---\n")
        return brief

    except Exception as e:
        print(f"  [!] LLM call failed: {e}")
        print("  [!] Falling back to template brief.\n")
        return fallback_template_brief(top_stories)

def fallback_template_brief(top_stories):
    """
    No-LLM fallback: a plain Markdown list of the top stories.
    Keeps the pipeline alive when the LLM is unreachable/rate-limited.
    """
    lines = ["## Top stories", ""]
    for story in top_stories:
        title = story.get("clean_title", "") or story.get("title", "")
        link = story.get("link", "")
        source = story.get("source", "")
        if link:
            lines.append(f"- [{title}]({link}) — {source}")
        else:
            lines.append(f"- {title} — {source}")
    return "\n".join(lines)
