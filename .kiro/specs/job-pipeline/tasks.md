# Implementation Plan: Job Pipeline

## Overview

Implement a local-first, privacy-first CLI tool that searches jobs via JobSpy, tailors resumes and cover letters using pluggable LLM providers, renders PDFs with RenderCV and WeasyPrint, and maintains a per-user markdown and CSV tracker. The implementation is staged: project scaffolding → core models and exceptions → configuration → LLM abstraction → job search and filtering → resume/cover letter/match tailoring → PDF rendering → tracker → pipeline orchestration → CLI entry point → tests.

## Tasks

- [x] 1. Set up project structure and core foundation
  - Create `pyproject.toml` with `uv` project metadata, Python ≥ 3.10 constraint, and dependencies: `python-jobspy`, `hypothesis`, `pytest`, `weasyprint`, `markdown`, `python-dotenv`, `pyyaml`, `anthropic`, `openai`, `requests`
  - Create `uv.lock` by running `uv lock`
  - Create `.env.example` with `ANTHROPIC_API_KEY=` and `OPENAI_API_KEY=` placeholders
  - Create `config.yaml.example` with all supported keys and inline comments matching the design's config structure
  - Create `src/__init__.py`, `src/llm/__init__.py`
  - Create `prompts/resume.md`, `prompts/cover_letter.md`, `prompts/match_notes.md` with default prompt templates using `{{base_resume}}` and `{{job_description}}` placeholders
  - Create `users/` directory entry in `.gitignore`
  - _Requirements: 9.1, 9.2, 11.1, 11.4, 14.8_

- [x] 2. Implement data models and exception classes
  - [x] 2.1 Create `src/models.py` with `Job` and `MatchResult` dataclasses
    - `Job`: fields `id`, `title`, `company`, `location`, `salary_min`, `salary_max`, `source_url`, `description`, `slug`
    - `MatchResult`: fields `score`, `strong_matches`, `gaps`, `suggestions`, `raw_text`
    - `Job.id` is a 16-char hex string computed as `sha256(company + title + source_url)[:16]`
    - `Job.slug` is derived by calling `make_job_slug(company, title)`
    - _Requirements: 1.7, 6.3, 10.1_
  - [x] 2.2 Create `src/exceptions.py` with six exception classes
    - `ConfigError`, `UserError`, `LLMError`, `RenderError`, `PromptError`, `ValidationError`
    - Each inherits from `Exception`; include a docstring describing when it is raised
    - _Requirements: 3.6, 3.7, 9.4, 13.8_

- [x] 3. Implement configuration loader
  - [x] 3.1 Create `src/config.py` with `SearchConfig`, `PdfConfig`, and `AppConfig` dataclasses and `load_config()` function
    - `load_config(config_path: Path) -> AppConfig` reads `config.yaml`, loads `.env` via `python-dotenv`, validates required keys (`provider`, `model`, `base_resume`, `output_dir`, `search`), raises `ConfigError` naming the missing key on failure
    - `SearchConfig` fields: `keywords`, `location`, `remote`, `results_wanted`, `min_salary`, `exclude_companies`
    - `PdfConfig` fields: `theme` (default `"sb2nov"`)
    - `AppConfig` fields: `provider`, `model`, `base_url`, `base_resume`, `output_dir`, `search: SearchConfig`, `pdf: PdfConfig`
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  - [x]* 3.2 Write unit tests for `src/config.py` in `tests/unit/test_config.py`
    - Test that `ConfigError` is raised with the correct key name for each missing required field
    - Test that `.env` variables are loaded before reading API keys
    - Test that optional keys (`base_url`, `pdf`, `min_salary`, `exclude_companies`) default correctly
    - _Requirements: 9.4, 9.5_

