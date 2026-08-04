import json
import tempfile
import pytest
from hypothesis import given, strategies as st
from pathlib import Path
from src.search_jobs import _save_job
from tests.conftest import job_strategy

@given(st.lists(job_strategy(), min_size=1, max_size=5))
def test_job_file_pair_written(jobs):
    # Requirements: 1.6, 1.7 Accepted job files are always written as a pair

    with tempfile.TemporaryDirectory() as temp_dir:
        tmp_path = Path(temp_dir)
        for job in jobs:
            _save_job(job, tmp_path)

            job_dir = tmp_path / job.slug

            # Verify both job.md and job.json exist
            assert (job_dir / "job.md").exists()
            assert (job_dir / "job.json").exists()

            # Verify job.json has expected content
            with open(job_dir / "job.json", "r", encoding="utf-8") as f:
                data = json.load(f)

            assert data["title"] == job.title
            assert data["company"] == job.company
            assert data["location"] == job.location
            assert data["source_url"] == job.source_url
