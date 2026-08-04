# Requirements Document

## Introduction

The Job Pipeline is a local-first, privacy-first Python pipeline that helps job seekers find relevant jobs, tailor their existing resume and cover letter using local or cloud LLMs, generate PDFs from markdown output, and maintain a manual application tracker. The pipeline is provider-agnostic, markdown-first, and never fabricates resume content. All job applications remain fully manual — the system only prepares materials.

## Glossary

- **Pipeline**: The Job Pipeline system as a whole
- **User**: A named individual using the pipeline locally, identified by a directory name under `users/`
- **User_Dir**: The directory `users/{username}/` containing all data, config, and output specific to one user
- **Job_Searcher**: The component responsible for querying job sources and filtering results
- **Job_Filter**: The sub-component that applies user-defined criteria to raw job results
- **Resume_Tailor**: The component that rewrites a base resume to match a specific job description
- **Cover_Letter_Generator**: The component that generates a cover letter for a specific job
- **Match_Analyzer**: The component that produces a match score, strengths, gaps, and suggestions
- **LLM_Provider**: An abstraction layer over a language model backend (local or cloud)
- **PDF_Renderer**: The component that converts tailored resume and cover letter into PDF documents using RenderCV (for resumes) and WeasyPrint/Pandoc (for cover letters)
- **RenderCV_Theme**: A named visual template supported by RenderCV (`classic`, `moderncv`, `sb2nov`, `engineeringresumes`, `engineeringclassic`)
- **Tracker**: The component that maintains `tracker.md` and `tracker.csv` within a User_Dir
- **Incremental_Processor**: The component that reads and writes `processed_jobs.json` within a User_Dir to skip previously processed jobs
- **Config**: The `config.yaml` file inside a User_Dir that controls all pipeline behaviour for that user
- **Base_Resume**: A markdown file inside a User_Dir containing the user's original, unmodified resume
- **Resume_Profile**: A named markdown file in the `users/{username}/resumes/` directory representing a specific resume variant
- **Job_Slug**: A filesystem-safe string derived from company name and job title used as the output folder name
- **Output_Dir**: The `users/{username}/output/` directory that contains per-job folders and tracker files for that user
- **Processed_Jobs**: The `users/{username}/processed_jobs.json` file recording all job IDs previously processed by that user
- **Prompt_Template**: A markdown file in `prompts/` (global) or `users/{username}/prompts/` (user-level override) used to instruct the LLM for a specific task
- **Match_Score**: An integer from 0 to 100 representing how well the candidate's resume matches a job description

---

## Requirements

### Requirement 1: Job Search

**User Story:** As a job seeker, I want to search for jobs across multiple sources using configurable filters, so that I receive a curated list of relevant positions without manually browsing each job board.

#### Acceptance Criteria

1. WHEN the user runs a search, THE Job_Searcher SHALL query Indeed and LinkedIn via JobSpy using the keywords, location, and remote preference specified in Config.
2. WHEN raw job results are returned, THE Job_Filter SHALL remove duplicate jobs where two or more listings share the same company name and job title.
3. WHEN raw job results are returned, THE Job_Filter SHALL remove jobs whose description length is fewer than 100 characters.
4. WHEN a minimum salary is specified in Config, THE Job_Filter SHALL exclude jobs whose listed maximum salary is less than the configured minimum salary.
5. WHEN a company exclusion list is specified in Config, THE Job_Filter SHALL exclude jobs from any company whose name appears in that list.
6. WHEN job results are filtered, THE Job_Searcher SHALL save each accepted job as both `job.md` and `job.json` inside a Job_Slug subdirectory of Output_Dir.
7. WHEN a job is saved, THE Job_Searcher SHALL record the job title, company, location, salary range, and source URL in `job.json`.

---

### Requirement 2: Incremental Processing

**User Story:** As a job seeker running the pipeline repeatedly, I want already-processed jobs to be skipped automatically, so that I do not waste time or LLM tokens reprocessing jobs I have already seen.

#### Acceptance Criteria

1. WHEN the pipeline starts, THE Incremental_Processor SHALL read `users/{username}/processed_jobs.json` to load the set of previously processed job IDs for that user.
2. WHEN a job is selected for tailoring, THE Incremental_Processor SHALL check whether the job's ID exists in Processed_Jobs.
3. IF a job's ID exists in Processed_Jobs, THEN THE Incremental_Processor SHALL skip that job and log a message indicating it was already processed.
4. WHEN a job is successfully tailored and all output files are written, THE Incremental_Processor SHALL append the job's ID to `users/{username}/processed_jobs.json`.
5. IF `users/{username}/processed_jobs.json` does not exist, THEN THE Incremental_Processor SHALL create it with an empty list before writing any entries.