- [x] 4. Implement shared utilities
  - [x] 4.1 Create `src/utils.py` with `make_job_slug()`, `load_prompt()`, and `scaffold_user_dir()`
    - `make_job_slug(company, title)`: lowercase, replace non-alphanumeric with hyphens, collapse consecutive hyphens, strip leading/trailing hyphens, truncate to 80 chars
    - `load_prompt(template_name, user_dir, variables)`: look in `user_dir/prompts/` first, fall back to project-root `prompts/`; substitute `{{base_resume}}` and `{{job_description}}` via `str.replace()`; raise `PromptError` if file not found
    - `scaffold_user_dir(user_dir)`: create `resumes/`, `output/`, `prompts/`; write stub `config.yaml`; write empty `processed_jobs.json`
    - _Requirements: 10.2, 11.2, 11.3, 14.4, 14.5_
  - [x]* 4.2 Write property test P1 — slug filesystem-safety in `tests/property/test_slug_properties.py`
    - **Property 1: Job slug is deterministic and filesystem-safe**
    - Use `@given(st.text(), st.text())` for company and title; assert result contains only `[a-z0-9-]` and `len <= 80`
    - **Validates: Requirements 10.2**
  - [x]* 4.3 Write property test P2 — slug stability in `tests/property/test_slug_properties.py`
    - **Property 2: Slug is stable across equivalent inputs**
    - Use `@given(st.text(), st.text())`; call `make_job_slug` twice with same args; assert equality
    - **Validates: Requirements 10.2**
  - [x]* 4.4 Write unit tests for `src/utils.py` in `tests/unit/test_utils.py`
    - Test `make_job_slug` with known inputs: spaces → hyphens, 80-char truncation, special characters
    - Test `load_prompt` loads user-level override when present, falls back to global otherwise
    - Test `scaffold_user_dir` creates expected directories and files
    - _Requirements: 10.2, 11.2, 14.4_
  - [x]* 4.5 Write property test P8 — prompt substitution completeness in `tests/property/test_prompt_properties.py`
    - **Property 8: Prompt variable substitution is complete**
    - Use `@given(st.text(min_size=1), st.text(min_size=1))`; assert result contains neither `{{base_resume}}` nor `{{job_description}}`
    - **Validates: Requirements 11.2**

- [x] 5. Implement LLM provider abstraction
  - [x] 5.1 Create `src/llm/base.py` with `LLMProvider` ABC and `get_provider()` factory
    - `LLMProvider`: abstract base class with `complete(self, prompt: str) -> str`
    - `get_provider(config: AppConfig) -> LLMProvider`: match `config.provider` to `lmstudio`, `ollama`, `anthropic`, `openai`; raise `ConfigError` for unknown values
    - _Requirements: 3.1, 3.6_
  - [x] 5.2 Create `src/llm/lmstudio_provider.py` with `LMStudioProvider`
    - Uses OpenAI-compatible chat completions endpoint at `config.base_url`
    - Raises `LLMError` with provider name and status code on HTTP/network failure
    - _Requirements: 3.2, 3.7_
  - [x] 5.3 Create `src/llm/ollama_provider.py` with `OllamaProvider`
    - Posts to Ollama REST API at `config.base_url/api/generate`
    - Raises `LLMError` with provider name and status code on HTTP/network failure
    - _Requirements: 3.3, 3.7_
  - [x] 5.4 Create `src/llm/anthropic_provider.py` with `AnthropicProvider`
    - Uses `anthropic` SDK, reads `ANTHROPIC_API_KEY` from environment
    - Raises `LLMError` with provider name on API failure
    - _Requirements: 3.4, 3.7_
  - [x] 5.5 Create `src/llm/openai_provider.py` with `OpenAIProvider`
    - Uses `openai` SDK, reads `OPENAI_API_KEY` from environment
    - Raises `LLMError` with provider name on API failure
    - _Requirements: 3.5, 3.7_
  - [x]* 5.6 Write unit tests for LLM providers in `tests/unit/test_config.py`
    - Test that `get_provider()` raises `ConfigError` for unknown provider string
    - Test that each provider is returned for its respective key
    - _Requirements: 3.6_
  - [x] 5.7 Implement Rate-Limiting and Exponential Backoff
    - Wrap API calls in `AnthropicProvider` and `OpenAIProvider` with retry logic.
    - Implement exponential backoff for HTTP 429 (Rate Limit) responses to prevent crashes during large batches.

