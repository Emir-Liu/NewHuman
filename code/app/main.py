"""
FastAPI 主入口
提供 API 服务和跨域支持
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import time
from datetime import datetime
from contextlib import asynccontextmanager

# 导入路由模块
from api.v1.chat_messages import router as chat_messages_router
from api.v1.conversations import router as conversations_router
from api.v1.knowledge_bases import router as kb_router

# 导入Nacos服务注册和服务配置
from core.nacos import register_service, deregister_service
from config.service_config import ServiceConfig


# ==================== 生命周期管理 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动和关闭时的处理逻辑
    """
    # 初始化服务配置
    service_config = ServiceConfig()

    # 启动时执行
    print(f"[{datetime.now()}] 服务启动中...")

    # 注册到Nacos
    try:
        await register_service(service_config.port)
        print(f"[{datetime.now()}] Nacos注册完成（不一定成功）")
    except Exception as e:
        print(f"[{datetime.now()}] Nacos注册失败: {e}")

    yield  # 服务运行期间

    # 关闭时执行
    print(f"[{datetime.now()}] 服务关闭...")

    # 从Nacos注销
    try:
        await deregister_service(service_config.port)
        print(f"[{datetime.now()}] Nacos注销成功")
    except Exception as e:
        print(f"[{datetime.now()}] Nacos注销失败: {e}")


# ==================== 创建 FastAPI 应用 ====================

app = FastAPI(
    title="Dify-LangGraph API",
    description="基于 LangGraph 的 AI 应用编排平台 API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",           # Swagger UI 地址
    redoc_url="/redoc",         # ReDoc 地址
    openapi_url="/openapi.json" # OpenAPI 规范地址
)


# ==================== 跨域配置 ====================

# 允许的源（开发环境可以设置为 *，生产环境需要指定具体域名）
ALLOWED_ORIGINS = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,      # 允许的源列表
    allow_credentials=True,              # 允许携带 Cookie
    allow_methods=["*"],                 # 允许所有 HTTP 方法
    allow_headers=["*"],                 # 允许所有请求头
    expose_headers=["*"],                # 暴露的响应头
    max_age=600,                         # 预检请求缓存时间（秒）
)


# ==================== 中间件 ====================

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    请求处理时间中间件
    为每个响应添加 X-Process-Time 头
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.3f}s"
    return response


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """
    请求追踪中间件
    可以添加请求ID用于日志追踪
    """
    # request_id = str(uuid.uuid4())
    # request.state.request_id = request_id
    response = await call_next(request)
    # response.headers["X-Request-ID"] = request_id
    return response


# ==================== 异常处理 ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理
    """
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "服务器内部错误",
            "detail": str(exc) if app.debug else "请联系管理员"
        }
    )


# ==================== 路由 ====================

@app.get("/", tags=["健康检查"])
async def root():
    """
    根路径 - 服务状态检查
    """
    return {
        "status": "ok",
        "service": "dify-langgraph-api",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat()
    }


# ==================== API 路由注册（后续添加） ====================

# 对话相关 API
app.include_router(
    chat_messages_router,
    prefix="/v1",
    tags=["对话消息"]
)

# 会话管理 API
app.include_router(
    conversations_router,
    prefix="/v1",
    tags=["会话管理"]
)

# 知识库相关 API
app.include_router(
    kb_router,
    prefix="/v1",
    tags=["知识库"]
)


# ==================== 启动入口 ====================

if __name__ == "__main__":
    # 开发环境启动
    service_config = ServiceConfig()

    uvicorn.run(
        "main:app",
        host=service_config.host,
        port=service_config.port,
        reload=True,         # 热重载（开发环境）
        workers=1,           # 工作进程数
        log_level="info"     # 日志级别
    )
