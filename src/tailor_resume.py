import re
import logging
from pathlib import Path
from src.config import AppConfig
from src.exceptions import ValidationError, PromptError
from src.llm.base import LLMProvider
from src.models import Job, MatchResult
from src.utils import load_prompt

def tailor_resume(job: Job, config: AppConfig, user_dir: Path, llm: LLMProvider) -> Path:
    """Tailors a resume using an LLM and saves it to the output dir."""
    job_output_dir = Path(config.output_dir) / job.slug
    job_output_dir.mkdir(parents=True, exist_ok=True)

    base_resume_path = user_dir / config.base_resume
    try:
        with open(base_resume_path, "r", encoding="utf-8") as f:
            base_resume = f.read()
    except Exception as e:
        raise ValidationError(f"Failed to read base resume: {e}")

    job_md_path = job_output_dir / "job.md"
    try:
        with open(job_md_path, "r", encoding="utf-8") as f:
            job_md = f.read()
    except Exception:
        # Fallback to the object's description if job.md isn't written yet
        job_md = job.description

    variables = {
        "base_resume": base_resume,
        "job_description": job_md,
    }

    prompt = load_prompt("resume.md", user_dir, variables)
    response = llm.complete(prompt)

    if len(response) < 50:
        raise ValidationError("LLM response too short (< 50 chars)")

    output_path = job_output_dir / "resume.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response)

    return output_path

def generate_cover_letter(job: Job, config: AppConfig, user_dir: Path, llm: LLMProvider) -> Path:
    """Generates a cover letter using an LLM and saves it to the output dir."""
    job_output_dir = Path(config.output_dir) / job.slug
    job_output_dir.mkdir(parents=True, exist_ok=True)

    resume_path = job_output_dir / "resume.md"
    try:
        with open(resume_path, "r", encoding="utf-8") as f:
            resume_md = f.read()
    except Exception as e:
        raise ValidationError(f"Failed to read tailored resume: {e}")

    job_md_path = job_output_dir / "job.md"
    try:
        with open(job_md_path, "r", encoding="utf-8") as f:
            job_md = f.read()
    except Exception:
        job_md = job.description

    variables = {
        "resume": resume_md,
        "job_description": job_md,
    }

    prompt = load_prompt("cover_letter.md", user_dir, variables)
    response = llm.complete(prompt)

    if len(response) < 50:
        raise ValidationError("LLM response too short (< 50 chars)")

    output_path = job_output_dir / "cover_letter.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response)

    return output_path

def analyze_match(job: Job, config: AppConfig, user_dir: Path, llm: LLMProvider) -> MatchResult:
    """Analyzes job match using an LLM, returning a MatchResult and writing notes."""
    job_output_dir = Path(config.output_dir) / job.slug
    job_output_dir.mkdir(parents=True, exist_ok=True)

    base_resume_path = user_dir / config.base_resume
    try:
        with open(base_resume_path, "r", encoding="utf-8") as f:
            base_resume = f.read()
    except Exception as e:
        raise ValidationError(f"Failed to read base resume: {e}")

    job_md_path = job_output_dir / "job.md"
    try:
        with open(job_md_path, "r", encoding="utf-8") as f:
            job_md = f.read()
    except Exception:
        job_md = job.description

    variables = {
        "base_resume": base_resume,
        "job_description": job_md,
    }

    prompt = load_prompt("match_notes.md", user_dir, variables)
    response = llm.complete(prompt)

    match = re.search(r'(?i)(?:score|match)[\s:]*(\d{1,3})', response)
    if match:
        score = int(match.group(1))
    else:
        # Fallback to just finding the first number if format differs
        nums = re.findall(r'\b\d{1,3}\b', response)
        score = int(nums[0]) if nums else 0

    if not (0 <= score <= 100):
        logging.warning(f"Match score out of bounds: {score}, clamping to [0, 100]")
        score = max(0, min(100, score))

    output_path = job_output_dir / "match_notes.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response)

    # We will assume LLM output contains text we can just pass through for now,
    # as splitting it cleanly depends on prompt structure.
    return MatchResult(
        score=score,
        strong_matches=[],
        gaps=[],
        suggestions=[],
        raw_text=response
    )
