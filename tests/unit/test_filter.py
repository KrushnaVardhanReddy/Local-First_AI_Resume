import pytest
import pandas as pd
from src.search_jobs import _filter_jobs, _save_job
from src.config import AppConfig, SearchConfig
from src.models import Job

def test_filter_removes_duplicates():
    df = pd.DataFrame([
        {'title': 'T1', 'company': 'C1', 'description': 'a' * 100},
        {'title': 'T1', 'company': 'C1', 'description': 'b' * 100}, # duplicate
        {'title': 'T2', 'company': 'C1', 'description': 'c' * 100}
    ])

    config = AppConfig(
        provider="dummy", model="dummy", base_resume="dummy", output_dir="dummy",
        search=SearchConfig(keywords="dummy", location="dummy", remote=True, results_wanted=10)
    )

    filtered_df = _filter_jobs(df, config)

    assert len(filtered_df) == 2
    assert filtered_df['title'].tolist() == ['T1', 'T2']

def test_filter_removes_short_description():
    df = pd.DataFrame([
        {'title': 'T1', 'company': 'C1', 'description': 'a' * 50}, # short
        {'title': 'T2', 'company': 'C1', 'description': 'b' * 100},
        {'title': 'T3', 'company': 'C2', 'description': None} # NaN
    ])

    config = AppConfig(
        provider="dummy", model="dummy", base_resume="dummy", output_dir="dummy",
        search=SearchConfig(keywords="dummy", location="dummy", remote=True, results_wanted=10)
    )

    filtered_df = _filter_jobs(df, config)

    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]['title'] == 'T2'

def test_filter_removes_below_salary_threshold():
    df = pd.DataFrame([
        {'title': 'T1', 'company': 'C1', 'max_amount': 90000, 'description': 'a' * 100},
        {'title': 'T2', 'company': 'C1', 'max_amount': 100000, 'description': 'b' * 100},
        {'title': 'T3', 'company': 'C2', 'description': 'c' * 100} # no salary
    ])

    config = AppConfig(
        provider="dummy", model="dummy", base_resume="dummy", output_dir="dummy",
        search=SearchConfig(keywords="dummy", location="dummy", remote=True, results_wanted=10, min_salary=100000)
    )

    filtered_df = _filter_jobs(df, config)

    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]['title'] == 'T2'

def test_filter_excludes_companies():
    df = pd.DataFrame([
        {'title': 'T1', 'company': 'BadCo', 'description': 'a' * 100},
        {'title': 'T2', 'company': 'GoodCo', 'description': 'b' * 100}
    ])

    config = AppConfig(
        provider="dummy", model="dummy", base_resume="dummy", output_dir="dummy",
        search=SearchConfig(keywords="dummy", location="dummy", remote=True, results_wanted=10, exclude_companies=['BadCo'])
    )

    filtered_df = _filter_jobs(df, config)

    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]['company'] == 'GoodCo'

def test_save_job_writes_files_to_correct_path_structure(tmp_path):
    job = Job(
        title="Software Engineer",
        company="Tech Corp",
        location="Remote",
        salary_min=100000,
        salary_max=150000,
        source_url="http://example.com/job",
        description="This is a really great job " * 10
    )

    _save_job(job, tmp_path)

    job_dir = tmp_path / job.slug
    assert job_dir.exists()
    assert job_dir.is_dir()

    md_path = job_dir / "job.md"
    assert md_path.exists()

    json_path = job_dir / "job.json"
    assert json_path.exists()

    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    assert "Software Engineer" in md_content
    assert "Tech Corp" in md_content
    assert "Remote" in md_content
    assert "100000 - 150000" in md_content
    assert "http://example.com/job" in md_content
