# Prompt Log

## AI tools/models used
- OpenAI Codex-style coding assistant (GPT-5.2-Codex)

## Significant prompts and development process
1. **Project framing prompt:** Build a fresh Project 2 web app with strict title-only filtering, resume-aware analysis, skill gaps, sponsorship classification, saved jobs, and polished UX.
2. **Architecture prompt:** First design architecture, folder structure, pipeline, taxonomy policy, scoring logic, and assignment compliance mapping.
3. **Implementation prompt:** Then implement modular Flask backend and modern frontend step-by-step with deterministic explainable logic.
4. **Quality prompt:** Ensure robust error handling, secure env-var secret handling, README + prompt_log documentation, and test coverage.

## Development timeline summary
1. Created Flask app scaffold with modular `services` for text processing, skills, jobs, resume parsing, and sponsorship logic.
2. Implemented strict title-based search with normalized case-insensitive matching and optional salary/location filters.
3. Implemented canonical taxonomy + tiered vocabulary extraction and deterministic fit scoring with missing-skill penalties.
4. Built sponsorship/work authorization conservative classifier.
5. Built frontend workflow for search/upload/analyze results, visualization chart, and saved jobs with localStorage.
6. Added documentation and tests.

## What was substantially written or modified by me
- Core skill extraction and scoring logic (`app/services/skill_engine.py`)
- Sponsorship classification rules (`app/services/sponsorship.py`)
- Frontend rendering/state/UX flow (`static/js/app.js` + `templates/index.html` + CSS)
- Project docs and architecture rationale (`README.md`)

## Learning outcomes
- Designed explainable and interview-friendly NLP-lite pipeline without black-box ML.
- Balanced product usability with project scope constraints.
- Practiced robust API error handling and modular full-stack architecture.
