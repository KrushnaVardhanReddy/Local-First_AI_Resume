from hypothesis import given, strategies as st
from src.render_pdf import _json_to_rendercv_yaml

@given(st.dictionaries(keys=st.text(), values=st.text()))
def test_resume_json_to_rendercv_yaml_structure(json_content):
    personal_info = {"theme": "classic"}
    result = _json_to_rendercv_yaml(json_content, personal_info)

    assert "cv" in result
    assert "design" in result

    assert "sections" in result["cv"]
