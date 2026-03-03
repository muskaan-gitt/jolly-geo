import re
from anthropic import Anthropic
from core.llm_clients.base_client import BaseLLMClient
from models.data_models import LLMResponse, LLMProvider, PromptCategory, Source
from core.scraper import extract_domain
from config.settings import ANTHROPIC_MODEL


class AnthropicClient(BaseLLMClient):
    provider = LLMProvider.ANTHROPIC

    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)

    def execute_prompt(
        self,
        prompt: str,
        prompt_category: PromptCategory,
        system_context: str,
    ) -> LLMResponse:
        try:
            response = self.client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=4096,
                system=system_context,
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 5,
                }],
                messages=[{"role": "user", "content": prompt}],
            )

            full_text = ""
            sources = []
            seen_urls = set()

            for block in response.content:
                if block.type == "text":
                    full_text += block.text
                    # Extract citations from text block annotations
                    if hasattr(block, "citations") and block.citations:
                        for cite in block.citations:
                            if hasattr(cite, "url") and cite.url:
                                url = cite.url
                                if url not in seen_urls:
                                    seen_urls.add(url)
                                    sources.append(Source(
                                        url=url,
                                        title=getattr(cite, "title", ""),
                                        domain=extract_domain(url),
                                    ))
                elif block.type == "web_search_tool_result":
                    # Extract sources from web search results
                    if hasattr(block, "content") and block.content:
                        for result in block.content:
                            if hasattr(result, "url") and result.url:
                                url = result.url
                                if url not in seen_urls:
                                    seen_urls.add(url)
                                    sources.append(Source(
                                        url=url,
                                        title=getattr(result, "title", ""),
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
