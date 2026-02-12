"""
Centralized constants for the TailorMade backend.
Single source of truth — imported by image_gen, scene_planner, content_filter, etc.
"""

# ── Print / Image Constants ────────────────────────────────────────────────────

# 300 DPI is the professional print standard for high-quality output
# https://www.printivity.com/insights/image-resolution-for-print/
PRINT_DPI = 300

# US Letter size (8.5" × 11") at print resolution
LETTER_WIDTH_PX = int(8.5 * PRINT_DPI)   # 2550px
LETTER_HEIGHT_PX = int(11 * PRINT_DPI)    # 3300px

# Thumbnail maintains US Letter aspect ratio for gallery previews
THUMBNAIL_SIZE = (400, 518)

# 128 is 50% gray — optimal threshold for B&W line art conversion
# Lower = more black (harder to color), Higher = more white (lost detail)
THRESHOLD_BINARY = 128


# ── Age Range Definitions ──────────────────────────────────────────────────────

AGE_RANGES = {
    "toddler": {"min": 3, "max": 5, "label": "Ages 3-5", "value": "3-5"},
    "kids":    {"min": 6, "max": 9, "label": "Ages 6-9", "value": "6-9"},
    "tweens":  {"min": 10, "max": 12, "label": "Ages 10-12", "value": "10-12"},
}

# Overall age range for content safety prompts
APP_AGE_RANGE = "ages 3-12"


# ── Concurrency Limits ─────────────────────────────────────────────────────────

# Max concurrent fal.ai image generations per request
# 3 concurrent × ~4MB raw ≈ 12MB vs 12 concurrent × ~4MB ≈ 48MB peak memory
MAX_CONCURRENT_IMAGES = 3

# Max downloaded image size (10MB) — prevents abnormally large responses
MAX_IMAGE_BYTES = 10 * 1024 * 1024


# ── Timeout Defaults (seconds) ─────────────────────────────────────────────────

HTTPX_TIMEOUT = 30.0
ANTHROPIC_TIMEOUT = 15.0
