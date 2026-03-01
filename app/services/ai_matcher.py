import json
import logging
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

import google.generativeai as genai

from app.data.skill_taxonomy import SKILL_TAXONOMY

logger = logging.getLogger(__name__)


@dataclass
class AIMatchResult:
    matched_skills: list[str]
    missing_skills: list[str]
    confidence_score: int
    explanation: str
    raw_response: str = ""


class GeminiMatcher:
    """AI-powered skill matcher using Google Gemini API."""

    def __init__(self, api_key: str = None):
        """Initialize Gemini matcher with API key from env or parameter."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable not set. "
                "Please set it in .env (local) or in Render environment variables (production). "
                "Get a free key from https://ai.google.dev/"
            )
        logger.info("✓ GEMINI_API_KEY found, initializing Gemini API")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-pro")
        self.vision_model = genai.GenerativeModel("gemini-1.5-pro")  # For file analysis
        logger.info("✓ Gemini models initialized successfully")

    def _save_temp_file(self, filename: str, file_bytes: bytes) -> str:
        """Save uploaded file to temp location for Gemini to read."""
        temp_dir = tempfile.gettempdir()
        temp_path = Path(temp_dir) / filename
        temp_path.write_bytes(file_bytes)
        return str(temp_path)

    def match_skills_with_file(
        self,
        resume_filename: str,
        resume_bytes: bytes,
        job_description: str,
    ) -> AIMatchResult:
        """
        Use Gemini AI to match skills by reading the actual resume file.
        
        Args:
            resume_filename: Original filename (e.g., "resume.pdf")
            resume_bytes: File contents as bytes
            job_description: Job description text (or JD file path)
        
        Returns:
            AIMatchResult with matched skills, missing skills, and confidence score
        """
        logger.info(f"Starting AI matching for {resume_filename}")
        
        if not resume_bytes or not job_description:
            logger.warning("Empty resume or job description provided")
            return AIMatchResult(
                matched_skills=[],
                missing_skills=[],
                confidence_score=0,
                explanation="Empty resume or job description",
            )

        try:
            # Save temp file for Gemini to process
            temp_path = self._save_temp_file(resume_filename, resume_bytes)
            logger.info(f"Saved temp resume file to: {temp_path}")

            # Upload file to Gemini
            logger.info(f"Uploading resume file to Gemini: {resume_filename}")
            uploaded_file = genai.upload_file(temp_path)
            logger.info(f"✓ File uploaded successfully. File ID: {uploaded_file.name}")

            # Create prompt with file reference
            prompt = f"""You are an expert recruiter and skill matcher. Your job is to evaluate how well a candidate's resume matches a job description.

I'm uploading the candidate's resume file directly. Please read and understand the entire resume, including:
- Work experience and achievements
- Skills and technical abilities
- Education and certifications
- Any projects or volunteer work
- Soft skills and competencies

Then match it against the job requirements below.

IMPORTANT: Focus on SEMANTIC matching, not just exact keyword matches. 
- Understand that different terms mean the same thing (e.g., "go-to-market strategy", "product launch", "market entry")
- Recognize related skills even if worded differently
- Consider context and implied skills from job titles and descriptions
- Be generous with matching for relevant skills and experience
- Look at the spirit of what the candidate can do, not just literal matches

JOB DESCRIPTION:
{job_description[:3000]}

Task:
1. Extract the KEY SKILLS and EXPERIENCE from the RESUME FILE (both technical and soft skills, responsibility areas)
2. Extract the KEY SKILLS REQUIRED by the JOB DESCRIPTION
3. Match resume skills to job requirements using SEMANTIC understanding
   - Exact matches count
   - Closely related skills count (e.g., "marketing" matches job asking for "campaign management")
   - Similar experience areas count (e.g., "product launches" matches "go-to-market strategy")
4. Identify job skills that are MISSING from resume
5. Provide confidence score (0-100) - be realistic:
   - 80-100: Strong match, candidate well-prepared
   - 60-79: Good match, candidate can learn on the job
   - 40-59: Partial match, candidate would need some growth
   - 0-39: Weak match, significant gaps

