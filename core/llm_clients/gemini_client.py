import re
from google import genai
from google.genai import types
from core.llm_clients.base_client import BaseLLMClient
from models.data_models import LLMResponse, LLMProvider, PromptCategory, Source
from core.scraper import extract_domain
from config.settings import GEMINI_MODEL, REQUEST_TIMEOUT_SECONDS


class GeminiClient(BaseLLMClient):
    provider = LLMProvider.GEMINI

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def execute_prompt(
        self,
        prompt: str,
        prompt_category: PromptCategory,
        system_context: str,
    ) -> LLMResponse:
        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_context,
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_SECONDS * 1000),
                ),
            )

            full_text = response.text or ""
            sources = []
            seen_urls = set()

            # Extract sources from grounding metadata
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                grounding = getattr(candidate, "grounding_metadata", None)
                if grounding:
                    # Get grounding chunks (direct source references)
                    chunks = getattr(grounding, "grounding_chunks", None)
                    if chunks:
                        for chunk in chunks:
                            web = getattr(chunk, "web", None)
                            if web:
                                url = getattr(web, "uri", "") or ""
                                title = getattr(web, "title", "") or ""
                                if url and url not in seen_urls:
                                    seen_urls.add(url)
                                    sources.append(Source(
                                        url=url,
                                        title=title,
                                        domain=extract_domain(url),
                                    ))

                    # Also check grounding_supports for additional sources
                    supports = getattr(grounding, "grounding_supports", None)
                    if supports:
                        for support in supports:
                            refs = getattr(support, "grounding_chunk_indices", [])
                            # These reference the chunks above, already captured

            # Fallback: parse URLs from text
            if not sources:
                sources = self._parse_urls_from_text(full_text)

            return self._make_response(
                prompt=prompt,
                prompt_category=prompt_category,
                raw_response=full_text,
                sources=sources,
            )
        except Exception as e:
            return self._make_response(
                prompt=prompt,
                prompt_category=prompt_category,
                error=str(e),
            )

    def _parse_urls_from_text(self, text: str) -> list[Source]:
        url_pattern = r'https?://[^\s\)\]\"\'<>]+'
        urls = re.findall(url_pattern, text)
        sources = []
        seen = set()
        for url in urls:
            url = url.rstrip(".,;:)")
            if url not in seen:
                seen.add(url)
                sources.append(Source(
                    url=url,
                    title="",
                    domain=extract_domain(url),
                ))
        return sources
