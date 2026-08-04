import re
from pathlib import Path
from typing import Dict
from .exceptions import PromptError

def make_job_slug(company: str, title: str) -> str:
    """
    Lowercase, hyphenate, collapse consecutive hyphens, strip leading/trailing hyphens,
    and truncate to 80 chars.
    """
    slug_str = f"{company} {title}".lower()
    # Replace non-alphanumeric characters with hyphens
    slug_str = re.sub(r'[^a-z0-9]', '-', slug_str)
    # Collapse consecutive hyphens
    slug_str = re.sub(r'-+', '-', slug_str)
    # Strip leading and trailing hyphens
    slug_str = slug_str.strip('-')
    # Truncate to 80 characters
    return slug_str[:80]

def load_prompt(template_name: str, user_dir: Path, variables: Dict[str, str]) -> str:
    """
    Look in `user_dir/prompts/` first, fall back to project-root `prompts/`.
    Substitute variables via `str.replace()`.
    Raise `PromptError` if file not found.
    """
    user_prompt_path = user_dir / "prompts" / template_name
    global_prompt_path = Path("prompts") / template_name

    if user_prompt_path.exists():
        target_path = user_prompt_path
    elif global_prompt_path.exists():
        target_path = global_prompt_path
    else:
        raise PromptError(f"Prompt template '{template_name}' not found.")

    try:
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        raise PromptError(f"Error reading prompt template '{template_name}': {e}")

    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        content = content.replace(placeholder, value)

    return content

def scaffold_user_dir(user_dir: Path) -> None:
    """
    Create `resumes/`, `output/`, `prompts/`, `templates/` in `user_dir`.
    Write stub `config.yaml` if it doesn't exist.
    Write empty `processed_jobs.json` if it doesn't exist.
    """
    (user_dir / "resumes").mkdir(parents=True, exist_ok=True)
    (user_dir / "output").mkdir(parents=True, exist_ok=True)
    (user_dir / "prompts").mkdir(parents=True, exist_ok=True)
    (user_dir / "templates").mkdir(parents=True, exist_ok=True)

    config_path = user_dir / "config.yaml"
    if not config_path.exists():
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("provider: lmstudio\nmodel: qwen3-8b\nbase_resume: resumes/backend.md\noutput_dir: output/\nsearch:\n  keywords: \"backend engineer\"\n  location: \"Remote\"\n  remote: true\n  results_wanted: 10\n")

    processed_jobs_path = user_dir / "processed_jobs.json"
    if not processed_jobs_path.exists():
        with open(processed_jobs_path, 'w', encoding='utf-8') as f:
            f.write("{}")
