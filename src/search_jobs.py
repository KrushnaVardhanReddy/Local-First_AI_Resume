import json
from pathlib import Path
import pandas as pd
from jobspy import scrape_jobs
from .models import Job
from .config import AppConfig

def _filter_jobs(jobs_df: pd.DataFrame, config: AppConfig) -> pd.DataFrame:
    if jobs_df.empty:
        return jobs_df

    # Requirements: deduplication by (company, title)
    df = jobs_df.drop_duplicates(subset=['company', 'title'], keep='first').copy()

    # Fill NaN descriptions with empty string
    if 'description' not in df.columns:
        df['description'] = ''
    else:
        df['description'] = df['description'].fillna('')

    # Requirements: remove entries with description len < 100
    df = df[df['description'].str.len() >= 100]

    # Requirements: apply salary filter if min_salary set
    if config.search.min_salary is not None:
        # jobspy returns max_amount
        if 'max_amount' in df.columns:
            # Need to handle NaN properly
            df = df[df['max_amount'].fillna(0) >= config.search.min_salary]
        else:
            # If no salary data exists, filter out jobs since min_salary is required
            df = pd.DataFrame(columns=df.columns)

    # Requirements: apply company exclusion list
    if config.search.exclude_companies:
        df = df[~df['company'].isin(config.search.exclude_companies)]

    return df

def _save_job(job: Job, output_dir: Path) -> None:
    job_dir = output_dir / job.slug
    job_dir.mkdir(parents=True, exist_ok=True)

    # Write job.md
    job_md_content = f"# {job.title} at {job.company}\n\n"
    job_md_content += f"**Location:** {job.location}\n"
    if job.salary_min or job.salary_max:
        job_md_content += f"**Salary:** {job.salary_min} - {job.salary_max}\n"
    job_md_content += f"**URL:** {job.source_url}\n\n"
    job_md_content += "## Description\n\n"
    job_md_content += job.description

    with open(job_dir / "job.md", "w", encoding="utf-8") as f:
        f.write(job_md_content)

    # Write job.json
    job_json_content = {
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "source_url": job.source_url
    }

    with open(job_dir / "job.json", "w", encoding="utf-8") as f:
        json.dump(job_json_content, f, indent=2)

def search_jobs(config: AppConfig, user_dir: Path) -> list[Job]:
    jobs_df = scrape_jobs(
        site_name=["linkedin", "indeed", "glassdoor", "zip_recruiter"],
        search_term=config.search.keywords,
        location=config.search.location,
        results_wanted=config.search.results_wanted,
        is_remote=config.search.remote
    )

    filtered_df = _filter_jobs(jobs_df, config)

    output_dir = user_dir / config.output_dir

    accepted_jobs = []
    for _, row in filtered_df.iterrows():
        job = Job(
            title=row.get('title', ''),
            company=row.get('company', ''),
            location=row.get('location', ''),
            salary_min=int(row['min_amount']) if pd.notna(row.get('min_amount')) else None,
            salary_max=int(row['max_amount']) if pd.notna(row.get('max_amount')) else None,
            source_url=row.get('job_url', ''),
            description=row.get('description', '')
        )
        _save_job(job, output_dir)
        accepted_jobs.append(job)

    return accepted_jobs
