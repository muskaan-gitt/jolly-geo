from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


class PromptCategory(Enum):
    COMMERCIAL = "Commercial Intent"
    COMPARISON = "Comparison Intent"
    INFORMATIONAL = "Informational Intent"


class SourceCategory(Enum):
    OFFICIAL_SITE = "Official Site"
    BLOG = "Blog"
    NEWS = "News"
    REVIEW_SITE = "Review Site"
    FORUM_COMMUNITY = "Forum / Community"
    SOCIAL_MEDIA = "Social Media"
    WIKI = "Wiki / Encyclopedia"
    ECOMMERCE = "E-commerce"
    VIDEO = "Video"
    OTHER = "Other"


class LLMProvider(Enum):
    OPENAI = "ChatGPT (OpenAI)"
    ANTHROPIC = "Claude (Anthropic)"
    GEMINI = "Gemini (Google)"
    PERPLEXITY = "Perplexity"


@dataclass
class BrandInput:
    brand_name: str
    website_url: str
    brand_description: str = ""
    competitors: list[str] = field(default_factory=list)
    prompts: dict = field(default_factory=dict)  # PromptCategory -> list[str]


@dataclass
class Source:
    url: str
    title: str = ""
    category: SourceCategory = SourceCategory.OTHER
    domain: str = ""


@dataclass
class LLMResponse:
    provider: LLMProvider
    prompt: str
    prompt_category: PromptCategory
    raw_response: str
    sources: list[Source] = field(default_factory=list)
    brand_mentioned: bool = False
    brand_cited: bool = False
    competitor_mentions: dict = field(default_factory=dict)  # competitor_name -> bool
    error: Optional[str] = None


@dataclass
class VisibilityScore:
    entity_name: str
    overall_score: float = 0.0
    by_provider: dict = field(default_factory=dict)    # provider_name -> float
    by_category: dict = field(default_factory=dict)    # category_name -> float
    by_prompt: dict = field(default_factory=dict)      # prompt_text -> float


@dataclass
class WeakPoint:
    description: str
    prompt: str
    prompt_category: PromptCategory
    providers: list = field(default_factory=list)
    dominating_competitors: list = field(default_factory=list)
    recommended_service: str = ""
    rationale: str = ""


@dataclass
class StrategyRecommendation:
    priority: str  # "high", "medium", "low"
    service: str   # Jolly SEO service name
    rationale: str
    action_items: list[str] = field(default_factory=list)


@dataclass
class GEOReport:
    brand_input: BrandInput
    responses: list[LLMResponse] = field(default_factory=list)
    brand_visibility: Optional[VisibilityScore] = None
    competitor_visibility: dict = field(default_factory=dict)  # name -> VisibilityScore
    all_sources: list[Source] = field(default_factory=list)
    source_counts_by_category: dict = field(default_factory=dict)
    weak_points: list[WeakPoint] = field(default_factory=list)
    strategy_recommendations: list[StrategyRecommendation] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
