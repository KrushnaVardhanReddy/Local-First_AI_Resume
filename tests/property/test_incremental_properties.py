import pytest
from hypothesis import given, strategies as st
from src.incremental import is_processed

@given(processed_ids=st.sets(st.text()), new_id=st.text())
def test_incremental_processor_never_reprocesses(processed_ids, new_id):
    """
    Property 7: Incremental processor never reprocesses a seen job.
    Use st.sets(st.text()) for processed IDs and st.text() for a known ID in the set;
    assert is_processed returns True and job is skipped.
    """
    # Guarantee that new_id is in processed_ids to test that a seen job is identified as processed
    processed_ids.add(new_id)

    assert is_processed(new_id, processed_ids) is True
