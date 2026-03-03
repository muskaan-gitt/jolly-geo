from models.data_models import (
    WeakPoint, StrategyRecommendation, VisibilityScore,
    PromptCategory, SourceCategory,
)
from collections import Counter


def generate_recommendations(
    weak_points: list[WeakPoint],
    source_counts: dict,
    brand_visibility: VisibilityScore,
    brand_name: str,
) -> list[StrategyRecommendation]:
    """Generate strategy recommendations mapped to Jolly SEO services."""
    recommendations = []
    service_reasons = {}  # service -> list of reasons

    # Aggregate weak points by recommended service
    for wp in weak_points:
        service = wp.recommended_service
        if service not in service_reasons:
            service_reasons[service] = []
        service_reasons[service].append(wp)

    # Generate recommendations per service
    for service, weak_pts in service_reasons.items():
        priority = _calculate_priority(weak_pts, brand_visibility)
        rationale = _build_rationale(service, weak_pts, brand_name)
        action_items = _build_action_items(service, weak_pts, brand_name)

        recommendations.append(StrategyRecommendation(
            priority=priority,
            service=service,
            rationale=rationale,
            action_items=action_items,
        ))

    # Add recommendations based on source gaps even if no weak points mapped
    _add_source_gap_recommendations(recommendations, source_counts, brand_name)

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda r: priority_order.get(r.priority, 3))

    # Deduplicate by service
    seen_services = set()
    unique = []
    for rec in recommendations:
        if rec.service not in seen_services:
            seen_services.add(rec.service)
            unique.append(rec)

    return unique


def _calculate_priority(weak_points: list[WeakPoint], brand_vis: VisibilityScore) -> str:
    """Determine priority based on severity."""
    # Count commercial intent gaps (highest impact)
    commercial_gaps = sum(
        1 for wp in weak_points
        if wp.prompt_category == PromptCategory.COMMERCIAL
    )
    # Count multi-provider gaps
    multi_provider = sum(
        1 for wp in weak_points
        if len(wp.providers) >= 3
    )

    if commercial_gaps >= 2 or multi_provider >= 2 or brand_vis.overall_score < 0.3:
        return "high"
    elif commercial_gaps >= 1 or len(weak_points) >= 3:
        return "medium"
    else:
        return "low"


def _build_rationale(service: str, weak_points: list[WeakPoint], brand_name: str) -> str:
    """Build a clear rationale for the recommendation."""
    rationales = {
        "Backlinks": (
            f"{brand_name} has low domain authority signals, causing AI models to "
            f"overlook it in favor of competitors with stronger backlink profiles. "
            f"High-authority backlinks improve how LLMs rank and cite brands."
        ),
        "Community Mentions": (
            f"{brand_name} lacks presence in community platforms like Reddit, Quora, "
            f"and forums. AI models heavily reference community discussions when "
            f"answering user queries. Organic community mentions build trust signals."
        ),
        "Blogs": (
            f"{brand_name} needs more in-depth blog content that directly addresses "
            f"comparison and informational queries. AI models cite detailed blog posts "
            f"as primary sources when comparing products."
        ),
        "PR / News Mentions": (
            f"{brand_name} lacks press coverage and news mentions. AI models use "
            f"authoritative news sources as trust signals. PR coverage can significantly "
            f"boost brand visibility in AI responses."
        ),
        "Review Site Presence": (
            f"{brand_name} needs stronger presence on review platforms like G2, "
            f"Capterra, and Trustpilot. AI models frequently cite review sites when "
            f"answering commercial intent queries about product quality and value."
        ),
    }

    base = rationales.get(service, f"Improve {service} for {brand_name}.")

    # Add specific context from weak points
    competitor_names = set()
    for wp in weak_points:
        competitor_names.update(wp.dominating_competitors)
    if competitor_names:
        base += f" Currently, {', '.join(list(competitor_names)[:3])} dominate these queries."

    return base


def _build_action_items(service: str, weak_points: list[WeakPoint], brand_name: str) -> list[str]:
    """Generate specific action items for each service."""
    actions = {
        "Backlinks": [
            f"Build high-authority backlinks from industry-relevant websites to {brand_name}'s key pages",
            "Target backlinks from domains that LLMs frequently cite as sources",
            "Focus on editorial backlinks from authoritative publications in the industry",
            "Create linkable assets (research, data studies, tools) that naturally attract links",
        ],
        "Community Mentions": [
            f"Create organic discussion threads about {brand_name} on Reddit in relevant subreddits",
            f"Answer questions on Quora and forums where {brand_name}'s product category is discussed",
            "Engage authentically in community discussions — provide value, not just promotion",
            "Monitor and respond to brand mentions in online communities",
        ],
        "Blogs": [
            f"Publish in-depth comparison posts: '{brand_name} vs [Competitor]' for each major competitor",
            f"Create authoritative 'best of' and buyer's guide content that features {brand_name}",
            "Write detailed how-to guides and tutorials that demonstrate product value",
            "Publish data-driven content that can be cited as a primary source by AI models",
        ],
        "PR / News Mentions": [
            f"Issue press releases for {brand_name}'s key product updates and milestones",
            "Pitch story angles to industry journalists and tech publications",
            "Contribute expert commentary and thought leadership articles",
            "Build relationships with journalists covering the product category",
        ],
        "Review Site Presence": [
            f"Encourage satisfied customers to leave reviews of {brand_name} on G2, Capterra, and Trustpilot",
            "Ensure complete and optimized profiles on major review platforms",
            "Respond to existing reviews professionally to boost engagement signals",
            "Seek inclusion in editorial review roundups and comparison articles",
        ],
    }

    return actions.get(service, [f"Improve {service} presence for {brand_name}"])


def _add_source_gap_recommendations(
    recommendations: list[StrategyRecommendation],
    source_counts: dict,
    brand_name: str,
):
    """Add recommendations for source types that have zero presence."""
    existing_services = {r.service for r in recommendations}

    gap_map = {
        SourceCategory.BLOG.value: "Blogs",
        SourceCategory.FORUM_COMMUNITY.value: "Community Mentions",
        SourceCategory.NEWS.value: "PR / News Mentions",
        SourceCategory.REVIEW_SITE.value: "Review Site Presence",
    }

    for source_type, service in gap_map.items():
        if source_type not in source_counts and service not in existing_services:
            recommendations.append(StrategyRecommendation(
                priority="medium",
                service=service,
                rationale=(
                    f"No {source_type} sources were found referencing {brand_name} "
                    f"across any LLM responses. This represents a content gap that "
                    f"should be addressed."
                ),
                action_items=_build_action_items(service, [], brand_name),
            ))
