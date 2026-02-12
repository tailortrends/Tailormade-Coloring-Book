# Image Generation SOP

**Layer**: 1 (Architecture)  
**Service**: `backend/app/services/image_gen.py`  
**Last Updated**: 2026-02-12

---

## Goal

Generate print-quality, black-and-white line art suitable for coloring books using fal.ai's FLUX model. Process images to ensure true B&W (no grays) for optimal coloring experience.

---

## Input

- `scenes` (list[dict]): List of scene dictionaries, each containing:
  - `page_number` (int): Page order (1-indexed)
  - `description` (string): Human-readable scene description
  - `image_prompt` (string): Prompt sent to fal.ai

---

## Output

- `scenes` (list[dict]): Same input list with added keys:
  - `image_bytes` (bytes): Cleaned PNG at 300 DPI (US Letter size)
  - `thumbnail_bytes` (bytes): JPEG preview thumbnail

---

## Process

### Step 1: Bounded Concurrent Generation

1. **Semaphore Control**: Max 3 concurrent requests
   - **Rationale**: Balance speed vs memory usage
   - 3 concurrent × 4MB = ~12MB peak memory
   - 12 concurrent × 4MB = ~48MB peak memory (too high)

2. **For Each Scene** (in parallel, respecting semaphore):
   - Acquire semaphore slot
   - Call `_generate_single(image_prompt)`
   - Process image with `_clean_line_art()`
   - Create thumbnail with `_make_thumbnail()`
   - Add `image_bytes` and `thumbnail_bytes` to scene dict
   - Release semaphore slot

### Step 2: Generate Single Image (`_generate_single`)

1. **Call fal.ai API**:
   - Model: `fal-ai/flux/dev` (settings.fal_model)
   - Arguments:
     - `prompt`: Scene's image_prompt
     - `image_size`: "portrait_4_3" (aspect ratio for coloring book)
     - `num_inference_steps`: 28 (quality vs speed tradeoff)
     - `guidance_scale`: 3.5 (adherence to prompt)
     - `num_images`: 1
     - `output_format`: "png"

2. **Download Image**:
   - Extract URL from API response: `result["images"][0]["url"]`
   - Download with httpx (30s timeout)
   - Validate size < 10MB (prevents abnormal responses)
   - Return raw PNG bytes

3. **Retry Logic** (via `@retry` decorator):
   - Max attempts: 3
   - Wait: Exponential backoff (2s, 4s, 8s)
   - Retry on: `httpx.HTTPError`, `ConnectionError`, `TimeoutError`
   - **Rationale**: Temporary network issues should not fail entire book

### Step 3: Clean Line Art (`_clean_line_art`)

**Goal**: Convert fal.ai output to true black-and-white for coloring.

1. **Grayscale Conversion**:
   - PIL `Image.convert("L")` → 8-bit grayscale

2. **Binary Threshold**:
   - Pixels < 128 → Black (0)
   - Pixels ≥ 128 → White (255)
   - Convert to 1-bit mode: `img.point(lambda p: 0 if p < 128 else 255, "1")`
   - **Rationale**: Ensures #FFFFFF white for bucket fill tools

3. **Convert Back to RGB**:
   - Required for PDF embedding and R2 storage

4. **Upscale to Print Resolution**:
   - Target: 2550 × 3300 pixels (8.5" × 11" at 300 DPI)
   - Resampling: Lanczos (high-quality interpolation)
   - **Rationale**: Professional print standard

5. **Encode as PNG**:
   - DPI metadata: (300, 300)
   - Return bytes

### Step 4: Create Thumbnail (`_make_thumbnail`)

1. **Resize**: 400 × 518 pixels (maintains US Letter aspect ratio)
2. **Compression**: JPEG quality 85 (good preview size/quality balance)
3. **Rationale**: Frontend uses thumbnails for gallery view

---

## Edge Cases

### Large Response Size
- **Scenario**: fal.ai returns > 10MB image
- **Action**: Raise `ValueError`, fail generation
- **User Impact**: "Generation failed" error

### Network Timeout
- **Scenario**: fal.ai API or image download times out
- **Action**: Retry up to 3 times with exponential backoff
- **User Impact**: Slightly longer wait, transparent retry

### Concurrent Limit Reached
- **Scenario**: All 3 semaphore slots in use
- **Action**: Wait for slot to free up (automatic via asyncio)
- **User Impact**: None (transparent queuing)

---

## Error Handling

### FAL_KEY Missing or Invalid
- **Symptom**: `fal_client` auth error
- **Fix**: Explicitly set `os.environ["FAL_KEY"]` before import
- **Location**: Line 15-16 of `image_gen.py`

### Image Too Large
- **Symptom**: Downloaded image > 10MB
- **Action**: Raise `ValueError` with explicit message
- **Propagation**: Caught by router, returns 500 with user-facing message

### PIL Processing Error
- **Symptom**: Image corrupt or unsupported format
- **Action**: Raise exception, fail generation
- **User Impact**: "Generation failed, please try again"

---

## Performance Requirements

- **Single Image Generation**: 5-10 seconds (depends on fal.ai load)
- **8-Page Book (concurrent)**: ~30-60 seconds total
- **Line Art Processing**: < 1 second per image
- **Thumbnail Creation**: < 0.5 seconds per image
- **Total Pipeline SLA**: < 90 seconds for 8-page book

---

## Constants

| Constant | Value | Rationale |
|----------|-------|-----------|
| `PRINT_DPI` | 300 | Professional print standard |
| `LETTER_WIDTH_PX` | 2550 | 8.5" × 300 DPI |
| `LETTER_HEIGHT_PX` | 3300 | 11" × 300 DPI |
| `THUMBNAIL_SIZE` | 400×518 | US Letter aspect ratio |
| `THRESHOLD_BINARY` | 128 | 50% gray threshold for B&W |
| `MAX_CONCURRENT_IMAGES` | 3 | Balance speed vs memory |
| `MAX_IMAGE_BYTES` | 10MB | Prevent abnormal responses |

---

## Dependencies

- `fal_client` for fal.ai API
- `httpx` for async HTTP downloads
- `PIL` (Pillow) for image processing
- `tenacity` for retry logic
- `app.config.get_settings()` for `fal_key` and `fal_model`

---

## Testing Checklist

- [ ] Generate single image with valid prompt
- [ ] Test concurrent generation (8 scenes)
- [ ] Verify binary threshold produces true #FFFFFF white
- [ ] Verify upscaled image is 2550×3300 at 300 DPI
- [ ] Test retry logic with simulated network error
- [ ] Test rejection of > 10MB response
- [ ] Verify thumbnail creation and JPEG quality

---

## Maintenance Notes

### When to Adjust Concurrency
- ✏️ Memory usage too high → Reduce `MAX_CONCURRENT_IMAGES`
- ✏️ Generation too slow → Increase (if memory allows)

### When to Adjust Threshold
- ✏️ Images too dark → Increase `THRESHOLD_BINARY` (more white)
- ✏️ Lost detail → Decrease `THRESHOLD_BINARY` (more black)
- 🎯 Current value (128) is optimal for most use cases

### When to Update Model
- ✏️ fal.ai releases better line art model
- ✏️ Change `settings.fal_model` in `.env`
- ✏️ Test thoroughly before production

---

## Related SOPs

- [Scene Planning](scene_planning.md) — Generates prompts for this service
- [PDF Pipeline](pdf_pipeline.md) — Consumes image_bytes output
- [Storage](storage.md) — Uploads generated images to R2
- [Content Safety](content_safety.md) — Validates prompts before generation
