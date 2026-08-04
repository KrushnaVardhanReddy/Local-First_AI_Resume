import json
import tempfile
import re
from pathlib import Path
from hypothesis import given, strategies as st

from src.models import Job, MatchResult
from src.config import AppConfig, SearchConfig
from src.pipeline import write_metadata_json

@given(
    st.text(min_size=1),
    st.text(min_size=1),
    st.integers(min_value=0, max_value=100)
)
def test_metadata_json_contains_required_fields(provider, model, score):
    """
    Property 13: Metadata JSON contains all required fields after processing
    """
    job = Job("Test Title", "Test Company", "Location", 100, 200, "http://url", "Description")
    match = MatchResult(
        score=score,
        strong_matches=[],
        gaps=[],
        suggestions=[],
        raw_text="dummy"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config = AppConfig(
            provider=provider,
            model=model,
            base_resume="base.md",
            output_dir="output",
            search=SearchConfig("keys", "loc", True, 10)
        )

        usage_stats = {"total_tokens": 100}

        write_metadata_json(job, match, config, tmp_path, usage_stats)

        metadata_file = tmp_path / "metadata.json"
        assert metadata_file.exists()

        with open(metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "job_slug" in data
        assert "processed_at" in data
        assert "provider" in data
        assert "model" in data
        assert "match_score" in data

        assert data["job_slug"] == job.slug
        assert data["provider"] == provider
        assert data["model"] == model
        assert data["match_score"] == score

        # Verify ISO 8601 pattern roughly
        assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", data["processed_at"])
