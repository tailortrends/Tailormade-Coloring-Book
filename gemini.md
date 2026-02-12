# 🧠 TailorMade Coloring Book — Project Constitution (gemini.md)

**Last Updated**: 2026-02-12  
**Status**: Active Development  
**System**: B.L.A.S.T. Framework (Blueprint, Link, Architect, Stylize, Trigger)

---

## 🎯 North Star

> **Generate personalized, print-ready coloring books for children through AI-powered image generation, ensuring consistent characters, appropriate content, and professional-quality output.**

---

## 📋 Data Schemas

### Input Schema: Book Generation Request

```json
{
  "theme": "string",           // Story/theme description
  "age_range": "4-6 | 7-9 | 10-12",
  "num_pages": "number",       // 4-12 pages
  "style_preference": "string" // Optional: "simple", "detailed", etc.
}
```

### Output Schema: Book Response

```json
{
  "book_id": "string",
  "status": "generating | completed | failed",
  "pdf_url": "string",          // R2 public URL
  "pages": [
    {
      "page_number": "number",
      "image_url": "string",    // R2 URL for individual PNG
      "prompt": "string",       // Generation prompt used
      "description": "string"   // Scene description
    }
  ],
  "metadata": {
    "created_at": "ISO8601",
    "user_id": "string",
    "total_pages": "number",
    "generation_time_seconds": "number"
  }
}
```

### User Schema (Firestore)

```json
{
  "uid": "string",
  "email": "string",
  "display_name": "string",
  "usage": {
    "books_generated_today": "number",
    "last_generation_date": "ISO8601",
    "total_books": "number"
  },
  "subscription_tier": "free | pro"
}
```

### Rate Limit Schema

```json
{
  "daily_limit": 5,
  "current_usage": "number",
  "reset_time": "ISO8601"
}
```

---

## 🔐 Security & Authentication

### Authentication Flow
1. **Frontend**: Google Sign-In via Firebase Auth
2. **Token**: ID Token retrieved via `auth.currentUser.getIdToken()`
3. **Transport**: Axios interceptor attaches `Authorization: Bearer <token>`
4. **Validation**: Backend verifies token using Firebase Admin SDK
5. **User Context**: Extracted `uid` and `email` used for authorization

### CORS & Security Headers
- **COOP**: `same-origin-allow-popups` (allows Google OAuth popup)
- **CSRF**: Not implemented (stateless API, token-based auth)
- **Rate Limiting**: 5 books/day per user (tracked in Firestore)

---

## 🏗️ Architectural Invariants

### Layer 1: Architecture (SOPs)
- All business logic must have a corresponding markdown SOP in `architecture/`
- SOPs must define: Goal, Inputs, Process, Edge Cases, Error Handling
- **Golden Rule**: Update the SOP **before** changing the code

### Layer 2: Navigation (Decision Making)
- The AI agent routes data between SOPs and Tools
- No complex business logic is performed by the AI directly
- AI calls deterministic tools in the correct sequence

### Layer 3: Tools (Execution)
- Python scripts in `backend/app/services/`
- All scripts must be atomic and testable
- Environment variables stored in `.env`
- Temporary files go to `.tmp/` (not implemented yet, using system temp)

---

## 🎨 Design System

### Brand Colors
- **Primary**: Black (`#000000`)
- **Accent**: Lime Green (`#C5F82A`)
- **Aesthetic**: Brutalist (sharp edges, no border radius)

### Typography
- **Font Family**: Inter (Google Fonts)
- **Headings**: Bold, uppercase for impact
- **Body**: Regular weight, high contrast

### UI Components
- **Buttons**: KidButton component (bright, large, accessible)
- **Forms**: High contrast, large touch targets
- **Navigation**: AppNavbar with user auth state
- **Canvas**: Studio view for editing generated images

---

## 🔗 Integration Points

### External Services

| Service | Purpose | Authentication | Status |
|---------|---------|----------------|--------|
| **Firebase Auth** | User authentication | Service account JSON | ✅ Active |
| **Firebase Firestore** | Data persistence | Service account JSON | ✅ Active |
| **Cloudflare R2** | Image/PDF storage | Access Key + Secret | ✅ Active |
| **fal.ai** | AI image generation | API Key (`FAL_KEY`) | ✅ Active |
| **Anthropic Claude** | Content safety filter | API Key (`ANTHROPIC_API_KEY`) | ⚠️ Fallback only |
| **WeasyPrint** | PDF generation | System library (`libpango`) | ✅ Active |

### API Endpoints

