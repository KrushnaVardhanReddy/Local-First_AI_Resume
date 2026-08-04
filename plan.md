1. **13.1 Create `src/pipeline.py`**
   - Create `src/pipeline.py` with functions: `run_search(config, user_dir)`, `run_tailor(config, user_dir, force)`, `run_all(config, user_dir, force)` and `write_metadata_json(job, match, config, output_dir)`.
   - `run_search` will call `search_jobs()` from `src/search_jobs.py` and log the count of accepted jobs.
   - `run_tailor` will iterate through processed jobs based on `users/<username>/output/*/job.json`, skipping if already in `processed_jobs.json` unless `force` is `True`. Wrap processing in `try/except` to prevent single job failure from crashing the pipeline. Call `tailor_resume()`, `generate_cover_letter()`, `analyze_match()`, `render_resume_pdf()`, `render_cover_letter_pdf()`, `update_tracker()`, `write_metadata_json()`, `mark_processed()`.
   - `run_all` will execute `run_search` then `run_tailor`.
2. **13.2 Write property test P13**
   - Create `tests/property/test_metadata_properties.py` using `@given` from Hypothesis to test `write_metadata_json()` verifies `job_slug`, `processed_at`, `provider`, `model`, `match_score` fields in JSON result and ISO 8601 format.
3. **13.3 Track LLM Token Usage**
   - We need to modify `src/llm/base.py` and all LLM provider files to return both text and token usage (or a `LLMResponse` object). Wait, `tailor_resume` and `analyze_match` expect just text? Wait, I will return a tuple `(text, usage)`. Need to adjust `tailor_resume`, `generate_cover_letter`, `analyze_match` to unpack or handle this.
   - `usage` object can be `{"prompt_tokens": int, "completion_tokens": int, "total_tokens": int, "cost": float}`.
   - Update `write_metadata_json` to include token usage and cost.
   - Wait, `tailor_resume` currently just expects `llm.complete(prompt) -> str`. I should update `LLMProvider.complete` to return a `LLMResponse` object containing `.text` and `.usage`.
   - Update all providers (`openai`, `anthropic`, `lmstudio`, `ollama`).
   - Add `--dry-run` flag handling to CLI and pipeline to estimate tokens instead of executing API calls. Wait, estimating tokens without API call could mean just using `tiktoken` or a simple length-based heuristic if `tiktoken` is not available, or just returning mock responses. The prompt says "estimate tokens without executing actual API calls."
4. **14.1 Create `main.py` CLI**
   - Create `main.py` using `argparse`. Parse `--user`, `--config`, `--force`, `--dry-run`. Subcommands: `search`, `tailor`, `all`.
   - Check if `--user` is omitted.
   - Call `scaffold_user_dir()` from `src.utils`? Let me check if it exists.
   - Load config, handle errors.
5. **14.2 Write unit tests for `main.py`**
   - Create `tests/unit/test_config.py` to test CLI error handling.
6. **Execute Tests**
   - Run unit and property tests.
7. **Complete pre commit steps**
   - Run `pre_commit_instructions` and follow them to complete verification.
8. **Finalize**
   - Mark as completed in `tasks.md`.