---

### Requirement 3: LLM Provider Abstraction

**User Story:** As a developer, I want to switch between local and cloud LLM providers using only config changes, so that I can use any supported model without modifying Python code.

#### Acceptance Criteria

1. THE LLM_Provider SHALL expose a single `complete(prompt: str) -> str` interface that all provider implementations satisfy.
2. WHEN `provider: lmstudio` is set in Config, THE LLM_Provider SHALL send requests to the LM Studio OpenAI-compatible API at the configured `base_url`.
3. WHEN `provider: ollama` is set in Config, THE LLM_Provider SHALL send requests to the Ollama REST API at the configured `base_url`.
4. WHEN `provider: anthropic` is set in Config, THE LLM_Provider SHALL send requests to the Anthropic Messages API using the API key from the environment variable `ANTHROPIC_API_KEY`.
5. WHEN `provider: openai` is set in Config, THE LLM_Provider SHALL send requests to the OpenAI Chat Completions API using the API key from the environment variable `OPENAI_API_KEY`.
6. IF the configured provider value does not match a supported provider name, THEN THE LLM_Provider SHALL raise a descriptive configuration error before making any API call.
7. WHEN an LLM API call fails with a network or HTTP error, THE LLM_Provider SHALL raise an exception containing the provider name, HTTP status code (if available), and original error message.

---

### Requirement 4: Resume Tailoring

**User Story:** As a job seeker, I want my base resume rewritten to highlight skills relevant to a specific job description, so that my application materials are targeted without my needing to edit them manually.

#### Acceptance Criteria

1. WHEN resume tailoring is triggered for a job, THE Resume_Tailor SHALL load the Base_Resume specified in Config and the job description from the job's `job.md` file.
2. WHEN constructing the LLM prompt, THE Resume_Tailor SHALL load and use the `prompts/resume.md` Prompt_Template.
3. THE Resume_Tailor SHALL instruct the LLM to reorder, rephrase, and emphasise existing experience only — never to add companies, job titles, dates, or projects that do not appear in the Base_Resume.
4. WHEN the LLM returns a tailored resume, THE Resume_Tailor SHALL write the output to `resume.md` inside the job's Job_Slug subdirectory of Output_Dir.
5. IF the LLM response is empty or contains fewer than 50 characters, THEN THE Resume_Tailor SHALL raise an error and not write a partial output file.
6. WHERE multiple Resume_Profiles are configured, THE Resume_Tailor SHALL use the profile whose filename matches the `base_resume` value in Config.

---

### Requirement 5: Cover Letter Generation

**User Story:** As a job seeker, I want a tailored cover letter generated for each job, so that I can submit a personalised letter without writing one from scratch.

#### Acceptance Criteria

1. WHEN cover letter generation is triggered for a job, THE Cover_Letter_Generator SHALL load the tailored `resume.md` and the job description from `job.md` for that job.
2. WHEN constructing the LLM prompt, THE Cover_Letter_Generator SHALL load and use the `prompts/cover_letter.md` Prompt_Template.
3. THE Cover_Letter_Generator SHALL instruct the LLM to reference only experience that appears in the tailored resume.
4. WHEN the LLM returns a cover letter, THE Cover_Letter_Generator SHALL write the output to `cover_letter.md` inside the job's Job_Slug subdirectory of Output_Dir.
5. IF the LLM response is empty or contains fewer than 50 characters, THEN THE Cover_Letter_Generator SHALL raise an error and not write a partial output file.

---

### Requirement 6: Match Analysis

**User Story:** As a job seeker, I want a match score and gap analysis for each job, so that I can prioritise which applications to pursue.

#### Acceptance Criteria

1. WHEN match analysis is triggered for a job, THE Match_Analyzer SHALL load the Base_Resume and the job description from `job.md`.
2. WHEN constructing the LLM prompt, THE Match_Analyzer SHALL load and use the `prompts/match_notes.md` Prompt_Template.
3. WHEN the LLM returns match analysis, THE Match_Analyzer SHALL parse and validate that the response contains a Match_Score integer between 0 and 100.
4. WHEN match analysis is complete, THE Match_Analyzer SHALL write the full analysis to `match_notes.md` inside the job's Job_Slug subdirectory of Output_Dir.
5. IF the parsed Match_Score is outside the range 0–100, THEN THE Match_Analyzer SHALL clamp the value to the nearest valid boundary (0 or 100) and log a warning.
6. THE Match_Analyzer SHALL record at least one strong match, one gap, and one suggestion in the analysis output when the LLM response contains those sections.

