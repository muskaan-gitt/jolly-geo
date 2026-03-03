# Fallback templates — use {category_label} (a SHORT 2-4 word label like "SEO tools").
# These are only used when the LLM generation call fails entirely.

COMMERCIAL_TEMPLATES = [
    "What are the best {category_label} in 2026?",
    "Top {category_label} for small businesses",
    "Which {category_label} offer the best value for money?",
]

COMPARISON_TEMPLATES = [
    "{competitor} vs alternatives — what are better options?",
    "Best alternatives to {competitor} in 2026",
    "How do the top {category_label} compare?",
]

INFORMATIONAL_TEMPLATES = [
    "What are {category_label} and why do they matter?",
    "How to choose the right {category_label} for my needs",
    "What features should I look for in {category_label}?",
]

# ── LLM Prompt Generation (single call for all 9 prompts) ──────────

PROMPT_GENERATION_SYSTEM = (
    "You are a search behavior expert specializing in how real users discover "
    "products and services through AI assistants like ChatGPT, Claude, Gemini, "
    "and Perplexity.\n\n"
    "YOUR TASK: Given a brand and what it does, generate exactly 9 discovery prompts "
    "that a real user might type into an AI assistant. These prompts should be the kind "
    "of queries where the brand MIGHT get mentioned in the AI's answer — but the prompt "
    "itself should NOT contain the brand name.\n\n"
    "OUTPUT FORMAT (follow EXACTLY):\n"
    "CATEGORY_LABEL: <2-4 word product category label, e.g. 'SEO tools', 'CRM platforms', "
    "'GEO optimization services'>\n\n"
    "COMMERCIAL:\n"
    "<prompt 1>\n"
    "<prompt 2>\n"
    "<prompt 3>\n\n"
    "COMPARISON:\n"
    "<prompt 4>\n"
    "<prompt 5>\n"
    "<prompt 6>\n\n"
    "INFORMATIONAL:\n"
    "<prompt 7>\n"
    "<prompt 8>\n"
    "<prompt 9>\n\n"
    "RULES:\n"
    "1. NEVER include the target brand name in any prompt.\n"
    "2. Prompts must be specific to the industry/niche — not generic like 'best software'.\n"
    "3. For Comparison, you may use competitor names or general category terms.\n"
    "4. Each prompt should be a natural question or search query a real person would type.\n"
    "5. CATEGORY_LABEL must be SHORT (2-4 words), plural, and fit grammatically into "
    "'best [label] in 2026' and 'how do [label] compare'.\n\n"
    "EXAMPLES:\n\n"
    "--- Example 1 ---\n"
    "Brand: Ahrefs | Does: All-in-one SEO toolset for backlink analysis, keyword research, "
    "and site auditing | Competitors: SEMrush, Moz, SE Ranking\n\n"
    "CATEGORY_LABEL: SEO tools\n\n"
    "COMMERCIAL:\n"
    "What are the best SEO tools for keyword research in 2026?\n"
    "Which backlink analysis tool is worth investing in for a growing website?\n"
    "Best SEO software for digital marketing agencies\n\n"
    "COMPARISON:\n"
    "How does SEMrush compare to Moz for backlink analysis?\n"
    "What are the best alternatives to SEMrush for site auditing?\n"
    "Top SEO tools comparison — which one is best for enterprise use?\n\n"
    "INFORMATIONAL:\n"
    "How does backlink analysis help improve search rankings?\n"
    "What is technical SEO and why does it matter for website performance?\n"
    "How to choose the right SEO tool for a small business\n\n"
    "--- Example 2 ---\n"
    "Brand: Jolly SEO | Does: GEO optimization service that helps brands appear in "
    "AI-generated answers through backlinks, community mentions, and content | "
    "Competitors: Terakeet, seoClarity\n\n"
    "CATEGORY_LABEL: GEO optimization services\n\n"
    "COMMERCIAL:\n"
    "Best services for improving brand visibility in AI search results\n"
    "Which GEO optimization services are worth paying for in 2026?\n"
    "Top services for getting your brand mentioned by ChatGPT and Perplexity\n\n"
    "COMPARISON:\n"
    "How do GEO optimization companies compare?\n"
    "Terakeet vs other AI search optimization providers\n"
    "Best alternatives to traditional SEO for AI visibility\n\n"
    "INFORMATIONAL:\n"
    "What is generative engine optimization and how does it work?\n"
    "How do brands get cited in ChatGPT responses?\n"
    "How to improve brand visibility in AI-generated answers\n"
    "---"
)

PROMPT_GENERATION_USER = (
    "Generate 9 discovery prompts for this brand.\n\n"
    "Target Brand (DO NOT use this name in the prompts): {brand_name}\n"
    "What they do: {brand_description}\n"
    "Known competitors: {competitors}\n\n"
    "Follow the output format exactly. Start with CATEGORY_LABEL, then COMMERCIAL, "
    "COMPARISON, and INFORMATIONAL sections with 3 prompts each."
)

# ── Competitor Discovery ────────────────────────────────────────────

COMPETITOR_DISCOVERY_SYSTEM = (
    "You are a competitive intelligence analyst specializing in finding the "
    "closest business competitors. Your task is to identify companies that a "
    "user searching for the target brand's product/service would ALSO discover "
    "and compare.\n\n"
    "ANALYSIS FACTORS (consider ALL of these):\n"
    "1. SAME PRODUCT CATEGORY — companies offering the same core service/product\n"
    "2. SAME TARGET AUDIENCE — companies targeting the same buyer persona and company size\n"
    "3. AI SEARCH OVERLAP — companies that appear in AI responses for the same queries\n"
    "4. DIRECT ALTERNATIVES — companies a buyer would evaluate side-by-side\n"
    "5. PRICING TIER — companies in a similar price range / market segment\n"
    "6. FEATURE OVERLAP — companies with substantially overlapping capabilities\n\n"
    "RULES:\n"
    "- Return ONLY real, currently active companies — no defunct or imaginary brands\n"
    "- Prefer companies with a strong online presence (likely to appear in AI answers)\n"
    "- Avoid parent companies or conglomerates unless they compete directly\n"
    "- Avoid generic industry categories or product types\n"
    "- Each competitor must be a specific, named company/brand\n\n"
    "OUTPUT FORMAT:\n"
    "Return ONLY the competitor names, one per line. No numbering, no explanations, "
    "no URLs, no extra text."
)

COMPETITOR_DISCOVERY_USER = (
    "Find exactly {count} competitors for {brand_name}.\n\n"
    "Brand: {brand_name}\n"
    "Website: {website_url}\n"
    "Description: {brand_description}\n\n"
    "Already identified competitors (DO NOT repeat these): {existing}\n\n"
    "Search the web to verify these are real, active competitors that a buyer "
    "would compare against {brand_name}. Return exactly {count} competitor names."
)

# ── Brand Description Fallback ─────────────────────────────────────

BRAND_DESCRIPTION_SYSTEM = (
    "You are a business analyst. Given a brand name and website URL, research "
    "the brand and produce a concise 1-2 sentence description of what the "
    "company does, what product/service they offer, and who their target "
    "audience is.\n\n"
    "RULES:\n"
    "- Be factual and specific — mention the actual product category\n"
    "- Include the target audience (e.g., 'for small businesses', 'for enterprise teams')\n"
    "- Keep it under 200 characters\n"
    "- Return ONLY the description, no preamble"
)

BRAND_DESCRIPTION_USER = (
    "Research this brand and write a concise description:\n\n"
    "Brand: {brand_name}\n"
    "Website: {website_url}\n\n"
    "What does this company do? What product/service do they offer? "
    "Who is their target customer?"
)
