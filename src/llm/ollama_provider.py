import requests
from src.llm.base import LLMProvider, LLMResponse
from src.config import AppConfig
from src.exceptions import LLMError

class OllamaProvider(LLMProvider):
    def __init__(self, config: AppConfig):
        self.config = config
        self.base_url = config.base_url or "http://localhost:11434"

    def complete(self, prompt: str) -> LLMResponse:
        url = f"{self.base_url.rstrip('/')}/api/generate"

        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            text = result['response']
            usage = {
                "prompt_tokens": result.get("prompt_eval_count", 0),
                "completion_tokens": result.get("eval_count", 0),
                "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
            }
            return LLMResponse(text=text, usage=usage)
        except requests.exceptions.RequestException as e:
            status_code = e.response.status_code if e.response is not None else 'Network Error'
            raise LLMError(f"Ollama failed with status {status_code}: {e}")
