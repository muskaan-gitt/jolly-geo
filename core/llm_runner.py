import time
from typing import Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.data_models import BrandInput, LLMResponse, LLMProvider, PromptCategory
from core.llm_clients.openai_client import OpenAIClient
from core.llm_clients.anthropic_client import AnthropicClient
from core.llm_clients.gemini_client import GeminiClient
from core.llm_clients.perplexity_client import PerplexityClient
from config.settings import LLM_SYSTEM_PROMPT, MAX_RETRIES, RETRY_BACKOFF_SECONDS


def run_all_prompts(
    brand_input: BrandInput,
    api_keys: dict,
    progress_callback: Optional[Callable] = None,
) -> list[LLMResponse]:
    """
    Run all prompts against all available LLMs in PARALLEL.
    Uses ThreadPoolExecutor with progress updates on the MAIN thread
    (via the as_completed loop) so Streamlit widgets update correctly.
    """
    # Initialize available clients
    clients = []
    client_map = {
        "openai": OpenAIClient,
        "anthropic": AnthropicClient,
        "gemini": GeminiClient,
        "perplexity": PerplexityClient,
    }
    for key_name, ClientClass in client_map.items():
        api_key = api_keys.get(key_name, "").strip()
        if api_key:
            try:
                clients.append(ClientClass(api_key))
            except Exception as e:
                print(f"Warning: Failed to initialize {key_name} client: {e}")

    if not clients:
        return []

    # Collect all prompts
    all_prompts = []
    for category, prompts in brand_input.prompts.items():
        for prompt_text in prompts:
            all_prompts.append((category, prompt_text))

    total = len(all_prompts) * len(clients)

    # Fire all calls in parallel — up to 3 concurrent requests per provider
    max_workers = min(len(clients) * 3, total)
    results = []
    completed_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for category, prompt_text in all_prompts:
            for client in clients:
                future = executor.submit(
                    _execute_with_retry, client, prompt_text, category
                )
                futures[future] = (client.provider, prompt_text, category)

        # as_completed runs on the MAIN thread — safe to update Streamlit widgets
        for future in as_completed(futures):
            completed_count += 1
            provider, prompt_text, category = futures[future]

            if progress_callback:
                progress_callback(
                    completed_count, total,
                    f"[{completed_count}/{total}] {provider.value}: {prompt_text[:45]}..."
                )

            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append(LLMResponse(
                    provider=provider,
                    prompt=prompt_text,
                    prompt_category=category,
                    raw_response="",
                    error=str(e),
                ))

    if progress_callback:
        progress_callback(total, total, "All LLM queries completed")

    # Sort results back into deterministic prompt order
    prompt_order = {(cat, txt): i for i, (cat, txt) in enumerate(all_prompts)}
    provider_order = {c.provider: i for i, c in enumerate(clients)}
    results.sort(key=lambda r: (
        prompt_order.get((r.prompt_category, r.prompt), 999),
        provider_order.get(r.provider, 999),
    ))

    return results


def _execute_with_retry(
    client,
    prompt: str,
    category: PromptCategory,
) -> LLMResponse:
    """Execute a prompt with retry logic."""
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        response = client.execute_prompt(
            prompt=prompt,
            prompt_category=category,
            system_context=LLM_SYSTEM_PROMPT,
        )
        if response.error is None:
            return response

        last_error = response.error

        retryable_keywords = ["rate", "429", "500", "502", "503", "timeout", "overloaded"]
        is_retryable = any(kw in last_error.lower() for kw in retryable_keywords)

        if not is_retryable or attempt >= MAX_RETRIES:
            return response

        if attempt < len(RETRY_BACKOFF_SECONDS):
            time.sleep(RETRY_BACKOFF_SECONDS[attempt])
        else:
            time.sleep(4)

    return response
