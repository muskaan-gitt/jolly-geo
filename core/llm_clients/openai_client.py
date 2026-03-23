import re
from openai import OpenAI
from core.llm_clients.base_client import BaseLLMClient
from models.data_models import LLMResponse, LLMProvider, PromptCategory, Source
from core.scraper import extract_domain
from config.settings import OPENAI_MODEL, REQUEST_TIMEOUT_SECONDS


class OpenAIClient(BaseLLMClient):
    provider = LLMProvider.OPENAI

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key, timeout=REQUEST_TIMEOUT_SECONDS)

    def execute_prompt(
        self,
        prompt: str,
        prompt_category: PromptCategory,
        system_context: str,
    ) -> LLMResponse:
        try:
            # Use responses API with web search for grounded answers
            response = self.client.responses.create(
                model=OPENAI_MODEL,
                tools=[{"type": "web_search"}],
                input=[
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": prompt},
                ],
            )

            # Extract text and citations from the response
            full_text = ""
            sources = []
            seen_urls = set()

            for item in response.output:
                if item.type == "message":
                    for block in item.content:
                        if block.type == "output_text":
                            full_text += block.text
                            # Extract url_citation annotations
                            if hasattr(block, "annotations") and block.annotations:
                                for ann in block.annotations:
                                    if ann.type == "url_citation":
                                        url = ann.url
                                        if url and url not in seen_urls:
                                            seen_urls.add(url)
                                            sources.append(Source(
                                                url=url,
                                                title=ann.title if hasattr(ann, "title") else "",
                                                domain=extract_domain(url),
                                            ))

            # Fallback: parse URLs from text if no annotations found
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
