#!/usr/bin/env python3
"""Comprehensive debug script for scoring pipeline."""

from app.services.resume_parser import extract_resume_text
from app.services.skill_engine import (
    extract_canonical_skills,
    score_fit,
    aggregate_skill_gaps,
)
from app.data.mock_jobs import MOCK_JOBS

# Create a mock resume text
MOCK_RESUME = """
Senior Product Marketing Manager with 8+ years experience.

Skills:
- Go-to-market strategy and product launches
- Market research & competitive analysis
- Customer insights and voice of customer
- Product marketing and PMM strategy
- SQL and data analysis
- Tableau dashboards
- A/B testing and experimentation
- Conversion optimization
- Cross-functional collaboration and stakeholder management
- Campaign strategy and execution
"""

print("=" * 90)
print("SCORING DEBUG: Resume vs. Mock Jobs")
print("=" * 90)

# Extract resume skills
print("\n📄 RESUME ANALYSIS")
print("-" * 90)
resume_normalized = extract_canonical_skills(MOCK_RESUME)
print(f"Extracted {len(resume_normalized)} skills from resume:")
for label, evidence in sorted(resume_normalized.items()):
    print(f"  - {label} (Tier {evidence.tier}, matched via: {evidence.aliases_matched})")

# Analyze each job
print("\n" + "=" * 90)
print("JOB ANALYSIS & SCORING")
print("=" * 90)

all_analyses = []
for i, job in enumerate(MOCK_JOBS):
    print(f"\n\nJob #{i+1}: {job['title']} @ {job['company']}")
    print(f"  Location: {job['location']}")
    print(f"  Salary: ${job['salary_min']:,} - ${job['salary_max']:,}" if job['salary_min'] else "  Salary: Not listed")
    print("-" * 90)
    
    # Extract JD skills
    jd_skills = extract_canonical_skills(job['description'])
    print(f"\n  📋 JD Skills ({len(jd_skills)} found):")
    tier1_jd = [label for label, ev in jd_skills.items() if ev.tier == 1]
    tier2_jd = [label for label, ev in jd_skills.items() if ev.tier == 2]
    print(f"    Tier 1: {tier1_jd if tier1_jd else '(none)'}")
    print(f"    Tier 2: {tier2_jd if tier2_jd else '(none)'}")
    
    # Calculate fit
    fit_result = score_fit(resume_normalized, jd_skills)
    print(f"\n  ⚖️  FIT ANALYSIS:")
    print(f"    Matched Strengths ({len(fit_result['matched_strengths'])}): {fit_result['matched_strengths']}")
    print(f"    Missing Skills ({len(fit_result['missing_skills'])}): {fit_result['missing_skills']}")
    print(f"    Score Explanation: {fit_result['explanation']}")
    print(f"    ✓ FINAL SCORE: {fit_result['score']}/100")
    
    # Store for aggregation
    all_analyses.append({
        "job": job,
        "jd_skills": jd_skills,
        "fit_score": fit_result["score"],
        "matched_strengths": fit_result["matched_strengths"],
        "missing_skills": fit_result["missing_skills"],
    })

# Aggregate skill gaps
print("\n" + "=" * 90)
print("SKILL GAP AGGREGATION ACROSS ALL JOBS")
print("=" * 90)
gaps = aggregate_skill_gaps(all_analyses)
print(f"\nTop recurring missing skills:")
for gap in gaps[:8]:
    print(f"  - {gap['skill']}: mentioned in {gap['count']} job(s)")

# Summary
print("\n" + "=" * 90)
print("SUMMARY")
print("=" * 90)
scores = [a["fit_score"] for a in all_analyses]
print(f"\nFit score distribution:")
print(f"  Scores: {scores}")
print(f"  Average: {sum(scores) / len(scores):.1f}")
print(f"  Min: {min(scores)}")
print(f"  Max: {max(scores)}")
print(f"  Non-zero: {sum(1 for s in scores if s > 0)}/{len(scores)}")

if any(s == 0 for s in scores):
    print("\n⚠️  WARNING: Some jobs still scoring 0. Investigate further.")
else:
    print("\n✓ SUCCESS: All jobs have non-zero scores!")
