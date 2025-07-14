"""
FastAPI 自定义中间件
"""
import time
import json
import uuid
from typing import Callable, Dict, Any
from datetime import datetime
import logging

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .config import settings
from .cache import cache_manager
from .auth import auth_manager

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取客户端信息
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # 记录请求信息
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"- ID: {request_id} - IP: {client_ip} - UA: {user_agent}"
        )
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"- ID: {request_id} - Status: {response.status_code} "
                f"- Time: {process_time:.3f}s"
            )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 记录错误
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"- ID: {request_id} - Error: {str(e)} - Time: {process_time:.3f}s"
            )
            raise
    
    def get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP"""
        # 检查代理头部
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 返回直接连接IP
        return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1分钟窗口
        
        # 排除的路径（不进行速率限制）
        self.excluded_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/ws"  # WebSocket连接
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否为排除路径
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # 获取客户端标识
        client_id = self.get_client_identifier(request)
        
        # 检查速率限制
        if not await self.check_rate_limit(client_id):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"最多每分钟 {self.requests_per_minute} 次请求",
                    "retry_after": self.window_size
                },
                headers={"Retry-After": str(self.window_size)}
            )
        
        return await call_next(request)
    
    def get_client_identifier(self, request: Request) -> str:
        """获取客户端标识符"""
        # 优先使用用户ID（如果已认证）
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header[7:]
                payload = auth_manager.decode_token(token)
                user_id = payload.get("sub")
                if user_id:
                    return f"user:{user_id}"
            except:
                pass
        
        # 使用IP地址
        client_ip = request.headers.get("X-Forwarded-For", request.client.host)
        return f"ip:{client_ip}"
    
    async def check_rate_limit(self, client_id: str) -> bool:
        """检查速率限制"""
        try:
            key = f"rate_limit:{client_id}"
            
            # 获取当前计数
            current_count = await cache_manager.get(key, 0)
            
            if current_count >= self.requests_per_minute:
                return False
            
            # 增加计数
            new_count = await cache_manager.increment(key)
            
            # 设置过期时间（仅在第一次时）
            if new_count == 1:
                await cache_manager.expire(key, self.window_size)
            
            return True
            
        except Exception as e:
            logger.error(f"速率限制检查失败: {e}")
            # 发生错误时允许请求通过
            return True


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头部中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 检查是否为Swagger文档路径
        is_swagger_path = request.url.path in ["/docs", "/redoc"] or request.url.path.startswith("/openapi")
        
        # 添加安全头部
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
        
        # 为Swagger文档设置宽松的CSP，为其他页面设置严格的CSP
        if is_swagger_path:
            security_headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none';"
            )
        else:
            security_headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none';"
            )
        
        # 仅在生产环境添加HSTS
        if not settings.debug:
            security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


class DatabaseSessionMiddleware(BaseHTTPMiddleware):
    """数据库会话中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # 记录数据库相关错误
            if "database" in str(e).lower() or "connection" in str(e).lower():
                logger.error(f"Database error in {request.method} {request.url.path}: {e}")
            raise


class CacheMiddleware(BaseHTTPMiddleware):
    """缓存中间件"""
    
    def __init__(self, app, cache_duration: int = 300):
        super().__init__(app)
        self.cache_duration = cache_duration
        
        # 可缓存的路径模式
        self.cacheable_paths = {
            "/api/v1/rooms",
            "/api/v1/users/online",
            "/api/v1/stats"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 只缓存GET请求
        if request.method != "GET":
            return await call_next(request)
        
        # 检查是否为可缓存路径
        if not any(request.url.path.startswith(path) for path in self.cacheable_paths):
            return await call_next(request)
        
        # 生成缓存键
        cache_key = f"http_cache:{request.url.path}:{str(request.query_params)}"
        
        # 尝试从缓存获取
        try:
            cached_response = await cache_manager.get(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for {request.url.path}")
                return JSONResponse(
                    content=cached_response["content"],
                    status_code=cached_response["status_code"],
                    headers=cached_response.get("headers", {})
                )
        except Exception as e:
            logger.warning(f"缓存读取失败: {e}")
        
        # 执行请求
        response = await call_next(request)
        
        # 缓存成功响应
        if response.status_code == 200:
            try:
                # 读取响应内容
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                
                # 解析JSON内容
                content = json.loads(response_body.decode())
                
                # 缓存响应
                cache_data = {
                    "content": content,
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                }
                await cache_manager.set(cache_key, cache_data, self.cache_duration)
                
                logger.debug(f"Cached response for {request.url.path}")
                
                # 创建新的响应对象
                return JSONResponse(
                    content=content,
                    status_code=response.status_code,
                    headers=response.headers
                )
                
            except Exception as e:
                logger.warning(f"缓存写入失败: {e}")
        
        return response


class UserActivityTrackingMiddleware(BaseHTTPMiddleware):
    """用户活动跟踪中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取用户信息
        user_id = await self.get_user_id_from_request(request)
        
        # 记录用户活动
        if user_id:
            await self.track_user_activity(user_id, request)
        
        return await call_next(request)
    
    async def get_user_id_from_request(self, request: Request) -> str:
        """从请求中获取用户ID"""
        try:
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                payload = auth_manager.decode_token(token)
                return payload.get("sub")
        except:
            pass
        return None
    
    async def track_user_activity(self, user_id: str, request: Request):
        """跟踪用户活动"""
        try:
            activity_data = {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "method": request.method,
                "path": request.url.path,
                "ip": request.headers.get("X-Forwarded-For", request.client.host),
                "user_agent": request.headers.get("user-agent", "")
            }
            
            # 更新用户在线状态
            await cache_manager.cache_user_online_status(user_id, True)
            
            # 记录活动（可选：存储到数据库或分析系统）
            await cache_manager.set(
                f"user_activity:{user_id}:latest",
                activity_data,
                expire=3600
            )
            
        except Exception as e:
            logger.warning(f"用户活动跟踪失败: {e}")


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """错误处理中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except HTTPException:
            # FastAPI的HTTP异常直接抛出
            raise
        except Exception as e:
            # 记录未处理的异常
            request_id = getattr(request.state, 'request_id', 'unknown')
            logger.exception(
                f"Unhandled exception in {request.method} {request.url.path} "
                f"- ID: {request_id}"
            )
            
            # 返回统一的错误响应
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "message": "服务器内部错误，请稍后重试",
                    "request_id": request_id
                }
            )


class WebSocketConnectionMiddleware:
    """WebSocket连接中间件（装饰器形式）"""
    
    @staticmethod
    def track_connection(websocket_handler):
        """跟踪WebSocket连接的装饰器"""
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            connection_id = str(uuid.uuid4())
            
            logger.info(f"WebSocket connection started - ID: {connection_id}")
            
            try:
                # 执行原始处理器
                return await websocket_handler(*args, **kwargs)
            except Exception as e:
                logger.error(f"WebSocket error - ID: {connection_id} - Error: {e}")
                raise
            finally:
                duration = time.time() - start_time
                logger.info(f"WebSocket connection ended - ID: {connection_id} - Duration: {duration:.3f}s")
        
        return wrapper


# 中间件配置函数
def setup_middleware(app):
    """设置所有中间件"""
    
    # 暂时只保留必要的中间件来解决CORS问题
    
    # 请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)
    
    # 错误处理中间件
    app.add_middleware(ErrorHandlingMiddleware)
    
    logger.info("核心中间件已设置完成（已简化以解决CORS问题）") 