import json
import os
from dataclasses import asdict, dataclass

import google.generativeai as genai

from app.data.skill_taxonomy import SKILL_TAXONOMY


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
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-pro")

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
    """Factory function to get Gemini matcher instance."""
    return GeminiMatcher()
