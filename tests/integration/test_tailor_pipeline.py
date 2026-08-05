import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging

from main import main
from src.models import Job, MatchResult
from src.llm.base import LLMResponse

# We will let logging output show up for debugging
logging.getLogger().setLevel(logging.DEBUG)

# Mock LLM provider
class StubProvider:
    def complete(self, prompt, **kwargs):
        # We need to return valid outputs based on what's being prompted
        long_text = "This is a sufficiently long text to pass the length guard which requires at least 50 chars. " * 3
        if "cover letter" in prompt.lower():
            return LLMResponse(text=long_text + "This is a cover letter.", usage={"total_tokens": 100})
        elif "match analysis score" in prompt.lower():
            # Return valid JSON for MatchResult
            res = {
                "score": 85,
                "strengths": ["Python", "Testing"],
                "weaknesses": ["None"],
                "reasoning": "Good fit because " + long_text
            }
            # Note: length check is for the raw text response
            text_response = json.dumps(res) + " " * 100 # Pad it just in case
            return LLMResponse(text=text_response, usage={"total_tokens": 50})
        else:
            # Assume it's the resume
            return LLMResponse(text=long_text + "This is a tailored resume.", usage={"total_tokens": 200})

@patch("src.pipeline.get_provider")
@patch("src.pipeline.render_resume_pdf")
@patch("src.pipeline.render_cover_letter_pdf")
def test_tailor_pipeline(mock_render_cl, mock_render_resume, mock_get_provider, tmp_path, monkeypatch):
    mock_get_provider.return_value = StubProvider()

    monkeypatch.chdir(tmp_path)

    # Create necessary scaffold
    user = "testuser"
    user_dir = tmp_path / "users" / user
    user_dir.mkdir(parents=True, exist_ok=True)

    # Create a basic config.yaml
    config_yaml = """
provider: lmstudio
model: qwen
base_resume: resume.md
output_dir: output
search:
  keywords: "Software Engineer"
  location: "Remote"
  remote: true
  results_wanted: 10
    """
    (user_dir / "config.yaml").write_text(config_yaml)

    # Need a job in output dir to tailor
    output_dir = user_dir / "output"
    job_slug = "tech-corp-software-engineer"
    job_dir = output_dir / job_slug
    job_dir.mkdir(parents=True, exist_ok=True)

    job_json = {
        "title": "Software Engineer",
        "company": "Tech Corp",
        "location": "Remote",
        "salary_min": 100000,
        "salary_max": 150000,
        "source_url": "http://example.com/job1"
    }
    with open(job_dir / "job.json", "w") as f:
        json.dump(job_json, f)

    (job_dir / "job.md").write_text("Job description here.")

    # Need prompt templates and base resume
    templates_dir = user_dir / "prompts"
    templates_dir.mkdir(parents=True, exist_ok=True)
    (templates_dir / "resume.md").write_text("Prompt for resume")
    (templates_dir / "cover_letter.md").write_text("Prompt for cover letter")
    (templates_dir / "match_notes.md").write_text("Prompt for match analysis score")

    (user_dir / "resume.md").write_text("My base resume")

    # Need prompt templates and base resume
    templates_dir = user_dir / "prompts"
    templates_dir.mkdir(parents=True, exist_ok=True)
    (templates_dir / "resume.md").write_text("Prompt for resume")
    (templates_dir / "cover_letter.md").write_text("Prompt for cover letter")
    (templates_dir / "match_notes.md").write_text("Prompt for match analysis score")

    (user_dir / "resume.md").write_text("My base resume")

    # Mock provider response to valid JSON
    class ValidJSONStubProvider:
        def complete(self, prompt):
            from src.llm.base import LLMResponse
            if "Score" in prompt or "match analysis score" in prompt:
                return LLMResponse(text="Score: 90", usage={"test": 10})
            if "cover letter" in prompt:
                return LLMResponse(text="Valid cover letter content > 50 chars as expected.", usage={"test": 10})
            return LLMResponse(text='{"basics": {"name": "Test"}, "work": [], "education": [], "skills": [{"name": "Test", "keywords": ["1", "2"]}], "extra_long_string_to_pass_len_check": "1234567890123456789012345678901234567890"}', usage={"test": 10})

    mock_get_provider.return_value = ValidJSONStubProvider()

    # Mock render functions to just touch the PDF files
    def mock_resume_pdf(job, jdir, theme, udir, engine):
        (jdir / "resume.pdf").touch()
    mock_render_resume.side_effect = mock_resume_pdf

    def mock_cl_pdf(job, jdir):
        (jdir / "cover_letter.pdf").touch()
    mock_render_cl.side_effect = mock_cl_pdf

    # Run the tailor command
    import sys
    monkeypatch.setattr(sys, "argv", ["main.py", "--user", user, "tailor"])
    main()

    # Verifications
    if not (job_dir / "resume.json").exists():
        import pytest
        pytest.fail("tailor command probably errored out on this job, check logs.")

    assert (job_dir / "resume.pdf").exists()
    assert (job_dir / "cover_letter.md").exists()
    assert (job_dir / "cover_letter.pdf").exists()
    assert (job_dir / "match_notes.md").exists()
    assert (job_dir / "metadata.json").exists()

    with open(job_dir / "metadata.json") as f:
        metadata = json.load(f)
        assert metadata["job_slug"] == job_slug
        assert metadata["match_score"] == 90
        assert metadata["provider"] == "lmstudio"

    # Tracker check
    tracker_csv = output_dir / "tracker.csv"
    tracker_md = output_dir / "tracker.md"
    assert tracker_csv.exists()
    assert tracker_md.exists()

    # Read tracker to ensure row is added
    tracker_content = tracker_csv.read_text()
    assert "Tech Corp" in tracker_content
    assert "Software Engineer" in tracker_content

    # Run again without force, should skip
    mock_render_resume.reset_mock()
    monkeypatch.setattr(sys, "argv", ["main.py", "--user", user, "tailor"])
    main()
    mock_render_resume.assert_not_called()

    # Run again with force, should re-process
    monkeypatch.setattr(sys, "argv", ["main.py", "--user", user, "--force", "tailor"])
    main()
    mock_render_resume.assert_called_once()
