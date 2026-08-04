import pytest
from hypothesis import given, strategies as st
from src.models import Job
from src.tailor_resume import analyze_match
from src.config import AppConfig, SearchConfig
from pathlib import Path
import tempfile
import shutil

class StubLLM:
    def __init__(self, response):
        self.response = response
    def complete(self, prompt):
        from src.llm.base import LLMResponse
        return LLMResponse(text=self.response, usage={"test": 0})

@given(st.text())
def test_match_score_is_always_within_bounds(response_text):
    """
    Property 6: Match score is always within bounds [0, 100].
    """
    job = Job("Test", "Company", "Loc", 10, 100, "url", "desc")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        config = AppConfig(
            provider="dummy",
            model="dummy",
            base_resume="base.md",
            output_dir=str(tmp_path / "output"),
            search=SearchConfig("keys", "loc", True, 10)
        )

        # Setup dummy base resume and prompt
        (tmp_path / "base.md").write_text("base resume")
        (tmp_path / "prompts").mkdir(parents=True, exist_ok=True)
        (tmp_path / "prompts" / "match_notes.md").write_text("dummy prompt")

        llm = StubLLM(response_text)

        result, usage = analyze_match(job, config, tmp_path, llm)

        assert 0 <= result.score <= 100