---

### Requirement 7: PDF Generation

**User Story:** As a job seeker, I want PDF versions of my tailored resume and cover letter, so that I can upload professional-looking documents to job applications.

#### Acceptance Criteria

1. WHEN PDF generation is triggered for a job, THE PDF_Renderer SHALL use RenderCV to convert the tailored resume YAML into `resume.pdf` inside the job's Job_Slug subdirectory.
2. WHEN PDF generation is triggered for a job, THE PDF_Renderer SHALL convert `cover_letter.md` to `cover_letter.pdf` inside the job's Job_Slug subdirectory using WeasyPrint or Pandoc.
3. WHEN converting a tailored resume for PDF rendering, THE PDF_Renderer SHALL transform the LLM-generated markdown output into a RenderCV-compatible YAML structure before invoking RenderCV.
4. THE PDF_Renderer SHALL invoke RenderCV via its CLI (`rendercv render`) using the theme specified in Config (default: `sb2nov`).
5. THE Config SHALL support a `pdf.theme` key accepting any valid RenderCV theme name (`classic`, `moderncv`, `sb2nov`, `engineeringresumes`, `engineeringclassic`), defaulting to `sb2nov`.
6. IF the source markdown file does not exist at the expected path, THEN THE PDF_Renderer SHALL raise an error with the missing file path before attempting conversion.
7. WHEN a PDF is generated, THE PDF_Renderer SHALL verify that the output PDF file exists at the expected path after RenderCV completes, and raise an error if it does not.
8. WHEN a PDF is generated, THE PDF_Renderer SHALL produce an ATS-readable PDF where the text layer is not rasterised and can be extracted by standard PDF parsers.

---

### Requirement 8: Application Tracker

**User Story:** As a job seeker, I want a tracker updated after each processed job, so that I have a consolidated view of all my applications and their statuses.

#### Acceptance Criteria

1. WHEN a job is fully processed, THE Tracker SHALL append or update a row for that job in both `users/{username}/output/tracker.md` and `users/{username}/output/tracker.csv`.
2. THE Tracker SHALL record the following columns for each job: Company, Title, Location, Match Score, Salary, Link, Resume (path to generated resume.pdf), Status.
3. WHEN a new entry is written, THE Tracker SHALL set the Status field to an unchecked markdown checkbox (`- [ ]`).
4. IF a job entry already exists in the tracker (matched by company name and job title), THEN THE Tracker SHALL update the existing row rather than appending a duplicate.
5. THE Tracker SHALL write `tracker.md` using a markdown table format and `tracker.csv` using comma-separated values with a header row.

---

### Requirement 9: Configuration System

**User Story:** As a developer, I want all pipeline behaviour controlled through `config.yaml`, so that I can change providers, models, filters, and paths without editing Python source files.

#### Acceptance Criteria

1. THE Config SHALL support the following top-level keys: `provider`, `model`, `base_url` (optional), `base_resume`, `output_dir`, `search`.
2. THE Config `search` key SHALL support the following sub-keys: `keywords`, `location`, `remote` (boolean), `results_wanted` (integer), `min_salary` (integer, optional), `exclude_companies` (list, optional).
3. WHEN the pipeline starts, THE Pipeline SHALL validate that `config.yaml` exists and that all required keys are present.
4. IF a required config key is missing, THEN THE Pipeline SHALL exit with a descriptive error message naming the missing key.
5. THE Pipeline SHALL load environment variables from `.env` if that file exists, before reading any API keys from the environment.

---

### Requirement 10: Output File Structure

**User Story:** As a job seeker, I want all generated files organised into per-job folders, so that I can find and manage application materials for each position easily.

#### Acceptance Criteria

1. WHEN a job is processed, THE Pipeline SHALL create a subdirectory under Output_Dir named using the Job_Slug derived from the company name and job title.
2. THE Job_Slug SHALL be constructed by lowercasing the company name and job title, replacing spaces and special characters with hyphens, and truncating the result to 80 characters.
3. WHEN all pipeline steps complete for a job, the job's subdirectory SHALL contain: `job.md`, `job.json`, `resume.md`, `resume.pdf`, `cover_letter.md`, `cover_letter.pdf`, `match_notes.md`, and `metadata.json`.
4. WHEN output files are written, THE Pipeline SHALL record the job slug, processing timestamp (ISO 8601), provider name, model name, and match score in `metadata.json`.
5. IF an output subdirectory already exists and all expected files are present, THEN THE Pipeline SHALL skip regeneration for that job unless a `--force` flag is passed.

---

### Requirement 11: Prompt Template System

