from collections import Counter
from dataclasses import dataclass

from app.data.skill_taxonomy import IGNORED_TERMS, SKILL_TAXONOMY, WEAK_SUPPORT_SIGNALS
from app.services.text_processing import contains_phrase, normalize_text


@dataclass
class SkillEvidence:
    label: str
    cluster: str
    tier: int
    aliases_matched: list[str]


def extract_canonical_skills(text: str) -> dict[str, SkillEvidence]:
    normalized = normalize_text(text)
    found: dict[str, SkillEvidence] = {}

    for cluster_block in SKILL_TAXONOMY:
        cluster = cluster_block["cluster"]
        for skill in cluster_block["skills"]:
            matches = []
            for alias in skill["aliases"]:
                alias_norm = normalize_text(alias)
                
                # Determine if this is a single-word or multi-word alias
                # Multi-word means: contains spaces, hyphens, or slashes (after trim)
                is_multi_word = (
                    ' ' in alias.strip() or 
                    '-' in alias or 
                    '/' in alias
                )
                
                # Tier 1 single-word-ok skills: match anywhere
                if skill["tier"] == 1 and skill.get("single_word_ok", False):
                    if contains_phrase(normalized, alias_norm):
                        matches.append(alias)
                # Tier 2 or multi-word aliases: require word boundaries via contains_phrase
                # (contains_phrase pads with spaces to prevent substring matches)
                elif is_multi_word and contains_phrase(normalized, alias_norm):
                    matches.append(alias)
                    
            if matches:
                found[skill["label"]] = SkillEvidence(skill["label"], cluster, skill["tier"], matches)
    return found


def detect_weak_signals(text: str) -> list[str]:
    normalized = normalize_text(text)
    return sorted([signal for signal in WEAK_SUPPORT_SIGNALS if contains_phrase(normalized, signal)])


def ignored_term_hits(text: str) -> list[str]:
    normalized = normalize_text(text)
    return sorted([term for term in IGNORED_TERMS if contains_phrase(normalized, term)])


def score_fit(resume_skills: dict[str, SkillEvidence], jd_skills: dict[str, SkillEvidence]) -> dict:
    jd_labels = set(jd_skills.keys())
    resume_labels = set(resume_skills.keys())
    overlap = sorted(jd_labels & resume_labels)
    missing = sorted(jd_labels - resume_labels)

    if not jd_labels:
        return {
            "score": 0,
            "matched_strengths": [],
            "missing_skills": [],
            "explanation": "No canonical job-description skills were recognized, so fit score stays conservative.",
        }

    # 改善评分算法：计算加权匹配率
    tier2_total = 0
    tier2_hit = 0
    tier1_total = 0
    tier1_hit = 0
    
    for label, evidence in jd_skills.items():
        if evidence.tier == 2:
            tier2_total += 1
            if label in resume_labels:
                tier2_hit += 1
        else:
            tier1_total += 1
            if label in resume_labels:
                tier1_hit += 1
    
    # 权重：Tier 2 技能占 60%，Tier 1 技能占 40%
    tier2_score = (tier2_hit / tier2_total * 100) if tier2_total > 0 else 0
    tier1_score = (tier1_hit / tier1_total * 100) if tier1_total > 0 else 0
    
    raw_score = tier2_score * 0.6 + tier1_score * 0.4
    
    # 改进的缺失惩罚：使用对数函数而不是线性，避免完全塌陷到0
    # 1-2 缺失：~0-2 分  | 3-5 缺失：~3-8 分  | 6+ 缺失：~9-15 分
    if missing:
        import math
        missing_count = len(missing)
        missing_penalty = min(math.log(missing_count + 1) * 3.5, 15)
        score = max(0, round(raw_score - missing_penalty))
    else:
        score = round(raw_score)

    explanation = (
        f"Matched {len(overlap)} of {len(jd_labels)} canonical JD skills ({len(overlap)}/{len(jd_labels)}). "
        f"Tier 2: {tier2_hit}/{tier2_total}, Tier 1: {tier1_hit}/{tier1_total}."
    )
    return {
        "score": score,
        "matched_strengths": overlap[:8],
        "missing_skills": missing[:10],
        "explanation": explanation,
    }


def aggregate_skill_gaps(job_analyses: list[dict]) -> list[dict]:
    counter: Counter = Counter()
    for analysis in job_analyses:
        counter.update(analysis.get("missing_skills", []))
    return [{"skill": skill, "count": count} for skill, count in counter.most_common(8)]


def score_fit_with_ai(resume_text: str, job_description: str, use_ai: bool = True) -> dict:
    """
    Score job fit using hybrid approach: keyword matching + optional AI matching.
    
    Args:
        resume_text: Extracted resume text
        job_description: Job description text
        use_ai: Whether to use AI matching (requires GEMINI_API_KEY)
    
    Returns:
        Dictionary with score, matched skills, missing skills, and explanation
    """
    if use_ai:
        try:
            from app.services.ai_matcher import get_ai_matcher
            
            matcher = get_ai_matcher()
            ai_result = matcher.match_skills(resume_text, job_description)
            
            return {
                "score": ai_result.confidence_score,
                "matched_strengths": ai_result.matched_skills[:8],
                "missing_skills": ai_result.missing_skills[:10],
                "explanation": ai_result.explanation,
                "ai_powered": True,
            }
        except Exception as e:
            # Fallback to keyword matching if AI fails
            print(f"AI matching failed, falling back to keyword matching: {e}")
            return score_fit_hybrid(resume_text, job_description, use_ai=False)
    
    return score_fit_hybrid(resume_text, job_description, use_ai=False)


def score_fit_hybrid(resume_text: str, job_description: str, use_ai: bool = False) -> dict:
    """
    Hybrid skill matching: combines keyword matching with optional AI enhancement.
    
    Args:
        resume_text: Extracted resume text
        job_description: Job description text
        use_ai: Whether to use AI matching
    
    Returns:
        Dictionary with score and skill analysis
    """
    resume_skills = extract_canonical_skills(resume_text)
    jd_skills = extract_canonical_skills(job_description)
    
    # Get keyword-based results
    fit_result = score_fit(resume_skills, jd_skills)
    
    # Optionally enhance with AI
    if use_ai:
        try:
            from app.services.ai_matcher import get_ai_matcher
            
            matcher = get_ai_matcher()
            ai_result = matcher.match_skills(resume_text, job_description)
            
            # Merge AI findings with keyword results
            enhanced_matched = list(set(fit_result["matched_strengths"] + ai_result.matched_skills))
            enhanced_missing = list(set(fit_result["missing_skills"] + ai_result.missing_skills))
            
            return {
                "score": (fit_result["score"] + ai_result.confidence_score) // 2,
                "matched_strengths": enhanced_matched[:8],
                "missing_skills": enhanced_missing[:10],
                "explanation": f"Hybrid (Keyword + AI): {fit_result['explanation']} | AI: {ai_result.explanation}",
                "ai_powered": True,
            }
        except Exception as e:
            print(f"AI enhancement failed, using keyword results only: {e}")
            return fit_result
    
    return fit_result
