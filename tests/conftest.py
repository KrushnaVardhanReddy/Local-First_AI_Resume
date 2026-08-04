import pytest
from hypothesis import strategies as st
from src.models import Job

@st.composite
def job_strategy(draw):
    title = draw(st.text(min_size=1))
    company = draw(st.text(min_size=1))
    location = draw(st.text(min_size=1))
    salary_min = draw(st.one_of(st.none(), st.integers(min_value=0)))
    salary_max = draw(st.one_of(st.none(), st.integers(min_value=0)))
    source_url = draw(st.text(min_size=1))
    description = draw(st.text(min_size=100))
    return Job(
        title=title,
        company=company,
        location=location,
        salary_min=salary_min,
        salary_max=salary_max,
        source_url=source_url,
        description=description
    )
