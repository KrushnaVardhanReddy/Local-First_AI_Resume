import json
from pathlib import Path
import pandas as pd
import concurrent.futures
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from jobspy import scrape_jobs
from .models import Job
from .config import AppConfig

class SearchProvider(ABC):
    @abstractmethod
    def search(self, config: AppConfig, hours_old: int | None = None) -> pd.DataFrame:
        pass

class JobspyProvider(SearchProvider):
    def search(self, config: AppConfig, hours_old: int | None = None) -> pd.DataFrame:
        kwargs = {
            "site_name": ["linkedin", "indeed", "glassdoor", "zip_recruiter"],
            "search_term": config.search.keywords,
            "location": config.search.location,
            "results_wanted": config.search.results_wanted,
            "is_remote": config.search.remote,
        }
        if config.search.job_type:
            kwargs["job_type"] = config.search.job_type
        if config.search.proxies:
            kwargs["proxies"] = config.search.proxies
        if hours_old is not None:
            kwargs["hours_old"] = hours_old

        return scrape_jobs(**kwargs)

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

    # Requirements: apply keyword exclusion filtering on description
    if config.search.exclude_keywords:
        # Create a boolean mask indicating if any excluded keyword is in the description
        pattern = '|'.join(config.search.exclude_keywords)
        # Using case-insensitive search
        mask = df['description'].str.contains(pattern, case=False, na=False, regex=True)
        # Keep jobs that DO NOT match the mask
        df = df[~mask]

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
    providers = [JobspyProvider()]

    last_search_path = user_dir / "last_search.json"
    hours_old = None
    if last_search_path.exists():
        try:
            with open(last_search_path, "r", encoding="utf-8") as f:
                last_search_data = json.load(f)
            last_search_time = datetime.fromisoformat(last_search_data["timestamp"])
            now = datetime.now(timezone.utc)
            delta = now - last_search_time
            hours_old = int(delta.total_seconds() / 3600)
            if hours_old < 1:
                hours_old = 1 # At least 1 hour
        except Exception as e:
            print(f"Error reading last_search.json: {e}")

    dfs = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_provider = {executor.submit(p.search, config, hours_old): p for p in providers}
        for future in concurrent.futures.as_completed(future_to_provider):
            try:
                df = future.result()
                if not df.empty:
                    dfs.append(df)
            except Exception as exc:
                print(f"A search provider generated an exception: {exc}")

    if not dfs:
        jobs_df = pd.DataFrame()
    else:
        jobs_df = pd.concat(dfs, ignore_index=True)

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

    # Write last_search.json
    try:
        with open(last_search_path, "w", encoding="utf-8") as f:
            json.dump({"timestamp": datetime.now(timezone.utc).isoformat()}, f, indent=2)
    except Exception as e:
        print(f"Error writing last_search.json: {e}")

    return accepted_jobs
