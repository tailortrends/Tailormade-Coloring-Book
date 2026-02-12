# 🛠️ TailorMade Verification Tools

This directory contains scripts to verify API connectivity and system health for the TailorMade project.

---

## Scripts Overview

### Individual Verification Scripts

| Script | Purpose | Tests |
|--------|---------|-------|
| `verify_firebase.py` | Firebase Auth + Firestore | Service account, Auth API, Firestore read/write, Collections existence |
| `verify_r2.py` | Cloudflare R2 Storage | Connection, Upload, Download, Public URL access, Cleanup |
| `verify_fal.py` | fal.ai Image Generation | API key, Model access, Image generation, Response format |
| `verify_anthropic.py` | Anthropic Claude API | API key, Content safety checks, Fallback behavior |

### Master Health Check

| Script | Purpose |
|--------|---------|
| `health_check.py` | Runs all verification scripts and provides comprehensive system status |

---

## Usage

### Run Individual Tests

Test a specific service:

```bash
# Firebase
python tools/verify_firebase.py

# Cloudflare R2
python tools/verify_r2.py

# fal.ai
python tools/verify_fal.py

# Anthropic Claude
python tools/verify_anthropic.py
```

### Run Complete Health Check

Test all services at once:

```bash
python tools/health_check.py
```

---

## Prerequisites

### Environment Variables

All scripts require proper configuration in `backend/.env`:

```env
# Firebase
# (Service account JSON file should be in project root)

# Cloudflare R2
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET_NAME=your_bucket_name
R2_PUBLIC_URL=https://your-domain.com

# fal.ai
FAL_KEY=your_fal_api_key

# Anthropic (optional - falls back to keyword filtering)
ANTHROPIC_API_KEY=your_anthropic_key
```

### Python Dependencies

Install required packages:

```bash
cd backend
pip install -r requirements.txt
```

Or with uv:

```bash
cd backend
uv sync
```

---

## Exit Codes

All scripts use standard exit codes:

- **0**: All tests passed ✅
- **1**: Some tests failed ❌

Use in CI/CD:

```bash
python tools/health_check.py
if [ $? -eq 0 ]; then
    echo "System healthy, proceeding with deployment"
else
    echo "Health check failed, aborting"
    exit 1
fi
```

---

## Test Details

### Firebase Tests
1. ✅ Service account credentials valid
2. ✅ Firebase Auth API accessible
3. ✅ Firestore read/write operations
4. ✅ Expected collections exist (`users`, `books`)
5. ✅ Cleanup of test data

### R2 Tests
1. ✅ Bucket connection successful
2. ✅ File upload works
3. ✅ File download works
4. ✅ Public URL accessible
5. ✅ Cleanup successful

### fal.ai Tests
1. ✅ API key configured
2. ✅ Model access verified
3. ✅ Image generation successful
4. ✅ Response format valid
5. ✅ Image URL accessible

### Anthropic Tests
1. ✅ API key configured (or fallback mode)
2. ✅ Content safety check works (if key present)
3. ✅ Safe content passes
4. ✅ Unsafe content blocked
5. ✅ Fallback filtering functional

---

## Troubleshooting

### Firebase Errors

**Error**: `Service account file not found`
- **Solution**: Ensure `tailormade-coloring-book-firebase-adminsdk-*.json` is in project root

**Error**: `Permission denied`
- **Solution**: Check Firebase project permissions for service account

### R2 Errors

**Error**: `Bucket does not exist`
- **Solution**: Verify `R2_BUCKET_NAME` in `.env` matches actual bucket

**Error**: `Access denied`
- **Solution**: Check R2 API credentials have read/write permissions

### fal.ai Errors

**Error**: `fal_client not installed`
- **Solution**: Run `pip install fal-client`

**Error**: `Generation failed`
- **Solution**: Check `FAL_KEY` is valid and has credits

### Anthropic Errors

**Error**: `API credits exhausted`
- **Solution**: This is expected, system will use fallback mode

**Error**: `anthropic package not installed`
- **Solution**: Run `pip install anthropic`

---

## CI/CD Integration

Add to GitHub Actions workflow:

```yaml
name: Health Check

on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run health check
        env:
          FAL_KEY: ${{ secrets.FAL_KEY }}
          R2_ACCESS_KEY_ID: ${{ secrets.R2_ACCESS_KEY_ID }}
          R2_SECRET_ACCESS_KEY: ${{ secrets.R2_SECRET_ACCESS_KEY }}
        run: python tools/health_check.py
```

---

## Maintenance

### Adding New Verification Scripts

1. Create new script in `tools/` directory
2. Follow existing script structure:
   - Main verification functions
   - Summary output
   - Exit codes (0 = pass, 1 = fail)
3. Add to `health_check.py` checks list
4. Update this README

### Test Data Cleanup

All scripts clean up after themselves:
- Firebase: Deletes test documents from `_health_check` collection
- R2: Deletes uploaded test files from `_health_check/` prefix
- fal.ai: No cleanup needed (ephemeral API response)
- Anthropic: No cleanup needed (stateless API)

---

## Related Documentation

- [authentication.md](../architecture/authentication.md) — Firebase Auth SOP
- [storage.md](../architecture/storage.md) — R2 Storage SOP
- [image_generation.md](../architecture/image_generation.md) — fal.ai SOP
- [content_safety.md](../architecture/content_safety.md) — Anthropic SOP

---

**Last Updated**: 2026-02-12  
**Phase**: 2 (Link - Connectivity Verification)
