import re
from models.data_models import (
    LLMResponse, VisibilityScore, PromptCategory, LLMProvider,
)


def analyze_brand_visibility(
    brand_name: str,
    responses: list[LLMResponse],
) -> VisibilityScore:
    """Compute brand visibility scores across all responses."""
    valid = [r for r in responses if r.error is None]
    if not valid:
        return VisibilityScore(entity_name=brand_name)

    # Detect mentions in each response
    for r in valid:
        mentioned, cited = detect_mention(r.raw_response, brand_name)
        r.brand_mentioned = mentioned
        r.brand_cited = cited

    # Overall score
    mentioned_count = sum(1 for r in valid if r.brand_mentioned)
    overall = mentioned_count / len(valid) if valid else 0.0

    # By provider
    by_provider = {}
    for provider in LLMProvider:
        prov_responses = [r for r in valid if r.provider == provider]
        if prov_responses:
            ct = sum(1 for r in prov_responses if r.brand_mentioned)
            by_provider[provider.value] = ct / len(prov_responses)

    # By category
    by_category = {}
    for cat in PromptCategory:
        cat_responses = [r for r in valid if r.prompt_category == cat]
        if cat_responses:
            ct = sum(1 for r in cat_responses if r.brand_mentioned)
            by_category[cat.value] = ct / len(cat_responses)

    # By prompt
    by_prompt = {}
    prompts = set(r.prompt for r in valid)
    for prompt in prompts:
        pr = [r for r in valid if r.prompt == prompt]
        if pr:
            ct = sum(1 for r in pr if r.brand_mentioned)
            by_prompt[prompt] = ct / len(pr)

    return VisibilityScore(
        entity_name=brand_name,
        overall_score=overall,
        by_provider=by_provider,
        by_category=by_category,
        by_prompt=by_prompt,
    )


def analyze_competitor_visibility(
    competitors: list[str],
    responses: list[LLMResponse],
) -> dict:
    """Compute visibility scores for each competitor."""
    valid = [r for r in responses if r.error is None]

    # Detect competitor mentions
    for r in valid:
        r.competitor_mentions = {}
        for comp in competitors:
            mentioned, _ = detect_mention(r.raw_response, comp)
            r.competitor_mentions[comp] = mentioned

    result = {}
    for comp in competitors:
        mentioned_count = sum(1 for r in valid if r.competitor_mentions.get(comp, False))
        overall = mentioned_count / len(valid) if valid else 0.0

        by_provider = {}
        for provider in LLMProvider:
            prov_responses = [r for r in valid if r.provider == provider]
            if prov_responses:
                ct = sum(1 for r in prov_responses if r.competitor_mentions.get(comp, False))
                by_provider[provider.value] = ct / len(prov_responses)

        by_category = {}
        for cat in PromptCategory:
            cat_responses = [r for r in valid if r.prompt_category == cat]
            if cat_responses:
                ct = sum(1 for r in cat_responses if r.competitor_mentions.get(comp, False))
                by_category[cat.value] = ct / len(cat_responses)

        by_prompt = {}
        prompts_set = set(r.prompt for r in valid)
        for prompt in prompts_set:
            pr = [r for r in valid if r.prompt == prompt]
            if pr:
                ct = sum(1 for r in pr if r.competitor_mentions.get(comp, False))
                by_prompt[prompt] = ct / len(pr)

        result[comp] = VisibilityScore(
            entity_name=comp,
            overall_score=overall,
            by_provider=by_provider,
            by_category=by_category,
            by_prompt=by_prompt,
        )

    return result


def detect_mention(text: str, entity_name: str) -> tuple:
    """
    Detect if an entity is mentioned in the text.
    Returns (is_mentioned, is_cited_as_recommendation).
    """
    if not text or not entity_name:
        return False, False

    text_lower = text.lower()
    name_lower = entity_name.lower()

    # Check for exact match (case-insensitive)
    mentioned = name_lower in text_lower

    # Also check common variations
    if not mentioned:
        # Try without spaces: "Brand Name" -> "brandname"
        no_space = name_lower.replace(" ", "")
        mentioned = no_space in text_lower.replace(" ", "")

    if not mentioned:
        # Try hyphenated: "Brand Name" -> "brand-name"
        hyphenated = name_lower.replace(" ", "-")
        mentioned = hyphenated in text_lower

    # Check if cited as recommendation
    cited = False
    if mentioned:
        recommendation_patterns = [
            rf"recommend\w*\s+.*{re.escape(name_lower)}",
            rf"{re.escape(name_lower)}.*(?:is|are)\s+(?:a\s+)?(?:great|excellent|top|best|leading|strong|popular)",
            rf"(?:consider|try|check out|look at|use)\s+{re.escape(name_lower)}",
            rf"{re.escape(name_lower)}\s+(?:stands out|excels|leads|offers)",
            rf"(?:top|best|leading)\s+.*{re.escape(name_lower)}",
        ]
        for pattern in recommendation_patterns:
            if re.search(pattern, text_lower):
                cited = True
                break

    return mentioned, cited
