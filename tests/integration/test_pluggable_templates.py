import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

from src.utils import load_prompt
from src.render_pdf import render_resume_pdf
from src.models import Job

def test_pluggable_prompts(tmp_path, monkeypatch):
    user_dir = tmp_path / "users" / "testuser"
    user_dir.mkdir(parents=True, exist_ok=True)

    # Global prompts
    global_prompts = tmp_path / "prompts"
    global_prompts.mkdir(exist_ok=True)
    (global_prompts / "resume.md").write_text("GLOBAL PROMPT")

    # Change working directory so that 'prompts/' exists in CWD
    monkeypatch.chdir(tmp_path)

    # Test reading global prompt
    content = load_prompt("resume.md", user_dir, {})
    assert content == "GLOBAL PROMPT"

    # Now user overrides it
    user_prompts = user_dir / "prompts"
    user_prompts.mkdir(exist_ok=True)
    (user_prompts / "resume.md").write_text("USER PROMPT OVERRIDE")

    content = load_prompt("resume.md", user_dir, {})
    assert content == "USER PROMPT OVERRIDE"

@patch("subprocess.run")
def test_pluggable_templates_for_rendercv(mock_run, tmp_path, monkeypatch):
    user_dir = tmp_path / "users" / "testuser"
    user_dir.mkdir(parents=True, exist_ok=True)

    # Create user template
    templates_dir = user_dir / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    theme_dir = templates_dir / "my_custom_theme"
    theme_dir.mkdir(exist_ok=True)

    job = Job(
        title="Software Engineer",
        company="Tech Corp",
        location="Remote",
        salary_min=100000,
        salary_max=150000,
        source_url="http://example.com/job1",
        description="Desc"
    )
    job.slug = "tech-corp-software-engineer"

    job_dir = tmp_path / "output" / job.slug
    job_dir.mkdir(parents=True, exist_ok=True)

    (job_dir / "resume.md").write_text("# Resume")

    # Since render_resume_pdf expects a PDF in rendercv_output, mock subprocess to create one
    def mock_run_effect(*args, **kwargs):
        pdf_dir = job_dir / "rendercv_output"
        pdf_dir.mkdir(exist_ok=True)
        (pdf_dir / "resume.pdf").touch()
        return MagicMock(returncode=0)

    mock_run.side_effect = mock_run_effect

    monkeypatch.chdir(tmp_path)

    render_resume_pdf(job, job_dir, "my_custom_theme", user_dir)

    # Verify that rendercv was called
    mock_run.assert_called_once()

    # Verify that rendercv yaml contains the right theme reference
    yaml_files = list(job_dir.glob("*.yaml"))
    assert len(yaml_files) > 0
    yaml_file = yaml_files[0]

    with open(yaml_file) as f:
        data = yaml.safe_load(f)

    assert "cv" in data
    assert "design" in data
    assert "my_custom_theme" in data["design"]["theme"]

    # Also verify that the theme directory was copied to output dir
    assert (job_dir / "my_custom_theme").exists()
