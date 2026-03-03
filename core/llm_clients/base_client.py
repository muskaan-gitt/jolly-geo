from abc import ABC, abstractmethod
from models.data_models import LLMResponse, LLMProvider, PromptCategory


class BaseLLMClient(ABC):
    """Abstract base class for all LLM clients."""

    provider: LLMProvider

    @abstractmethod
    def execute_prompt(
        self,
        prompt: str,
        prompt_category: PromptCategory,
        system_context: str,
    ) -> LLMResponse:
        """Execute a prompt and return a structured response with sources."""
        raise NotImplementedError

    def _make_response(
        self,
        prompt: str,
        prompt_category: PromptCategory,
        raw_response: str = "",
        sources: list = None,
        error: str = None,
    ) -> LLMResponse:
        return LLMResponse(
            provider=self.provider,
            prompt=prompt,
            prompt_category=prompt_category,
            raw_response=raw_response,
            sources=sources or [],
            error=error,
        )
