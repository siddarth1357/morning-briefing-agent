# config.py
import os
from dotenv import load_dotenv

# Load environment variables from a .env file if you create one later
load_dotenv()

# The time you want the agent to run every day (24-hour format)
# For testing, set this to a time 2 minutes from now!
BRIEFING_TIME = "07:00" 

# Later, we will add API keys here, like:
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- STEP 5: RANKING CONFIGURATION ---

# Interest Profile: keywords mapped to importance (0.0 to 1.0)
INTEREST_PROFILE = {
    "ai": 0.9,
    "artificial intelligence": 0.9,
    "machine learning": 0.8,
    "cloud security": 0.9,
    "cybersecurity": 0.9,
    "payments": 0.85,
    "fintech": 0.8,
    "cloud": 0.7,
    "aws": 0.7,
    "azure": 0.7,
    "gcp": 0.7,
    "security": 0.7,
    "openai": 0.9,
    "llm": 0.8,
    "gpt": 0.8,
    "stripe": 0.7,
    "developer": 0.6,
    "engineering": 0.6,
    "startup": 0.5,
}

# Source Weights: trusted sources rank higher
SOURCE_WEIGHTS = {
    "TechCrunch": 1.0,
    "The Verge": 0.95,
    "Hacker News": 0.9,
    "Stripe Blog": 0.9,
    "Cloudflare Blog": 0.95,
    "AWS News": 0.9,
    "OpenAI Blog": 1.0,
}

# Final formula weights (must sum to 1.0)
WEIGHT_INTEREST = 0.50
WEIGHT_SOURCE   = 0.25
WEIGHT_RECENCY  = 0.25

# How many stories to include in the final brief
MAX_STORIES = 12

# Recency decay: half-life in hours
RECENCY_HALF_LIFE_HOURS = 24

# --- STEP 5b: RANKING HARDENING ---

# Max stories from any one source in the final brief.
# Prevents a single aggressive feed from dominating.
MAX_PER_SOURCE = 4

# Titles/summaries containing these patterns are filtered out
# (marketing content, event promos, deal roundups).
JUNK_PATTERNS = [
    "register now",
    "join us",
    "sign up today",
    "prime day",
    "black friday",
    "cyber monday",
    "deal of the day",
    "best deals",
    "save big",
    "limited time offer",
    "tc event",
    "disrupt event",
    "tickets are",
    "early bird",
]

# --- STEP 6: LLM CONFIGURATION (FREE VERSION) ---
LLM_PROVIDER = "openrouter"
LLM_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"  # Verified working. Alternatives: openrouter/free (reasoning; raise max_tokens), google/gemma-4-31b-it:free (often 429)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Brief personalization (used in the Step 6 prompt)
USER_PROFILE_DESCRIPTION = (
    "a hands-on developer who follows AI/LLM progress, cloud and "
    "cybersecurity, and fintech/payments"
)
BRIEFING_TARGET_WORDS = 300  # ~2-minute read

# --- STEP 7: DELIVERY CONFIGURATION ---
EMAIL_ENABLED          = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
EMAIL_FROM             = os.getenv("EMAIL_FROM")
EMAIL_TO               = os.getenv("EMAIL_TO")
EMAIL_APP_PASSWORD     = os.getenv("EMAIL_APP_PASSWORD")

SLACK_ENABLED          = os.getenv("SLACK_ENABLED", "false").lower() == "true"
SLACK_WEBHOOK_URL      = os.getenv("SLACK_WEBHOOK_URL")

BRIEFING_SUBJECT = "☀️ Your Morning Briefing"
