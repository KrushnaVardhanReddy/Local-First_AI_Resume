import re

def make_job_slug(company: str, title: str) -> str:
    """
    Lowercase, hyphenate, collapse consecutive hyphens, strip leading/trailing hyphens,
    and truncate to 80 chars.
    """
    slug_str = f"{company} {title}".lower()
    # Replace non-alphanumeric characters with hyphens
    slug_str = re.sub(r'[^a-z0-9]', '-', slug_str)
    # Collapse consecutive hyphens
    slug_str = re.sub(r'-+', '-', slug_str)
    # Strip leading and trailing hyphens
    slug_str = slug_str.strip('-')
    # Truncate to 80 characters
    return slug_str[:80]
