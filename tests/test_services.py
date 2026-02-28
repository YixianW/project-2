from app.services.skill_engine import extract_canonical_skills, score_fit
from app.services.sponsorship import classify_sponsorship


def test_phrase_required_skill_not_counted_from_single_word():
    skills = extract_canonical_skills("I have experience in product and strategy functions.")
    assert "product strategy" not in skills


def test_fit_scoring_overlap_and_missing():
    resume = extract_canonical_skills("SQL Python Tableau go-to-market")
    jd = extract_canonical_skills("Need SQL, Tableau, go-to-market, lifecycle marketing")
    fit = score_fit(resume, jd)
    assert fit["score"] > 0
    assert "lifecycle marketing" in fit["missing_skills"]


def test_sponsorship_classification_conservative():
    txt = "Candidates must be authorized to work in the United States without restriction."
    assert classify_sponsorship(txt) == "work_authorization_required"
