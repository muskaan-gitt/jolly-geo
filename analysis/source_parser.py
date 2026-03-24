from urllib.parse import urlparse
from collections import Counter
from models.data_models import LLMResponse, Source, SourceCategory
from config.settings import (
    NEWS_DOMAINS, REVIEW_DOMAINS, FORUM_DOMAINS, SOCIAL_DOMAINS,
    WIKI_DOMAINS, ECOMMERCE_DOMAINS, BLOG_DOMAINS, VIDEO_DOMAINS,
)


def categorize_all_sources(
    responses: list[LLMResponse],
    brand_domain: str = "",
    competitors: list[str] = None,
) -> list[Source]:
    """Extract, categorize, and deduplicate all sources from LLM responses."""
    all_sources = []
    seen_urls = set()

    for response in responses:
        if response.error:
            continue
        for source in response.sources:
            normalized = _normalize_url(source.url)
            if normalized and normalized not in seen_urls:
                seen_urls.add(normalized)
                source.category = categorize_source(
                    source.url, source.title, brand_domain, competitors or [],
                )
                if not source.domain:
                    source.domain = _extract_domain(source.url)
                all_sources.append(source)

    return all_sources


def categorize_source(
    url: str,
    title: str = "",
    brand_domain: str = "",
    competitors: list[str] = None,
) -> SourceCategory:
    """Categorize a source URL using domain lists, then smart pattern matching."""
    domain = _extract_domain(url)
    path = urlparse(url).path.lower() if url.startswith("http") else ""

    # ── 1. Brand's own site ──
    if brand_domain and domain and (domain == brand_domain or domain.endswith(f".{brand_domain}")):
        return SourceCategory.OFFICIAL_SITE

    # ── 2. Competitor sites ──
    if competitors:
        domain_clean = domain.replace(".", "").replace("-", "").lower()
        for comp in competitors:
            comp_slug = comp.lower().replace(" ", "").replace("-", "")
            if comp_slug and comp_slug in domain_clean:
                return SourceCategory.COMPETITOR_SITE

    # ── 3. Fast pass: known domain lists ──
    if _domain_in_set(domain, VIDEO_DOMAINS):
        return SourceCategory.VIDEO
    if _domain_in_set(domain, NEWS_DOMAINS):
        return SourceCategory.NEWS
    if _domain_in_set(domain, REVIEW_DOMAINS):
        return SourceCategory.REVIEW_SITE
    if _domain_in_set(domain, FORUM_DOMAINS):
        return SourceCategory.FORUM_COMMUNITY
    if _domain_in_set(domain, SOCIAL_DOMAINS):
        return SourceCategory.SOCIAL_MEDIA
    if _domain_in_set(domain, WIKI_DOMAINS):
        return SourceCategory.WIKI
    if _domain_in_set(domain, ECOMMERCE_DOMAINS):
        return SourceCategory.ECOMMERCE
    if _domain_in_set(domain, BLOG_DOMAINS):
        return SourceCategory.BLOG

    # ── 4. TLD-based patterns ──
    if domain.endswith(".gov") or ".gov." in domain:
        return SourceCategory.GOVERNMENT
    if domain.endswith(".edu") or ".edu." in domain or domain.endswith(".ac.uk"):
        return SourceCategory.EDUCATION

    # ── 5. Subdomain patterns ──
    if any(domain.startswith(p) for p in ["docs.", "help.", "support.", "developer.", "learn.", "dev."]):
        return SourceCategory.DOCUMENTATION
    if domain.startswith("blog."):
        return SourceCategory.BLOG
    if domain.startswith("news."):
        return SourceCategory.NEWS
    if any(domain.startswith(p) for p in ["community.", "forum.", "discuss.", "forums."]):
        return SourceCategory.FORUM_COMMUNITY
    if any(domain.startswith(p) for p in ["shop.", "store."]):
        return SourceCategory.ECOMMERCE

    # ── 6. URL path patterns ──
    if any(p in path for p in ["/docs/", "/documentation/", "/help/", "/support/", "/api/", "/reference/", "/guide/", "/tutorial/", "/guides/"]):
        return SourceCategory.DOCUMENTATION
    if any(p in path for p in ["/blog/", "/posts/", "/articles/"]):
        return SourceCategory.BLOG
    if any(p in path for p in ["/forum/", "/community/", "/discuss/", "/t/", "/questions/", "/threads/"]):
        return SourceCategory.FORUM_COMMUNITY
    if any(p in path for p in ["/news/", "/press/", "/media/", "/announcements/", "/newsroom/"]):
        return SourceCategory.NEWS
    if any(p in path for p in ["/shop/", "/product/", "/products/", "/buy/", "/store/", "/pricing/"]):
        return SourceCategory.ECOMMERCE
    if any(p in path for p in ["/review/", "/reviews/", "/compare/", "/vs/", "/versus/", "/alternatives/", "/comparison/"]):
        return SourceCategory.REVIEW_SITE
    if any(p in path for p in ["/wiki/", "/w/"]):
        return SourceCategory.WIKI
    if any(p in path for p in ["/watch", "/video/", "/videos/"]):
        return SourceCategory.VIDEO

    # ── 7. Domain name keyword analysis ──
    domain_words = domain.replace(".", " ").replace("-", " ").lower()
    if any(kw in domain_words for kw in ["review", "rating", "compare", "versus", "alternative"]):
        return SourceCategory.REVIEW_SITE
    if any(kw in domain_words for kw in ["forum", "community", "discuss", "answers"]):
        return SourceCategory.FORUM_COMMUNITY
    if any(kw in domain_words for kw in [
        "news", "journal", "times", "post", "herald", "gazette",
        "tribune", "daily", "press", "wire", "report", "insider",
    ]):
        return SourceCategory.NEWS
    if any(kw in domain_words for kw in ["blog", "digest"]):
        return SourceCategory.BLOG
    if any(kw in domain_words for kw in ["wiki", "pedia"]):
        return SourceCategory.WIKI
    if any(kw in domain_words for kw in ["shop", "store", "market", "buy", "deal"]):
        return SourceCategory.ECOMMERCE
    if any(kw in domain_words for kw in ["scholar", "research", "academic", "science", "arxiv", "pubmed"]):
        return SourceCategory.RESEARCH
    if any(kw in domain_words for kw in ["docs", "developer", "reference", "readme"]):
        return SourceCategory.DOCUMENTATION
    if any(kw in domain_words for kw in ["video", "tube", "stream", "watch"]):
        return SourceCategory.VIDEO

    # ── 8. Title heuristics ──
    title_lower = (title or "").lower()
    if any(w in title_lower for w in [
        "review", "rating", "comparison", "best ", "top 10", "top 5",
        " vs ", "versus", "alternative", "compared",
    ]):
        return SourceCategory.REVIEW_SITE
    if any(w in title_lower for w in ["news", "press release", "announcement", "breaking", "update:", "report:"]):
        return SourceCategory.NEWS
    if any(w in title_lower for w in ["how to", "tutorial", "guide", "getting started", "documentation", "api reference"]):
        return SourceCategory.DOCUMENTATION
    if any(w in title_lower for w in ["study", "research", "paper", "journal", "findings", "whitepaper"]):
        return SourceCategory.RESEARCH
    if any(w in title_lower for w in ["forum", "discussion", "thread", "community"]):
        return SourceCategory.FORUM_COMMUNITY

    # ── 9. .org TLD heuristic ──
    if domain.endswith(".org"):
        return SourceCategory.RESEARCH

    # ── 10. Third-party article catchall ──
    if any(p in path for p in ["/article/", "/post/", "/insight/", "/resource/", "/learn/"]):
        return SourceCategory.THIRD_PARTY_ARTICLE
    # Remaining content sites with deep paths are likely articles
    if domain.endswith((".com", ".io", ".co", ".net")) and len(path.strip("/").split("/")) >= 2:
        return SourceCategory.THIRD_PARTY_ARTICLE

    return SourceCategory.OTHER


def get_source_counts(sources: list[Source]) -> dict:
    """Count sources by category."""
    counts = Counter(s.category.value for s in sources)
    return dict(counts)


def get_top_domains(sources: list[Source], top_n: int = 15) -> list[tuple]:
    """Get most frequently cited domains."""
    domain_counter = Counter(s.domain for s in sources if s.domain)
    return domain_counter.most_common(top_n)


def _extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def _normalize_url(url: str) -> str:
    """Normalize URL for deduplication."""
    try:
        parsed = urlparse(url)
        # Strip fragment and trailing slash
        path = parsed.path.rstrip("/")
        return f"{parsed.scheme}://{parsed.netloc}{path}"
    except Exception:
        return url


def _domain_in_set(domain: str, domain_set: set) -> bool:
    """Check if domain or its parent is in the set."""
    if domain in domain_set:
        return True
    # Check parent domain: sub.example.com -> example.com
    parts = domain.split(".")
    if len(parts) > 2:
        parent = ".".join(parts[-2:])
        return parent in domain_set
    return False