**Backend Base**: `http://localhost:8000/api/v1/`

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/health` | GET | Health check | No |
| `/auth/login` | POST | Token verification | Yes |
| `/books/generate` | POST | Generate coloring book | Yes |
| `/books/{book_id}` | GET | Retrieve book data | Yes |
| `/photos/upload` | POST | Upload reference photo | Yes (Phase 2) |

---

## 📊 Content Safety Rules

### Keyword Blocklist (Layer 1)
- Violence, weapons, inappropriate content
- Instant rejection if matched

### Semantic Check (Layer 2)
- Claude Haiku API call for nuanced safety
- Fallback to keyword-only if API fails or no credits
- **Never block valid children's content** (pirates, dinosaurs, etc.)

### Age Appropriateness
- 4-6: Simple shapes, minimal detail
- 7-9: Moderate complexity
- 10-12: Detailed scenes, intricate patterns

---

## ⚡ Performance Requirements

### Generation Pipeline SLA
- **Content Safety**: < 2 seconds
- **Scene Planning**: < 1 second (deterministic logic)
- **Image Generation**: 30-60 seconds (8 concurrent requests)
- **PDF Compilation**: < 5 seconds
- **Total Pipeline**: < 90 seconds for 8-page book

### Storage Optimization
- Images: PNG, optimized for print (300 DPI)
- Binary threshold ensures true B&W (no grays)
- PDF: US Letter size, WeasyPrint HTML template

---

## 🚨 Error Handling Protocols

### Graceful Degradation
1. **Missing Firebase Credentials**: Backend starts but logs warning
2. **Anthropic API Failure**: Falls back to keyword-only filter
3. **FAL_KEY Missing**: Explicit error with setup instructions
4. **WeasyPrint Import Error**: Lazy-loaded, only fails if PDF generation requested

### User-Facing Errors
- **429 Rate Limit**: "Daily limit reached. Try again tomorrow."
- **400 Unsafe Content**: "Theme not appropriate for children's content."
- **500 Generation Failure**: "Something went wrong. Please try again."

---

## 🛠️ Behavioral Rules

### DO
- ✅ Always validate input against schema
- ✅ Log all generation requests with timestamps
- ✅ Increment usage counter **only after successful generation**
- ✅ Store all prompts and metadata for debugging
- ✅ Use concurrent requests for image generation (faster)
- ✅ Lazy-load heavy dependencies (WeasyPrint)

### DO NOT
- ❌ Never trust user input without validation
- ❌ Never expose API keys in responses
- ❌ Never increment rate limit on failed requests
- ❌ Never skip content safety checks
- ❌ Never generate without user authentication
- ❌ Never store sensitive data in localStorage

---

## 📁 File Structure Reference

```
tailormade/
├── gemini.md              # THIS FILE - Project Constitution
├── task_plan.md           # B.L.A.S.T. phases and checklists
├── findings.md            # Research and discoveries
├── progress.md            # Work log and test results
├── architecture/          # Layer 1: SOPs (to be created)
│   ├── authentication.md
│   ├── image_generation.md
│   ├── content_safety.md
│   └── pdf_pipeline.md
├── .tmp/                  # Temporary files (to be created)
├── backend/
│   ├── .env              # Secrets (DO NOT COMMIT)
│   ├── app/
│   │   ├── services/     # Layer 3: Tools
│   │   ├── routers/      # API endpoints
│   │   ├── middleware/   # Auth & Rate Limiting
│   │   └── models/       # Pydantic schemas
│   └── tests/            # Unit & integration tests
└── frontend/
    ├── .env.local        # Public Firebase config
    └── src/
        ├── store/        # Pinia state management
        ├── api/          # Axios client
        ├── components/   # Vue components
        └── views/        # Pages
```

---

## 🔄 Change Log

### 2026-02-12: Initial B.L.A.S.T. Setup
- Created Project Constitution (`gemini.md`)
- Documented all data schemas
- Defined architectural invariants
- Established integration points and behavioral rules

### Previous Fixes (Pre-B.L.A.S.T.)
- Fixed Google Sign-In COOP header issue
- Implemented fallback for Anthropic API failures
- Corrected rate limiting to count only successful generations
- Added lazy loading for WeasyPrint to prevent startup crashes
- Explicit FAL_KEY environment variable setting

---

## 📝 Maintenance Notes

### When to Update This File
- ✏️ Schema changes (new fields, types, or endpoints)
- ✏️ New integration added (external service)
- ✏️ Architectural decision changes (e.g., switching from R2 to S3)
- ✏️ New behavioral rule discovered (e.g., "Always validate age_range")

### When NOT to Update This File
- ❌ Routine bug fixes (use `progress.md`)
- ❌ Temporary discoveries (use `findings.md`)
- ❌ Task-specific notes (use `task_plan.md`)

---

**This is the source of truth. All code must align with these principles.**
