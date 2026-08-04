import os
import anthropic
from tenacity import retry, wait_exponential, retry_if_exception_type, stop_after_attempt
from src.llm.base import LLMProvider
from src.config import AppConfig
from src.exceptions import LLMError

class AnthropicProvider(LLMProvider):
    def __init__(self, config: AppConfig):
        self.config = config
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMError("ANTHROPIC_API_KEY environment variable not set")
        self.client = anthropic.Anthropic(api_key=api_key)

    def complete(self, prompt: str) -> str:
        @retry(
            retry=retry_if_exception_type(anthropic.RateLimitError),
            wait=wait_exponential(multiplier=1, min=2, max=60),
            stop=stop_after_attempt(5)
        )
        def _do_complete():
            return self.client.messages.create(
                model=self.config.model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

        try:
            response = _do_complete()
            return response.content[0].text
        except anthropic.RateLimitError as e:
            raise LLMError(f"Anthropic rate limited: {e}")
        except anthropic.APIConnectionError as e:
            raise LLMError(f"Anthropic connection failed: {e}")
        except anthropic.APIError as e:
            raise LLMError(f"Anthropic API failed: {e}")
        except Exception as e:
            raise LLMError(f"Anthropic request failed: {e}")