- [x] 6. Implement job search and filtering
  - [x] 6.1 Create `src/search_jobs.py` with `search_jobs()`, `_filter_jobs()`, and `_save_job()`
    - `search_jobs(config, user_dir)`: call `jobspy.scrape_jobs()` with configured keywords/location/remote/results_wanted; call `_filter_jobs()`; call `_save_job()` for each accepted job; return `list[Job]`
    - `_filter_jobs(jobs_df, config)`: apply deduplication by (company, title); remove entries with description `len < 100`; apply salary filter if `min_salary` set; apply company exclusion list
    - `_save_job(job, output_dir)`: write `job.md` (human-readable) and `job.json` (structured with title, company, location, salary range, source_url) inside `output_dir/{job.slug}/`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_
  - [x]* 6.2 Write property test P3 — duplicate filter in `tests/property/test_filter_properties.py`
    - **Property 3: Duplicate job filter removes exact duplicates**
    - Use `st.lists(job_strategy())` and inject duplicate (company, title) pairs; assert each pair appears at most once in output
    - **Validates: Requirements 1.2**
  - [x]* 6.3 Write property test P4 — short-description filter in `tests/property/test_filter_properties.py`
    - **Property 4: Short-description filter removes all sub-threshold jobs**
    - Use `st.lists(job_strategy())` and inject entries with `len(description) < 100`; assert none remain in output
    - **Validates: Requirements 1.3**
  - [x]* 6.4 Write property test P5 — salary filter in `tests/property/test_filter_properties.py`
    - **Property 5: Salary filter excludes all below-threshold jobs**
    - Use `st.integers()` for threshold and `st.lists(job_strategy())`; assert no job with `salary_max < T` in output
    - **Validates: Requirements 1.4**
  - [x]* 6.5 Write property test P11 — job file pair written in `tests/property/test_search_output_properties.py`
    - **Property 11: Accepted job files are always written as a pair**
    - Use `st.lists(job_strategy(), min_size=1)`; after calling `_save_job()` verify both `job.md` and `job.json` exist and `job.json` has non-empty title, company, location, source_url
    - **Validates: Requirements 1.6, 1.7**
  - [x]* 6.6 Write unit tests for `src/search_jobs.py` in `tests/unit/test_filter.py`
    - Test each filter rule independently with known fixtures
    - Test that `_save_job` writes files to the correct path structure
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6_
  - [x] 6.7 Add job type filtering
    - Add `job_type: Optional[str] = None` to `SearchConfig` (and `config.yaml.example`).
    - Update `src/search_jobs.py` to pass `job_type=config.search.job_type` to the scraper.
  - [x] 6.8 Implement Multi-Provider Concurrent Search
    - Abstract the search provider logic so we can support other scrapers (e.g., SerpAPI, rapidAPI) alongside JobSpy.
    - Use `concurrent.futures` or `asyncio` to run multiple search providers concurrently.
    - Merge and deduplicate the `DataFrame` results returned by all providers.
  - [x] 6.9 Add Proxy Support for Scrapers
    - Add an optional `proxies` field in `SearchConfig` to pass rotating proxies down to JobSpy and other search providers to avoid IP bans.
  - [x] 6.10 Add Keyword Exclusion Filtering
    - Add an `exclude_keywords` list in `SearchConfig`.
    - Update `_filter_jobs()` to drop any jobs containing those red-flag keywords (e.g. "US Citizen", "Clearance") in the description.
  - [x] 6.11 Implement Time-Bounded Incremental Search (Search Caching)
    - Write a `users/{username}/last_search.json` file with a timestamp after every successful search run.
    - On subsequent runs, calculate the hours since the last run and pass `hours_old=X` to JobSpy to only fetch newly posted jobs.

- [x] 7. Checkpoint — Ensure all tests pass so far
  - Run `uv run pytest tests/unit/ tests/property/test_slug_properties.py tests/property/test_filter_properties.py tests/property/test_prompt_properties.py tests/property/test_search_output_properties.py -v`
  - Ensure all tests pass; ask the user if questions arise.

