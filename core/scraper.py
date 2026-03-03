import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from anthropic import Anthropic
from config.prompts import BRAND_DESCRIPTION_SYSTEM, BRAND_DESCRIPTION_USER
from config.settings import ANTHROPIC_MODEL


def scrape_brand_description(url: str) -> str:
    """Extract brand description from a website URL."""
    try:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Try meta description first
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content", "").strip():
            return meta_desc["content"].strip()[:500]

        # Try og:description
        og_desc = soup.find("meta", attrs={"property": "og:description"})
        if og_desc and og_desc.get("content", "").strip():
            return og_desc["content"].strip()[:500]

        # Try first meaningful paragraphs from main/article content
        main = soup.find("main") or soup.find("article") or soup.find("body")
        if main:
            paragraphs = main.find_all("p")
            texts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 40:
                    texts.append(text)
                if len(" ".join(texts)) > 400:
                    break
            if texts:
                return " ".join(texts)[:500]

        return ""
    except Exception as e:
        return ""


def research_brand_description(
    brand_name: str, website_url: str, anthropic_api_key: str
) -> str:
    """
    Fallback: use Claude with web search to research a brand when scraping fails.
    Returns a concise description of what the brand does.
    """
    try:
        client = Anthropic(api_key=anthropic_api_key)
        user_prompt = BRAND_DESCRIPTION_USER.format(
            brand_name=brand_name,
            website_url=website_url,
        )

        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=300,
            system=BRAND_DESCRIPTION_SYSTEM,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 3,
            }],
            messages=[{"role": "user", "content": user_prompt}],
        )

        # Extract text from response
        text = ""
        for block in response.content:
            if block.type == "text":
                text += block.text

        description = text.strip()
        # Sanity check: should be a reasonable description, not a long essay
        if description and len(description) > 10:
            return description[:500]
        return ""
    except Exception:
        return ""


def extract_domain(url: str) -> str:
    """Extract the root domain from a URL."""
    try:
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""
