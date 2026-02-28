from app.services.text_processing import contains_phrase, normalize_text

SPONSORSHIP_AVAILABLE_PATTERNS = [
    "visa sponsorship is available",
    "h-1b sponsorship is available",
    "we provide visa sponsorship",
    "provide immigration support",
    "offer sponsorship",
    "support visa transfers",
    "support stem opt",
    "sponsor permanent residency",
]

NO_SPONSORSHIP_PATTERNS = [
    "will not sponsor visas",
    "sponsorship is not available",
    "h-1b sponsorship is not available",
    "not able to provide sponsorship",
    "no visa sponsorship",
    "will not sponsor now or in the future",
    "must not require sponsorship now or in the future",
    "without the need for visa sponsorship now or in the future",
]

WORK_AUTH_REQUIRED_PATTERNS = [
    "must be authorized to work in the u s",
    "legal authorization to work in the united states is a precondition of employment",
    "currently authorized to work in the u s on a full-time basis without restriction",
    "must have a valid work permit that does not require any company action",
    "no employer sponsorship required",
    "only u s citizens or permanent residents",
    "open only to u s citizens or permanent residents",
    "must be authorized to work in the united states",
    "without restriction",
]

UNCLEAR_PATTERNS = [
    "proof of eligibility to work in the united states",
    "employment eligibility verification required",
    "subject to verification of work authorization",
]


def classify_sponsorship(description: str) -> str:
    normalized = normalize_text(description)

    for pattern in NO_SPONSORSHIP_PATTERNS:
        if contains_phrase(normalized, pattern):
            return "no_sponsorship"
    for pattern in SPONSORSHIP_AVAILABLE_PATTERNS:
        if contains_phrase(normalized, pattern):
            return "sponsorship_available"
    for pattern in WORK_AUTH_REQUIRED_PATTERNS:
        if contains_phrase(normalized, pattern):
            return "work_authorization_required"
    for pattern in UNCLEAR_PATTERNS:
        if contains_phrase(normalized, pattern):
            return "unclear"
    return "unclear"
