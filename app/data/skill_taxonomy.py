"""Canonical skill taxonomy with tiered matching policy."""

SKILL_TAXONOMY = [
    {
        "cluster": "Data / Analytics",
        "skills": [
            {"label": "sql", "tier": 1, "aliases": ["sql", "structured query language"], "single_word_ok": True},
            {"label": "python", "tier": 1, "aliases": ["python", "pandas", "numpy"], "single_word_ok": True},
            {"label": "excel", "tier": 1, "aliases": ["excel", "microsoft excel"], "single_word_ok": True},
            {"label": "tableau", "tier": 1, "aliases": ["tableau"], "single_word_ok": True},
            {"label": "power bi", "tier": 1, "aliases": ["power bi", "powerbi"], "single_word_ok": False},
            {"label": "looker", "tier": 1, "aliases": ["looker", "google looker"], "single_word_ok": True},
            {"label": "data visualization", "tier": 2, "aliases": ["data visualization", "visualize data", "dashboard development"], "single_word_ok": False},
            {"label": "ab testing", "tier": 2, "aliases": ["a/b testing", "ab testing", "split testing", "multivariate testing"], "single_word_ok": False},
            {"label": "conversion optimization", "tier": 2, "aliases": ["conversion optimization", "cvr optimization", "landing page optimization"], "single_word_ok": False},
        ],
    },
    {
        "cluster": "Marketing",
        "skills": [
            {"label": "seo", "tier": 1, "aliases": ["seo", "search engine optimization"], "single_word_ok": True},
            {"label": "sem", "tier": 1, "aliases": ["sem", "search engine marketing", "paid search"], "single_word_ok": True},
            {"label": "digital marketing", "tier": 2, "aliases": ["digital marketing", "digital campaign strategy"], "single_word_ok": False},
            {"label": "growth marketing", "tier": 2, "aliases": ["growth marketing", "growth strategy", "acquisition marketing"], "single_word_ok": False},
            {"label": "performance marketing", "tier": 2, "aliases": ["performance marketing", "paid media", "performance media"], "single_word_ok": False},
            {"label": "campaign strategy", "tier": 2, "aliases": ["campaign strategy", "campaign planning", "campaign optimization"], "single_word_ok": False},
            {"label": "user acquisition", "tier": 2, "aliases": ["user acquisition", "customer acquisition", "demand generation"], "single_word_ok": False},
            {"label": "segmentation strategy", "tier": 2, "aliases": ["segmentation strategy", "audience segmentation", "target segment strategy"], "single_word_ok": False},
        ],
    },
    {
        "cluster": "CRM / Lifecycle",
        "skills": [
            {"label": "crm", "tier": 1, "aliases": ["crm", "customer relationship management"], "single_word_ok": True},
            {"label": "salesforce", "tier": 1, "aliases": ["salesforce"], "single_word_ok": True},
            {"label": "hubspot", "tier": 1, "aliases": ["hubspot"], "single_word_ok": True},
            {"label": "lifecycle marketing", "tier": 2, "aliases": ["lifecycle marketing", "lifecycle campaigns", "retention marketing"], "single_word_ok": False},
            {"label": "email automation", "tier": 2, "aliases": ["email automation", "automated email journeys", "drip campaigns"], "single_word_ok": False},
        ],
    },
    {
        "cluster": "Product / Strategy",
        "skills": [
            {"label": "product marketing", "tier": 2, "aliases": ["product marketing", "pmm"], "single_word_ok": False},
            {"label": "go-to-market", "tier": 2, "aliases": ["go-to-market", "gtm", "go to market"], "single_word_ok": False},
            {"label": "launch strategy", "tier": 2, "aliases": ["launch strategy", "product launch planning"], "single_word_ok": False},
            {"label": "product strategy", "tier": 2, "aliases": ["product strategy", "roadmap strategy"], "single_word_ok": False},
            {"label": "pricing strategy", "tier": 2, "aliases": ["pricing strategy", "price packaging", "monetization strategy"], "single_word_ok": False},
            {"label": "market research", "tier": 2, "aliases": ["market research", "market analysis", "competitive analysis"], "single_word_ok": False},
            {"label": "customer insights", "tier": 2, "aliases": ["customer insights", "voice of customer", "consumer insights"], "single_word_ok": False},
        ],
    },
    {
        "cluster": "Execution / Collaboration",
        "skills": [
            {"label": "project management", "tier": 2, "aliases": ["project management", "program management"], "single_word_ok": False},
            {"label": "stakeholder management", "tier": 2, "aliases": ["stakeholder management", "executive stakeholder communication"], "single_word_ok": False},
            {"label": "cross-functional collaboration", "tier": 2, "aliases": ["cross-functional collaboration", "cross functional teamwork", "xfn collaboration"], "single_word_ok": False},
            {"label": "jira", "tier": 1, "aliases": ["jira"], "single_word_ok": True},
            {"label": "figma", "tier": 1, "aliases": ["figma"], "single_word_ok": True},
        ],
    },
]

WEAK_SUPPORT_SIGNALS = {
    "communication",
    "leadership",
    "collaboration",
    "presentation",
    "organization",
    "problem solving",
}

IGNORED_TERMS = {
    "passionate",
    "innovative",
    "dynamic",
    "self starter",
    "team player",
    "fast paced",
    "preferred",
    "plus",
    "familiarity with",
    "responsible for",
    "motivated",
    "results driven",
}
