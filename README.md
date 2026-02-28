# Job Fit Navigator (Project 2)

## Project overview
Job Fit Navigator is a portfolio-ready web app for job seekers built around a clear product idea: **strict title-based job search + resume-aware fit analysis + actionable skill-gap insights**.

This rebuild intentionally separates:
1. **Search inclusion logic** (strict job title filtering), and
2. **Analysis/ranking logic** (resume-to-JD canonical skill matching).

## Architecture proposal (implemented)
### Stack
- **Backend:** Flask + modular Python services
- **Frontend:** HTML/CSS/vanilla JS (single-page flow)
- **Data visualization:** Chart.js bar chart for skill gaps
- **Job data:** Adzuna API (with env vars), fallback mock dataset
- **Saved jobs:** localStorage (lightweight, upgradeable)

### Folder structure
```text
app/
  __init__.py
  routes.py
  data/
    mock_jobs.py
    skill_taxonomy.py
  services/
    job_service.py
    resume_parser.py
    skill_engine.py
    sponsorship.py
    text_processing.py
static/
  css/styles.css
  js/app.js
templates/index.html
run.py
requirements.txt
tests/test_services.py
README.md
prompt_log.md
```

### Data flow
1. User enters role title + optional filters + optional resume upload.
2. Frontend posts to `/api/analyze`.
3. Backend performs **strict title matching only** for inclusion.
4. Resume is parsed (PDF/DOCX), normalized, mapped to canonical skills.
5. Each title-matched JD is mapped to canonical skills.
6. Deterministic fit score + missing skills + sponsorship classification generated.
7. Frontend renders ranked cards + skill-gap chart + save-job actions.

## Matching pipeline
1. Text normalization/preprocessing
2. Canonical skill taxonomy mapping (shared structure for resume and JD)
3. Resume skill extraction
4. JD skill extraction
5. Scoring (weighted overlap + missing penalties)
6. Missing-skill output
7. Explanation generation for each job

## Canonical taxonomy + tiered vocabulary
- **Tier 1 exact-safe:** SQL, Python, Tableau, Salesforce, HubSpot, SEO, etc.
- **Tier 2 phrase-required:** product marketing, go-to-market, lifecycle marketing, stakeholder management, etc.
- **Tier 3 weak-support:** communication, leadership, collaboration (explanatory only)
- **Tier 4 ignored:** resume/JD filler terms (not scored)

## Sponsorship/work authorization classification
Conservative rule-based classifier using exactly these labels:
- `sponsorship_available`
- `no_sponsorship`
- `work_authorization_required`
- `unclear`

Pattern lists are separated for maintainability and transparency.

## Features
- Strict role-title job search (case-insensitive normalized title matching)
- Resume upload (PDF/DOCX)
- Explainable resume-to-JD fit scoring
- Salary + location filtering
- Skill-gap summary chart across top jobs
- Saved jobs in localStorage
- Sponsorship/work authorization classification
- Graceful error handling for invalid input, parsing failures, API failures, and empty results

## How to run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```
Open `http://localhost:5000`.

## Environment variables
- `ADZUNA_APP_ID`
- `ADZUNA_APP_KEY`

If not set, app uses a built-in mock dataset for demo/development.

## Deployment notes
- Deploy Flask app on Render/Railway/Fly.io.
- Set Adzuna secrets in deployment environment.
- Verify frontend serves from Flask and `/api/analyze` is reachable.

## Tradeoffs vs naive keyword extraction
- More conservative and explainable.
- Fewer false-positive matches from broad words like "strategy" or "marketing".
- Easier to explain in class/interviews than opaque black-box methods.
- Limitation: fixed taxonomy may miss very niche domain terms; can be expanded safely over time.

## Assignment compliance mapping
- Publicly deployable architecture with real frontend-backend communication.
- Third-party API integration with env-var secret handling.
- Substantial analytics via deterministic fit scoring + skill-gap charting.
- Includes robust error cases and user-friendly UI messaging.
- Modular components support multiple meaningful commits.
- Easy demo narrative: strict search -> upload resume -> explain fit -> show gaps -> save jobs.

## Best modules for you to personally write/modify
1. `app/services/skill_engine.py` (core matching + scoring logic)
2. `app/services/sponsorship.py` (conservative classification logic)
3. `static/js/app.js` (UI rendering + state management + chart wiring)

These are excellent for class explanation because they are deterministic and product-critical.

## Portfolio project blurb
**Job Fit Navigator** is a full-stack Flask web app that helps job seekers run strict title-based searches, upload resumes, and get explainable fit scores against job descriptions using a canonical skill taxonomy. It highlights matched strengths, recurring missing skills, and sponsorship constraints in a polished interface with interactive skill-gap visualization.

## Limitations and future improvements
- Add user accounts + persistent saved jobs.
- Add pagination and caching for large job result sets.
- Add confidence scores per extracted skill alias.
- Expand taxonomy with role families beyond marketing/product/analytics.
