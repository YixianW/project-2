import os

import requests

from app.data.mock_jobs import MOCK_JOBS
from app.services.text_processing import contains_phrase, normalize_text


def _fetch_adzuna_jobs(query: str, location: str | None = None) -> list[dict]:
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        return MOCK_JOBS

    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "results_per_page": 30,
        "content-type": "application/json",
    }
    if location:
        params["where"] = location

    response = requests.get(
        "https://api.adzuna.com/v1/api/jobs/us/search/1",
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    data = response.json().get("results", [])
    jobs = []
    for item in data:
        jobs.append(
            {
                "id": item.get("id") or item.get("redirect_url"),
                "title": item.get("title", ""),
                "company": (item.get("company") or {}).get("display_name", "Unknown"),
                "location": (item.get("location") or {}).get("display_name", "Unknown"),
                "salary_min": item.get("salary_min"),
                "salary_max": item.get("salary_max"),
                "description": item.get("description", ""),
                "redirect_url": item.get("redirect_url", ""),
            }
        )
    return jobs


def search_jobs_strict_title(query: str, location: str | None, min_salary: int | None) -> list[dict]:
    if not query.strip():
        return []

    jobs = _fetch_adzuna_jobs(query, location)
    query_norm = normalize_text(query)

    strict_title_matches = [
        job for job in jobs if contains_phrase(normalize_text(job.get("title", "")), query_norm)
    ]

    if location:
        loc_norm = normalize_text(location)
        strict_title_matches = [
            job for job in strict_title_matches if contains_phrase(normalize_text(job.get("location", "")), loc_norm)
        ]

    if min_salary:
        strict_title_matches = [
            job
            for job in strict_title_matches
            if (job.get("salary_max") or job.get("salary_min") or 0) >= min_salary
        ]

    strict_title_matches.sort(key=lambda j: (j.get("salary_max") or 0), reverse=True)
    return strict_title_matches
