import pytest
from pathlib import Path
from src.models import Job
from src.config import AppConfig, SearchConfig
from src.tailor_resume import tailor_resume, generate_cover_letter
from src.exceptions import ValidationError

class StubLLM:
    def __init__(self, response):
        self.response = response
    def complete(self, prompt):
        from src.llm.base import LLMResponse
        return LLMResponse(text=self.response, usage={"test": 0})

def test_tailor_resume_writes_valid_content(tmp_path: Path):
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
    (tmp_path / "prompts" / "resume.md").write_text("dummy prompt")

    valid_content = "This is a valid tailored resume that is long enough to pass the guard of 50 characters."
    llm = StubLLM(valid_content)

    output_path, usage = tailor_resume(job, config, tmp_path, llm)

    assert output_path.exists()
    assert output_path.name == "resume.md"
    assert output_path.read_text() == valid_content

def test_generate_cover_letter_writes_valid_content(tmp_path: Path):
    job = Job("Test", "Company", "Loc", 10, 100, "url", "desc")
    config = AppConfig(
        provider="dummy",
        model="dummy",
        base_resume="base.md",
        output_dir=str(tmp_path / "output"),
        search=SearchConfig("keys", "loc", True, 10)
    )

    job_output_dir = tmp_path / "output" / job.slug
    job_output_dir.mkdir(parents=True, exist_ok=True)
    (job_output_dir / "resume.md").write_text("existing tailored resume")

    (tmp_path / "prompts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "prompts" / "cover_letter.md").write_text("dummy prompt")

    valid_content = "This is a valid cover letter that is long enough to pass the length guard of 50 characters."
    llm = StubLLM(valid_content)

    output_path, usage = generate_cover_letter(job, config, tmp_path, llm)

    assert output_path.exists()
    assert output_path.name == "cover_letter.md"
    assert output_path.read_text() == valid_content

def test_ai_cliche_filter_raises_validation_error(tmp_path: Path):
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
    (tmp_path / "prompts" / "resume.md").write_text("dummy prompt")

    cliche_content = "This is a long enough resume that decides to delve into the innovative and dynamic synergy of things."
    llm = StubLLM(cliche_content)

    with pytest.raises(ValidationError, match="too many AI clichés"):
        tailor_resume(job, config, tmp_path, llm)