**User Story:** As a developer or power user, I want to customise LLM prompts without changing Python code, so that I can tune model behaviour for my specific needs.

#### Acceptance Criteria

1. THE Pipeline SHALL load resume, cover letter, and match analysis prompts from `prompts/resume.md`, `prompts/cover_letter.md`, and `prompts/match_notes.md` respectively.
2. WHEN a Prompt_Template is loaded, THE Pipeline SHALL perform variable substitution, replacing `{{base_resume}}` with Base_Resume content and `{{job_description}}` with the job description.
3. IF a required prompt file is missing, THEN THE Pipeline SHALL raise an error naming the missing file before invoking the LLM.
4. THE Pipeline SHALL ship default prompt files that produce structurally valid resume, cover letter, and match notes output out of the box.

---

### Requirement 12: Multiple Resume Profiles

**User Story:** As a job seeker applying to different roles, I want to maintain multiple resume variants and select one per run, so that I can apply to backend, data, and AI roles with appropriately targeted resumes.

#### Acceptance Criteria

1. THE Pipeline SHALL support a `users/{username}/resumes/` directory containing multiple markdown resume files.
2. WHEN `base_resume` in Config is set to a filename inside `users/{username}/resumes/`, THE Resume_Tailor SHALL load that specific file as the Base_Resume for the run.
3. IF the file referenced by `base_resume` in Config does not exist under `users/{username}/resumes/`, THEN THE Pipeline SHALL exit with a descriptive error message naming the missing file and its expected path.
4. THE Pipeline SHALL treat each Resume_Profile as read-only; no pipeline step SHALL modify the source file in `users/{username}/resumes/`.

---

### Requirement 14: Multi-User Support

**User Story:** As a household or team sharing one machine, I want each person to have their own isolated workspace, so that my resumes, job searches, outputs, and tracker do not interfere with anyone else's.

#### Acceptance Criteria

1. THE Pipeline SHALL organise all user-specific data under `users/{username}/`, where `username` is a lowercase alphanumeric string supplied via the `--user` CLI flag.
2. WHEN the `--user` flag is provided, THE Pipeline SHALL resolve all paths — Config, Base_Resume, Output_Dir, Processed_Jobs, and Tracker — relative to `users/{username}/`.
3. IF the `--user` flag is omitted, THE Pipeline SHALL exit with a descriptive error message instructing the user to specify `--user`.
4. WHEN a username is provided for the first time, THE Pipeline SHALL create the `users/{username}/` directory and scaffold the expected subdirectories (`resumes/`, `output/`, `prompts/`) along with a default `config.yaml` and an empty `processed_jobs.json`.
5. THE Pipeline SHALL support a global `prompts/` directory at the project root as a fallback; WHEN a `users/{username}/prompts/` directory exists and contains a matching prompt file, THE Pipeline SHALL use the user-level file in preference to the global one.
6. WHEN two users run the pipeline concurrently on the same machine, each user's Output_Dir, Processed_Jobs, and Tracker SHALL remain independent with no shared mutable state between them.
7. IF the `users/{username}/config.yaml` file does not exist, THEN THE Pipeline SHALL exit with a descriptive error message naming the missing file and the expected path.
8. THE `users/` directory SHALL be listed in `.gitignore` so that no user's personal resume data, job output, or API keys are accidentally committed to version control.

---

### Requirement 13: CLI Entry Point

**User Story:** As a developer, I want a single `main.py` entry point with clear command-line arguments, so that I can run individual pipeline stages or the full pipeline from the terminal.

#### Acceptance Criteria

1. THE Pipeline SHALL expose a `main.py` CLI that accepts the following commands: `search`, `tailor`, `all`.
2. THE Pipeline SHALL require a `--user {username}` flag on every command, resolving all paths under `users/{username}/`.
3. WHEN the `search` command is run, THE Pipeline SHALL execute only the Job_Searcher and Job_Filter steps.
4. WHEN the `tailor` command is run, THE Pipeline SHALL execute Resume_Tailor, Cover_Letter_Generator, Match_Analyzer, PDF_Renderer, and Tracker steps for all unprocessed jobs belonging to that user.
5. WHEN the `all` command is run, THE Pipeline SHALL execute all steps sequentially: search, then tailor.
6. THE Pipeline SHALL accept a `--config` flag to specify an alternative config file path, defaulting to `users/{username}/config.yaml`.
7. THE Pipeline SHALL accept a `--force` flag that bypasses Incremental_Processor checks and reprocesses all jobs for that user.
8. WHEN any pipeline step raises an unhandled exception, THE Pipeline SHALL log the error with the username and job slug and continue processing remaining jobs rather than exiting.
