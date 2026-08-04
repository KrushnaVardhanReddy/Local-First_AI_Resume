import json
import logging
from pathlib import Path
from datetime import datetime, timezone

from src.config import AppConfig
from src.exceptions import ConfigError
from src.models import Job, MatchResult
from src.search_jobs import search_jobs
from src.incremental import load_processed_ids, mark_processed, is_processed
from src.tailor_resume import tailor_resume, generate_cover_letter, analyze_match
from src.render_pdf import render_resume_pdf, render_cover_letter_pdf
from src.tracker import update_tracker
from src.llm.base import get_provider

def run_search(config: AppConfig, user_dir: Path) -> None:
    logging.info("Starting job search...")
    accepted_jobs = search_jobs(config, user_dir)
    logging.info(f"Search complete. Found {len(accepted_jobs)} accepted jobs.")

def write_metadata_json(job: Job, match: MatchResult, config: AppConfig, output_dir: Path, usage_stats: dict) -> None:
    metadata = {
        "job_slug": job.slug,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "provider": config.provider,
        "model": config.model,
        "match_score": match.score,
        "usage": usage_stats
    }
    with open(output_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

def run_tailor(config: AppConfig, user_dir: Path, force: bool = False, dry_run: bool = False) -> None:
    processed_ids = load_processed_ids(user_dir)
    output_base_dir = user_dir / config.output_dir
    llm = get_provider(config)

    if not output_base_dir.exists():
        logging.info("Output directory does not exist. No jobs to process.")
        return

    # Find all job.json files
    job_files = list(output_base_dir.rglob("job.json"))
    logging.info(f"Found {len(job_files)} jobs in output directory.")

    for job_file in job_files:
        job_dir = job_file.parent
        slug = job_dir.name

        try:
            with open(job_file, "r", encoding="utf-8") as f:
                job_data = json.load(f)

            job = Job(
                title=job_data.get("title", ""),
                company=job_data.get("company", ""),
                location=job_data.get("location", ""),
                salary_min=job_data.get("salary_min"),
                salary_max=job_data.get("salary_max"),
                source_url=job_data.get("source_url", ""),
                description="" # Will read from job.md
            )
            # Slug generation in Job.__post_init__ should match if title/company are identical.
            # But the dir is already named after the original slug. We will assume the job slug generated matches.
        except Exception as e:
            logging.error(f"Failed to read job data in {job_dir}: {e}")
            continue

        # Read description from job.md if present
        job_md_file = job_dir / "job.md"
        if job_md_file.exists():
            try:
                with open(job_md_file, "r", encoding="utf-8") as f:
                    job.description = f.read()
            except Exception:
                pass

        # Use the actual slug from the directory structure, in case title/company generated differently due to bug/fixes.
        job.slug = slug

        if is_processed(job.id, processed_ids) and not force:
            logging.info(f"Skipping {job.slug} (already processed)")
            continue

        logging.info(f"Processing {job.slug}...")
        if dry_run:
            logging.info(f"[DRY-RUN] Would process {job.slug}")
            continue

        try:
            resume_path, resume_usage = tailor_resume(job, config, user_dir, llm)
            cl_path, cl_usage = generate_cover_letter(job, config, user_dir, llm)
            match_result, match_usage = analyze_match(job, config, user_dir, llm)

            render_resume_pdf(job, job_dir, config.pdf.theme, user_dir)
            render_cover_letter_pdf(job, job_dir)

            update_tracker(job, match_result, output_base_dir)

            # Combine usage
            total_usage = {}
            for k in set(resume_usage.keys()).union(cl_usage.keys(), match_usage.keys()):
                total_usage[k] = resume_usage.get(k, 0) + cl_usage.get(k, 0) + match_usage.get(k, 0)

            write_metadata_json(job, match_result, config, job_dir, total_usage)
            mark_processed(job.id, user_dir)

            logging.info(f"Successfully processed {job.slug}")

        except Exception as e:
            logging.error(f"Error processing {job.slug}: {e}")
            continue

def run_all(config: AppConfig, user_dir: Path, force: bool = False, dry_run: bool = False) -> None:
    run_search(config, user_dir)
    run_tailor(config, user_dir, force, dry_run)
