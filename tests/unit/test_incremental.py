import json
import pytest
from pathlib import Path
from src.incremental import load_processed_ids, mark_processed

def test_load_processed_ids_creates_empty_file_if_missing(tmp_path: Path):
    """
    Test that if processed_jobs.json is missing, load_processed_ids creates it
    with an empty list and returns an empty set.
    """
    file_path = tmp_path / "processed_jobs.json"
    assert not file_path.exists()

    result = load_processed_ids(tmp_path)

    assert result == set()
    assert file_path.exists()

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == []

def test_mark_processed_appends_to_file(tmp_path: Path):
    """Test that mark_processed successfully appends to the json list."""
    job_id = "test_id_1"

    mark_processed(job_id, tmp_path)

    file_path = tmp_path / "processed_jobs.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data == [job_id]

    # Add another one
    mark_processed("test_id_2", tmp_path)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data == [job_id, "test_id_2"]
