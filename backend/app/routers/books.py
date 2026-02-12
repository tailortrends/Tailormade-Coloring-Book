import logging
import uuid
from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth import get_current_user
from app.middleware.rate_limit import check_rate_limit
from app.models.book import BookRequest, BookResponse, BookSummary, GenerationStatus
from app.models.user import FirebaseUser
from app.services.firebase_db import get_user_books, get_book
from app.tasks import generate_book_task

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/generate", response_model=GenerationStatus, status_code=status.HTTP_202_ACCEPTED)
async def generate_book(
    request: BookRequest,
    user: FirebaseUser = Depends(check_rate_limit),  # includes auth + rate limit
):
    """
    Start async book generation job.
    Returns job_id to poll status.
    """
    # Dispatch Celery task
    # We pass Pydantic models as dicts because Celery serializer is JSON
    task = generate_book_task.delay(
        request.model_dump(),
        user.model_dump(),
    )
    
    logger.info("job_dispatched job_id=%s uid=%s", task.id, user.uid)
    
    return GenerationStatus(
        job_id=task.id,
        status="pending",
        progress=0,
        message="Queued for generation...",
    )


@router.get("/generate/{job_id}", response_model=GenerationStatus)
async def get_generation_status(job_id: str, user: FirebaseUser = Depends(get_current_user)):
    """
    Poll status of a generation job.
    Returns progress, message, and final result if complete.
    """
    task_result = AsyncResult(job_id)
    
    response = GenerationStatus(
        job_id=job_id,
        status=task_result.status.lower(),  # PENDING, STARTED, RETRY, FAILURE, SUCCESS
        progress=0,
        message="Processing...",
    )

    if task_result.state == "PROGRESS":
        # Custom state set by update_state()
        meta = task_result.info or {}
        response.status = "generating"
        response.progress = meta.get("progress", 0)
        response.message = meta.get("message", "Generating...")
        
    elif task_result.state == "SUCCESS":
        # Task completed successfully
        result_data = task_result.result
        if result_data.get("status") == "failed":
            # Logic error inside task (e.g. content unsafe)
            response.status = "failed"
            response.message = result_data.get("error", "Unknown error")
        else:
            response.status = "complete"
            response.progress = 100
            response.message = "Complete!"
            # Rehydrate BookResponse from dict
            if "book" in result_data:
                response.result = BookResponse(**result_data["book"])

    elif task_result.state == "FAILURE":
        # Exception raised
        response.status = "failed"
        response.message = str(task_result.result)

    return response


@router.get("/", response_model=list[BookSummary])
async def list_books(user: FirebaseUser = Depends(get_current_user)):
    """Return the authenticated user's book gallery (most recent first)."""
    return get_user_books(user.uid)


@router.get("/{book_id}", response_model=BookResponse)
async def get_book_detail(book_id: str, user: FirebaseUser = Depends(get_current_user)):
    """Return full book detail. Enforces ownership."""
    data = get_book(book_id, user.uid)
    if not data:
        raise HTTPException(status_code=404, detail="Book not found.")
    return BookResponse(**data)
