import pytest
from hypothesis import given, strategies as st
from src.models import Job
from src.tailor_resume import tailor_resume, generate_cover_letter
from src.config import AppConfig, SearchConfig
from src.exceptions import ValidationError
from pathlib import Path
import tempfile

class StubLLM:
    def __init__(self, response):
        self.response = response
    def complete(self, prompt):
        return self.response

@given(st.text(max_size=49))
def test_llm_response_length_guard(response_text):
    """
    Property 9: LLM response length guard prevents empty file writes.
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

        # Setup dummy base resume and prompts
        (tmp_path / "base.md").write_text("base resume")
        (tmp_path / "prompts").mkdir(parents=True, exist_ok=True)
        (tmp_path / "prompts" / "resume.md").write_text("dummy prompt")
        (tmp_path / "prompts" / "cover_letter.md").write_text("dummy prompt")

        # Also need a dummy tailored resume for cover letter gen
        job_output_dir = tmp_path / "output" / job.slug
        job_output_dir.mkdir(parents=True, exist_ok=True)
        (job_output_dir / "resume.md").write_text("existing tailored resume")

        llm = StubLLM(response_text)

        with pytest.raises(ValidationError, match="LLM response too short"):
            tailor_resume(job, config, tmp_path, llm)

        with pytest.raises(ValidationError, match="LLM response too short"):
            generate_cover_letter(job, config, tmp_path, llm)
