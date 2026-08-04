import json
from pathlib import Path
from typing import Set

def load_processed_ids(user_dir: Path) -> Set[str]:
    """Reads processed_jobs.json from user_dir. Creates with empty list if missing."""
    file_path = user_dir / "processed_jobs.json"
    if not file_path.exists():
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        return set()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        data = []

    if isinstance(data, dict):
        # Handle the case where scaffold created {}
        return set(data.keys())
    elif isinstance(data, list):
        return set(data)
    else:
        return set()

def is_processed(job_id: str, processed_ids: Set[str]) -> bool:
    """Returns True if job_id is in processed_ids."""
    return job_id in processed_ids

def mark_processed(job_id: str, user_dir: Path) -> None:
    """Appends job_id to processed_jobs.json."""
    file_path = user_dir / "processed_jobs.json"

    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []
    else:
        data = []

    if isinstance(data, dict):
        # Convert to list if it was a dict
        data = list(data.keys())
    elif not isinstance(data, list):
        data = []

    if job_id not in data:
        data.append(job_id)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
