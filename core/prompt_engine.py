from anthropic import Anthropic
from models.data_models import PromptCategory
from config.prompts import (
    PROMPT_GENERATION_SYSTEM,
    PROMPT_GENERATION_USER,
)
from config.settings import ANTHROPIC_MODEL


def build_prompt_set(
    brand_name: str,
    brand_description: str,
    competitors: list[str],
    user_prompts: dict,
    anthropic_api_key: str = None,
) -> dict:
    """
    Build a complete set of 9 prompts (3 per category).
    Generates ALL missing prompts in a single Claude API call.
    Falls back to templates using a short category label.
    """
    # Count what we already have from the user
    total_existing = sum(
        len([p for p in user_prompts.get(cat, []) if p.strip()])
        for cat in PromptCategory
    )

    # If user provided all 9, just return them
    if total_existing >= 9:
        return {
            cat: [p.strip() for p in user_prompts.get(cat, []) if p.strip()][:3]
            for cat in PromptCategory
        }

    # Single LLM call to generate all 9 prompts + category label
    generated = {}
    category_label = None
    if anthropic_api_key:
        generated, category_label = _generate_all_prompts_via_llm(
            brand_name, brand_description, competitors, anthropic_api_key
        )

    # Fallback label if LLM didn't return one
    if not category_label:
        category_label = _extract_short_category(brand_description, brand_name)

    # Merge: user prompts take priority → then LLM-generated → then templates
    result = {}
    for category in PromptCategory:
        existing = [p.strip() for p in user_prompts.get(category, []) if p.strip()]
        gen = generated.get(category, [])

        # Add generated prompts that aren't duplicates
        for p in gen:
            if len(existing) >= 3:
                break
            if p not in existing:
                existing.append(p)

        # If still not enough, fill with dynamic fallbacks
        if len(existing) < 3:
            fallbacks = _generate_dynamic_fallback(
                category, category_label, competitors, brand_description,
                offset=len(existing),
            )
            for fb in fallbacks:
                if len(existing) >= 3:
                    break
                if fb not in existing:
                    existing.append(fb)

        # Safety net: if still < 3 after all sources, pad with generic prompts
        generic_fillers = [
            f"What are the best {category_label} available right now?",
            f"How should a business evaluate {category_label} options?",
            f"What do experts recommend when choosing {category_label}?",
        ]
        filler_idx = 0
        while len(existing) < 3 and filler_idx < len(generic_fillers):
            if generic_fillers[filler_idx] not in existing:
                existing.append(generic_fillers[filler_idx])
            filler_idx += 1

        result[category] = existing[:3]

    return result


# ── Single-call LLM generation ──────────────────────────────

def _generate_all_prompts_via_llm(
    brand_name: str,
    brand_description: str,
    competitors: list[str],
    api_key: str,
) -> tuple:
    """
    Generate all 9 prompts + category label in a single Claude call.
    Returns (dict[PromptCategory, list[str]], category_label | None).
    """
    try:
        client = Anthropic(api_key=api_key)
        user_msg = PROMPT_GENERATION_USER.format(
            brand_name=brand_name,
            brand_description=brand_description or "N/A",
            competitors=", ".join(competitors) if competitors else "N/A",
        )
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=800,
            system=PROMPT_GENERATION_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        text = response.content[0].text.strip()
        return _parse_structured_response(text, brand_name)
    except Exception:
        return {}, None


