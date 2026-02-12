# 🔍 TailorMade — Findings & Research Log

**Created**: 2026-02-12  
**Purpose**: Document discoveries, constraints, and research findings during development

---

## 📚 Initial Project Analysis (2026-02-12)

### Technology Stack Discovery

**Frontend:**
- Vue 3 with TypeScript and Composition API
- Vite as build tool
- Tailwind CSS + DaisyUI for styling (partially replaced with custom brutalist design)
- Pinia for state management
- Axios for HTTP client with interceptors

**Backend:**
- FastAPI (Python 3.12) with async/await
- uv for dependency management
- Pydantic for data validation
- Firebase Admin SDK for auth and database
- WeasyPrint for PDF generation (requires libpango system dependency)

### External Dependencies

| Service | Purpose | Current Status | Notes |
|---------|---------|----------------|-------|
| Firebase Auth | User authentication | ✅ Working | Requires COOP header fix in Vite |
| Firebase Firestore | NoSQL database | ✅ Working | Stores users, books, usage data |
| Cloudflare R2 | Object storage | ✅ Working | Zero egress fees vs Firebase Storage |
| fal.ai | AI image generation | ✅ Working | Uses `fal-ai/flux/dev` model |
| Anthropic Claude | Content safety | ⚠️ Fallback mode | Haiku model, credit issues noted |
| WeasyPrint | PDF generation | ✅ Working | Requires `brew install pango` on macOS |

### Known Issues & Fixes

1. **Google Sign-In COOP Error**
   - **Issue**: Cross-Origin-Opener-Policy blocked OAuth popup
   - **Fix**: Added `Cross-Origin-Opener-Policy: same-origin-allow-popups` to `vite.config.ts`
   - **Location**: `frontend/vite.config.ts`

2. **Firebase Service Account Loading**
   - **Issue**: Backend crashes if `firebase-service-account.json` missing
   - **Fix**: Graceful degradation in `main.py` startup
   - **Location**: `backend/app/main.py`

3. **Rate Limiting Over-Counting**
   - **Issue**: Failed generation attempts consumed daily quota
   - **Fix**: Increment usage counter **only after** successful generation
   - **Location**: `backend/app/middleware/rate_limit.py`

4. **Anthropic API 500 Errors**
   - **Issue**: No credits in account causing content filter to fail
   - **Fix**: Fallback to keyword-only filtering
   - **Location**: `backend/app/services/content_filter.py`

5. **FAL API Authentication**
   - **Issue**: `fal-client` not finding credentials from environment
   - **Fix**: Explicitly set `os.environ["FAL_KEY"]` before import
   - **Location**: `backend/app/services/image_gen.py`

6. **WeasyPrint Import Crash**
   - **Issue**: Missing `libpango` system library causes startup failure
   - **Fix**: Lazy-load WeasyPrint only when PDF generation requested
   - **Location**: `backend/app/services/pdf_builder.py`

### Design System Research

**Brand Identity:**
- Colors: Black (`#000000`) + Lime Green (`#C5F82A`)
- Aesthetic: Brutalist (sharp edges, no rounded corners)
- Typography: Inter font family from Google Fonts

**UI Components:**
- Custom `KidButton` component with bright colors and large touch targets
- `AppNavbar` with auth state management
- Studio view with canvas editing (Phase 2)

### Content Safety Research

**Two-Layer Approach:**

1. **Layer 1: Keyword Blocklist**
   - Instant rejection for violence, weapons, inappropriate terms
   - Zero API cost
   - Deterministic

2. **Layer 2: Semantic Analysis**
   - Claude Haiku API for nuanced understanding
   - Handles edge cases (pirates, dinosaurs are OK)
   - Falls back to Layer 1 if API unavailable

**Age-Appropriate Complexity:**
- 4-6 years: Simple shapes, thick lines, minimal detail
- 7-9 years: Moderate complexity, recognizable objects
- 10-12 years: Detailed scenes, intricate patterns

---

## 🏗️ Architecture Discoveries

### Generation Pipeline (8 Steps)

1. **Content Safety Check** (2 seconds)
   - Keyword filter (instant)
   - Semantic check via Claude (if available)

2. **Scene Planning** (< 1 second)
   - Deterministic logic based on age range and theme
   - No AI cost

3. **Image Generation** (30-60 seconds)
   - Concurrent API calls to fal.ai
   - 8 pages generated in parallel
   - Uses `fal-ai/flux/dev` model

