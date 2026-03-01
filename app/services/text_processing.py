import re
import unicodedata


WHITESPACE_RE = re.compile(r"\s+")
NON_ALNUM_RE = re.compile(r"[^a-z0-9+/#\-\s]")


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    text = text.lower().replace("&", " and ")
    text = NON_ALNUM_RE.sub(" ", text)
    return WHITESPACE_RE.sub(" ", text).strip()


def contains_phrase(text: str, phrase: str) -> bool:
    """Check if phrase appears as a word boundary-respecting substring in text.
    
    Both text and phrase are normalized using the same rules to ensure
    consistent matching even if input text is already normalized.
    """
    text_norm = normalize_text(text)
    phrase_norm = normalize_text(phrase)
    # Pad with spaces to ensure word boundary matching
    padded = f" {text_norm} "
    candidate = f" {phrase_norm} "
    return candidate in padded
