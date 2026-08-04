import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
import yaml
from dotenv import load_dotenv

from .exceptions import ConfigError

@dataclass
class SearchConfig:
    keywords: str
    location: str
    remote: bool
    results_wanted: int
    min_salary: Optional[int] = None
    exclude_companies: List[str] = field(default_factory=list)
    job_type: Optional[str] = None
    proxies: List[str] = field(default_factory=list)
    exclude_keywords: List[str] = field(default_factory=list)

@dataclass
class PdfConfig:
    theme: str = "sb2nov"

@dataclass
class AppConfig:
    provider: str
    model: str
    base_resume: str
    output_dir: str
    search: SearchConfig
    pdf: PdfConfig = field(default_factory=PdfConfig)
    base_url: Optional[str] = None

def load_config(config_path: Path) -> AppConfig:
    load_dotenv()

    if not config_path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Error parsing YAML: {e}")

    if data is None:
        data = {}

    required_keys = ['provider', 'model', 'base_resume', 'output_dir', 'search']
    for key in required_keys:
        if key not in data:
            raise ConfigError(f"Missing required configuration key: '{key}'")

    search_data = data['search']
    if not isinstance(search_data, dict):
        raise ConfigError("The 'search' configuration must be a dictionary")

    search_required_keys = ['keywords', 'location', 'remote', 'results_wanted']
    for key in search_required_keys:
        if key not in search_data:
            raise ConfigError(f"Missing required configuration key: 'search.{key}'")

    search_config = SearchConfig(
        keywords=search_data['keywords'],
        location=search_data['location'],
        remote=bool(search_data['remote']),
        results_wanted=int(search_data['results_wanted']),
        min_salary=search_data.get('min_salary'),
        exclude_companies=search_data.get('exclude_companies', []),
        job_type=search_data.get('job_type'),
        proxies=search_data.get('proxies', []),
        exclude_keywords=search_data.get('exclude_keywords', [])
    )

    pdf_data = data.get('pdf', {})
    pdf_config = PdfConfig(
        theme=pdf_data.get('theme', "sb2nov")
    )

    return AppConfig(
        provider=data['provider'],
        model=data['model'],
        base_resume=data['base_resume'],
        output_dir=data['output_dir'],
        search=search_config,
        pdf=pdf_config,
        base_url=data.get('base_url')
    )
