from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.post("/upload")
async def upload_reference_photo():
    """
    Phase 2: Upload a reference photo (parent's photo of child) to generate
    a personalized character likeness using img2img / ControlNet pipeline.
    Coming soon.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Photo upload pipeline coming in Phase 2.",
    )