4. **Line Art Cleanup** (< 5 seconds)
   - Convert to grayscale
   - Binary threshold to pure B&W
   - Ensures #FFFFFF white for bucket fill tools

5. **PDF Compilation** (< 5 seconds)
   - WeasyPrint HTML→PDF conversion
   - US Letter size (8.5" x 11")
   - 300 DPI for print quality

6. **R2 Upload** (5-10 seconds)
   - Upload all PNGs
   - Upload final PDF
   - Generate public URLs

7. **Firestore Persistence** (< 1 second)
   - Save book metadata
   - Update user usage stats

8. **Response** (instant)
   - Return `BookResponse` with URLs to frontend

**Total SLA**: < 90 seconds for 8-page book

### State Management

**Frontend (Pinia):**
- `authStore`: User authentication state, Google Sign-In
- `drawingStore`: Book generation state, image URLs, download handling

**Backend (Firestore):**
- `users` collection: User profiles, subscription tier, total books
- `books` collection: Book metadata, generation timestamps, prompts
- `usage` subcollection: Daily usage tracking, rate limit enforcement

### Error Handling Strategy

**Graceful Degradation:**
- Missing dependencies → Log warning, delayed failure
- API failures → Fallback to simpler methods
- Rate limits → Clear user-facing messages

**User-Facing Messages:**
- Never expose stack traces
- Provide actionable next steps
- Log full errors server-side for debugging

---

## 🔬 Research Tasks (Pending)

### GitHub Research
- [ ] Search for AI-powered content generation pipelines
- [ ] Review image-to-image transformation examples
- [ ] Find coloring book line art extraction techniques
- [ ] Investigate concurrent API request patterns in Python

### Best Practices
- [ ] Research COPPA compliance for children's apps
- [ ] Review accessibility standards (WCAG AA) for kid-friendly UIs
- [ ] Investigate PDF optimization techniques (file size reduction)
- [ ] Study rate limiting patterns for public APIs

### Alternative Technologies
- [ ] Evaluate Puppeteer vs WeasyPrint for PDF generation
- [ ] Compare fal.ai vs Replicate vs Stability AI for image generation
- [ ] Research Firebase alternatives (Supabase, Appwrite)
- [ ] Investigate Cloudflare Images for on-the-fly transformations

---

## 📊 Performance Benchmarks

### Current Performance (Estimated)

| Operation | Time | Notes |
|-----------|------|-------|
| Content Safety | 2s | With Anthropic API; 0.1s with keyword only |
| Scene Planning | 0.5s | Pure Python logic |
| Image Generation (8 pages) | 45s | Concurrent requests to fal.ai |
| Line Art Processing | 3s | PIL transforms on 8 images |
| PDF Compilation | 4s | WeasyPrint HTML rendering |
| R2 Upload | 7s | 8 PNGs + 1 PDF |
| Firestore Write | 0.5s | Single document update |
| **Total** | ~62s | Fastest observed generation |

### Optimization Opportunities
- [ ] Cache common prompts to reduce generation time
- [ ] Pre-warm WeasyPrint process to reduce PDF compilation time
- [ ] Investigate streaming uploads to R2 for faster perceived performance
- [ ] Consider WebP format for faster uploads (convert to PNG client-side if needed)

---

## 🔒 Security Constraints

### Secrets Management
- ❌ **Never commit** `.env` files
- ✅ Service account JSON stored locally only
- ✅ API keys in environment variables
- ⚠️ Frontend `.env.local` contains **public** Firebase config (OK to expose)

### Rate Limiting Strategy
- 5 books/day for free tier
- Usage resets at midnight UTC
- Counter increments **only** on successful generation
- Future: Implement paid tiers with higher limits

### Content Moderation
- No user-uploaded images in Phase 1 (reduces abuse risk)
- All prompts logged for audit trail
- Manual review queue for flagged content (future feature)

---

## 📝 Documentation Gaps

### Missing Documentation
- [ ] API integration guide for third-party developers
- [ ] Deployment runbook (environment setup, domain configuration)
- [ ] Incident response playbook
- [ ] User onboarding guide (how to create your first book)

### Incomplete SOPs
- [ ] No formal SOP for authentication flow
- [ ] No formal SOP for rate limiting reset logic
- [ ] No formal SOP for error recovery procedures

---

## 🔄 Update History

### 2026-02-12
- Initial findings log created
- Documented current technology stack
- Cataloged all known issues and fixes
- Identified research tasks and documentation gaps
