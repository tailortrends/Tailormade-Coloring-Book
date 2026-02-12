# PDF Pipeline SOP

**Layer**: 1 (Architecture)  
**Service**: `backend/app/services/pdf_builder.py`  
**Last Updated**: 2026-02-12

---

## Goal

Compile generated coloring book pages into a professional, print-ready PDF with cover page. Optimize for US Letter size (8.5" × 11") at 300 DPI.

---

## Input

- `title` (string): Book title for cover page
- `pages` (list[dict]): List of page dictionaries, each containing:
  - `page_number` (int): Page order (1-indexed)
  - `description` (string): Scene description (not used in PDF)
  - `image_bytes` (bytes): Clean PNG at 300 DPI

---

## Output

- `pdf_bytes` (bytes): Complete PDF ready for download/print

---

## Process

### Step 1: Lazy-Load WeasyPrint

**CRITICAL**: Import WeasyPrint **inside the function**, not at module level.

**Rationale**:
- WeasyPrint requires `libpango` system library
- If missing, import fails and crashes entire backend
- Lazy loading delays failure until PDF generation actually called
- Allows backend to start in environments without `libpango`

```python
def build_pdf(...):
    from weasyprint import HTML, CSS  # Import HERE, not at top of file
```

### Step 2: Build HTML Document

**Components**:

1. **Cover Page**:
   - Title (48pt, centered)
   - Subtitle: "My Personal Coloring Book"
   - Branding: "TailorMade Coloring Book" (footer)
   - CSS: `page-break-after: always` (forces new page)

2. **Coloring Pages** (for each page):
   - Embed image as base64 data URI
   - Image width: 7.5 inches (leaves 0.5" margin on each side)
   - Page label: "Page {n}" below image
   - CSS: `page-break-before: always` (each page on new sheet)

**Security**: Escape title with `html.escape()` to prevent XSS injection

### Step 3: Apply CSS Styling

**Page Settings**:
- Size: 8.5in × 11in (US Letter)
- Margins: 0.5in on all sides
- Font: 'Fredoka One', 'Comic Sans MS' (kid-friendly fallback)

**Layout**:
- Cover: Flexbox centering (vertical + horizontal)
- Pages: Center-aligned images with labels

### Step 4: Compile PDF via Tempfile

**Memory Optimization**:
- WeasyPrint writes to temp file, not BytesIO buffer
- **Rationale**: Prevents holding HTML + PDF bytes simultaneously in RAM
- Reduces peak memory usage by ~50%

**Process**:
1. Create temp file: `tempfile.mkstemp(suffix=".pdf")`
2. Close file descriptor (WeasyPrint will reopen)
3. Render HTML to PDF: `HTML(string=full_html).write_pdf(tmp_path, stylesheets=[page_css])`
4. Read PDF bytes from temp file
5. **Always** delete temp file in `finally` block (cleanup guarantee)

### Step 5: Log and Return

- Log: `pdf_generated pages={count} size_bytes={size}`
- Return: PDF bytes

---

## Edge Cases

### Large Page Count
- **Scenario**: 12+ pages, each 2550×3300 at 300 DPI
- **Action**: Tempfile approach prevents memory issues
- **User Impact**: Slightly slower (disk I/O vs memory)

### Invalid Image Bytes
- **Scenario**: Corrupted `image_bytes` in pages list
- **Action**: WeasyPrint raises exception during rendering
- **Propagation**: Caught by router, returns 500

### Title with Special Characters
- **Scenario**: Title contains `<`, `>`, `&`, quotes
- **Action**: `html.escape()` sanitizes for safe HTML embedding
- **Example**: `"Luna's <Adventure>"` → `"Luna&#x27;s &lt;Adventure&gt;"`

### WeasyPrint Not Installed
- **Scenario**: Missing `libpango` or WeasyPrint package
- **Action**: Import fails when function called (not at startup)
- **User Impact**: Clear error message: "PDF generation unavailable. Install WeasyPrint and libpango."

---

## Error Handling

### Import Error (WeasyPrint Missing)
- **Symptom**: `ImportError` when function called
- **Action**: Raise with helpful message
- **Prevention**: Lazy loading keeps backend operational

### Tempfile Cleanup Failure
- **Symptom**: `OSError` when deleting temp file
- **Action**: Silently ignore (file may already be deleted)
- **Rationale**: PDF generation succeeded; cleanup failure is non-critical

### Base64 Encoding Error
- **Symptom**: Invalid `image_bytes` (not valid PNG)
- **Action**: Encoding fails, raises exception
- **Propagation**: Caught by router, user sees "Generation failed"

---

## Performance Requirements

- **Single Page**: ~0.5 seconds
- **8-Page Book**: ~4 seconds
- **12-Page Book**: ~6 seconds
- **SLA**: < 5 seconds for 8-page book

**Bottleneck**: WeasyPrint rendering speed (CPU-bound)

---

## Constants

### CSS Template (`_PAGE_CSS_STRING`)

**Page Dimensions**:
- Size: `8.5in × 11in`
- Margins: `0.5in` (all sides)

**Typography**:
- Font: `'Fredoka One', 'Comic Sans MS', cursive`
- Cover title: 48pt
- Cover subtitle: 18pt
- Page labels: 12pt

**Layout**:
- Cover: Flexbox centering
- Images: 7.5in width (auto height to maintain aspect ratio)

---

## Dependencies

- `weasyprint` (lazy-loaded): HTML → PDF conversion
- `base64`: Image embedding in HTML
- `html`: XSS prevention for title
- `tempfile`: Memory-optimized temp file handling

---

## Testing Checklist

- [ ] Generate PDF with 4, 8, and 12 pages
- [ ] Verify cover page has correct title
- [ ] Verify each page on separate sheet
- [ ] Test title with special characters (`<`, `>`, `&`, quotes)
- [ ] Verify images display at correct size (7.5in wide)
- [ ] Test without WeasyPrint installed (graceful degradation)
- [ ] Verify temp file cleanup in both success and failure cases

---

## Maintenance Notes

### When to Update CSS
- ✏️ User feedback on page layout
- ✏️ Branding changes (colors, fonts)
- ✏️ Margin adjustments for different printers

### When to Update Page Size
- ✏️ Support for A4 (210mm × 297mm) in addition to US Letter
- ⚠️ Requires coordination with image generation (different aspect ratio)

### When to Optimize Memory
- ✏️ If memory usage still too high with tempfile approach
- ✏️ Consider streaming PDF generation (not supported by WeasyPrint)

---

## Related SOPs

- [Image Generation](image_generation.md) — Produces image_bytes input
- [Storage](storage.md) — Uploads PDF to Cloudflare R2
- [API Endpoint: Generate Book](../routers/books.md) — Orchestrates PDF creation
