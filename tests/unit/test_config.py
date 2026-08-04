import os
from pathlib import Path
import pytest
from src.config import load_config, AppConfig, SearchConfig, PdfConfig
from src.exceptions import ConfigError

@pytest.fixture
def temp_config_file(tmp_path):
    config_file = tmp_path / "config.yaml"
    return config_file

def test_missing_required_keys(temp_config_file):
    import yaml
    base_data = {
        'provider': 'lmstudio',
        'model': 'qwen',
        'base_resume': 'resume.md',
        'output_dir': 'output',
        'search': {
            'keywords': 'test',
            'location': 'remote',
            'remote': True,
            'results_wanted': 10
        }
    }

    required_keys = ['provider', 'model', 'base_resume', 'output_dir', 'search']

    for key in required_keys:
        test_data = base_data.copy()
        del test_data[key]

        with open(temp_config_file, 'w') as f:
            yaml.dump(test_data, f)

        with pytest.raises(ConfigError) as exc_info:
            load_config(temp_config_file)

        assert f"Missing required configuration key: '{key}'" in str(exc_info.value)

def test_missing_search_keys(temp_config_file):
    import yaml
    base_data = {
        'provider': 'lmstudio',
        'model': 'qwen',
        'base_resume': 'resume.md',
        'output_dir': 'output',
        'search': {
            'keywords': 'test',
            'location': 'remote',
            'remote': True,
            'results_wanted': 10
        }
    }

    search_keys = ['keywords', 'location', 'remote', 'results_wanted']

    for key in search_keys:
        test_data = base_data.copy()
        test_data['search'] = base_data['search'].copy()
        del test_data['search'][key]

        with open(temp_config_file, 'w') as f:
            yaml.dump(test_data, f)

        with pytest.raises(ConfigError) as exc_info:
            load_config(temp_config_file)

        assert f"Missing required configuration key: 'search.{key}'" in str(exc_info.value)

def test_env_loaded_before_reading(tmp_path, monkeypatch):
    import yaml
    # We create a dummy .env file in the current working directory
    # that python-dotenv will load.
    cwd = Path.cwd()
    env_file = cwd / ".env"
    env_file.write_text("TEST_ENV_VAR=loaded_value")

    config_file = tmp_path / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump({
            'provider': 'lmstudio',
            'model': 'qwen',
            'base_resume': 'resume.md',
            'output_dir': 'output',
            'search': {
                'keywords': 'test',
                'location': 'remote',
                'remote': True,
                'results_wanted': 10
            }
        }, f)

    try:
        # Before load_config, it should not be in os.environ, except if it leaked from before.
        # But we verify it's there after. Actually load_dotenv loads into os.environ.
        load_config(config_file)
        assert os.environ.get("TEST_ENV_VAR") == "loaded_value"
    finally:
        if env_file.exists():
            env_file.unlink()
        if "TEST_ENV_VAR" in os.environ:
            del os.environ["TEST_ENV_VAR"]

def test_optional_keys_default_correctly(temp_config_file):
    import yaml
    base_data = {
        'provider': 'lmstudio',
        'model': 'qwen',
        'base_resume': 'resume.md',
        'output_dir': 'output',
        'search': {
            'keywords': 'test',
            'location': 'remote',
            'remote': True,
            'results_wanted': 10
        }
    }

    with open(temp_config_file, 'w') as f:
        yaml.dump(base_data, f)

    config = load_config(temp_config_file)

    assert config.base_url is None
    assert config.pdf.theme == "sb2nov"
    assert config.search.min_salary is None
    assert config.search.exclude_companies == []
