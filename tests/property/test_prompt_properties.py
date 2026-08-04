import pytest
from hypothesis import given, settings, strategies as st
from src.utils import load_prompt
from src.exceptions import PromptError
from pathlib import Path
import tempfile
import os

@given(st.text(min_size=1), st.text(min_size=1))
@settings(max_examples=50) # run slightly fewer times to speed up IO
def test_prompt_substitution_completeness(text1, text2):
    with tempfile.TemporaryDirectory() as temp_dir:
        tmp_path = Path(temp_dir)
        # Setup temp user dir and prompt file
        user_dir = tmp_path / "user"
        user_dir.mkdir()
        prompts_dir = user_dir / "prompts"
        prompts_dir.mkdir()

        template_name = "test_template.md"
        template_path = prompts_dir / template_name
        template_content = "Resume: {{base_resume}}\nJob: {{job_description}}\n"
        template_path.write_text(template_content)

        variables = {
            "base_resume": text1,
            "job_description": text2
        }

        result = load_prompt(template_name, user_dir, variables)

        assert "{{base_resume}}" not in result
        assert "{{job_description}}" not in result
        assert text1 in result
        assert text2 in result
