from src.models import Job, MatchResult
import hashlib

def test_job_post_init():
    job = Job(
        title="Software Engineer",
        company="Acme Corp",
        location="Remote",
        salary_min=100000,
        salary_max=150000,
        source_url="http://example.com/job",
        description="Great job."
    )

    assert job.slug == "acme-corp-software-engineer"
    expected_hash_input = b"Acme CorpSoftware Engineerhttp://example.com/job"
    expected_id = hashlib.sha256(expected_hash_input).hexdigest()[:16]
    assert job.id == expected_id

def test_match_result():
    mr = MatchResult(
        score=85,
        strong_matches=["Python", "Go"],
        gaps=["Java"],
        suggestions=["Learn Java"],
        raw_text="The score is 85."
    )
    assert mr.score == 85
    assert len(mr.strong_matches) == 2
