# System Workflow Mapping

**Layer**: 2 (Navigation Decision Making)  
**Purpose**: Map B.L.A.S.T. layers to existing TailorMade codebase  
**Last Updated**: 2026-02-12

---

## Overview

The TailorMade project follows the **A.N.T. 3-Layer Architecture**:

- **Layer 1 (Architecture)**: SOPs in `architecture/` directory
- **Layer 2 (Navigation)**: This document + request orchestration in routers
- **Layer 3 (Tools)**: Deterministic services in `backend/app/services/`

---

## Complete Book Generation Workflow

### User Request Flow

```
Frontend (Vue 3)
    ↓
API Request: POST /api/v1/books/generate
    ↓
Layer 2: Router (books.py) — Orchestration
    ↓
├─→ Layer 3: Authentication (auth.py)
│   └─→ Layer 1 SOP: authentication.md
├─→ Layer 3: Rate Limiting (rate_limit.py)
│   └─→ Layer 1 SOP: rate_limiting.md
├─→ Layer 3: Content Safety (content_filter.py)
│   └─→ Layer 1 SOP: content_safety.md
├─→ Layer 3: Scene Planning (scene_planner.py)
│   └─→ Layer 1 SOP: scene_planning.md
├─→ Layer 3: Image Generation (image_gen.py)
│   └─→ Layer 1 SOP: image_generation.md
├─→ Layer 3: PDF Building (pdf_builder.py)
│   └─→ Layer 1 SOP: pdf_pipeline.md
├─→ Layer 3: Storage Upload (storage.py)
│   └─→ Layer 1 SOP: storage.md
└─→ Layer 3: Database Persistence (firebase_db.py)
    └─→ Layer 1 SOP: firebase_db.md
```

---

## Layer 1: Architecture (SOPs)

**Purpose**: Define business logic, edge cases, and error handling.

### Existing SOPs

| SOP File | Service | Purpose |
|----------|---------|---------|
| `authentication.md` | `middleware/auth.py` | Firebase token verification |
| `rate_limiting.md` | `middleware/rate_limit.py` | Tier-based daily limits |
| `content_safety.md` | `services/content_filter.py` | Two-layer content filtering |
| `scene_planning.md` | `services/scene_planner.py` | Deterministic story arc generation |
| `image_generation.md` | `services/image_gen.py` | fal.ai integration + post-processing |
| `pdf_pipeline.md` | `services/pdf_builder.py` | WeasyPrint PDF compilation |
| `storage.md` | `services/storage.py` | Cloudflare R2 uploads |
| `firebase_db.md` | `services/firebase_db.py` | Firestore operations |

### Golden Rule

**Update the SOP BEFORE changing the code.**

If a bug fix or feature requires new logic, document it in the SOP first. This ensures:
- ✅ Behavior is well-defined
- ✅ Edge cases are considered
- ✅ Future developers understand why it works this way

---

## Layer 2: Navigation (Decision Making)

**Purpose**: Route requests through Layer 3 tools in the correct order.

### Current Router: `backend/app/routers/books.py`

This router implements Layer 2 decision-making:

```python
@router.post("/generate")
async def generate_book(
    request: BookRequest,
    user: FirebaseUser = Depends(check_rate_limit),  # Layer 3: Auth + Rate Limit
):
    # STEP 1: Content Safety (Layer 3)
    safe, reason = await is_content_safe(request.theme)
    if not safe:
        raise HTTPException(status_code=400, detail=reason)
    
    # STEP 2: Scene Planning (Layer 3)
    scenes = plan_scenes(
        theme=request.theme,
        page_count=request.page_count,
        art_style=request.art_style,
        age_range=request.age_range,
    )
    
    # STEP 3: Image Generation (Layer 3)
    pages = await generate_pages(scenes)
    
    # STEP 4: PDF Building (Layer 3)
    pdf_bytes = build_pdf(title=request.theme, pages=pages)
    
    # STEP 5: Upload to Storage (Layer 3)
    pdf_url = upload_bytes(pdf_bytes, key=build_key(...), content_type="application/pdf")
    for page in pages:
        page["image_url"] = upload_bytes(page["image_bytes"], ...)
    
    # STEP 6: Persist to Database (Layer 3)
    book_response = BookResponse(...)
    save_book(book_response)
    
    # STEP 7: Increment Usage (Layer 3)
    increment_usage(user.uid)
    
    return book_response
```

### Decision Points in Layer 2

1. **Authentication Required?** → Yes, use `check_rate_limit` dependency
2. **Content Safe?** → If not, return 400 immediately
3. **Generation Failed?** → Don't increment usage counter
4. **Upload Failed?** → Propagate error, mark book as "failed"

---

## Layer 3: Tools (Execution)

**Purpose**: Atomic, testable, deterministic operations.

### Service Mapping

| Service | Functions | Inputs | Outputs | SOP |
|---------|-----------|--------|---------|-----|
| **auth.py** | `get_current_user()` | Bearer token | FirebaseUser | authentication.md |
| **rate_limit.py** | `check_rate_limit()`, `increment_usage()` | FirebaseUser, uid | User or 429 | rate_limiting.md |
| **content_filter.py** | `is_content_safe()` | text | (is_safe, reason) | content_safety.md |
| **scene_planner.py** | `plan_scenes()` | theme, page_count, art_style, age_range | scenes list | scene_planning.md |
| **image_gen.py** | `generate_pages()` | scenes | scenes + image_bytes | image_generation.md |
| **pdf_builder.py** | `build_pdf()` | title, pages | pdf_bytes | pdf_pipeline.md |
| **storage.py** | `upload_bytes()`, `build_key()` | bytes, key, content_type | public_url | storage.md |
| **firebase_db.py** | `save_book()`, `get_user_books()`, `get_book()` | book data, uid | None or list | firebase_db.md |

