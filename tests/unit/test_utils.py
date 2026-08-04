import pytest
from pathlib import Path
from src.utils import make_job_slug, load_prompt, scaffold_user_dir
from src.exceptions import PromptError

def test_make_job_slug_known_inputs():
    assert make_job_slug("Google", "Software Engineer") == "google-software-engineer"
    assert make_job_slug("Meta!", "Frontend Dev@HQ") == "meta-frontend-dev-hq"
    assert make_job_slug("A" * 100, "B") == "a" * 80 # Truncates correctly

def test_load_prompt_user_override(tmp_path):
    user_dir = tmp_path / "user"
    user_dir.mkdir()

    (user_dir / "prompts").mkdir(parents=True)
    (user_dir / "prompts" / "test.md").write_text("User: {{var}}")

    result = load_prompt("test.md", user_dir, {"var": "value"})
    assert result == "User: value"

def test_load_prompt_fallback(tmp_path, monkeypatch):
    user_dir = tmp_path / "user"
    user_dir.mkdir()

    # Setup global prompts
    global_prompts = tmp_path / "global_prompts"
    global_prompts.mkdir()
    (global_prompts / "test.md").write_text("Global: {{var}}")

    # Mock Path("prompts") to point to our global_prompts
    class MockPath:
        def __init__(self, *args, **kwargs):
            self.p = Path(global_prompts, *args)
        def __truediv__(self, other):
            return self.p / other

    # Not clean to mock Path like this, so let's mock it inside utils module by changing current directory
    import os
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    Path("prompts").mkdir()
    Path("prompts/test.md").write_text("Global: {{var}}")
    try:
        result = load_prompt("test.md", user_dir, {"var": "value"})
        assert result == "Global: value"
    finally:
        os.chdir(original_cwd)

def test_load_prompt_missing(tmp_path):
    user_dir = tmp_path / "user"
    user_dir.mkdir()

    with pytest.raises(PromptError):
        load_prompt("missing.md", user_dir, {})

def test_scaffold_user_dir(tmp_path):
    user_dir = tmp_path / "user"
    scaffold_user_dir(user_dir)

    assert (user_dir / "resumes").exists()
    assert (user_dir / "resumes").is_dir()
    assert (user_dir / "output").exists()
    assert (user_dir / "output").is_dir()
    assert (user_dir / "prompts").exists()
    assert (user_dir / "prompts").is_dir()
    assert (user_dir / "config.yaml").exists()
    assert (user_dir / "processed_jobs.json").exists()

    with open(user_dir / "processed_jobs.json") as f:
        assert f.read() == "{}"
