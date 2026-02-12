"""Typed model for Firebase decoded token — replaces raw dict everywhere."""

from pydantic import BaseModel


class FirebaseUser(BaseModel):
    """Structured representation of a decoded Firebase ID token."""
    uid: str
    email: str | None = None
    name: str | None = None
    picture: str | None = None
    email_verified: bool = False
    tier: str = "free"

    @classmethod
    def from_decoded_token(cls, decoded: dict) -> "FirebaseUser":
        """Create from firebase_admin.auth.verify_id_token() result."""
        return cls(
            uid=decoded["uid"],
            email=decoded.get("email"),
            name=decoded.get("name"),
            picture=decoded.get("picture"),
            email_verified=decoded.get("email_verified", False),
        )
