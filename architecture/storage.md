# Storage SOP

**Layer**: 1 (Architecture)  
**Service**: `backend/app/services/storage.py`  
**Last Updated**: 2026-02-12

---

## Goal

Upload generated images and PDFs to Cloudflare R2 object storage and generate public URLs for user downloads. Zero egress fees compared to Firebase Storage.

---

## Input

- `file_bytes` (bytes): File content to upload
- `file_name` (string): Destination file name in bucket
- `content_type` (string): MIME type (e.g., "image/png", "application/pdf")

---

## Output

- `public_url` (string): Full HTTPS URL for accessing the uploaded file

---

## Process

### Step 1: Initialize S3 Client

Cloudflare R2 is S3-compatible, use boto3:

1. **Configuration**:
   - Endpoint: `https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com`
   - Access Key: `settings.r2_access_key_id`
   - Secret Key: `settings.r2_secret_access_key`
   - Region: `auto` (R2 doesn't use traditional regions)

2. **Client Creation**:
   - `boto3.client("s3", endpoint_url=..., aws_access_key_id=..., aws_secret_access_key=...)`

### Step 2: Upload File

1. **Put Object**:
   - Bucket: `settings.r2_bucket_name`
   - Key: `file_name` (path within bucket)
   - Body: `file_bytes`
   - ContentType: `content_type` (ensures proper browser handling)

2. **Example Call**:
   ```python
   s3.put_object(
       Bucket="tailormade-books",
       Key="books/abc123/page_1.png",
       Body=image_bytes,
       ContentType="image/png"
   )
   ```

### Step 3: Generate Public URL

1. **Build URL**:
   - Base: `settings.r2_public_url` (e.g., `https://books.tailormade.app`)
   - Path: `/{file_name}`
   - Result: Full HTTPS URL

2. **Example**:
   - Input: `books/abc123/coloring_book.pdf`
   - Output: `https://books.tailormade.app/books/abc123/coloring_book.pdf`

### Step 4: Return URL

- URL is immediately accessible (R2 bucket configured as public)
- No signed URLs needed for public content

---

## File Naming Convention

### Structure
```
books/{book_id}/{file_type}_{page_number}.{ext}
```

### Examples
- **PDF**: `books/550e8400-e29b-41d4-a716-446655440000/coloring_book.pdf`
- **Page Image**: `books/550e8400-e29b-41d4-a716-446655440000/page_1.png`
- **Thumbnail**: `books/550e8400-e29b-41d4-a716-446655440000/thumb_1.jpg`

### Rationale
- Book ID as folder → Easy to delete entire book
- Descriptive file names → Clear in bucket browser
- Extensions → Proper MIME type detection

---

## Edge Cases

### Upload Failure
- **Scenario**: Network timeout, R2 service unavailable, invalid credentials
- **Action**: boto3 raises exception
- **Propagation**: Caught by router, user sees "Upload failed"
- **Retry**: Not implemented (manual retry by user)

### Large File Size
- **Scenario**: 12-page book PDF > 50MB
- **Action**: R2 supports files up to 5TB, no special handling needed
- **Performance**: Slower upload, transparent to user

### Duplicate File Names
- **Scenario**: Upload same `file_name` twice
- **Action**: Overwrites previous file (S3 behavior)
- **Mitigation**: Use unique book IDs in file paths

### Invalid Characters in File Name
- **Scenario**: File name contains spaces, special characters
- **Action**: URL-encode file name before upload
- **Example**: `my book.pdf` → `my%20book.pdf`

---

## Error Handling

### Missing Credentials
- **Symptom**: boto3 raises `NoCredentialsError`
- **Action**: Fail fast, log error
- **User Impact**: "Storage service unavailable"

### Invalid Bucket Name
- **Symptom**: boto3 raises `NoSuchBucket`
- **Action**: Configuration error, check `.env`
- **Fix**: Verify `R2_BUCKET_NAME` is correct

### Network Timeout
- **Symptom**: boto3 raises `ConnectTimeoutError`
- **Action**: Retry with exponential backoff (not implemented)
- **Current Behavior**: Fail immediately

---

## Performance Requirements

- **Upload Speed**: Depends on file size and network
  - 1MB PNG: ~0.5 seconds
  - 10MB PDF: ~2 seconds
- **URL Generation**: < 1ms (string concatenation)
- **Total R2 Operations Per Book**: 9 uploads (8 pages + 1 PDF)

---

## Security Considerations

### Public vs Private Files
- ✅ **Current**: All files public (coloring books are shareable)
- ⚠️ **Future**: Private user photos (Phase 2) need signed URLs

### Access Control
- R2 bucket configured with public read access
- Write access restricted to backend via API keys
- No client-side uploads (prevents abuse)

### URL Expiration
- Public URLs never expire
- **Rationale**: Coloring books are permanent downloads
- **Future**: Implement TTL if needed for sensitive content

---

## Cost Optimization

### Why R2 vs Firebase Storage?
- **Egress Fees**: R2 = $0, Firebase = $0.12/GB
- **Storage**: Both ~$0.026/GB/month (comparable)
- **Operations**: Both charge per operation (negligible)
- **Savings**: ~$12 saved per 100GB downloaded

### Monitoring
- Track monthly storage size
- Monitor operation counts
- Alert if bucket size > 100GB

---

## Dependencies

- `boto3` for S3-compatible API
- `app.config.get_settings()` for R2 credentials
- Environment variables: `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_PUBLIC_URL`

---

## Testing Checklist

- [ ] Upload PNG image, verify public URL accessible
- [ ] Upload PDF, verify downloads correctly
- [ ] Upload multiple files with same book_id (folder structure)
- [ ] Test with missing R2 credentials (graceful error)
- [ ] Test with invalid bucket name (clear error message)
- [ ] Verify Content-Type headers set correctly (browser renders vs downloads)

---

## Maintenance Notes

### When to Implement Signed URLs
- ✏️ Adding private user content (Phase 2 photos)
- ✏️ Need to revoke access to specific files
- ⚠️ Requires TTL management and URL regeneration

### When to Implement Upload Retry
- ✏️ If network errors become common
- ✏️ Add tenacity decorator with exponential backoff
- ⚠️ Careful not to duplicate files

### When to Add Lifecycle Policies
- ✏️ Automatically delete old books after X days
- ✏️ Configure in R2 dashboard or via API
- ⚠️ Requires user notification before deletion

---

## Related SOPs

- [Image Generation](image_generation.md) — Produces image bytes to upload
- [PDF Pipeline](pdf_pipeline.md) — Produces PDF bytes to upload
- [API Endpoint: Generate Book](../routers/books.md) — Orchestrates upload after generation
