# Project Overview: TailorMade Coloring Book

**Current Status**: ✅ Operational
**Last Updated**: Feb 11, 2026

## 🎯 Goal
An AI-powered application that generates personalized coloring books for children. Users describe a story or theme, and the app generates consistent characters, plans scenes, creates line art suitable for coloring, and compiles a print-ready PDF.

## 🏗 Technology Stack

| Component | Tech | Details |
|---|---|---|
| **Frontend** | Vue 3 + Vite | TypeScript, Composition API, `<script setup>` |
| **State** | Pinia | Stores: `auth` (User state), `drawing` (Book/Image state) |
| **Styling** | Tailwind CSS + DaisyUI | Custom "Kid" theme, responsive design |
| **Backend** | FastAPI (Python 3.12) | Async endpoints, Pydantic validation |
| **Database** | Firebase Firestore | Collections: `users`, `books`, `usage` |
| **Auth** | Firebase Auth | Google Sign-In (Frontend), Bearer token verification (Backend) |
| **Storage** | Cloudflare R2 | Zero-egress fee storage for generated images & PDFs |
| **AI (Image)** | fal.ai | `fal-ai/flux/dev` model for image generation |
| **AI (Text)** | Anthropic (Claude) | `claude-haiku` for content safety & scene planning |
| **PDF** | WeasyPrint | HTML/CSS → PDF conversion (requires `pango`) |

## 📂 Project Structure

```
tailormade/
├── backend/
│   ├── app/
│   │   ├── middleware/      # Auth & Rate Limiting (fixed: counting only success)
│   │   ├── models/          # Pydantic schemas (BookRequest, BookResponse)
│   │   ├── routers/         # /api/v1/ endpoints (auth, books, photos)
│   │   ├── services/        # Core logic (image_gen, pdf_builder, firebase, storage)
│   │   ├── config.py        # Settings via pydantic-settings
│   │   └── main.py          # App entry point (lifespan handler)
│   └── .env                 # Secrets (FAL_KEY, ANTHROPIC_API_KEY, etc.)
│
└── frontend/
    ├── src/
    │   ├── api/             # Axios client + Interceptors
    │   ├── assets/          # Global styles (fonts, tailwind directives)
    │   ├── components/      # Vue components (KidButton, AppNavbar, etc.)
    │   ├── composables/     # Logic (useGeneration, useCanvas)
    │   ├── store/           # Pinia stores
    │   ├── views/           # Pages (Home, Create, Studio, Gallery)
    │   └── App.vue          # Root component
    ├── .env.local           # Public env vars (VITE_FIREBASE_*)
    └── vite.config.ts       # Proxy & COOP header config
```

## 🔄 Key Workflows

### 1. User Authentication
1. **Frontend**: `useAuthStore` calls `signInWithPopup(googleProvider)`.
   - **Fix**: Added `Cross-Origin-Opener-Policy: same-origin-allow-popups` to `vite.config.ts` to allow popup communication.
2. **Token Exchange**: Frontend gets Firebase ID Token via `auth.getIdToken()`.
3. **API Requests**: Axios interceptor (`client.ts`) attaches `Authorization: Bearer <token>`.
4. **Verification**: Backend `get_current_user` (`middleware/auth.py`) verifies token with Firebase Admin SDK.
   - **Fix**: Graceful degradation in `main.py` if `firebase-service-account.json` is missing.

### 2. Book Generation Pipeline (`/api/v1/books/generate`)
1. **Content Safety**: Checks prompt for unsafe content.
   - **Fix**: `content_filter.py` falls back to keyword-only check if Anthropic API (Layer 2) fails/no credits.
2. **Scene Planning**: Deterministic logic plans pages based on theme/age.
3. **Image Generation**: Concurrent calls to `fal.ai`.
   - **Fix**: `image_gen.py` explicitly sets `os.environ["FAL_KEY"]` from settings to ensure auth works.
4. **Post-Processing**: Converts images to grayscale, thresholds to binary B&W for easy coloring.
5. **PDF Building**: `weasyprint` compiles pages + cover into PDF.
   - **Fix**: Lazy-loaded inner imports in `pdf_builder.py` to prevent crash if system libraries (`libpango`) are missing at startup.
6. **Storage**: Uploads PNGs and PDF to Cloudflare R2.
7. **Persistence**: Saves metadata to Firestore.
8. **Rate Limiting**: Checks `users/UID/usage` in Firestore.
   - **Fix**: Only increments usage count *after* successful generation.

## 🛠 Setup & Configuration

### Required Environment Variables

**Backend (`.env`):**
- `FAL_KEY` (AI Image Gen)
- `ANTHROPIC_API_KEY` (AI Text/Safety)
- `FIREBASE_SERVICE_ACCOUNT_PATH` (Path to JSON)
- `FIREBASE_PROJECT_ID`
- `R2_*` (Cloudflare Storage creds)

**Frontend (`.env.local`):**
- `VITE_FIREBASE_*` (Public config)

### Running the Project

**Terminal 1 (Backend):**
```bash
cd backend
# Backend runs on port 8000
uv run uvicorn app.main:app --reload --port 8000
```
*Health Check*: http://localhost:8000/health

**Terminal 2 (Frontend):**
```bash
cd frontend
# Frontend runs on port 5173, proxies /api -> localhost:8000
pnpm run dev
```
*App Access*: http://localhost:5173

## 🐛 Recent Troubleshooting Summary

1. **Backend Crash (System Lib)**: Backend wouldn't start due to missing `libpango`.
   - *Resolution*: Lazy-loaded WeasyPrint in `pdf_builder.py`.
2. **Backend Crash (Firebase)**: Missing `firebase-service-account.json`.
   - *Resolution*: Added try/except in `main.py` startup + updated `.env` path to point to user's downloaded file.
3. **Authetication (COOP)**: Google Sign-In blocked by cross-origin policy.
   - *Resolution*: Added headers to `vite.config.ts`.
4. **Rate Limit 429**: Failed attempts consumed daily quota.
   - *Resolution*: Refactored `rate_limit.py`, bumped limit to 5.
5. **Anthropic 500**: API credit balance empty.
   - *Resolution*: Added fallback in `content_filter.py`.
6. **FAL Auth 500**: `fal-client` not finding credentials.
   - *Resolution*: Explicitly set `os.environ["FAL_KEY"]` in `image_gen.py`.
