import os
import openai
from tenacity import retry, wait_exponential, retry_if_exception_type, stop_after_attempt
from src.llm.base import LLMProvider
from src.config import AppConfig
from src.exceptions import LLMError

class OpenAIProvider(LLMProvider):
    def __init__(self, config: AppConfig):
        self.config = config
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise LLMError("OPENAI_API_KEY environment variable not set")
        self.client = openai.OpenAI(api_key=api_key)

    def complete(self, prompt: str) -> str:
        @retry(
            retry=retry_if_exception_type(openai.RateLimitError),
            wait=wait_exponential(multiplier=1, min=2, max=60),
            stop=stop_after_attempt(5)
        )
        def _do_complete():
            return self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

        try:
            response = _do_complete()
            return response.choices[0].message.content
        except openai.RateLimitError as e:
            raise LLMError(f"OpenAI rate limited: {e}")
        except openai.APIConnectionError as e:
            raise LLMError(f"OpenAI connection failed: {e}")
        except openai.APIError as e:
            raise LLMError(f"OpenAI API failed: {e}")
        except Exception as e:
            raise LLMError(f"OpenAI request failed: {e}")
