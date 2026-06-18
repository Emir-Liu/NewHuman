"""
FastAPI 主入口
提供 API 服务和跨域支持
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import time
from datetime import datetime
from contextlib import asynccontextmanager

from api.v1.chat_messages import router as chat_messages_router
from api.v1.conversations import router as conversations_router

try:
    from api.v1.knowledge_bases import router as kb_router
    _KB_AVAILABLE = True
except ImportError:
    kb_router = None
    _KB_AVAILABLE = False

from core.nacos import register_service, deregister_service
from config.service_config import ServiceConfig

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    service_config = ServiceConfig()
    print(f"[{datetime.now()}] Server starting...")

    from func.graph.agent_handler import agent_handler
    agent_handler.reset_agent()

    try:
        await register_service(service_config.port)
    except Exception as e:
        print(f"[{datetime.now()}] Nacos skipped/failed: {e}")

    yield

    print(f"[{datetime.now()}] Server stopping...")
    try:
        await deregister_service(service_config.port)
    except Exception as e:
        print(f"[{datetime.now()}] Nacos deregister failed: {e}")


app = FastAPI(
    title="NewHuman API",
    description="LangGraph ReAct Agent API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.time() - start_time:.3f}s"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "Internal server error",
            "detail": str(exc),
        },
    )


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "service": "newhuman-api",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/", tags=["UI"], include_in_schema=False)
async def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/chat", tags=["UI"], include_in_schema=False)
async def chat_page():
    return FileResponse(STATIC_DIR / "chat.html")


if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(chat_messages_router, prefix="/v1", tags=["Chat"])
app.include_router(conversations_router, prefix="/v1", tags=["Conversations"])

if _KB_AVAILABLE and kb_router is not None:
    app.include_router(kb_router, prefix="/v1", tags=["Knowledge Base"])


if __name__ == "__main__":
    service_config = ServiceConfig()
    uvicorn.run(
        "main:app",
        host=service_config.host,
        port=service_config.port,
        reload=False,
        workers=1,
        log_level="info",
    )
