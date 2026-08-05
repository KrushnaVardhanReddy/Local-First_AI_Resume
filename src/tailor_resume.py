import json
import re
import logging
import asyncio
from pathlib import Path
from src.config import AppConfig
from src.exceptions import ValidationError, PromptError
from src.llm.base import LLMProvider
from src.models import Job, MatchResult
from src.utils import load_prompt

from mcp.client.stdio import stdio_client, get_default_environment, StdioServerParameters
from mcp.client.session import ClientSession

AI_CLICHES = [
    "delve", "testament to", "innovative", "dynamic", "synergy",
    "leverage", "spearhead", "game-changer", "paradigm shift"
]

async def _fetch_mcp_resume(command: str, args: list, uri: str) -> str:
    server_params = StdioServerParameters(
        command=command,
        args=args,
        env=get_default_environment()
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.read_resource(uri)
            if not result.contents:
                raise ValidationError(f"MCP resource at {uri} returned empty contents.")
            return result.contents[0].text

def _read_base_resume(config: AppConfig, user_dir: Path) -> str:
    if config.mcp_base_resume:
        try:
            command = config.mcp_base_resume.get("command")
            args = config.mcp_base_resume.get("args", [])
            uri = config.mcp_base_resume.get("resource_uri")

            if not command or not uri:
                raise ValidationError("mcp_base_resume config missing 'command' or 'resource_uri'")

            return asyncio.run(_fetch_mcp_resume(command, args, uri))
        except Exception as e:
            raise ValidationError(f"Failed to read base resume from MCP: {e}")

    base_resume_path = user_dir / config.base_resume
    try:
        with open(base_resume_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise ValidationError(f"Failed to read base resume from file: {e}")

def check_ai_cliches(text: str) -> None:
    text_lower = text.lower()
    cliche_count = sum(1 for cliche in AI_CLICHES if cliche in text_lower)
    if cliche_count > 2:
        raise ValidationError(f"LLM response contains too many AI clichés ({cliche_count})")

from typing import Tuple

def tailor_resume(job: Job, config: AppConfig, user_dir: Path, llm: LLMProvider) -> Tuple[Path, dict]:
    """Tailors a resume using an LLM and saves it to the output dir. Returns path and token usage."""
    job_output_dir = user_dir / config.output_dir / job.slug
    job_output_dir.mkdir(parents=True, exist_ok=True)

    base_resume = _read_base_resume(config, user_dir)

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
    llm_response = llm.complete(prompt)
    response_text = llm_response.text
    usage = llm_response.usage

    if len(response_text) < 50:
        raise ValidationError("LLM response too short (< 50 chars)")

    try:
        json.loads(response_text)
    except json.JSONDecodeError:
        raise ValidationError("LLM did not return valid JSON")

    check_ai_cliches(response_text)

    output_path = job_output_dir / "resume.json"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response_text)

    return output_path, usage

def generate_cover_letter(job: Job, config: AppConfig, user_dir: Path, llm: LLMProvider) -> Tuple[Path, dict]:
    """Generates a cover letter using an LLM and saves it to the output dir. Returns path and token usage."""
    job_output_dir = user_dir / config.output_dir / job.slug
    job_output_dir.mkdir(parents=True, exist_ok=True)

    resume_path = job_output_dir / "resume.json"
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
    llm_response = llm.complete(prompt)
    response_text = llm_response.text
    usage = llm_response.usage

    if len(response_text) < 50:
        raise ValidationError("LLM response too short (< 50 chars)")

    check_ai_cliches(response_text)

    output_path = job_output_dir / "cover_letter.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response_text)

    return output_path, usage

def analyze_match(job: Job, config: AppConfig, user_dir: Path, llm: LLMProvider) -> Tuple[MatchResult, dict]:
    """Analyzes job match using an LLM, returning a MatchResult and token usage."""
    job_output_dir = user_dir / config.output_dir / job.slug
    job_output_dir.mkdir(parents=True, exist_ok=True)

    base_resume = _read_base_resume(config, user_dir)

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
    llm_response = llm.complete(prompt)
    response_text = llm_response.text
    usage = llm_response.usage

    match = re.search(r'(?i)(?:score|match)[\s:]*(\d{1,3})', response_text)
    if match:
        score = int(match.group(1))
    else:
        # Fallback to just finding the first number if format differs
        nums = re.findall(r'\b\d{1,3}\b', response_text)
        score = int(nums[0]) if nums else 0

    if not (0 <= score <= 100):
        logging.warning(f"Match score out of bounds: {score}, clamping to [0, 100]")
        score = max(0, min(100, score))

    output_path = job_output_dir / "match_notes.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response_text)

    # We will assume LLM output contains text we can just pass through for now,
    # as splitting it cleanly depends on prompt structure.
    match_result = MatchResult(
        score=score,
        strong_matches=[],
        gaps=[],
        suggestions=[],
        raw_text=response_text
    )
    return match_result, usage
