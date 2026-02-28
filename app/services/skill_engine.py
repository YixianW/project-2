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
                if skill["tier"] == 1 and skill.get("single_word_ok", False):
                    if contains_phrase(normalized, alias_norm):
                        matches.append(alias)
                else:
                    if len(alias_norm.split()) > 1 and contains_phrase(normalized, alias_norm):
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

    weighted_total = 0
    weighted_hit = 0
    for label, evidence in jd_skills.items():
        weight = 2 if evidence.tier == 2 else 1.5
        weighted_total += weight
        if label in resume_labels:
            weighted_hit += weight

    raw = (weighted_hit / weighted_total) * 100
    penalty = min(len(missing) * 3, 20)
    score = max(0, round(raw - penalty))

    explanation = (
        f"Matched {len(overlap)} of {len(jd_labels)} canonical JD skills. "
        f"Applied missing-skill penalty for {len(missing)} uncovered requirements."
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
