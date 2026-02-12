import asyncio
import logging
import os
import io
import fal_client
import httpx
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

if settings.fal_key:
    os.environ["FAL_KEY"] = settings.fal_key

# ── Constants ──────────────────────────────────────────────────────────────────
# 300 DPI is professional print standard
# https://www.printivity.com/insights/image-resolution-for-print/
PRINT_DPI = 300
LETTER_WIDTH_PX = int(8.5 * PRINT_DPI)   # 2550px — US Letter width at 300 DPI
LETTER_HEIGHT_PX = int(11 * PRINT_DPI)    # 3300px — US Letter height at 300 DPI
THUMBNAIL_SIZE = (400, 518)               # Maintain US Letter aspect ratio

# 128 is 50% gray — optimal threshold for B&W line art conversion
# Lower = more black (harder to color), Higher = more white (lost detail)
THRESHOLD_BINARY = 128

# Limit concurrent image generations to control memory usage
# 3 concurrent × ~4MB raw = ~12MB vs 12 concurrent × ~4MB = ~48MB
MAX_CONCURRENT_IMAGES = 3
_semaphore = asyncio.Semaphore(MAX_CONCURRENT_IMAGES)

# Max image download size (10MB) — prevents downloading abnormally large responses
MAX_IMAGE_BYTES = 10 * 1024 * 1024


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, ConnectionError, TimeoutError)),
    reraise=True,
)
async def _generate_single(prompt: str) -> bytes:
    """Call fal.ai and return raw PNG bytes. Retries up to 3x with exponential backoff."""
    result = await asyncio.to_thread(
        fal_client.run,
        settings.fal_model,
        arguments={
            "prompt": prompt,
            "image_size": "portrait_4_3",
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
            "num_images": 1,
            "output_format": "png",
        },
    )
    image_url = result["images"][0]["url"]
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        response = await client.get(image_url)
        response.raise_for_status()
        # Guard against abnormally large responses
        if len(response.content) > MAX_IMAGE_BYTES:
            raise ValueError(f"Image too large: {len(response.content)} bytes (max {MAX_IMAGE_BYTES})")
        return response.content


def _clean_line_art(image_bytes: bytes) -> bytes:
    """
    Post-process fal.ai output to ensure true B&W for coloring book use.
    - Converts to grayscale
    - Applies binary threshold so whites are #FFFFFF (required for bucket fill on frontend)
    - Upscales to print resolution (300 DPI, US Letter)
    Uses only Pillow to avoid OpenCV binary issues in all environments.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("L")  # grayscale

    # Binary threshold: pixels < 128 → black (0), >= 128 → white (255)
    img = img.point(lambda p: 0 if p < THRESHOLD_BINARY else 255, "1")
    img = img.convert("RGB")

    # Upscale to print resolution with high-quality resampling
    img = img.resize((LETTER_WIDTH_PX, LETTER_HEIGHT_PX), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG", dpi=(PRINT_DPI, PRINT_DPI))
    return buf.getvalue()


def _make_thumbnail(image_bytes: bytes) -> bytes:
    """Create a small preview thumbnail from the cleaned image."""
    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


async def generate_pages(scenes: list[dict]) -> list[dict]:
    """
    Generate all pages with bounded concurrency via semaphore.
    Returns scenes with added 'image_bytes' and 'thumbnail_bytes' keys.
    """
    async def process_scene(scene: dict) -> dict:
        async with _semaphore:  # Only MAX_CONCURRENT_IMAGES at a time
            logger.info("generating_page page=%d", scene["page_number"])
            raw = await _generate_single(scene["image_prompt"])
            cleaned = await asyncio.to_thread(_clean_line_art, raw)
            thumbnail = await asyncio.to_thread(_make_thumbnail, cleaned)
            return {**scene, "image_bytes": cleaned, "thumbnail_bytes": thumbnail}

    results = await asyncio.gather(*[process_scene(s) for s in scenes])
    return list(results)
