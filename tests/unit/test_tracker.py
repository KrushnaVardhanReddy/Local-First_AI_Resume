import pytest
from src.tracker import update_tracker
from src.models import Job, MatchResult
import csv

def test_tracker_reads_and_rewrites_existing(tmp_path):
    job = Job(title="Dev", company="Corp", location="Remote", salary_min=None, salary_max=None, source_url="http", description="desc")
    match = MatchResult(score=90, strong_matches=[], gaps=[], suggestions=[], raw_text="")

    update_tracker(job, match, tmp_path)

    # modify status manually
    tracker_csv = tmp_path / "tracker.csv"
    lines = tracker_csv.read_text(encoding='utf-8').splitlines()
    lines[1] = lines[1].replace("- [ ]", "- [x]")
    tracker_csv.write_text("\n".join(lines), encoding='utf-8')

    # update again
    update_tracker(job, match, tmp_path)

    # check that status is preserved
    with open(tracker_csv, 'r', encoding='utf-8') as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 1
        assert reader[0]["Status"] == "- [x]"

def test_new_entries_appended_correct_format(tmp_path):
    job1 = Job(title="Dev1", company="Corp1", location="Remote", salary_min=10, salary_max=20, source_url="http1", description="desc")
    job2 = Job(title="Dev2", company="Corp2", location="Remote", salary_min=30, salary_max=None, source_url="http2", description="desc")

    match = MatchResult(score=80, strong_matches=[], gaps=[], suggestions=[], raw_text="")

    update_tracker(job1, match, tmp_path)
    update_tracker(job2, match, tmp_path)

    tracker_csv = tmp_path / "tracker.csv"
    with open(tracker_csv, 'r', encoding='utf-8') as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 2
        assert reader[0]["Salary"] == "10-20"
        assert reader[1]["Salary"] == "30"
        assert reader[0]["Status"] == "- [ ]"

    tracker_md = tmp_path / "tracker.md"
    assert tracker_md.exists()
    md_content = tracker_md.read_text(encoding='utf-8')
    assert "| Company | Title | Location | Match Score | Salary | Link | Resume | Status |" in md_content
    assert "| Corp1 | Dev1 | Remote | 80 | 10-20 | http1 | output/corp1-dev1/resume.pdf | - [ ] |" in md_content
