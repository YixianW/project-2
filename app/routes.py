from flask import Blueprint, jsonify, render_template, request

from app.services.job_service import search_jobs_strict_title
from app.services.resume_parser import extract_resume_text
from app.services.skill_engine import (
    aggregate_skill_gaps,
    detect_weak_signals,
    extract_canonical_skills,
    ignored_term_hits,
    score_fit,
)
from app.services.sponsorship import classify_sponsorship

api = Blueprint("api", __name__)


@api.get("/")
def index():
    return render_template("index.html")


@api.post("/api/analyze")
def analyze_jobs():
    role_query = request.form.get("role", "").strip()
    location = request.form.get("location", "").strip() or None
    min_salary = request.form.get("minSalary", "").strip()

    if not role_query:
        return jsonify({"error": "Role title is required for strict title filtering."}), 400

    try:
        salary_filter = int(min_salary) if min_salary else None
    except ValueError:
        return jsonify({"error": "Minimum salary must be a valid integer."}), 400

    resume_file = request.files.get("resume")
    resume_text = ""
    if resume_file and resume_file.filename:
        try:
            resume_text = extract_resume_text(resume_file.filename, resume_file.read())
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": f"Resume parsing failed: {exc}"}), 400

    jobs = search_jobs_strict_title(role_query, location, salary_filter)
    if not jobs:
        return jsonify({"jobs": [], "skill_gap_summary": [], "message": "No title-matching jobs found."})

    resume_skills = extract_canonical_skills(resume_text)
    weak_resume_signals = detect_weak_signals(resume_text)

    analyses = []
    for job in jobs:
        jd_skills = extract_canonical_skills(job.get("description", ""))
        fit = score_fit(resume_skills, jd_skills)
        analyses.append(
            {
                "job": job,
                "fit_score": fit["score"],
                "matched_strengths": fit["matched_strengths"],
                "missing_skills": fit["missing_skills"],
                "jd_skills": sorted(jd_skills.keys()),
                "resume_skills": sorted(resume_skills.keys()),
                "weak_resume_signals": weak_resume_signals,
                "ignored_jd_terms": ignored_term_hits(job.get("description", "")),
                "sponsorship_classification": classify_sponsorship(job.get("description", "")),
                "explanation": fit["explanation"],
            }
        )

    analyses.sort(key=lambda a: a["fit_score"], reverse=True)
    return jsonify({"jobs": analyses, "skill_gap_summary": aggregate_skill_gaps(analyses)})
