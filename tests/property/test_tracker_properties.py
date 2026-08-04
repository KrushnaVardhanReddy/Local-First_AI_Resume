from hypothesis import given, strategies as st, settings, HealthCheck
from tests.conftest import job_strategy
from src.tracker import update_tracker
from src.models import MatchResult
import csv
import tempfile
from pathlib import Path

@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.lists(job_strategy()))
def test_tracker_upsert_uniqueness(jobs):
    with tempfile.TemporaryDirectory() as temp_dir:
        tmp_path = Path(temp_dir)
        for job in jobs:
            match = MatchResult(score=85, strong_matches=[], gaps=[], suggestions=[], raw_text="")
            update_tracker(job, match, tmp_path)

        tracker_csv = tmp_path / "tracker.csv"
        if tracker_csv.exists():
            with open(tracker_csv, 'r', encoding='utf-8') as f:
                reader = list(csv.DictReader(f))

                # Uniqueness check
                seen = set()
                for row in reader:
                    key = (row["Company"], row["Title"])
                    assert key not in seen
                    seen.add(key)

                for row in reader:
                    assert row["Status"] == "- [ ]"
