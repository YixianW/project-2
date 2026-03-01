from flask import Blueprint, jsonify, render_template, request

from app.services.job_service import search_jobs_strict_title
from app.services.resume_parser import extract_resume_text
from app.services.skill_engine import (
    aggregate_skill_gaps,
    score_fit_with_ai,
)
from app.services.sponsorship import classify_sponsorship

api = Blueprint("api", __name__)


@api.get("/")
def index():
    return render_template("index.html")


@api.post("/api/analyze")
def analyze_jobs():
    """
    Analyze job fit using AI-powered matching.
    
    Skill matching is now powered by Gemini AI for semantic understanding.
    Job title search remains strict (hardline requirement).
    """
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

    if not resume_text:
        return jsonify({"error": "Resume could not be parsed or is empty."}), 400

    # Step 1: Strict job title matching (hardline requirement)
    jobs = search_jobs_strict_title(role_query, location, salary_filter)
    if not jobs:
        return jsonify(
            {
                "jobs": [],
                "skill_gap_summary": [],
                "message": f"No jobs found matching title '{role_query}'.",
            }
        )

    # Step 2: AI-powered skill matching for all jobs
    analyses = []
    for job in jobs:
        try:
            # Use Gemini AI for intelligent skill matching
            fit = score_fit_with_ai(resume_text, job.get("description", ""), use_ai=True)

            analyses.append(
                {
                    "job": job,
                    "fit_score": fit["score"],
                    "matched_strengths": fit["matched_strengths"],
                    "missing_skills": fit["missing_skills"],
                    "explanation": fit["explanation"],
                    "ai_powered": True,
                }
            )
        except Exception as e:
            # Log error but continue with other jobs
            print(f"Error analyzing job {job.get('id')}: {e}")
            analyses.append(
                {
                    "job": job,
                    "fit_score": 0,
                    "matched_strengths": [],
                    "missing_skills": [],
                    "explanation": f"Analysis failed: {str(e)}",
                    "ai_powered": False,
                }
            )

    # Sort by fit score (highest first)
    analyses.sort(key=lambda a: a["fit_score"], reverse=True)

    return jsonify({"jobs": analyses, "skill_gap_summary": aggregate_skill_gaps(analyses)})
