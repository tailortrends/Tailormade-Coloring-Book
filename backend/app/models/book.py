import html
import re
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


class ArtStyle(str, Enum):
    simple = "simple"          # Ages 3-5: thick lines, large shapes
    standard = "standard"      # Ages 6-9: normal coloring book lines
    detailed = "detailed"      # Ages 10+: fine lines, more complexity


class AgeRange(str, Enum):
    toddler = "3-5"
    kids = "6-9"
    tweens = "10-12"


def _sanitize_text(v: str) -> str:
    """Strip HTML tags and escape special characters to prevent XSS/injection."""
    if not v:
        return v
    # Remove all HTML tags
    stripped = re.sub(r"<[^>]+>", "", v)
    # Escape remaining HTML entities
    return html.escape(stripped, quote=True)


class BookRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=80, description="Book title")
    theme: str = Field(..., min_length=5, max_length=300, description="Story theme and characters")
    page_count: int = Field(default=6, ge=2, le=12, description="Number of coloring pages")
    age_range: AgeRange = Field(default=AgeRange.kids)
    art_style: ArtStyle = Field(default=ArtStyle.standard)
    character_name: Optional[str] = Field(None, max_length=50)

    @field_validator("title", "theme", "character_name", mode="before")
    @classmethod
    def sanitize_input(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _sanitize_text(v)


class PageResult(BaseModel):
    page_number: int
    scene_description: str
    image_url: str             # R2 public URL
    thumbnail_url: str         # Smaller preview version


class BookResponse(BaseModel):
    book_id: str
    title: str
    theme: str
    page_count: int
    pages: list[PageResult]
    pdf_url: str               # Print-ready PDF on R2
    created_at: str
    user_uid: str


class BookSummary(BaseModel):
    """Lightweight version for gallery listings."""
    book_id: str
    title: str
    cover_thumbnail: str       # First page thumbnail
    page_count: int
    created_at: str


class GenerationStatus(BaseModel):
    job_id: str
    status: str                # pending | generating | complete | failed
    progress: int              # 0-100
    message: str
    result: Optional[BookResponse] = None
