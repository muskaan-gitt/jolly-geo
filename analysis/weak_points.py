from models.data_models import (
    LLMResponse, VisibilityScore, WeakPoint, PromptCategory, LLMProvider, Source,
    SourceCategory,
)
from collections import defaultdict


def identify_weak_points(
    brand_name: str,
    competitors: list[str],
    responses: list[LLMResponse],
    brand_visibility: VisibilityScore,
    competitor_visibility: dict,
    all_sources: list[Source],
) -> list[WeakPoint]:
    """Identify where the brand is weak relative to competitors."""
    weak_points = []
    valid = [r for r in responses if r.error is None]

    # Group responses by prompt
    by_prompt = defaultdict(list)
    for r in valid:
        by_prompt[r.prompt].append(r)

    # 1. Per-prompt gaps: brand not mentioned but competitors are
    for prompt, prompt_responses in by_prompt.items():
        brand_missing_providers = []
        dominating_competitors = set()

        for r in prompt_responses:
            if not r.brand_mentioned:
                brand_missing_providers.append(r.provider)
                for comp, mentioned in r.competitor_mentions.items():
                    if mentioned:
                        dominating_competitors.add(comp)

        if brand_missing_providers and dominating_competitors:
            provider_names = [p.value for p in brand_missing_providers]
            category = prompt_responses[0].prompt_category

            weak_points.append(WeakPoint(
                description=(
                    f"Brand is not mentioned for this prompt on "
                    f"{', '.join(provider_names)}, while "
                    f"{', '.join(dominating_competitors)} "
                    f"{'are' if len(dominating_competitors) > 1 else 'is'} cited."
                ),
                prompt=prompt,
                prompt_category=category,
                providers=brand_missing_providers,
                dominating_competitors=list(dominating_competitors),
                recommended_service=_map_to_service(category, all_sources),
            ))

    # 2. Category-level gaps
    for cat in PromptCategory:
        brand_cat_score = brand_visibility.by_category.get(cat.value, 0)
        if brand_cat_score < 0.5:
            # Check if competitors do better
            better_competitors = []
            for comp_name, comp_vis in competitor_visibility.items():
                comp_cat_score = comp_vis.by_category.get(cat.value, 0)
                if comp_cat_score > brand_cat_score:
                    better_competitors.append(comp_name)

            if better_competitors:
                weak_points.append(WeakPoint(
                    description=(
                        f"Low visibility ({brand_cat_score:.0%}) in {cat.value} queries. "
                        f"{', '.join(better_competitors)} perform better in this category."
                    ),
                    prompt=f"[All {cat.value} prompts]",
                    prompt_category=cat,
                    providers=[],
                    dominating_competitors=better_competitors,
                    recommended_service=_map_category_to_service(cat),
                ))

    # 3. Provider-specific gaps
    for provider in LLMProvider:
        brand_prov_score = brand_visibility.by_provider.get(provider.value, 0)
        if brand_prov_score < 0.34:  # Missing from >66% of prompts on this provider
            weak_points.append(WeakPoint(
                description=(
                    f"Very low visibility ({brand_prov_score:.0%}) on {provider.value}. "
                    f"The brand is barely mentioned in responses from this AI model."
                ),
                prompt=f"[All prompts on {provider.value}]",
                prompt_category=PromptCategory.COMMERCIAL,
                providers=[provider],
                dominating_competitors=[],
                recommended_service="Backlinks",
                rationale=(
                    "Improving domain authority through backlinks helps visibility "
                    "across all LLMs."
                ),
            ))

    # 4. Source-type gaps
    brand_source_types = set()
    for source in all_sources:
        brand_source_types.add(source.category)

    missing_types = {
        SourceCategory.BLOG: "Blogs",
        SourceCategory.FORUM_COMMUNITY: "Community Mentions",
        SourceCategory.NEWS: "PR / News Mentions",
        SourceCategory.REVIEW_SITE: "Review Site Presence",
    }

    for stype, service in missing_types.items():
        if stype not in brand_source_types:
            weak_points.append(WeakPoint(
                description=(
                    f"No {stype.value} sources reference the brand. "
                    f"This is a gap that competitors may be filling."
                ),
                prompt="[Source analysis]",
                prompt_category=PromptCategory.INFORMATIONAL,
                providers=[],
                dominating_competitors=[],
                recommended_service=service,
            ))

    return weak_points


def _map_to_service(category: PromptCategory, sources: list[Source]) -> str:
    """Map a weak point to the most relevant Jolly SEO service."""
    if category == PromptCategory.COMMERCIAL:
        return "Backlinks"
    elif category == PromptCategory.COMPARISON:
        return "Blogs"
    else:
        return "Community Mentions"


def _map_category_to_service(category: PromptCategory) -> str:
    if category == PromptCategory.COMMERCIAL:
        return "Backlinks"
    elif category == PromptCategory.COMPARISON:
        return "Blogs"
    else:
        return "Community Mentions"