- [x] 8. Implement incremental processor
  - [x] 8.1 Create incremental-processing functions in `src/pipeline.py` (or a dedicated `src/incremental.py` that `pipeline.py` imports)
    - `load_processed_ids(user_dir) -> set[str]`: read `processed_jobs.json`; create with empty list if missing; return set of IDs
    - `is_processed(job_id, processed_ids) -> bool`: return `job_id in processed_ids`
    - `mark_processed(job_id, user_dir) -> None`: append job ID to `processed_jobs.json` (read → append → write)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  - [x]* 8.2 Write property test P7 — incremental processor never reprocesses in `tests/property/test_incremental_properties.py`
    - **Property 7: Incremental processor never reprocesses a seen job**
    - Use `st.sets(st.text())` for processed IDs and `st.text()` for a known ID in the set; assert `is_processed` returns True and job is skipped
    - **Validates: Requirements 2.2, 2.3**
  - [x]* 8.3 Write unit test that `processed_jobs.json` is created with empty list when missing in `tests/unit/test_utils.py`
    - _Requirements: 2.5_

- [x] 9. Implement resume tailor, cover letter generator, and match analyzer
  - [x] 9.1 Create `src/tailor_resume.py` with `tailor_resume()`, `generate_cover_letter()`, and `analyze_match()`
    - `tailor_resume(job, config, user_dir, llm)`: load base resume and `job.md`; call `load_prompt("resume.md", ...)`; call `llm.complete()`; raise `ValidationError` if response `< 50 chars`; write `resume.md` to job output dir; return path
    - `generate_cover_letter(job, config, user_dir, llm)`: load tailored `resume.md` and `job.md`; call `load_prompt("cover_letter.md", ...)`; call `llm.complete()`; raise `ValidationError` if response `< 50 chars`; write `cover_letter.md`; return path
    - `analyze_match(job, config, user_dir, llm)`: load base resume and `job.md`; call `load_prompt("match_notes.md", ...)`; call `llm.complete()`; parse integer score, clamp to [0, 100] with warning log if outside; write `match_notes.md`; return `MatchResult`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  - [x]* 9.2 Write property test P6 — match score bounds in `tests/property/test_match_properties.py`
    - **Property 6: Match score is always within bounds**
    - Use `@given(st.text())` as raw LLM response; verify `MatchResult.score` is in `[0, 100]`
    - **Validates: Requirements 6.3, 6.5**
  - [x]* 9.3 Write property test P9 — LLM response length guard in `tests/property/test_llm_guard_properties.py`
    - **Property 9: LLM response length guard prevents empty file writes**
    - Use `@given(st.text(max_size=49))` as LLM response; assert `ValidationError` is raised and no file is written to output dir
    - **Validates: Requirements 4.5, 5.5**
  - [x]* 9.4 Write unit tests for `src/tailor_resume.py` in `tests/unit/test_tailor.py` and `tests/unit/test_match.py`
    - Test `tailor_resume` writes `resume.md` with valid content using a stub LLM
    - Test `generate_cover_letter` writes `cover_letter.md` with valid content
    - Test `analyze_match` returns `MatchResult` with score, strong matches, gaps, suggestions
    - Test `ValidationError` raised for responses `< 50 chars`
    - _Requirements: 4.4, 4.5, 5.4, 5.5, 6.3, 6.4, 6.5_
  - [x] 9.5 Enforce human-like tone in prompt templates
    - Update `prompts/resume.md` and `prompts/cover_letter.md` with strict anti-cliché constraints (e.g. forbid 'delve', 'testament to', 'innovative', 'dynamic').
    - Require tone to remain factual and strictly match the original base resume's voice.
  - [x] 9.6 Implement AI-cliché filter validation
    - Update `tailor_resume()` and `generate_cover_letter()` to check the LLM response against a blacklist of common AI buzzwords.
    - Raise `ValidationError` if the AI buzzword density is too high, preventing ATS bots from flagging the resume.
  - [x]* 9.7 Write unit test for AI-cliché filter in `tests/unit/test_tailor.py`
    - Test that `ValidationError` is raised when the LLM response contains too many blacklisted AI clichés.

