import re
import json
from openai import OpenAI
from core.llm_clients.base_client import BaseLLMClient
from models.data_models import LLMResponse, LLMProvider, PromptCategory, Source
from core.scraper import extract_domain
from config.settings import PERPLEXITY_MODEL, REQUEST_TIMEOUT_SECONDS


class PerplexityClient(BaseLLMClient):
    provider = LLMProvider.PERPLEXITY

    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai",
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    def execute_prompt(
        self,
        prompt: str,
        prompt_category: PromptCategory,
        system_context: str,
    ) -> LLMResponse:
        try:
            response = self.client.chat.completions.create(
                model=PERPLEXITY_MODEL,
                messages=[
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": prompt},
                ],
            )

            full_text = response.choices[0].message.content or ""
            sources = []
            seen_urls = set()

            # Perplexity returns citations as a custom field
            # Access via model_extra since it's not in the standard OpenAI schema
            raw_response = response.model_dump() if hasattr(response, "model_dump") else {}
            citations = raw_response.get("citations", [])

            if citations:
                for url in citations:
                    if isinstance(url, str) and url not in seen_urls:
                        seen_urls.add(url)
                        sources.append(Source(
                            url=url,
                            title="",
                            domain=extract_domain(url),
                        ))

            # Also check for search_results if available
            search_results = raw_response.get("search_results", [])
            if search_results:
                for result in search_results:
                    if isinstance(result, dict):
                        url = result.get("url", "")
                        title = result.get("title", "")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            sources.append(Source(
                                url=url,
                                title=title,
                                domain=extract_domain(url),
                            ))

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
