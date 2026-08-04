import pytest
from pathlib import Path
from src.models import Job, MatchResult
from src.config import AppConfig, SearchConfig
from src.tailor_resume import analyze_match

class StubLLM:
    def __init__(self, response):
        self.response = response
    def complete(self, prompt):
        return self.response

def test_analyze_match_returns_match_result(tmp_path: Path):
    job = Job("Test", "Company", "Loc", 10, 100, "url", "desc")
    config = AppConfig(
        provider="dummy",
        model="dummy",
        base_resume="base.md",
        output_dir=str(tmp_path / "output"),
        search=SearchConfig("keys", "loc", True, 10)
    )

    (tmp_path / "base.md").write_text("base resume content")
    (tmp_path / "prompts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "prompts" / "match_notes.md").write_text("dummy prompt")

    llm_response = "Here are the match notes.\nScore: 85\nStrong Matches: Python\nGaps: Java\nSuggestions: Learn Java"
    llm = StubLLM(llm_response)

    result = analyze_match(job, config, tmp_path, llm)

    assert isinstance(result, MatchResult)
    assert result.score == 85
    assert result.raw_text == llm_response