- [x] 10. Implement PDF renderer
  - [x] 10.1 Create `src/render_pdf.py` with `render_resume_pdf()`, `render_cover_letter_pdf()`, and `_md_to_rendercv_yaml()`
    - `_md_to_rendercv_yaml(md_content, personal_info)`: parse structured markdown resume sections (name, experience, education, skills); return dict with top-level keys `cv` (containing `name`, `email`, `sections`) and `design` (containing `theme`)
    - `render_resume_pdf(job, output_dir, theme)`: verify `resume.md` exists (raise `RenderError` if not); call `_md_to_rendercv_yaml()`; write `resume.yaml`; invoke `rendercv render resume.yaml` via `subprocess`; verify output PDF exists; raise `RenderError` if not; return PDF path
    - `render_cover_letter_pdf(job, output_dir)`: verify `cover_letter.md` exists (raise `RenderError` if not); convert markdown → HTML via `markdown` library; convert HTML → PDF via WeasyPrint; verify PDF written; return PDF path
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8_
  - [x]* 10.2 Write property test P12 — resume markdown to RenderCV YAML structure in `tests/property/test_render_properties.py`
    - **Property 12: Resume markdown to RenderCV YAML preserves required structure**
    - Use `@given(st.text())` as resume markdown; assert returned dict has top-level keys `cv` and `design`, and `cv` has `sections` with at least one entry
    - **Validates: Requirements 7.3**
  - [x]* 10.3 Write unit tests for `src/render_pdf.py` in `tests/unit/test_render.py`
    - Test `_md_to_rendercv_yaml` produces expected top-level keys for a sample resume markdown
    - Test `RenderError` raised when source markdown file is missing
    - Test `RenderError` raised when RenderCV exits non-zero
    - _Requirements: 7.3, 7.6, 7.7_

- [x] 11. Implement application tracker
  - [x] 11.1 Create `src/tracker.py` with `update_tracker()`
    - `update_tracker(job, match, output_dir)`: read existing `tracker.md` and `tracker.csv` if present; find row by (company, title) key; update in place or append new row with columns: Company, Title, Location, Match Score, Salary, Link, Resume, Status; new entries have `Status = "- [ ]"`; write both files atomically (write to temp file, then rename)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  - [x]* 11.2 Write property test P10 — tracker upsert uniqueness in `tests/property/test_tracker_properties.py`
    - **Property 10: Tracker upsert preserves uniqueness by (company, title)**
    - Use `st.lists(job_strategy())` and call `update_tracker()` multiple times; assert exactly one row per (company, title) pair in both `tracker.md` and `tracker.csv`; assert new entries have `Status = "- [ ]"`
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
  - [x]* 11.3 Write unit tests for `src/tracker.py` in `tests/unit/test_tracker.py`
    - Test that tracker reads and re-writes existing entries correctly (update path)
    - Test that new entries are appended with correct columns and unchecked status
    - Test that both `.md` and `.csv` are written with the correct format
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 12. Checkpoint — Ensure all unit and property tests pass
  - Run `uv run pytest tests/unit/ tests/property/ -v`
  - Ensure all tests pass; ask the user if questions arise.

