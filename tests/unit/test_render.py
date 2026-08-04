import pytest
from pathlib import Path
from src.render_pdf import _md_to_rendercv_yaml, render_resume_pdf
from src.exceptions import RenderError
import subprocess

def test_md_to_rendercv_yaml():
    md = "Some content"
    personal_info = {"theme": "classic"}
    result = _md_to_rendercv_yaml(md, personal_info)
    assert "cv" in result
    assert "design" in result
    assert "name" in result["cv"]
    assert "email" in result["cv"]
    assert "sections" in result["cv"]

def test_render_error_raised_when_markdown_missing(tmp_path):
    job = None
    with pytest.raises(RenderError, match="Source markdown file missing"):
        render_resume_pdf(job, tmp_path, "classic", tmp_path)

def test_render_error_raised_when_rendercv_exits_nonzero(tmp_path, monkeypatch):
    job = None
    (tmp_path / "resume.md").write_text("content")

    class FakeResult:
        returncode = 1
        stderr = "error"

    def fake_run(*args, **kwargs):
        return FakeResult()

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(RenderError, match="RenderCV exited with code 1"):
            render_resume_pdf(job, tmp_path, "classic", tmp_path)
