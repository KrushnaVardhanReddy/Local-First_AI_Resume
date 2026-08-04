from hypothesis import given, strategies as st
from src.render_pdf import _md_to_rendercv_yaml

@given(st.text())
def test_resume_markdown_to_rendercv_yaml_structure(md_content):
    personal_info = {"theme": "classic"}
    result = _md_to_rendercv_yaml(md_content, personal_info)

    assert "cv" in result
    assert "design" in result

    assert "sections" in result["cv"]
    assert len(result["cv"]["sections"]) >= 1
