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
                source.category = categorize_source(source.url, source.title, brand_domain)
                if not source.domain:
                    source.domain = _extract_domain(source.url)
                all_sources.append(source)

    return all_sources


def categorize_source(url: str, title: str = "", brand_domain: str = "") -> SourceCategory:
    """Categorize a source URL by its type."""
    domain = _extract_domain(url)
    path = urlparse(url).path.lower() if url.startswith("http") else ""

    # Check if it's the brand's own site
    if brand_domain and domain and (domain == brand_domain or domain.endswith(f".{brand_domain}")):
        return SourceCategory.OFFICIAL_SITE

    # Check against known domain lists
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

    # Heuristic checks
    if "/blog/" in path or "/blog" in path or "blog." in domain:
        return SourceCategory.BLOG

    # Check title for clues
    title_lower = (title or "").lower()
    if any(w in title_lower for w in ["review", "rating", "comparison"]):
        return SourceCategory.REVIEW_SITE
    if any(w in title_lower for w in ["news", "press release", "announcement"]):
        return SourceCategory.NEWS

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
