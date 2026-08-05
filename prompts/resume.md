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