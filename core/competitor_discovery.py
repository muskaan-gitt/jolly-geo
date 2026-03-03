from anthropic import Anthropic
from config.prompts import COMPETITOR_DISCOVERY_SYSTEM, COMPETITOR_DISCOVERY_USER
from config.settings import ANTHROPIC_MODEL, MAX_COMPETITORS


def discover_competitors(
    brand_name: str,
    brand_description: str,
    website_url: str,
    existing_competitors: list[str],
    anthropic_api_key: str,
) -> list[str]:
    """
    Auto-discover competitors using Claude with web search.
    Uses multi-factor analysis: same product category, target audience,
    AI search overlap, pricing tier, and feature overlap.
    """
    needed = MAX_COMPETITORS - len(existing_competitors)
    if needed <= 0:
        return existing_competitors[:MAX_COMPETITORS]

    try:
        client = Anthropic(api_key=anthropic_api_key)
        user_prompt = COMPETITOR_DISCOVERY_USER.format(
            count=needed,
            brand_name=brand_name,
            brand_description=brand_description or "N/A",
            website_url=website_url,
            existing=", ".join(existing_competitors) if existing_competitors else "None",
        )

        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=300,
            system=COMPETITOR_DISCOVERY_SYSTEM,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 3,
            }],
            messages=[{"role": "user", "content": user_prompt}],
        )

        # Extract text from response (may contain tool_use blocks from web search)
        text = ""
        for block in response.content:
            if block.type == "text":
                text += block.text

        text = text.strip()
        lines = [line.strip().lstrip("0123456789.-) ") for line in text.split("\n") if line.strip()]

        # Filter out the brand itself, existing competitors, and junk lines
        brand_lower = brand_name.lower()
        existing_lower = {c.lower() for c in existing_competitors}
        new_competitors = []
        for name in lines:
            # Skip empty, too short, too long, or lines that look like sentences
            if not name or len(name) < 2 or len(name) > 60:
                continue
            if name.lower() == brand_lower:
                continue
            if name.lower() in existing_lower:
                continue
            # Skip lines that look like descriptions rather than names
            if any(word in name.lower() for word in ["http", "www.", "the ", "this ", "here "]):
                continue
            new_competitors.append(name)

        all_competitors = existing_competitors + new_competitors[:needed]
        return all_competitors[:MAX_COMPETITORS]

    except Exception:
        return existing_competitors
