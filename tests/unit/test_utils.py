from src.utils import make_job_slug

def test_make_job_slug():
    assert make_job_slug("Google", "Senior Software Engineer!!") == "google-senior-software-engineer"
    assert make_job_slug("  Apple  ", "  Data Scientist  ") == "apple-data-scientist"
    long_title = "A" * 100
    assert len(make_job_slug("Company", long_title)) == 80