- [x] 13. Implement pipeline orchestration
  - [x] 13.1 Create `src/pipeline.py` with `run_search()`, `run_tailor()`, and `run_all()`
    - `run_search(config, user_dir)`: call `search_jobs()`; log count of accepted jobs; write nothing else
    - `run_tailor(config, user_dir, force)`: load processed IDs; iterate over job JSON files in `output/`; skip if ID in processed IDs and `force=False` (log skip); for each unprocessed job wrap in `try/except`; call `tailor_resume()`, `generate_cover_letter()`, `analyze_match()`, `render_resume_pdf()`, `render_cover_letter_pdf()`, `update_tracker()`, `write_metadata_json()`, `mark_processed()`; log error and `continue` on any exception
    - `run_all(config, user_dir, force)`: call `run_search()` then `run_tailor()`
    - `write_metadata_json(job, match, config, output_dir)`: write `metadata.json` with fields `job_slug`, `processed_at` (ISO 8601), `provider`, `model`, `match_score`
    - _Requirements: 2.2, 2.3, 10.3, 10.4, 10.5, 13.3, 13.4, 13.5, 13.8_
  - [x]* 13.2 Write property test P13 — metadata JSON fields in `tests/property/test_metadata_properties.py`
    - **Property 13: Metadata JSON contains all required fields after processing**
    - Use `job_strategy()` plus run context (provider, model, score); call `write_metadata_json()`; assert result JSON has exactly `job_slug`, `processed_at`, `provider`, `model`, `match_score`; assert `processed_at` matches ISO 8601 pattern
    - **Validates: Requirements 10.4**
  - [x] 13.3 Track LLM Token Usage and Estimated Cost
    - Update `LLMProvider.complete()` to return both text and token usage statistics.
    - Update `write_metadata_json()` to log the usage and estimated cost per job.
    - Add a `--dry-run` flag to the CLI (`main.py`) to estimate tokens without executing actual API calls.

- [x] 14. Implement CLI entry point
  - [x] 14.1 Create `main.py` with `argparse` CLI wiring
    - Parse `--user` (required), `--config` (optional, default `users/{username}/config.yaml`), `--force` (flag)
    - Subcommands: `search`, `tailor`, `all`
    - Raise `UserError` (exit with message) if `--user` omitted
    - Call `scaffold_user_dir()` on first run; raise `UserError` if `config.yaml` missing
    - Call `load_config()` → `get_provider()` → delegate to appropriate `run_*` function
    - Catch `ConfigError` and `UserError` at top level: print message and exit with code 1
    - _Requirements: 13.1, 13.2, 13.6, 13.7, 14.1, 14.2, 14.3, 14.7_
  - [x]* 14.2 Write unit tests for `main.py` CLI wiring in `tests/unit/test_config.py`
    - Test `--user` omitted → exits with descriptive message
    - Test missing `config.yaml` → exits with descriptive message naming expected path
    - Test `--force` flag is passed through correctly
    - _Requirements: 13.2, 14.3, 14.7_

- [x] 15. Write integration tests
  - [x] 15.1 Create `tests/integration/test_search_pipeline.py`
    - Full `search` command with a mocked `scrape_jobs()` returning a fixture DataFrame
    - Verify job files (`job.md`, `job.json`) are written to the correct `output/{slug}/` paths
    - Verify filter rules are applied (duplicate and short-description entries excluded)
    - _Requirements: 1.1, 1.2, 1.3, 1.6, 1.7_
  - [x] 15.2 Create `tests/integration/test_tailor_pipeline.py`
    - Full `tailor` command with a stub LLM that returns fixture markdown
    - Verify all expected output files written: `resume.md`, `resume.pdf`, `cover_letter.md`, `cover_letter.pdf`, `match_notes.md`, `metadata.json`
    - Verify tracker updated with correct row
    - Verify `--force` flag causes already-processed jobs to be reprocessed
    - _Requirements: 2.4, 4.4, 5.4, 6.4, 7.1, 7.2, 8.1, 10.3, 10.5, 13.7_
  - [x] 15.3 Create `tests/integration/test_pluggable_templates.py`
    - Verify that placing a mock LaTeX theme in `users/{username}/templates/` allows RenderCV to load it without error.
    - Verify that placing a mock `resume.md` in `users/{username}/prompts/` overrides the default `prompts/resume.md` file correctly.

- [x] 16. Support Pluggable Community Templates and Add-ons
  - [x] 16.1 Custom RenderCV Themes: Ensure the architecture supports loading custom RenderCV theme folders from a `users/{username}/templates/` directory so users can install third-party PDF themes.
  - [x] 16.2 Custom Prompt Packs: Ensure `load_prompt()` supports reading prompt overrides from a `users/{username}/prompts/` directory to allow users to drop in community "Prompt Packs".

