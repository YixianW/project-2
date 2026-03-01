from flask import Blueprint, jsonify, render_template, request
import logging

from app.services.ai_matcher import get_ai_matcher
from app.services.job_service import search_jobs_strict_title
from app.services.skill_engine import aggregate_skill_gaps

logger = logging.getLogger(__name__)
api = Blueprint("api", __name__)


@api.get("/")
def index():
    return render_template("index.html")


@api.post("/api/analyze")
def analyze_jobs():
    """
    Analyze job fit using AI-powered matching with direct file analysis.
    
    Workflow:
    1. Strict job title search (filter by title, location, salary)
    2. Gemini AI reads the actual resume file (PDF/DOCX)
    3. Gemini AI reads each job description
    4. Gemini AI performs semantic skill matching
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
    if not resume_file or not resume_file.filename:
        return jsonify({"error": "Resume file is required"}), 400

    # Read resume file bytes
    resume_filename = resume_file.filename
    resume_bytes = resume_file.read()
    
    if not resume_bytes:
        return jsonify({"error": "Resume file is empty"}), 400

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

    # Step 2: AI-powered skill matching using direct file analysis
    try:
        matcher = get_ai_matcher()
    except ValueError as e:
        logger.error(f"API Configuration Error: {e}")
        return jsonify({
            "error": str(e),
            "hint": "Make sure GEMINI_API_KEY is set in your environment"
        }), 500
    except Exception as e:
        logger.error(f"Failed to initialize Gemini: {e}", exc_info=True)
        return jsonify({
            "error": f"Gemini initialization failed: {str(e)}"
        }), 500
    
    analyses = []
    
    for job in jobs:
        try:
            logger.info(f"Analyzing job: {job.get('title')}")
            # Gemini AI reads the actual resume file and matches against JD
            fit = matcher.match_skills_with_file(
                resume_filename=resume_filename,
                resume_bytes=resume_bytes,
                job_description=job.get("description", ""),
            )

            analyses.append(
                {
                    "job": job,
                    "fit_score": fit.confidence_score,
                    "matched_strengths": fit.matched_skills[:8],
                    "missing_skills": fit.missing_skills[:10],
                    "explanation": fit.explanation,
                    "ai_powered": True,
                }
            )
        except Exception as e:
            # Log error but continue with other jobs
            logger.error(f"Error analyzing job {job.get('id')}: {e}", exc_info=True)
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
