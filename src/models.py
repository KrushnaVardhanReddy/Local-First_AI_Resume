from dataclasses import dataclass, field
import hashlib
from typing import Optional
from src.utils import make_job_slug

@dataclass
class Job:
    title: str
    company: str
    location: str
    salary_min: Optional[int]
    salary_max: Optional[int]
    source_url: str
    description: str
    id: str = field(init=False)
    slug: str = field(init=False)

    def __post_init__(self):
        # id is a 16-char hex string computed as sha256(company + title + source_url)[:16]
        hash_input = f"{self.company}{self.title}{self.source_url}".encode("utf-8")
        self.id = hashlib.sha256(hash_input).hexdigest()[:16]

        # slug is derived by calling make_job_slug(company, title)
        self.slug = make_job_slug(self.company, self.title)

@dataclass
class MatchResult:
    score: int
    strong_matches: list[str]
    gaps: list[str]
    suggestions: list[str]
    raw_text: str