- [x] 17. Final checkpoint — Ensure all tests pass
  - Run `uv run pytest tests/ -v`
  - Ensure all unit, property, and integration tests pass; ask the user if questions arise.

## Phase 2: Local Web UI (Streamlit)

- [ ] 17. Implement Streamlit Dashboard
  - [ ] 17.1 Configuration Editor: UI to visually edit `SearchConfig` (keywords, location, proxy settings) instead of editing `config.yaml` manually.
  - [ ] 17.2 Prompt & Base Resume Editor: Text area components to edit the base resume and prompt templates on the fly.
  - [ ] 17.3 Job Review & Match Analysis: Display `tracker.csv` and new jobs in a Kanban board. Show the LLM Match Score alongside the job description.
  - [ ] 17.4 PDF Previewer: Embed the generated output `resume.pdf` and `cover_letter.pdf` in the browser so users can verify it before applying.

## Phase 3: Model Context Protocol (MCP) Integration

- [ ] 18. Expose Pipeline as an MCP Server
  - [ ] 18.1 Create `src/mcp_server.py`: Use the `mcp` Python SDK to expose our job search and resume tailoring functions as tools.
  - [ ] 18.2 Expose `search_jobs` tool: Allow external AI agents (like Claude Desktop) to trigger a job search and read the results.
  - [ ] 18.3 Expose `tailor_resume` tool: Allow external AI agents to trigger the pipeline for a specific job slug.
- [ ] 19. Support MCP Clients for Base Resumes
  - [ ] 19.1 Update config to optionally read the base resume from an external MCP server (e.g., pulling directly from the user's local Obsidian vault or Notion workspace instead of a static `resume.md` file).

## Phase 4: Packaging & Distribution

- [ ] 20. Create Standalone Executables
  - [ ] 20.1 Package CLI with PyInstaller: Bundle the Python environment and CLI into a single `.exe` (Windows) and binary (macOS/Linux) so users don't need Python installed.
  - [ ] 20.2 Package Web UI: Wrap the Streamlit UI into a desktop executable (using PyInstaller or PyWebView) so non-technical users can just double-click an icon to launch the dashboard.
  - [ ] 20.3 Automated Build Pipeline: Set up GitHub Actions to automatically build and release the executables on every new version.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP development
- Each task references specific requirements for traceability
- Property tests use the Hypothesis `@given` decorator and validate universal properties; run with `uv run pytest tests/property/ -v`
- The `job_strategy()` Hypothesis strategy (a composite strategy returning `Job` instances) should be defined in `tests/conftest.py` and shared across all property test files
- Per-job error isolation (Requirement 13.8) is enforced in `run_tailor()` via `try/except` wrapping each job; startup errors (`ConfigError`, `UserError`) are fatal and exit before any processing begins
- Atomic file writes (write to temp → rename) are required for `tracker.md` and `tracker.csv` to avoid partial writes under concurrent use
- All paths must be resolved relative to `users/{username}/` — no hardcoded absolute paths in any `src/` module

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["2.1", "2.2"] },
    { "id": 1, "tasks": ["3.1", "4.1"] },
    { "id": 2, "tasks": ["3.2", "4.2", "4.3", "4.4", "4.5", "5.1"] },
    { "id": 3, "tasks": ["5.2", "5.3", "5.4", "5.5", "6.1"] },
    { "id": 4, "tasks": ["5.6", "6.2", "6.3", "6.4", "6.5", "6.6", "8.1"] },
    { "id": 5, "tasks": ["8.2", "8.3", "9.1"] },
    { "id": 6, "tasks": ["9.2", "9.3", "9.4", "10.1"] },
    { "id": 7, "tasks": ["10.2", "10.3", "11.1"] },
    { "id": 8, "tasks": ["11.2", "11.3", "13.1"] },
    { "id": 9, "tasks": ["13.2", "14.1"] },
    { "id": 10, "tasks": ["14.2", "15.1", "15.2"] }
  ]
}
```
