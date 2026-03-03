from anthropic import Anthropic
from models.data_models import PromptCategory
from config.prompts import (
    PROMPT_GENERATION_SYSTEM,
    PROMPT_GENERATION_USER,
    COMMERCIAL_TEMPLATES,
    COMPARISON_TEMPLATES,
    INFORMATIONAL_TEMPLATES,
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

        # If still not enough, fill with templates
        if len(existing) < 3:
            templates = _get_templates(category)
            for tmpl in templates:
                if len(existing) >= 3:
                    break
                filled = _fill_template(tmpl, brand_name, category_label, competitors)
                if filled not in existing:
                    existing.append(filled)

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
        if not clean_line or len(clean_line) < 10:
            continue

        # Filter out prompts that contain the brand name
        if brand_name.lower() in clean_line.lower():
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


# ── Template helpers ────────────────────────────────────────

def _get_templates(category: PromptCategory) -> list[str]:
    if category == PromptCategory.COMMERCIAL:
        return COMMERCIAL_TEMPLATES
    elif category == PromptCategory.COMPARISON:
        return COMPARISON_TEMPLATES
    else:
        return INFORMATIONAL_TEMPLATES


def _fill_template(
    template: str,
    brand_name: str,
    category_label: str,
    competitors: list[str],
) -> str:
    """Fill template placeholders using the short category label."""
    competitor = competitors[0] if competitors else "leading tools"
    return (
        template
        .replace("{brand_name}", brand_name)
        .replace("{competitor}", competitor)
        .replace("{category_label}", category_label)
    )
