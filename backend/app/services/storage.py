import boto3
from botocore.config import Config
from app.config import get_settings

settings = get_settings()


def _get_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def upload_bytes(
    data: bytes,
    key: str,
    content_type: str = "application/octet-stream",
) -> str:
    """Upload raw bytes to R2. Returns the public URL."""
    client = _get_client()
    client.put_object(
        Bucket=settings.r2_bucket_name,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return f"{settings.r2_public_url}/{key}"


def build_key(uid: str, book_id: str, filename: str) -> str:
    """Consistent key structure: users/{uid}/books/{book_id}/{filename}"""
    return f"users/{uid}/books/{book_id}/{filename}"