def _parse_structured_response(text: str, brand_name: str) -> tuple:
    """
    Parse the structured LLM response:
        CATEGORY_LABEL: <label>
        COMMERCIAL:
        <3 prompts>
        COMPARISON:
        <3 prompts>
        INFORMATIONAL:
        <3 prompts>
    Returns (dict[PromptCategory, list[str]], category_label | None).
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    category_label = None
    result = {cat: [] for cat in PromptCategory}
    current_section = None

    section_map = {
        "COMMERCIAL": PromptCategory.COMMERCIAL,
        "COMPARISON": PromptCategory.COMPARISON,
        "INFORMATIONAL": PromptCategory.INFORMATIONAL,
    }

    for line in lines:
        # Check for category label line
        if line.upper().startswith("CATEGORY_LABEL"):
            raw = line.split(":", 1)[1].strip() if ":" in line else ""
            if raw:
                # Cap at 5 words
                words = raw.split()
                category_label = " ".join(words[:5])
            continue

        # Check for section headers
        clean_header = line.rstrip(": ").upper()
        if clean_header in section_map:
            current_section = section_map[clean_header]
            continue

        # Clean the line (strip numbering, bullets, etc.)
        clean_line = line.lstrip("0123456789.-) •").strip()
        if not clean_line:
            continue

        # Add to the current section
        if current_section and len(result[current_section]) < 3:
            result[current_section].append(clean_line)

    return result, category_label


# ── Fallback: short category label extraction ───────────────

def _extract_short_category(description: str, brand_name: str) -> str:
    """
    Extract a SHORT 2-4 word category label. Used only when LLM call fails.
    Returns labels like "SEO tools", "GEO optimization services", "CRM platforms".
    """
    if not description:
        return "software tools"

    desc_lower = description.lower()

    # Known category patterns (most specific first)
    patterns = [
        ("geo optimization", "GEO optimization services"),
        ("generative engine optimization", "GEO optimization services"),
        ("ai search optimization", "AI search optimization tools"),
        ("seo tool", "SEO tools"),
        ("seo software", "SEO tools"),
        ("seo platform", "SEO platforms"),
        ("backlink", "SEO tools"),
        ("keyword research", "SEO tools"),
        ("crm", "CRM platforms"),
        ("customer relationship", "CRM platforms"),
        ("project management", "project management tools"),
        ("email marketing", "email marketing tools"),
        ("marketing automation", "marketing automation platforms"),
        ("analytics", "analytics platforms"),
        ("content management", "CMS platforms"),
        ("e-commerce", "e-commerce platforms"),
        ("ecommerce", "e-commerce platforms"),
        ("cloud storage", "cloud storage services"),
        ("cybersecurity", "cybersecurity tools"),
        ("design tool", "design tools"),
        ("graphic design", "design tools"),
        ("video editing", "video editing tools"),
        ("accounting", "accounting software"),
        ("invoicing", "invoicing tools"),
        ("hr software", "HR software"),
        ("recruiting", "recruiting platforms"),
        ("helpdesk", "helpdesk tools"),
        ("customer support", "customer support tools"),
        ("chatbot", "chatbot platforms"),
        ("social media", "social media tools"),
    ]

    for pattern, label in patterns:
        if pattern in desc_lower:
            return label

    # Fallback: take first sentence, remove brand name, take first 4 words
    first_sentence = description.split(".")[0].strip()
    clean = first_sentence
    for variant in [brand_name, brand_name.lower(), brand_name.upper()]:
        clean = clean.replace(variant, "").strip()

    for prefix in ["is a ", "is an ", "is the ", "is ", "- ", "— ", "provides ", "offers "]:
        if clean.lower().startswith(prefix):
            clean = clean[len(prefix):]

    words = clean.strip(" ,.-—").split()
    short = " ".join(words[:4])
    return short if short else "software tools"


# ── Dynamic fallback prompt generation ─────────────────────

def _extract_use_cases(brand_description: str) -> list[str]:
    """Extract specific use cases / capabilities from the brand description."""
    if not brand_description:
        return []

    use_cases = []
    desc = brand_description

    # Split on common delimiters that separate capabilities
    for sep in [",", " and ", " & ", ";", " through ", " including ", " such as "]:
        parts = desc.split(sep)
        if len(parts) > 1:
            for part in parts:
                cleaned = part.strip().strip(".")
                # Only keep phrases that look like capabilities (3-8 words)
                word_count = len(cleaned.split())
                if 2 <= word_count <= 10 and cleaned not in use_cases:
                    use_cases.append(cleaned)

    # If nothing extracted, use the full description
    if not use_cases:
        use_cases = [brand_description.split(".")[0].strip()]

    return use_cases[:5]


def _generate_dynamic_fallback(
    category: PromptCategory,
    category_label: str,
    competitors: list[str],
    brand_description: str,
    offset: int = 0,
) -> list[str]:
    """
    Generate context-aware fallback prompts dynamically from brand info.
    No hardcoded templates — constructs prompts from the available context.
    """
    use_cases = _extract_use_cases(brand_description)
    prompts = []

    if category == PromptCategory.COMMERCIAL:
        # Each prompt targets a different angle: specific capability, audience, evaluation
        if use_cases:
            prompts.append(
                f"Which {category_label} do professionals recommend for {use_cases[0]}?"
            )
        if len(use_cases) > 1:
            prompts.append(
                f"I need a solution for {use_cases[1]} — what are the top-rated {category_label}?"
            )
        else:
            prompts.append(
                f"What {category_label} are industry professionals recommending right now?"
            )
        prompts.append(
            f"What should I evaluate when choosing between {category_label} for my business?"
        )

    elif category == PromptCategory.COMPARISON:
        # Each prompt uses a different competitor where possible
        used_competitors = set()
        for i in range(3):
            idx = (offset + i) % len(competitors) if competitors else -1
            comp = competitors[idx] if competitors and idx >= 0 else None

            # Avoid repeating a competitor — use varied patterns instead
            if comp and comp not in used_competitors:
                used_competitors.add(comp)
                if use_cases:
                    use_case = use_cases[i % len(use_cases)]
                    prompts.append(
                        f"What are the best alternatives to {comp} for {use_case}?"
                    )
                else:
                    prompts.append(
                        f"Which {category_label} compete with {comp} and what are their strengths?"
                    )
            else:
                # No more unique competitors — use varied generic patterns
                fallback_patterns = [
                    f"What are the top {category_label} and how do they compare?",
                    f"Which {category_label} are professionals switching to and why?",
                    f"How do the leading {category_label} differ in features and pricing?",
                ]
                pattern_idx = (i - len(used_competitors)) % len(fallback_patterns)
                prompts.append(fallback_patterns[pattern_idx])

    elif category == PromptCategory.INFORMATIONAL:
        # Each prompt asks about trends/practices tied to the brand's domain
        if use_cases:
            prompts.append(
                f"How are businesses leveraging {use_cases[0]} to stay competitive?"
            )
        else:
            prompts.append(
                f"What trends in {category_label} are shaping the industry right now?"
            )
        prompts.append(
            f"What should companies know about choosing the right {category_label} strategy?"
        )
        if len(use_cases) > 1:
            prompts.append(
                f"What role does {use_cases[1]} play in a modern {category_label} workflow?"
            )
        else:
            prompts.append(
                f"Which {category_label} practices are delivering the best results in 2026?"
            )

    return prompts
