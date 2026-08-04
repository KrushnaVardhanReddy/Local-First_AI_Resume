import requests
from src.llm.base import LLMProvider, LLMResponse
from src.config import AppConfig
from src.exceptions import LLMError

class LMStudioProvider(LLMProvider):
    def __init__(self, config: AppConfig):
        self.config = config
        self.base_url = config.base_url or "http://localhost:1234/v1"

    def complete(self, prompt: str) -> LLMResponse:
        # Assuming base_url is something like http://localhost:1234/v1
        url = f"{self.base_url.rstrip('/')}/chat/completions"

        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "model": self.config.model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            text = result['choices'][0]['message']['content']
            usage = result.get('usage', {})
            return LLMResponse(text=text, usage=usage)
        except requests.exceptions.RequestException as e:
            status_code = e.response.status_code if e.response is not None else 'Network Error'
            raise LLMError(f"LMStudio failed with status {status_code}: {e}")
