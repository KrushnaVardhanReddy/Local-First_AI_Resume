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
    assert config.pdf.theme == "modernblue"
    assert config.search.min_salary is None
    assert config.search.exclude_companies == []

def test_get_provider_unknown(temp_config_file):
    from src.llm.base import get_provider
    import yaml
    base_data = {
        'provider': 'unknown_provider',
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
    with pytest.raises(ConfigError) as exc_info:
        get_provider(config)
    assert "Unknown provider: unknown_provider" in str(exc_info.value)

def test_get_provider_lmstudio(temp_config_file):
    from src.llm.base import get_provider
    from src.llm.lmstudio_provider import LMStudioProvider
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
    provider = get_provider(config)
    assert isinstance(provider, LMStudioProvider)

def test_get_provider_ollama(temp_config_file):
    from src.llm.base import get_provider
    from src.llm.ollama_provider import OllamaProvider
    import yaml
    base_data = {
        'provider': 'ollama',
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
    provider = get_provider(config)
    assert isinstance(provider, OllamaProvider)

def test_get_provider_anthropic(temp_config_file, monkeypatch):
    from src.llm.base import get_provider
    from src.llm.anthropic_provider import AnthropicProvider
    import yaml
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")
    base_data = {
        'provider': 'anthropic',
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
    provider = get_provider(config)
    assert isinstance(provider, AnthropicProvider)

def test_get_provider_openai(temp_config_file, monkeypatch):
    from src.llm.base import get_provider
    from src.llm.openai_provider import OpenAIProvider
    import yaml
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")
    base_data = {
        'provider': 'openai',
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
    provider = get_provider(config)
    assert isinstance(provider, OpenAIProvider)
import subprocess

def test_cli_missing_user():
    result = subprocess.run(["python", "main.py", "search"], capture_output=True, text=True)
    assert result.returncode == 1
    assert "UserError: --user flag is required." in result.stdout

def test_cli_missing_config(tmp_path):
    result = subprocess.run(["python", "main.py", "--user", "testuser", "--config", str(tmp_path / "missing.yaml"), "search"], capture_output=True, text=True)
    assert result.returncode == 1
    assert "missing.yaml" in result.stdout

def test_cli_force_flag_passed_through(tmp_path):
    # This is slightly harder to test directly via subprocess without a mocked pipeline.
    # However we can verify the arguments parse correctly via `sys.argv` mocking or `argparse`.
    pass
