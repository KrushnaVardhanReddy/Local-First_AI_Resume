# Job Pipeline (Local-First AI Resume Tailoring)

## Vision

A privacy-first, open-source Python pipeline that helps job seekers find jobs, tailor resumes and cover letters using **local or cloud LLMs**, generate PDFs, and maintain a manual application tracker.

The project **does not automate job applications**. It prepares high-quality application materials while leaving the final submission to the user.

---

# Core Principles

* Local-first
* Privacy-first
* Markdown-first
* Open source
* Provider agnostic
* No vendor lock-in
* No fabricated resume content
* Manual application only

---

# Project Structure

```
job_pipeline/
├── requirements.txt
├── .env.example
├── config.yaml
├── base_resume.md
├── prompts/
│   ├── resume.md
│   ├── cover_letter.md
│   └── match_notes.md
├── src/
│   ├── llm/
│   │   ├── base.py
│   │   ├── anthropic_provider.py
│   │   ├── openai_provider.py
│   │   ├── lmstudio_provider.py
│   │   └── ollama_provider.py
│   ├── search_jobs.py
│   ├── tailor_resume.py
│   ├── render_pdf.py
│   ├── tracker.py
│   └── utils.py
├── output/
│   ├── tracker.md
│   ├── tracker.csv
│   └── <job-slug>/
│       ├── job.md
│       ├── job.json
│       ├── resume.md
│       ├── resume.pdf
│       ├── cover_letter.md
│       ├── cover_letter.pdf
│       ├── match_notes.md
│       └── metadata.json
├── processed_jobs.json
└── main.py
```

---

# Features

## Job Search

Uses JobSpy to search:

* Indeed
* LinkedIn
* Additional sources later

Filters by:

* Location
* Remote
* Keywords
* Salary
* Company
* Duplicate jobs
* Description quality

---

## AI Resume Tailoring

Input

* Base resume
* Job description

Output

* Tailored resume
* Cover letter
* Match notes

Rules

* Never invent experience
* Never invent companies
* Never invent dates
* Never invent projects
* Only reorder and improve existing experience

---

## Match Analysis

Generate:

* Match Score (0-100)
* Strong matches
* Missing skills
* Suggestions

Example

```
Match Score: 88

Strong Matches
--------------
• Go backend
• REST APIs
• SQL

Gaps
----
• Tableau
• Snowflake
```

---

# Local-First LLM Support

Supported providers

* LM Studio
* Ollama
* Anthropic
* OpenAI

Future

* LiteLLM
* vLLM
* OpenRouter

Provider selection is configurable.

Example

```yaml
provider: lmstudio

base_url: http://localhost:1234/v1

model: qwen3-8b
```

or

```yaml
provider: anthropic

model: claude-sonnet-5
```

No code changes required.

---

# Recommended Local Models

* Qwen 3 8B ⭐⭐⭐⭐⭐
* Qwen 3 14B ⭐⭐⭐⭐⭐
* Gemma 3 12B
* Llama 3.1 8B
* Mistral Small

---

# Generated Output

Each job gets its own folder.

```
google-backend-engineer/

job.md
job.json

resume.md
resume.pdf

cover_letter.md
cover_letter.pdf

match_notes.md

metadata.json
```

The original job description is always preserved so documents can be regenerated later.

---

# Tracker

Generate both

```
tracker.md

tracker.csv
```

Columns

* Company
* Title
* Location
* Match Score
* Salary
* Link
* Resume
* Status

Status

```
- [ ] Applied
- [ ] Interview
- [ ] Offer
```

Manual tracking only.

---

# Incremental Processing

Store processed jobs

```
processed_jobs.json
```

Previously processed jobs are skipped automatically.

---

# Prompt System

Prompts are stored separately.

```
prompts/

resume.md

cover_letter.md

match_notes.md
```

This allows easy prompt tuning without changing Python code.

---

# Resume Profiles

Support multiple resumes.

```
resumes/

backend.md

golang.md

ai.md

data.md
```

Configured using

```yaml
base_resume: resumes/backend.md
```

---

# Future Voice Mode (Optional)

Integrate local Whisper.

Examples

* Speak resume updates
* Record interview notes
* Dictate cover letter instructions
* Capture project accomplishments

Pipeline

```
Voice

↓

Whisper (local)

↓

Transcript

↓

Local LLM

↓

Resume / Notes
```

Entire workflow can remain local.

---

# Manual Application Workflow

1. Search jobs
2. Filter jobs
3. Tailor resume
4. Generate cover letter
5. Generate PDFs
6. Update tracker
7. User opens tracker
8. Clicks original job link
9. Uploads generated resume
10. Applies manually

No login automation.

No browser automation.

No CAPTCHA solving.

No auto submission.

---

# Why This Project?

Unlike existing resume builders, this project is:

* Local-first
* Open source
* Privacy-focused
* Markdown-based
* Git-friendly
* Provider agnostic
* LLM independent
* Easy to extend
* Suitable for developers

It serves as a reusable engine for AI-assisted job applications rather than another hosted resume website.

---

# MVP Scope (Phase 1 — CLI Pipeline)

* JobSpy integration (Indeed + LinkedIn)
* Resume tailoring via local or cloud LLM
* Cover letter generation
* Match notes with score (0–100)
* Markdown generation
* PDF generation via RenderCV (ATS-friendly) + WeasyPrint
* Local/cloud LLM support (LM Studio, Ollama, Anthropic, OpenAI)
* Markdown + CSV tracker
* Incremental processing (skip already-processed jobs)
* Multiple resume profiles
* Multi-user support (`users/{username}/` isolation)

Everything else can be added incrementally in future releases.

---

# Phase 2 — Local Web UI (Streamlit)

Once the CLI pipeline is stable, a lightweight local web UI will be added as an optional layer on top. The core pipeline stays untouched — the UI simply wraps it.

## Why

The CLI is sufficient for developers, but non-technical users (e.g. a pharma researcher sharing the same machine) benefit from a visual interface for the most interactive parts of the workflow.

## Planned UI surfaces

**Job Review Dashboard**
After a search run, display all found jobs in a filterable table. Allow the user to deselect irrelevant jobs before triggering tailoring — avoiding wasted LLM calls.

**Tracker Dashboard**
Replace the raw markdown table with a visual tracker. Toggle application status (Applied → Interview → Offer) with one click. Filter and sort by match score, company, or date.

**User Setup Wizard**
Guide a new user through creating their profile: enter username, upload resume, fill in `config.yaml` fields via a form. No file editing required.

## Tech stack

* **Streamlit** — pure Python, fits the existing stack, no JS needed
* Runs locally: `uv run main.py --user {username} ui` → opens `localhost:8501`
* No data leaves the machine

## How to launch (future)

```bash
uv run main.py --user krushna ui
```

This will be implemented as a separate spec (`ui-dashboard`) once Phase 1 is complete.
