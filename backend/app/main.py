import json
import logging

import firebase_admin
import sentry_sdk
from contextlib import asynccontextmanager
from firebase_admin import credentials, firestore
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import books, auth, photos

settings = get_settings()
logger = logging.getLogger(__name__)

# ── Sentry Initialization ─────────────────────────────────────────────────────
# Must be called before app creation so all errors/transactions are captured.
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        send_default_pii=True,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        environment=settings.app_env,
        release="tailormade@1.0.0",
        # FastAPI integration is auto-discovered by sentry-sdk[fastapi]
    )
    logger.info("sentry_initialized env=%s", settings.app_env)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────────────────
    # Validate production settings
    try:
        settings.validate_for_production()
    except ValueError as e:
        raise RuntimeError(f"Configuration error: {e}")

    # Initialize Firebase
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(settings.firebase_service_account_path)
            firebase_admin.initialize_app(cred)
        logger.info("✅ TailorMade API ready")
        print("✅ TailorMade API ready")
    except FileNotFoundError:
        if settings.is_production:
            raise RuntimeError(
                "Firebase credentials required in production. "
                "Set FIREBASE_SERVICE_ACCOUNT_PATH in .env"
            )
        logger.warning("firebase-service-account.json not found — Firebase Auth disabled")
        print(
            "⚠️  firebase-service-account.json not found — "
            "Firebase Auth will NOT work. Download it from Firebase Console → "
            "Project Settings → Service Accounts → Generate new private key."
        )
        print("✅ TailorMade API ready (limited — no Firebase)")

    # Test Redis connectivity
    if settings.redis_host:
        try:
            import redis as redis_lib
            r = redis_lib.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                username=settings.redis_username,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            r.ping()
            logger.info("redis_connected host=%s port=%d", settings.redis_host, settings.redis_port)
            print(f"✅ Redis connected ({settings.redis_host}:{settings.redis_port})")
            r.close()
        except Exception as e:
            logger.warning("redis_connection_failed error=%s", e)
            print(f"⚠️  Redis connection failed: {e}")

    yield
    # ── Shutdown ───────────────────────────────────────────────────────────────
    print("👋 TailorMade API shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="TailorMade Coloring Book API",
        description="AI-powered personalized coloring book generator",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # ── CORS ───────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ────────────────────────────────────────────────────────────────
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(books.router, prefix="/api/v1/books", tags=["books"])
    app.include_router(photos.router, prefix="/api/v1/photos", tags=["photos"])

    # ── Deep Health Check ──────────────────────────────────────────────────────
    @app.get("/health")
    async def health():
        checks = {}

        # Firebase / Firestore
        try:
            db = firestore.client()
            db.collection("_health").limit(1).get()
            checks["firebase"] = "ok"
        except Exception as e:
            checks["firebase"] = f"error: {type(e).__name__}"

        # R2 Storage
        try:
            from app.services.storage import _get_client
            client = _get_client()
            client.head_bucket(Bucket=settings.r2_bucket_name)
            checks["r2"] = "ok"
        except Exception as e:
            checks["r2"] = f"error: {type(e).__name__}"

        # Redis
        if settings.redis_host:
            try:
                import redis as redis_lib
                r = redis_lib.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    password=settings.redis_password,
                    username=settings.redis_username,
                    decode_responses=True,
                    socket_connect_timeout=3,
                )
                r.ping()
                checks["redis"] = "ok"
                r.close()
            except Exception as e:
                checks["redis"] = f"error: {type(e).__name__}"

        # Sentry
        checks["sentry"] = "ok" if settings.sentry_dsn else "not configured"

        overall = "ok" if all(v == "ok" for v in checks.values() if v != "not configured") else "degraded"
        code = 200 if overall == "ok" else 503

        return Response(
            content=json.dumps({
                "status": overall,
                "app": "TailorMade Coloring Book",
                "version": "1.0.0",
                "checks": checks,
            }),
            status_code=code,
            media_type="application/json",
        )

    return app


app = create_app()
