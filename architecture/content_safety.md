# Content Safety SOP

**Layer**: 1 (Architecture)  
**Service**: `backend/app/services/content_filter.py`  
**Last Updated**: 2026-02-12

---

## Goal

Ensure all user-submitted themes and prompts are appropriate for children's content before proceeding with image generation. Protect the platform from abuse while minimizing false positives (e.g., "pirates" and "dinosaurs" should pass).

---

## Input

- `text` (string): User-submitted theme or prompt to validate

---

## Output

- `(is_safe, reason)` tuple:
  - `is_safe` (bool): True if content is safe, False if blocked
  - `reason` (string): Empty if safe, explanation if blocked

---

## Process

### Layer 1: Keyword Blocklist (Instant, Deterministic)

1. **Normalize Text** to defeat unicode evasion:
   - NFKD decomposition to split composed characters
   - Strip combining characters (diacritics, accents)
   - Transliterate special characters (ø→o, μ→u, etc.)
   - Collapse all whitespace (so "g u n" → "gun")
   - Convert to lowercase

2. **Check Against Blocklist**:
   - Hardcoded list of 22 inappropriate keywords
   - Categories: violence, weapons, nudity, drugs, hate speech
   - If ANY keyword found → BLOCK instantly
   - Return: `(False, "Content contains inappropriate term: '{keyword}'")`

3. **Pass to Layer 2** if no keyword match

### Layer 2: Semantic Analysis (Anthropic Claude Haiku)

**Only runs if Layer 1 passed**

1. **API Call**:
   - Model: `claude-haiku-4-5-20251001`
   - Max tokens: 100
   - Timeout: 15 seconds
   - System prompt: "You are a content safety filter for children's coloring book app (ages 3-12)..."
   - User message: "Check this coloring book prompt: {text}"

2. **Response Parsing**:
   - Expected format: "SAFE" or "UNSAFE: <reason>"
   - If starts with "UNSAFE" → extract reason and BLOCK
   - If "SAFE" → ALLOW
   - Return: `(False, reason)` or `(True, "")`

3. **Fallback on Failure**:
   - If Anthropic API fails (no credits, network error, timeout)
   - Log warning: `anthropic_content_filter_unavailable`
   - Return Layer 1 result: `(True, "")`
   - **Rationale**: Layer 1 already blocked dangerous content; safe to proceed

---

## Edge Cases

### False Positives (Should ALLOW)
- ✅ "pirate adventure" (keyword: none)
- ✅ "dinosaur party" (keyword: none)
- ✅ "space battle" (Layer 2 understands context)
- ✅ "knight with wooden sword" (Layer 2 semantic check)

### True Positives (Should BLOCK)
- ❌ "gun fight" (Layer 1: keyword "gun")
- ❌ "violent battle" (Layer 1: keyword "violence")
- ❌ "beer party" (Layer 1: keyword "beer")
- ❌ Subtle inappropriate content (Layer 2 catches)

### Unicode Evasion (Defeated by Normalization)
- ❌ "vïølence" → normalized to "violence" → BLOCKED
- ❌ "g u n" → normalized to "gun" → BLOCKED
- ❌ "gμn" → normalized to "gun" → BLOCKED

---

## Error Handling

### Anthropic API Failures
- **Scenarios**: No credits, network timeout, rate limit, server error
- **Action**: Log warning, fall back to Layer 1 only
- **User Impact**: None (seamless fallback)
- **Example Log**: `anthropic_content_filter_unavailable error=<exception>`

### Invalid Input
- Empty string → Returns `(True, "")` (nothing to block)
- None value → Should be validated at router level before calling service

---

## Performance Requirements

- **Layer 1**: < 10ms (pure Python, no API)
- **Layer 2**: < 2 seconds (including 15s timeout)
- **Total SLA**: < 2 seconds (user experience)

---

## Dependencies

- `anthropic` package for Claude API
- `app.config.get_settings()` for `anthropic_api_key`
- `logging` for observability

---

## Testing Checklist

- [ ] Test Layer 1 blocks all 22 keywords
- [ ] Test unicode normalization (vïølence, g u n, gμn)
- [ ] Test Layer 2 allows kid-friendly edge cases (pirates, dinosaurs)
- [ ] Test Layer 2 blocks subtle inappropriate content
- [ ] Test fallback when Anthropic API unavailable
- [ ] Test with empty string input

---

## Maintenance Notes

### When to Update Keyword Blocklist
- ✏️ User reports false negative (inappropriate content passed)
- ✏️ Pattern analysis shows new evasion techniques
- ⚠️ Be conservative: Only add if clearly inappropriate for children

### When to Update Layer 2 Prompt
- ✏️ False positives on innocent themes (adjust system prompt)
- ✏️ New content categories need clarification
- ✏️ Age range changes (currently 3-12)

---

## Related SOPs

- [Authentication](authentication.md) — User context for logging abuse
- [Image Generation](image_generation.md) — Called before generating images
- [Rate Limiting](rate_limiting.md) — Prevents spam of safety checks
