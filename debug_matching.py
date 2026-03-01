#!/usr/bin/env python3
"""Debug script to trace the matching pipeline step-by-step."""

from app.services.text_processing import normalize_text, contains_phrase
from app.services.skill_engine import extract_canonical_skills
from app.data.mock_jobs import MOCK_JOBS

# Test 1: Basic normalization
print("=" * 80)
print("TEST 1: Text Normalization")
print("=" * 80)
test_phrases = [
    "go-to-market strategy",
    "go to market strategy",
    "A/B testing",
    "ab testing",
    "cross-functional collaboration",
    "cross functional collaboration",
    "customer insights",
]

for phrase in test_phrases:
    normalized = normalize_text(phrase)
    print(f"  '{phrase}' -> '{normalized}'")

# Test 2: Phrase matching with current logic
print("\n" + "=" * 80)
print("TEST 2: contains_phrase() behavior")
print("=" * 80)
text = "'Go-to-market strategy' mentioned in text"
test_phrases = [
    ("go-to-market", "hyphenated form"),
    ("go to market", "spaced form"),
    ("gtm", "abbreviation"),
]

for phrase, desc in test_phrases:
    # Current broken implementation
    padded = f" {text} "
    candidate = f" {normalize_text(phrase)} "
    result = candidate in padded
    print(f"\n  Looking for '{phrase}' ({desc}):")
    print(f"    text (raw):            '{text}'")
    print(f"    padded (NOT normalized): '{padded}'")
    print(f"    candidate (normalized): '{candidate}'")
    print(f"    Found: {result}")

# Test 3: Extract skills from mock job
print("\n" + "=" * 80)
print("TEST 3: Extract skills from mock jobs")
print("=" * 80)
for job in MOCK_JOBS[:2]:  # Test first 2 jobs
    print(f"\n\nJob: {job['title']} @ {job['company']}")
    print(f"Description length: {len(job['description'])} chars")
    print(f"Description: {job['description'][:150]}...")
    
    # Normalize and extract
    normalized_desc = normalize_text(job['description'])
    print(f"\nNormalized description ({len(normalized_desc)} chars):")
    print(f"  {normalized_desc[:150]}...")
    
    skills = extract_canonical_skills(job['description'])
    print(f"\nExtracted {len(skills)} skills:")
    for label, evidence in sorted(skills.items()):
        print(f"  - {label} (Tier {evidence.tier}, matched: {evidence.aliases_matched})")
    
    if len(skills) == 0:
        print("  ⚠️  NO SKILLS EXTRACTED!")

# Test 4: Check specific alias matching
print("\n" + "=" * 80)
print("TEST 4: Detailed alias matching for 'go-to-market'")
print("=" * 80)
job_desc = MOCK_JOBS[0]["description"]
normalized_desc = normalize_text(job_desc)
print(f"Normalized description snippet:\n  {normalized_desc[:200]}...\n")

# Manually check aliases
from app.data.skill_taxonomy import SKILL_TAXONOMY
gtm_skill = None
for cluster in SKILL_TAXONOMY:
    for skill in cluster["skills"]:
        if skill["label"] == "go-to-market":
            gtm_skill = skill
            break

if gtm_skill:
    print(f"go-to-market skill aliases:")
    for alias in gtm_skill["aliases"]:
        alias_norm = normalize_text(alias)
        split_count = len(alias_norm.split())
        padded_text = f" {normalized_desc} "
        candidate = f" {alias_norm} "
        found = candidate in padded_text
        print(f"\n  Alias: '{alias}'")
        print(f"    Normalized: '{alias_norm}'")
        print(f"    Split tokens: {split_count} (checking > 1: {split_count > 1})")
        print(f"    ' {alias_norm} ' in text: {found}")
        print(f"    Status: {'✓ MATCH' if found and split_count > 1 else '✗ SKIP' if split_count <= 1 else '✗ NOT FOUND'}")
