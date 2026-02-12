from datetime import datetime, timezone
from firebase_admin import firestore
from app.models.book import BookResponse, BookSummary


def save_book(book: BookResponse) -> None:
    """Persist completed book metadata to Firestore."""
    db = firestore.client()
    db.collection("books").document(book.book_id).set(book.model_dump())


def get_user_books(uid: str, limit: int = 20) -> list[BookSummary]:
    """Fetch lightweight gallery summaries for a user."""
    db = firestore.client()
    docs = (
        db.collection("books")
        .where("user_uid", "==", uid)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    summaries = []
    for doc in docs:
        data = doc.to_dict()
        cover = data["pages"][0]["thumbnail_url"] if data.get("pages") else ""
        summaries.append(
            BookSummary(
                book_id=data["book_id"],
                title=data["title"],
                cover_thumbnail=cover,
                page_count=data["page_count"],
                created_at=data["created_at"],
            )
        )
    return summaries


def get_book(book_id: str, uid: str) -> dict | None:
    """Fetch a single book, enforcing ownership."""
    db = firestore.client()
    doc = db.collection("books").document(book_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    # Ownership check
    if data.get("user_uid") != uid:
        return None
    return data


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
