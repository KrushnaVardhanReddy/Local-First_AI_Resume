import os
import subprocess
from pathlib import Path
import markdown
from weasyprint import HTML
import yaml
import re
import shutil

from src.exceptions import RenderError

def _md_to_rendercv_yaml(md_content: str, personal_info: dict) -> dict:
    """
    Parse structured markdown resume sections (name, experience, education, skills).
    Return dict with top-level keys `cv` (containing `name`, `email`, `sections`)
    and `design` (containing `theme`).
    """
    sections = {}
    current_section = "Summary"
    current_content = []

    for line in md_content.splitlines():
        # Match headings (## Section Name or # Section Name)
        heading_match = re.match(r'^#+\s+(.*)', line)
        if heading_match:
            if current_content:
                sections[current_section] = ["\n".join(current_content).strip()]
            current_section = heading_match.group(1).strip()
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        sections[current_section] = ["\n".join(current_content).strip()]

    # If the markdown was totally empty or no sections matched
    if not sections:
        sections["Summary"] = [md_content]

    cv_data = {
        "name": personal_info.get("name", "John Doe"),
        "email": personal_info.get("email", "john@example.com"),
        "sections": sections
    }
    design_data = {
        "theme": personal_info.get("theme", "classic")
    }
    return {"cv": cv_data, "design": design_data}

def render_resume_pdf(job, output_dir: Path, theme: str, user_dir: Path) -> Path:
    """
    Verify `resume.md` exists (raise `RenderError` if not); call `_md_to_rendercv_yaml()`;
    write `resume.yaml`; invoke `rendercv render resume.yaml` via `subprocess`;
    verify output PDF exists; raise `RenderError` if not; return PDF path.
    """
    resume_md_path = output_dir / "resume.md"
    if not resume_md_path.exists():
        raise RenderError(f"Source markdown file missing: {resume_md_path}")

    with open(resume_md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    personal_info = {"theme": theme}
    yaml_data = _md_to_rendercv_yaml(md_content, personal_info)

    resume_yaml_path = output_dir / "resume.yaml"
    with open(resume_yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f)

    # Check for custom theme
    custom_theme_dir = user_dir / "templates" / theme
    if custom_theme_dir.exists() and custom_theme_dir.is_dir():
        target_theme_dir = output_dir / theme
        shutil.copytree(custom_theme_dir, target_theme_dir, dirs_exist_ok=True)

    try:
        result = subprocess.run(["rendercv", "render", "resume.yaml"], cwd=output_dir, capture_output=True, text=True)
        if result.returncode != 0:
            raise RenderError(f"RenderCV exited with code {result.returncode}: {result.stderr}")
    except Exception as e:
        if isinstance(e, RenderError):
            raise
        raise RenderError(f"Failed to run RenderCV: {e}")

    pdf_dir = output_dir / "rendercv_output"
    pdfs = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []

    if not pdfs:
        raise RenderError("RenderCV finished but no PDF was generated.")

    output_pdf = output_dir / "resume.pdf"
    os.replace(pdfs[0], output_pdf)
    return output_pdf

def render_cover_letter_pdf(job, output_dir: Path) -> Path:
    """
    Verify `cover_letter.md` exists (raise `RenderError` if not);
    convert markdown → HTML via `markdown` library;
    convert HTML → PDF via WeasyPrint; verify PDF written; return PDF path.
    """
    cl_md_path = output_dir / "cover_letter.md"
    if not cl_md_path.exists():
        raise RenderError(f"Source markdown file missing: {cl_md_path}")

    with open(cl_md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    html_content = markdown.markdown(md_content)

    pdf_path = output_dir / "cover_letter.pdf"

    HTML(string=html_content).write_pdf(str(pdf_path))

    if not pdf_path.exists():
        raise RenderError("WeasyPrint finished but no PDF was generated.")

    return pdf_path
