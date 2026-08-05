## Task: Add JSON Resume dual-engine rendering support

The project currently uses RenderCV to render resumes from Markdown. We want to add a second rendering engine based on the JSON Resume standard (https://jsonresume.org), so users can choose between:
- `engine: rendercv` (current default — Typst-based PDF via `rendercv render`)
- `engine: jsonresume` (new — HTML/CSS themes via `resumed` CLI → PDF via Puppeteer/headless Chrome)

### 1. Update `src/config.py`

Add an `engine` field to the existing `PdfConfig` dataclass:

```python
@dataclass
class PdfConfig:
    theme: str = "modernblue"
    engine: str = "rendercv"   # NEW: "rendercv" or "jsonresume"
```

Also update the `load_config()` function to read `pdf.engine` from the YAML with a default of `"rendercv"`.

### 2. Update `prompts/resume.md`

Currently the prompt asks the LLM to produce Markdown. We need the prompt to produce a valid **JSON Resume** (https://jsonresume.org/schema) JSON object instead, so it can be used by both engines.

Replace the existing prompt body with the following:

```
You are an expert resume writer. Tailor the following base resume to the job description and output a valid JSON Resume object (https://jsonresume.org/schema).

Important Constraints:
1. Output ONLY a raw JSON object — no markdown fences, no explanation, just the JSON.
2. Maintain a factual, human-like tone. DO NOT use AI clichés like 'delve', 'synergy', 'leverage', or 'spearhead'.
3. For skills, group related items as a single keyword string separated by commas (e.g. "PostgreSQL, DynamoDB, Redis") rather than deeply nested lists.
4. The JSON must contain at minimum: basics, work, education, skills sections.

Base Resume:
{{base_resume}}

Job Description:
{{job_description}}
```

### 3. Update `src/tailor_resume.py`

In the `tailor_resume()` function:
- After getting `response_text` from the LLM, try to parse it as JSON using `json.loads()`.
- If it fails to parse, raise a `ValidationError("LLM did not return valid JSON")`.
- Save the output as `resume.json` (not `resume.md`) in the job output directory.
- Return the path to `resume.json`.

Also update the `generate_cover_letter()` function to read `resume.json` instead of `resume.md` when building the cover letter prompt variables. The cover letter prompt itself still outputs Markdown (not JSON).

### 4. Update `src/render_pdf.py`

Refactor `render_resume_pdf()` to dispatch based on `config.pdf.engine`:

#### For `engine == "jsonresume"`:
1. Read `resume.json` from `output_dir`.
2. Run: `npx -y resumed export --theme jsonresume-theme-class resume.json -o resume.html` in `output_dir`.
3. Run: `npx -y @puppeteer/browsers install chrome` if chrome is not available, then use a Node.js script or puppeteer CLI to convert `resume.html` to `resume.pdf`.
   - Simpler alternative: use `weasyprint` (already a dependency) to convert the rendered HTML to PDF via `HTML(filename="resume.html").write_pdf("resume.pdf")`.
4. Return the path to `resume.pdf`.

#### For `engine == "rendercv"` (existing behavior):
The existing `_md_to_rendercv_yaml()` logic must now read from `resume.json` instead of `resume.md`. Parse the JSON Resume object and map the fields as follows:
- `cv.name` ← `basics.name`
- `cv.email` ← `basics.email`
- `cv.sections["Summary"]` ← `[basics.summary]`
- `cv.sections["Skills"]` ← one entry per skill group: `"**{name}**: {keywords joined by ', '}"`
- `cv.sections["Experience"]` ← one entry per item in `work`, formatted as: `"**{company}**, {position}\n{summary}\n{highlights as bullet list}"`
- `cv.sections["Education"]` ← one entry per item in `education`
- `design.theme` ← `config.pdf.theme` (default: `"modernblue"`)

### 5. Update `Makefile`

Add a new `setup-node` target that installs the required npm packages globally:
```makefile
setup-node:
    npm install -g resumed jsonresume-theme-class
```

Also add `setup-node` as a dependency of the existing `install` target.

### 6. Update `config.yaml.example`

Add the new `engine` field to the `pdf` section example:
```yaml
pdf:
  theme: "modernblue"   # or "classic", "sleektech", etc.
  engine: "jsonresume"  # or "rendercv"
```

### Verification

After implementing, the code must be fully importable without errors. Do not break any existing functionality. The `rendercv` engine path must remain the default and continue to work exactly as before.
