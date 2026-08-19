from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.errors import AppError
from app.routes import admin, auth, chat, conversations, documents, feedback, suggestions, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="CRuX GPT API", version="1.0.0", lifespan=lifespan)

# Credentialed requests can't use "*" - the allowed origin is configurable via FRONTEND_URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(feedback.router)
app.include_router(suggestions.router)
app.include_router(admin.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
