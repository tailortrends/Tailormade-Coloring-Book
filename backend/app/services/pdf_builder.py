import base64
import html
import io
import logging
import os
import tempfile

logger = logging.getLogger(__name__)

_PAGE_CSS_STRING = """
    @page {
        size: 8.5in 11in;
        margin: 0.5in;
    }
    body {
        margin: 0;
        padding: 0;
        font-family: 'Fredoka One', 'Comic Sans MS', cursive;
        background: white;
    }
    .cover {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100vh;
        text-align: center;
        page-break-after: always;
    }
    .cover h1 {
        font-size: 48pt;
        color: #222;
        margin-bottom: 12pt;
    }
    .cover p {
        font-size: 18pt;
        color: #555;
    }
    .coloring-page {
        page-break-before: always;
        text-align: center;
    }
    .coloring-page img {
        width: 7.5in;
        height: auto;
        display: block;
        margin: 0 auto;
    }
    .page-label {
        font-size: 12pt;
        color: #888;
        margin-top: 6pt;
    }
"""


def build_pdf(title: str, pages: list[dict]) -> bytes:
    """
    Build a print-ready PDF from a list of pages.
    Each page dict must have: page_number, description, image_bytes (PNG bytes).
    Returns PDF as bytes.

    Uses tempfile to reduce peak memory — writes PDF to disk instead of
    holding the entire PDF in a BytesIO buffer alongside the HTML.
    """
    from weasyprint import HTML, CSS

    page_css = CSS(string=_PAGE_CSS_STRING)

    # Escape title to prevent XSS injection into the PDF HTML
    safe_title = html.escape(title, quote=True)

    # Cover page
    html_parts = [
        f"""
        <div class="cover">
            <h1>{safe_title}</h1>
            <p>My Personal Coloring Book</p>
            <p style="font-size:14pt; color:#999; margin-top:24pt;">TailorMade Coloring Book</p>
        </div>
        """
    ]

    for page in pages:
        b64 = base64.b64encode(page["image_bytes"]).decode()
        html_parts.append(
            f"""
            <div class="coloring-page">
                <img src="data:image/png;base64,{b64}" alt="Page {page['page_number']}" />
                <p class="page-label">Page {page['page_number']}</p>
            </div>
            """
        )

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{safe_title}</title>
    </head>
    <body>
        {''.join(html_parts)}
    </body>
    </html>
    """

    # Write to tempfile to reduce peak memory usage
    # (avoids holding HTML + PDF bytes simultaneously in RAM)
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    try:
        os.close(tmp_fd)
        HTML(string=full_html).write_pdf(tmp_path, stylesheets=[page_css])
        with open(tmp_path, "rb") as f:
            pdf_bytes = f.read()
        logger.info("pdf_generated pages=%d size_bytes=%d", len(pages), len(pdf_bytes))
        return pdf_bytes
    finally:
        # Always clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
