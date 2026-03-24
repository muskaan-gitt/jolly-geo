OPENAI_MODEL = "gpt-4o"
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
GEMINI_MODEL = "gemini-2.0-flash"
PERPLEXITY_MODEL = "sonar-pro"

MAX_RETRIES = 4
RETRY_BACKOFF_SECONDS = [2, 4, 8, 16]
REQUEST_TIMEOUT_SECONDS = 90

MAX_COMPETITORS = 4
PROMPTS_PER_CATEGORY = 3
TOTAL_PROMPTS = 9

JOLLY_SERVICES = [
    "Backlinks",
    "Community Mentions",
    "Blogs",
    "PR / News Mentions",
    "Review Site Presence",
]

LLM_SYSTEM_PROMPT = (
    "When answering this question, please provide a thorough and detailed response. "
    "Include specific sources, references, and URLs that support your answer. "
    "For each claim or recommendation, cite the source URL where possible. "
    "Format your sources as a numbered list at the end of your response under a "
    "'Sources:' heading. Include the full URL for each source."
)

# Domain-to-source-category mapping
NEWS_DOMAINS = {
    "nytimes.com", "bbc.com", "bbc.co.uk", "reuters.com", "techcrunch.com",
    "theverge.com", "forbes.com", "bloomberg.com", "cnbc.com", "wsj.com",
    "wired.com", "arstechnica.com", "mashable.com", "venturebeat.com",
    "businessinsider.com", "inc.com", "entrepreneur.com", "fastcompany.com",
    "zdnet.com", "cnet.com", "engadget.com", "thenextweb.com",
    "huffpost.com", "usatoday.com", "washingtonpost.com", "theguardian.com",
}

REVIEW_DOMAINS = {
    "g2.com", "trustpilot.com", "capterra.com", "yelp.com",
    "tripadvisor.com", "pcmag.com", "tomsguide.com", "wirecutter.com",
    "tomsguide.com", "producthunt.com", "softwareadvice.com",
    "getapp.com", "trustradius.com", "consumerreports.org",
}

FORUM_DOMAINS = {
    "reddit.com", "quora.com", "stackexchange.com", "stackoverflow.com",
    "discourse.org", "hackernews.com", "news.ycombinator.com",
}

SOCIAL_DOMAINS = {
    "twitter.com", "x.com", "linkedin.com", "facebook.com",
    "instagram.com", "youtube.com", "tiktok.com", "pinterest.com",
}

WIKI_DOMAINS = {
    "wikipedia.org", "wikihow.com", "fandom.com",
}

ECOMMERCE_DOMAINS = {
    "amazon.com", "amazon.co.uk", "shopify.com", "ebay.com",
    "walmart.com", "target.com", "bestbuy.com", "etsy.com",
}

BLOG_DOMAINS = {
    "medium.com", "substack.com", "dev.to", "hashnode.dev",
    "wordpress.com", "blogger.com", "ghost.io",
}

VIDEO_DOMAINS = {
    "youtube.com", "youtu.be", "vimeo.com", "dailymotion.com",
}

# ── Google Sheets (lead capture) ──────────────────────────
GOOGLE_SHEETS_CREDENTIALS = "config/google_credentials.json"
GOOGLE_SHEETS_SPREADSHEET_KEY = "1OKGE9gdFvlZqMXtohog3HQ2JiDA6fyW375sat4fCZgA"

PERSONAL_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "icloud.com", "mail.com", "protonmail.com", "zoho.com", "yandex.com",
    "live.com", "msn.com", "me.com", "gmx.com", "inbox.com",
}
