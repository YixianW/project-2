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
        
        # Try to detect available models
        logger.info("Detecting available Gemini models...")
        try:
            models = genai.list_models()
            available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            logger.info(f"Available models: {available_models}")
            
            # Prefer latest flash models in order: 2.5 > 2.0 > 1.5
            self.vision_model_name = "gemini-2.5-flash"
            if not any("gemini-2.5-flash" in m for m in available_models):
                self.vision_model_name = "gemini-2.0-flash"
                if not any("gemini-2.0-flash" in m for m in available_models):
                    self.vision_model_name = "gemini-1.5-flash"
                    logger.warning("gemini-2.5-flash and gemini-2.0-flash not available, using gemini-1.5-flash")
                else:
                    logger.info("Using gemini-2.0-flash (gemini-2.5-flash not available)")
        except Exception as e:
            logger.warning(f"Could not list models: {e}, using default gemini-2.5-flash")
            self.vision_model_name = "gemini-2.5-flash"
        
        self.vision_model = genai.GenerativeModel(self.vision_model_name)
        logger.info(f"✓ Gemini model initialized: {self.vision_model_name}")

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
        logger.info(f"Starting AI matching for {resume_filename} (size: {len(resume_bytes)} bytes)")
        
        if not resume_bytes or not job_description:
            logger.warning("Empty resume or job description provided")
            return AIMatchResult(
                matched_skills=[],
                missing_skills=[],
                confidence_score=0,
                explanation="Empty resume or job description",
            )

        temp_path = None
        uploaded_file = None
        
        try:
            # Save temp file for Gemini to process
            temp_path = self._save_temp_file(resume_filename, resume_bytes)
            logger.info(f"Saved temp resume file to: {temp_path}")
            
            # Clear resume_bytes from memory since we saved it
            resume_bytes_copy = None

            # Upload file to Gemini
            logger.info(f"Uploading resume file to Gemini: {resume_filename}")
            uploaded_file = genai.upload_file(temp_path)
            logger.info(f"✓ File uploaded successfully. File ID: {uploaded_file.name}")
            
            # Delete temp file immediately to free memory
            try:
                Path(temp_path).unlink(missing_ok=True)
                temp_path = None
                logger.info("✓ Temp file deleted from disk to free memory")
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")

            # Create a more concise prompt to speed up response
            prompt = f"""Analyze this resume against the job description. Return ONLY a JSON object with no other text.

JOB DESCRIPTION:
{job_description[:2000]}

RESPOND ONLY WITH THIS JSON FORMAT (no markdown, no explanation, no extra text):
{{"matched_skills": ["skill1", "skill2"], "missing_skills": ["skill3"], "confidence_score": 75, "explanation": "brief"}}

Rules:
- matched_skills: Skills from resume that match job requirements
- missing_skills: Job skills not in resume
- confidence_score: 0-100 (80+ strong match, 60-79 good, 40-59 partial, 0-39 weak)
- explanation: 1-2 sentences max
- MUST START WITH {{ AND END WITH }}
- NO TEXT BEFORE OR AFTER JSON
- NO MARKDOWN OR BACKTICKS"""

            # Call Gemini with file reference
            logger.info("Calling Gemini API for skill matching...")
            response = self.vision_model.generate_content(
                [prompt, uploaded_file],
                request_options={"timeout": 600}  # 10 minute timeout for Gemini
            )
            logger.info("✓ Gemini API response received")
            
            response_text = response.text if hasattr(response, 'text') else str(response)
            if response_text is None:
                response_text = ""
            response_text = response_text.strip()
            logger.info(f"Raw response length: {len(response_text)} chars, first 200: {response_text[:200]}")

            # Clean up: delete uploaded file
            if uploaded_file:
                genai.delete_file(uploaded_file.name)
                uploaded_file = None
                logger.info("✓ File deleted from Gemini")

            # Extract JSON from response - more robust parsing
            cleaned_text = response_text
            
            # Remove markdown code block wrappers (```json ... ``` or ``` ... ```)
            if "```" in cleaned_text:
                # Find content between triple backticks
                parts = cleaned_text.split("```")
                for part in parts:
                    part_stripped = part.strip()
                    if part_stripped.startswith("{"):
                        cleaned_text = part_stripped
                        break
            
            # Find and extract JSON object with bracket matching
            if not cleaned_text.strip().startswith("{"):
                json_start = cleaned_text.find("{")
                if json_start != -1:
                    # Find matching closing bracket
                    bracket_count = 0
                    json_end = -1
                    for i in range(json_start, len(cleaned_text)):
                        if cleaned_text[i] == "{":
                            bracket_count += 1
                        elif cleaned_text[i] == "}":
                            bracket_count -= 1
                            if bracket_count == 0:
                                json_end = i + 1
                                break
                    
                    if json_end > json_start:
                        cleaned_text = cleaned_text[json_start:json_end]
                        logger.info(f"Extracted JSON ({json_end-json_start} chars)")
            
            cleaned_text = cleaned_text.strip()
            logger.debug(f"Cleaned response: {cleaned_text[:200]}")

            if not cleaned_text or not cleaned_text.startswith("{"):
                logger.error(f"Invalid response format: {response_text[:300]}")
                return AIMatchResult(
                    matched_skills=[],
                    missing_skills=[],
                    confidence_score=0,
                    explanation="Invalid response from Gemini",
                )

            # Try JSON parsing with repair
            try:
                result_dict = json.loads(cleaned_text)
            except json.JSONDecodeError as parse_err:
                logger.warning(f"JSON parse error, attempting repair: {parse_err}")
                # Repair incomplete JSON
                if cleaned_text.count("{") > cleaned_text.count("}"):
                    cleaned_text = cleaned_text + "}" * (cleaned_text.count("{") - cleaned_text.count("}"))
                    try:
                        result_dict = json.loads(cleaned_text)
                        logger.info("✓ Repaired incomplete JSON")
                    except:
                        logger.error(f"Repair failed. Text: {cleaned_text[:300]}")
                        raise
                else:
                    raise
            
            logger.info(f"✓ Skill matching completed. Score: {result_dict.get('confidence_score', 0)}")

            return AIMatchResult(
                matched_skills=result_dict.get("matched_skills", []) or [],
                missing_skills=result_dict.get("missing_skills", []) or [],
                confidence_score=int(result_dict.get("confidence_score", 0) or 0),
                explanation=result_dict.get("explanation", "") or "",
                raw_response=cleaned_text,
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Attempted to parse: {cleaned_text if 'cleaned_text' in locals() else 'N/A'}")
            return AIMatchResult(
                matched_skills=[],
                missing_skills=[],
                confidence_score=0,
                explanation=f"JSON parsing error: {str(e)}",
                raw_response=response_text if 'response_text' in locals() else "",
            )
        except Exception as e:
            logger.error(f"AI matching error: {e}", exc_info=True)
            if 'response_text' in locals():
                logger.error(f"Response was: {response_text[:500]}")
            return AIMatchResult(
                matched_skills=[],
                missing_skills=[],
                confidence_score=0,
                explanation=f"AI matching failed: {str(e)}",
            )
        finally:
            # Clean up temp file and uploaded file
            try:
                if temp_path:
                    Path(temp_path).unlink(missing_ok=True)
                    logger.info("Temp file cleaned up")
            except Exception:
                pass
            
            try:
                if uploaded_file:
                    genai.delete_file(uploaded_file.name)
                    logger.info("Uploaded file cleaned up")
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
