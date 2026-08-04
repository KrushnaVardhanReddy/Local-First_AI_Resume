import pytest
from hypothesis import given, strategies as st
from src.utils import make_job_slug
import re

@given(st.text(), st.text())
def test_slug_filesystem_safety(company, title):
    slug = make_job_slug(company, title)
    assert len(slug) <= 80
    if slug:
        assert bool(re.match(r'^[a-z0-9-]+$', slug))

@given(st.text(), st.text())
def test_slug_stability(company, title):
    slug1 = make_job_slug(company, title)
    slug2 = make_job_slug(company, title)
    assert slug1 == slug2
