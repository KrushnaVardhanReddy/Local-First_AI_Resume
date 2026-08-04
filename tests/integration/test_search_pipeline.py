import pytest
import pandas as pd
from unittest.mock import patch
from pathlib import Path

from main import main
from src.models import Job

@patch("src.search_jobs.JobspyProvider.search")
def test_search_pipeline(mock_search, tmp_path, monkeypatch):
    # Mocking JobSpy search to return a fixed DataFrame
    # 3 Jobs:
    # 1. Valid Job
    # 2. Duplicate of Valid Job
    # 3. Short description job
    df = pd.DataFrame([
        {
            'title': 'Software Engineer',
            'company': 'Tech Corp',
            'location': 'Remote',
            'min_amount': 100000,
            'max_amount': 150000,
            'job_url': 'http://example.com/job1',
            'description': 'This is a valid long description for a job that meets all the criteria. ' * 10
        },
        {
            'title': 'Software Engineer',
            'company': 'Tech Corp',
            'location': 'Remote',
            'min_amount': 100000,
            'max_amount': 150000,
            'job_url': 'http://example.com/job2',
            'description': 'This is a duplicate job, it should be filtered out based on company and title. ' * 10
        },
        {
            'title': 'Backend Developer',
            'company': 'Another Corp',
            'location': 'Remote',
            'min_amount': 90000,
            'max_amount': 120000,
            'job_url': 'http://example.com/job3',
            'description': 'Short desc'
        }
    ])
    mock_search.return_value = df

    # Change working directory to tmp_path to isolate test output
    monkeypatch.chdir(tmp_path)

    # Create necessary scaffold
    user = "testuser"
    user_dir = tmp_path / "users" / user
    user_dir.mkdir(parents=True, exist_ok=True)

    # Create a basic config.yaml
    config_yaml = """
provider: lmstudio
model: qwen
base_resume: resume.md
output_dir: output
search:
  keywords: "Software Engineer"
  location: "Remote"
  remote: true
  results_wanted: 10
    """
    (user_dir / "config.yaml").write_text(config_yaml)

    # Mock sys.argv to run main with search command
    import sys
    monkeypatch.setattr(sys, "argv", ["main.py", "--user", user, "search"])

    # Run the main application
    main()

    # Verify that only the first job is saved in output_dir
    output_dir = user_dir / "output"

    assert output_dir.exists()

    # We should have exactly 1 directory in output
    job_dirs = [d for d in output_dir.iterdir() if d.is_dir()]
    assert len(job_dirs) == 1, f"Expected 1 job directory, found {len(job_dirs)}"

    job_dir = job_dirs[0]

    # Verify job.md and job.json exist
    assert (job_dir / "job.md").exists()
    assert (job_dir / "job.json").exists()

    import json
    with open(job_dir / "job.json", "r") as f:
        job_data = json.load(f)

    assert job_data["title"] == "Software Engineer"
    assert job_data["company"] == "Tech Corp"
    assert job_data["location"] == "Remote"