### Tool Principles

Each tool must:
- ✅ Be **atomic** (one clear purpose)
- ✅ Be **testable** (unit tests possible)
- ✅ Be **deterministic** (same inputs → same outputs)
- ✅ Use `.env` for configuration
- ✅ Use `.tmp/` for temporary files (where applicable)

---

## Frontend Architecture

### State Management (Pinia Stores)

**Auth Store** (`src/store/auth.ts`):
- Manages Firebase authentication state
- Handles Google Sign-In flow
- Provides ID token for API requests

**Drawing Store** (`src/store/drawing.ts`):
- Tracks book generation state
- Stores generated book data
- Manages download state

### API Client (`src/api/client.ts`)

- Axios instance with request interceptor
- Automatically attaches `Authorization: Bearer <token>` to all requests
- Base URL: `/api` (proxied to backend by Vite)

### Key Views

| View | Route | Purpose |
|------|-------|---------|
| Home | `/` | Landing page, CTA to create book |
| Create | `/create` | Book generation form |
| Gallery | `/gallery` | User's past books |
| Studio | `/studio` | Canvas editor (Phase 2) |

---

## Data Flow: User Creates Book

### Step-by-Step

1. **User fills form** on `/create` view
   - Theme, age range, art style, page count
   - Frontend stores draft in localStorage

2. **User clicks "Generate"**
   - `drawingStore.generateBook()` triggered
   - Axios POST to `/api/v1/books/generate`

3. **Backend processes** (Layer 2 orchestration)
   - Authenticate user (Layer 3: auth)
   - Check rate limit (Layer 3: rate_limit)
   - Validate content (Layer 3: content_safety)
   - Plan scenes (Layer 3: scene_planner)
   - Generate images (Layer 3: image_gen)
   - Build PDF (Layer 3: pdf_builder)
   - Upload to R2 (Layer 3: storage)
   - Save to Firestore (Layer 3: firebase_db)
   - Increment usage (Layer 3: rate_limit)

4. **Frontend receives response**
   - `BookResponse` with `pdf_url` and page URLs
   - Store in `drawingStore`
   - Navigate to success view

5. **User downloads PDF**
   - Click download button
   - Browser fetches from R2 public URL
   - No authentication needed (public link)

---

## Error Flow Example

### Scenario: Content Safety Failure

```
User submits theme: "violent battle"
    ↓
Layer 2: books.py calls content_filter.is_content_safe()
    ↓
Layer 3: content_filter.py
    ├─→ Layer 1 Check (keyword blocklist)
    │   └─→ "violence" detected → BLOCK
    └─→ Returns: (False, "Content contains inappropriate term: 'violence'")
    ↓
Layer 2: Raises HTTPException(400, detail="Content contains inappropriate term...")
    ↓
Frontend: Displays error toast
    ↓
User: Revises theme to "friendly adventure"
    ↓
SUCCESS ✅
```

---

## Self-Annealing Example

### Scenario: Anthropic API Failure

**Before Fix**:
- Anthropic API runs out of credits
- `is_content_safe()` crashes
- User sees 500 error
- Book generation fails

**Self-Annealing Process**:

1. ❌ **Error Detected**: Anthropic API returns 500
2. 🔍 **Analyze**: Read stack trace → API credit exhaustion
3. 🔧 **Patch**: Add fallback to `content_filter.py`:
   ```python
   try:
       return await _layer2_check(text)
   except Exception:
       return (True, "")  # Fall back to Layer 1 only
   ```
4. ✅ **Test**: Simulate API failure → fallback works
5. 📝 **Update SOP**: Document fallback behavior in `content_safety.md`

**Result**: System self-heals, never fails again for this reason.

---

## .tmp/ Directory Usage

**Purpose**: Store intermediate files that can be deleted.

**Not Yet Implemented**, but should be used for:
- ❌ Downloaded fal.ai raw images (before cleaning)
- ❌ Temporary PDF files during WeasyPrint compilation
- ❌ Debug logs from generation pipeline

**Future Work**: Implement tempfile usage in all services.

---

## Monitoring & Observability

### Logging Pattern

All services use Python's `logging` module:

```python
logger = logging.getLogger(__name__)

# Info: Normal operations
logger.info("book_generated book_id=%s pages=%d", book_id, page_count)

# Warning: Degraded but functional
logger.warning("anthropic_api_unavailable error=%s", exc)

# Error: Unexpected failures
logger.error("pdf_generation_failed book_id=%s", book_id, exc_info=True)
```

### Key Metrics to Track
- ✅ Books generated per day
- ✅ Average generation time
- ✅ 429 rate limit errors (by tier)
- ✅ Content safety blocks (Layer 1 vs Layer 2)
- ✅ fal.ai API errors
- ✅ R2 upload failures

---

## Phase 2 Extensions

### Photo Upload Feature

**New Workflow**:
1. User uploads photo of child
2. `POST /api/v1/photos/upload` → Store in R2
3. Pass photo URL to fal.ai as img2img reference
4. Generate character-likeness coloring pages

**New SOPs Needed**:
- `photo_upload.md` — Client-side image resize, validation
- `img2img_pipeline.md` — fal.ai img2img integration
- `photo_safety.md` — Ensure no inappropriate photos uploaded

---

## Related Documents

- **Project Constitution**: `gemini.md`
- **Task Plan**: `task_plan.md`
- **Findings Log**: `findings.md`
- **Progress Log**: `progress.md`
- **All SOPs**: `architecture/*.md`
