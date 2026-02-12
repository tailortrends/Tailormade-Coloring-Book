import asyncio
import uuid
import logging
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from app.models.book import BookRequest, BookResponse, PageResult
from app.models.user import FirebaseUser
from app.services.content_filter import is_content_safe
from app.services.scene_planner import plan_scenes
from app.services.image_gen import generate_pages
from app.services.pdf_builder import build_pdf
from app.services.storage import upload_bytes, build_key
from app.services.firebase_db import save_book, now_iso
from app.middleware.rate_limit import increment_usage

logger = logging.getLogger(__name__)


@shared_task(bind=True, soft_time_limit=300, name="generate_book_task")
def generate_book_task(self, request_data: dict, user_data: dict):
    """
    Background task to generate a book.
    - request_data: dict version of BookRequest
    - user_data: dict version of FirebaseUser
    """
    uid = user_data["uid"]
    book_id = str(uuid.uuid4())
    logger.info("task_started task_id=%s uid=%s", self.request.id, uid)

    try:
        # Rehydrate models
        # We handle validation in the API layer, so these dicts are trusted
        request = BookRequest(**request_data)
        
        # ── Step 1: Content safety ─────────────────────────────────────────────
        # Async function called synchronously via run()
        full_text = f"{request.title} {request.theme}"
        safe, reason = asyncio.run(is_content_safe(full_text))
        
        if not safe:
            logger.warning("content_rejected uid=%s reason=%s", uid, reason)
            return {"status": "failed", "error": f"Content unsafe: {reason}"}

        # ── Step 2: Plan scenes ────────────────────────────────────────────────
        self.update_state(state="PROGRESS", meta={"progress": 10, "message": "Planning scenes..."})
        scenes = plan_scenes(
            theme=request.theme,
            page_count=request.page_count,
            art_style=request.art_style,
            age_range=request.age_range,
            character_name=request.character_name,
        )

        # ── Steps 3 & 4: Generate images ───────────────────────────────────────
        self.update_state(state="PROGRESS", meta={"progress": 20, "message": "Drawing pages..."})
        
        # generate_pages is async, so we run it in a new event loop
        processed_scenes = asyncio.run(generate_pages(scenes))
        
        # ── Step 5: Build PDF ──────────────────────────────────────────────────
        self.update_state(state="PROGRESS", meta={"progress": 80, "message": "Assembling book..."})
        pdf_bytes = build_pdf(request.title, processed_scenes)

        # ── Step 6: Upload to R2 ───────────────────────────────────────────────
        self.update_state(state="PROGRESS", meta={"progress": 90, "message": "Publishing..."})
        
        page_results = []
        for scene in processed_scenes:
            page_num = scene["page_number"]
            
            # upload_bytes is sync (boto3)
            image_url = upload_bytes(
                scene["image_bytes"],
                build_key(uid, book_id, f"page_{page_num:02d}.png"),
                "image/png",
            )
            thumbnail_url = upload_bytes(
                scene["thumbnail_bytes"],
                build_key(uid, book_id, f"page_{page_num:02d}_thumb.jpg"),
                "image/jpeg",
            )
            page_results.append(
                PageResult(
                    page_number=page_num,
                    scene_description=scene["description"],
                    image_url=image_url,
                    thumbnail_url=thumbnail_url,
                )
            )

        pdf_url = upload_bytes(
            pdf_bytes,
            build_key(uid, book_id, "book.pdf"),
            "application/pdf",
        )

        # ── Step 7: Persist & Credit ───────────────────────────────────────────
        book = BookResponse(
            book_id=book_id,
            title=request.title,
            theme=request.theme,
            page_count=request.page_count,
            pages=page_results,
            pdf_url=pdf_url,
            created_at=now_iso(),
            user_uid=uid,
        )
        save_book(book)
        increment_usage(uid)

        logger.info("task_complete task_id=%s book_id=%s", self.request.id, book_id)
        
        # Return dict serialization of the result
        return {"status": "complete", "book": book.model_dump()}

    except SoftTimeLimitExceeded:
        logger.error("task_timeout uid=%s", uid)
        return {"status": "failed", "error": "Generation timed out."}
    except Exception as e:
        logger.exception("task_failed uid=%s", uid)
        return {"status": "failed", "error": str(e)}
