# TailorMade Coloring Book 🎨

AI-powered personalized coloring book generator for kids.  
Describe a story → AI draws the pages → Print and color.

**GitHub**: [tailortrends/Tailormade-Coloring-Book](https://github.com/tailortrends/Tailormade-Coloring-Book)

---

## Quick Start

```bash
# Clone repository
git clone https://github.com/tailortrends/Tailormade-Coloring-Book.git
cd Tailormade-Coloring-Book

# Follow setup instructions below for backend and frontend
```

---

## Project Structure

```
tailormade/
├── backend/          # FastAPI + uv (Python 3.11+)
└── frontend/         # Vue 3 + Vite + Tailwind + DaisyUI
```

---

## Backend Setup

```bash
cd backend

# 0. Install system dependency (macOS — required by WeasyPrint)
brew install pango

# 1. Install all dependencies
uv sync
uv sync --extra dev

# 2. Configure environment
cp .env.example .env
# Edit .env — minimum required: FAL_KEY, ANTHROPIC_API_KEY, Firebase + R2 credentials

# 3. Add Firebase service account
# Firebase Console → Project Settings → Service Accounts → Generate new private key
# Save as: backend/firebase-service-account.json

# 4. Run dev server
uv run uvicorn app.main:app --reload --port 8000

# Or press F5 in VSCode (uses .vscode/launch.json)
```

API available at:
- http://localhost:8000/docs — Swagger UI
- http://localhost:8000/health — Health check

### Run Tests
```bash
cd backend
uv run pytest tests/ -v
```

---

## Frontend Setup

```bash
cd frontend

# 1. Install dependencies
pnpm install

# 2. Configure environment
cp .env.example .env.local
# Fill in Firebase public config values from Firebase Console

# 3. Run dev server (proxies /api → localhost:8000)
pnpm dev
```

Frontend available at http://localhost:5173

### Frontend Scripts
```bash
pnpm dev          # Dev server
pnpm build        # Type-check + production build
pnpm type-check   # TypeScript check only
pnpm lint         # ESLint with auto-fix
```

---

## Environment Variables Quick Reference

### Backend (`backend/.env`)
| Variable | Where to get it |
|---|---|
| `FAL_KEY` | https://fal.ai/dashboard/keys |
| `ANTHROPIC_API_KEY` | https://console.anthropic.com |
| `FIREBASE_SERVICE_ACCOUNT_PATH` | Downloaded JSON file path |
| `FIREBASE_PROJECT_ID` | Firebase Console → Project Settings |
| `R2_ACCOUNT_ID` | Cloudflare Dashboard → R2 |
| `R2_ACCESS_KEY_ID` | Cloudflare → R2 → Manage API Tokens |
| `R2_SECRET_ACCESS_KEY` | Same as above |
| `R2_BUCKET_NAME` | Your R2 bucket name |
| `R2_PUBLIC_URL` | R2 bucket public URL |

### Frontend (`frontend/.env.local`)
All `VITE_FIREBASE_*` values from Firebase Console → Project Settings → General → Your apps.

---

## Key Architecture Decisions

- **No WebSockets** — polling is simpler and reliable enough for AI generation jobs
- **Cloudflare R2** over Firebase Storage — zero egress fees for PDF downloads
- **Two-layer content filter** — instant keyword blocklist + Claude Haiku semantic check
- **Client-side image resize** (`useImagePipeline.ts`) — never uploads raw 4K photos
- **localStorage draft** (`useGeneration.ts`) — kids don't lose progress on page refresh
- **Binary threshold post-processing** — ensures white is true #FFFFFF for bucket fill
- **`/api/v1/` versioned routes** — breaking changes won't break existing clients

---

## Generation Pipeline (8 steps)

1. Content safety check (keyword + Claude Haiku)
2. Plan scenes — zero API cost, pure logic
3. Generate all page images concurrently via fal.ai
4. Clean line art — binary threshold to true B&W
5. Build print-ready PDF via WeasyPrint (US Letter, 300 DPI)
6. Upload all assets to Cloudflare R2
7. Persist metadata to Firestore
8. Return `BookResponse` to frontend

## Phase 2 (Not yet built)
- Photo upload → img2img pipeline for character likenesses (`/api/v1/photos/upload`)

---

## Contributing

This project follows the B.L.A.S.T. methodology for structured development:

1. **Phase 0 (Baseline)**: ✅ Complete - Documentation and architecture SOPs
2. **Phase 1 (Link)**: ✅ Complete - Research and data schemas
3. **Phase 2 (Architect)**: ✅ Complete - API verification scripts
4. **Phase 3 (Stylize)**: In Progress - Unit tests and refinements
5. **Phase 4 (Trigger)**: Planned - Deployment and automation

See [`task_plan.md`](task_plan.md) for full project roadmap.

### Development Resources

- **Architecture SOPs**: [`architecture/`](architecture/) - Detailed service documentation
- **Verification Scripts**: [`tools/`](tools/) - Health check and API testing
- **Phase Summaries**: `PHASE_*_COMPLETE.md` - Completion reports
- **Project Constitution**: [`gemini.md`](gemini.md) - Data schemas and rules

---

## License

Proprietary - All Rights Reserved

---

## Contact

**Organization**: [tailortrends](https://github.com/tailortrends)  
**Repository**: [Tailormade-Coloring-Book](https://github.com/tailortrends/Tailormade-Coloring-Book)
