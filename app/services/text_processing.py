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
    padded = f" {text} "
    candidate = f" {normalize_text(phrase)} "
    return candidate in padded
