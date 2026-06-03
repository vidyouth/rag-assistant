from dotenv import load_dotenv
load_dotenv()

import os
import logging
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers import documents, chat

# ─── Logging setup ────────────────────────────────────────────────────────────
# This configures Python's built-in logger to print structured lines like:
# 2024-01-15 14:23:01 | INFO     | main | Server started
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")

# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Quill — Document Intelligence API",
    description="Upload documents, ask questions, get grounded answers with citations.",
    version="1.0.0",
    # Hide the raw /docs error details in production
    docs_url="/docs",
    redoc_url=None,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://rag-assistant-alpha.vercel.app",   # ← updated after Vercel deploy
        os.environ.get("FRONTEND_URL", ""),    # ← env var override
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request logging middleware ───────────────────────────────────────────────
# This runs on EVERY request before it hits your route handler.
# It logs: method, path, status code, and how long it took.
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]   # short ID to trace one request
    start = time.perf_counter()

    logger.info(f"[{request_id}] → {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        duration = round((time.perf_counter() - start) * 1000)
        logger.info(f"[{request_id}] ← {response.status_code} ({duration}ms)")
        return response
    except Exception as e:
        duration = round((time.perf_counter() - start) * 1000)
        logger.error(f"[{request_id}] ✗ Unhandled exception ({duration}ms): {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected server error occurred. Please try again."}
        )

# ─── Global exception handler ─────────────────────────────────────────────────
# Catches anything that slips past route-level try/except.
# Users NEVER see a raw Python traceback — they get a clean JSON message.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Our team has been notified."}
    )

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(documents.router)
app.include_router(chat.router)

# ─── Health endpoints ─────────────────────────────────────────────────────────
@app.get("/", tags=["health"])
def home():
    logger.info("Health check hit")
    return {
        "app": "Quill",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/ping", tags=["health"])
def ping():
    return {"status": "alive"}

logger.info("Quill API started successfully")