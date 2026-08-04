import pytest
from hypothesis import given, strategies as st
import pandas as pd
from src.search_jobs import _filter_jobs
from src.config import AppConfig, SearchConfig

from tests.conftest import job_strategy

@given(st.lists(job_strategy(), min_size=2, max_size=10))
def test_duplicate_job_filter_removes_exact_duplicates(jobs):
    # Requirements: 1.2 Duplicate filter removes exact duplicates

    # Create duplicates intentionally
    jobs.extend(jobs[:2])

    # Create DataFrame from jobs
    jobs_dict = []
    for j in jobs:
        jobs_dict.append({
            'title': j.title,
            'company': j.company,
            'location': j.location,
            'min_amount': j.salary_min,
            'max_amount': j.salary_max,
            'job_url': j.source_url,
            'description': j.description
        })

    df = pd.DataFrame(jobs_dict)

    # Setup dummy config
    config = AppConfig(
        provider="dummy", model="dummy", base_resume="dummy", output_dir="dummy",
        search=SearchConfig(keywords="dummy", location="dummy", remote=True, results_wanted=10)
    )

    filtered_df = _filter_jobs(df, config)

    # Assert no duplicates by (company, title)
    assert not filtered_df.duplicated(subset=['company', 'title']).any()

@given(st.lists(job_strategy(), min_size=1, max_size=10))
def test_short_description_filter_removes_all_sub_threshold_jobs(jobs):
    # Requirements: 1.3 Short-description filter removes all sub-threshold jobs

    jobs_dict = []
    for j in jobs:
        jobs_dict.append({
            'title': j.title,
            'company': j.company,
            'location': j.location,
            'min_amount': j.salary_min,
            'max_amount': j.salary_max,
            'job_url': j.source_url,
            'description': j.description[:50] # Force description < 100 chars
        })

    # Mix in some long descriptions
    jobs_dict.append({
        'title': 'Good Job',
        'company': 'Good Co',
        'location': 'Remote',
        'min_amount': None,
        'max_amount': None,
        'job_url': 'http://good.com',
        'description': 'a' * 150 # Force description >= 100 chars
    })

    df = pd.DataFrame(jobs_dict)

    config = AppConfig(
        provider="dummy", model="dummy", base_resume="dummy", output_dir="dummy",
        search=SearchConfig(keywords="dummy", location="dummy", remote=True, results_wanted=10)
    )

    filtered_df = _filter_jobs(df, config)

    # All resulting jobs must have descriptions >= 100 chars
    assert (filtered_df['description'].str.len() >= 100).all()
    # At least the 'Good Job' should have survived
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]['title'] == 'Good Job'

@given(st.integers(min_value=50000, max_value=200000), st.lists(job_strategy(), min_size=1, max_size=10))
def test_salary_filter_excludes_all_below_threshold_jobs(threshold, jobs):
    # Requirements: 1.4 Salary filter excludes all below-threshold jobs
    jobs_dict = []
    for j in jobs:
        jobs_dict.append({
            'title': j.title,
            'company': j.company,
            'location': j.location,
            'min_amount': j.salary_min,
            'max_amount': j.salary_max,
            'job_url': j.source_url,
            'description': j.description
        })

    # Inject a job that meets the threshold
    jobs_dict.append({
        'title': 'High Paying Job',
        'company': 'Rich Co',
        'location': 'Remote',
        'min_amount': threshold,
        'max_amount': threshold + 10000,
        'job_url': 'http://rich.com',
        'description': 'a' * 150
    })

    # Inject a job that doesn't meet threshold
    jobs_dict.append({
        'title': 'Low Paying Job',
        'company': 'Poor Co',
        'location': 'Remote',
        'min_amount': threshold - 20000,
        'max_amount': threshold - 10000,
        'job_url': 'http://poor.com',
        'description': 'a' * 150
    })

    df = pd.DataFrame(jobs_dict)

    config = AppConfig(
        provider="dummy", model="dummy", base_resume="dummy", output_dir="dummy",
        search=SearchConfig(keywords="dummy", location="dummy", remote=True, results_wanted=10, min_salary=threshold)
    )

    filtered_df = _filter_jobs(df, config)

    # All resulting jobs must have max_amount >= threshold
    assert (filtered_df['max_amount'] >= threshold).all()
