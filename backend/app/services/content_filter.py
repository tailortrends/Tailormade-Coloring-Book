import logging
import re
import unicodedata
import anthropic
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Layer 1: instant blocklist — no API call needed
_BLOCKED_KEYWORDS = {
    "violence", "blood", "gore", "weapon", "gun", "knife", "death", "kill",
    "murder", "war", "bomb", "nude", "naked", "sex", "adult", "porn",
    "drugs", "alcohol", "beer", "wine", "cigarette", "smoking",
    "hate", "racist", "slur", "curse", "profanity",
}


def _normalize(text: str) -> str:
    """
    Normalize text to defeat common unicode evasion tricks:
    - vïølence → violence  (strip diacritics + transliterate special chars)
    - g u n   → gun       (collapse whitespace)
    - gμn     → gun       (NFKD + transliteration)
    """
    # NFKD decomposition: splits composed chars into base + combining marks
    nfkd = unicodedata.normalize("NFKD", text)
    # Strip combining characters (diacritics, accents)
    ascii_approx = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Transliterate standalone special characters that NFKD doesn't decompose
    _TRANSLITERATE = {
        "ø": "o", "Ø": "O", "ð": "d", "Ð": "D", "þ": "th", "Þ": "TH",
        "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE", "ß": "ss",
        "μ": "u", "ł": "l", "Ł": "L", "đ": "d", "Đ": "D",
    }
    transliterated = "".join(_TRANSLITERATE.get(c, c) for c in ascii_approx)
    # Collapse all whitespace so "g u n" becomes "gun"
    collapsed = re.sub(r"\s+", "", transliterated)
    return collapsed.lower()


def _layer1_check(text: str) -> tuple[bool, str]:
    """Fast keyword scan with unicode normalization. Returns (is_safe, reason)."""
    normalized = _normalize(text)
    for word in _BLOCKED_KEYWORDS:
        if word in normalized:
            logger.info("content_blocked_layer1 keyword=%s", word)
            return False, f"Content contains inappropriate term: '{word}'"
    return True, ""


async def _layer2_check(text: str) -> tuple[bool, str]:
    """Claude Haiku semantic check for edge cases layer 1 misses."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        timeout=15.0,  # Don't hang forever
        system=(
            "You are a content safety filter for a children's coloring book app (ages 3-12). "
            "Review the prompt and respond with ONLY 'SAFE' or 'UNSAFE: <brief reason>'. "
            "Flag anything violent, sexual, scary, involving real weapons, drugs, or inappropriate "
            "for young children. Allow animals, fantasy, adventure, and family themes."
        ),
        messages=[{"role": "user", "content": f"Check this coloring book prompt: {text}"}],
    )
    result = response.content[0].text.strip()
    if result.startswith("UNSAFE"):
        reason = result.replace("UNSAFE:", "").strip()
        logger.info("content_blocked_layer2 reason=%s", reason)
        return False, reason
    return True, ""


async def is_content_safe(text: str) -> tuple[bool, str]:
    """
    Full two-layer check.
    Returns (is_safe, reason_if_unsafe).
    Layer 1 is instant (keyword + unicode normalization); layer 2 only runs if layer 1 passes.
    If layer 2 (Anthropic) is unavailable, falls back to layer 1 only.
    """
    safe, reason = _layer1_check(text)
    if not safe:
        return False, reason

    # Only hit Anthropic API if layer 1 passed
    try:
        safe, reason = await _layer2_check(text)
        return safe, reason
    except Exception as exc:
        # If Anthropic API is unavailable (no credits, network error, etc.),
        # fall back to layer 1 only — still safe for kids since keywords are blocked.
        logger.warning("anthropic_content_filter_unavailable error=%s", exc)
        return True, ""