Return ONLY a valid JSON object (no markdown, no code blocks):
{{
    "matched_skills": ["skill1", "skill2"],
    "missing_skills": ["skill3", "skill4"],
    "confidence_score": 75,
    "explanation": "Brief explanation of the match (1-2 sentences)"
}}"""

            # Call Gemini with file reference
            logger.info("Calling Gemini API for skill matching...")
            response = self.vision_model.generate_content(
                [prompt, uploaded_file]
            )
            logger.info("✓ Gemini API response received")
            
            response_text = response.text.strip()
            logger.debug(f"Raw response: {response_text[:200]}...")

            # Clean up: delete uploaded file
            genai.delete_file(uploaded_file.name)
            logger.info("✓ File deleted from Gemini")

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            response_text = response_text.strip()

            result_dict = json.loads(response_text)
            logger.info(f"✓ Skill matching completed. Score: {result_dict.get('confidence_score', 0)}")

            return AIMatchResult(
                matched_skills=result_dict.get("matched_skills", []),
                missing_skills=result_dict.get("missing_skills", []),
                confidence_score=int(result_dict.get("confidence_score", 0)),
                explanation=result_dict.get("explanation", ""),
                raw_response=response_text,
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return AIMatchResult(
                matched_skills=[],
                missing_skills=[],
                confidence_score=0,
                explanation=f"Failed to parse AI response: {str(e)}",
                raw_response=response_text if 'response_text' in locals() else "",
            )
        except Exception as e:
            logger.error(f"AI matching error: {e}", exc_info=True)
            return AIMatchResult(
                matched_skills=[],
                missing_skills=[],
                confidence_score=0,
                explanation=f"AI matching failed: {str(e)}",
            )
        finally:
            # Clean up temp file
            try:
                if 'temp_path' in locals():
                    Path(temp_path).unlink(missing_ok=True)
                    logger.info("Temp file cleaned up")
            except Exception:
                pass

    def get_skill_taxonomy_str(self) -> str:
        """Get formatted skill taxonomy for context (kept for backward compatibility)."""
        taxonomy_lines = []
        for cluster_block in SKILL_TAXONOMY:
            cluster = cluster_block["cluster"]
            for skill in cluster_block["skills"]:
                aliases = ", ".join(skill["aliases"])
                taxonomy_lines.append(f"- {skill['label']}: {aliases}")
        return "\n".join(taxonomy_lines)

    def match_skills(
        self,
        resume_text: str,
        job_description: str,
    ) -> AIMatchResult:
        """
        Use Gemini AI to match skills between resume and job description.
        
        Args:
            resume_text: Extracted resume text
            job_description: Job description text
        
        Returns:
            AIMatchResult with matched skills, missing skills, and confidence score
        """
        if not resume_text or not job_description:
            return AIMatchResult(
                matched_skills=[],
                missing_skills=[],
                confidence_score=0,
                explanation="Empty resume or job description",
            )

        prompt = f"""You are an expert recruiter and skill matcher. Your job is to evaluate how well a candidate's resume matches a job description.

IMPORTANT: Focus on SEMANTIC matching, not just exact keyword matches. 
- Understand that different terms mean the same thing (e.g., "go-to-market strategy", "product launch", "market entry")
- Recognize related skills even if worded differently
- Consider context and implied skills from job titles and descriptions
- Be generous with matching for relevant skills and experience

RESUME:
{resume_text[:3000]}

JOB DESCRIPTION:
{job_description[:3000]}

Task:
1. Extract the KEY SKILLS and EXPERIENCE from the RESUME (both technical and soft skills, responsibility areas)
2. Extract the KEY SKILLS REQUIRED by the JOB DESCRIPTION
3. Match resume skills to job requirements using SEMANTIC understanding
   - Exact matches count
   - Closely related skills count (e.g., "marketing" matches job asking for "campaign management")
   - Similar experience areas count (e.g., "product launches" matches "go-to-market strategy")
4. Identify job skills that are MISSING from resume
5. Provide confidence score (0-100) - be realistic:
   - 80-100: Strong match, candidate well-prepared
   - 60-79: Good match, candidate can learn on the job
   - 40-59: Partial match, candidate would need some growth
   - 0-39: Weak match, significant gaps

Return ONLY a valid JSON object (no markdown, no code blocks):
{{
    "matched_skills": ["skill1", "skill2"],
    "missing_skills": ["skill3", "skill4"],
    "confidence_score": 75,
    "explanation": "Brief explanation of the match (1-2 sentences)"
}}"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            response_text = response_text.strip()

            result_dict = json.loads(response_text)

            return AIMatchResult(
                matched_skills=result_dict.get("matched_skills", []),
                missing_skills=result_dict.get("missing_skills", []),
                confidence_score=int(result_dict.get("confidence_score", 0)),
                explanation=result_dict.get("explanation", ""),
                raw_response=response_text,
            )

        except json.JSONDecodeError as e:
            return AIMatchResult(
                matched_skills=[],
                missing_skills=[],
                confidence_score=0,
                explanation=f"Failed to parse AI response: {str(e)}",
                raw_response=response_text if 'response_text' in locals() else "",
            )
        except Exception as e:
            return AIMatchResult(
                matched_skills=[],
                missing_skills=[],
                confidence_score=0,
                explanation=f"AI matching failed: {str(e)}",
            )


def get_ai_matcher() -> GeminiMatcher:
    """
    Factory function to get Gemini matcher instance.
    
    Raises:
        ValueError: If GEMINI_API_KEY is not configured
    """
    logger.info("Initializing Gemini matcher...")
    try:
        matcher = GeminiMatcher()
        logger.info("✓ Gemini matcher initialized")
        return matcher
    except ValueError as e:
        logger.error(f"❌ Gemini initialization failed: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error initializing Gemini: {e}", exc_info=True)
        raise
