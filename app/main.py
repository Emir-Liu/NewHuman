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

# 导入路由模块（后续添加）
# from api.chat import router as chat_router
# from api.knowledge_base import router as kb_router


# ==================== 生命周期管理 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动和关闭时的处理逻辑
    """
    # 启动时执行
    print(f"[{datetime.now()}] 服务启动中...")
    
    # 可以在这里初始化数据库连接、加载模型等
    # 例如：await init_db()
    
    yield  # 服务运行期间
    
    # 关闭时执行
    print(f"[{datetime.now()}] 服务关闭...")
    # 可以在这里清理资源
    # 例如：await close_db()


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
    # "http://localhost",
    # "http://localhost:3000",     # React 开发服务器
    # "http://localhost:5173",     # Vite 开发服务器
    # "http://localhost:8080",     # Vue 开发服务器
    # "http://127.0.0.1:3000",
    # # "https://your-production-domain.com",  # 生产环境域名
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


# @app.get("/health", tags=["健康检查"])
# async def health_check():
#     """
#     健康检查接口
#     用于负载均衡或监控系统检测服务状态
#     """
#     return {
#         "status": "healthy",
#         "timestamp": datetime.now().isoformat(),
#         "components": {
#             "api": "ok",
#             # "database": "ok",    # 后续添加数据库检查
#             # "redis": "ok",       # 后续添加缓存检查
#         }
#     }


# @app.get("/ready", tags=["健康检查"])
# async def readiness_check():
#     """
#     就绪检查接口
#     用于 Kubernetes 等判断服务是否准备好接收流量
#     """
#     # 检查关键依赖是否就绪
#     checks = {
#         "api": True,
#         # "database": await check_db(),
#     }
    
#     all_ready = all(checks.values())
    
#     return JSONResponse(
#         status_code=200 if all_ready else 503,
#         content={
#             "ready": all_ready,
#             "checks": checks
#         }
#     )


# ==================== API 路由注册（后续添加） ====================

# 对话相关 API
# app.include_router(
#     chat_router,
#     prefix="/api/v1",
#     tags=["对话接口"]
# )

# 知识库相关 API
# app.include_router(
#     kb_router,
#     prefix="/api/v1",
#     tags=["知识库"]
# )

# # 示例路由
# @app.get("/api/v1/test/{item_id}", tags=["测试"])
# async def read_item(item_id: int, q: str = None):
#     """
#     测试路由 - 带路径参数和查询参数
#     """
#     return {"item_id": item_id, "q": q}


# @app.post("/api/v1/echo", tags=["测试"])
# async def echo(data: dict):
#     """
#     测试路由 - 回显收到的数据
#     """
#     return {
#         "received": data,
#         "timestamp": datetime.now().isoformat()
#     }


# ==================== 启动入口 ====================

if __name__ == "__main__":
    # 开发环境启动
    uvicorn.run(
        "main:app",
        host="0.0.0.0",      # 监听所有网卡
        port=8000,           # 端口
        reload=True,         # 热重载（开发环境）
        workers=1,           # 工作进程数
        log_level="info"     # 日志级别
    )
