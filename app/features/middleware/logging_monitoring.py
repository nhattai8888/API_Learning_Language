import time
import json
import logging
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class LoggingMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware để ghi log và monitor các request/response
    Ghi lại: method, path, status_code, response_time, client_ip, user_id
    """

    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip logging cho các path nhất định
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Ghi lại thời gian bắt đầu
        start_time = time.time()
        
        # Lấy thông tin request
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query_string = request.url.query
        
        # Cố gắng lấy user_id từ token hoặc session
        user_id = "anonymous"
        try:
            if "authorization" in request.headers:
                # Token có thể được extract ở đây nếu cần
                user_id = request.headers.get("authorization", "").split()[-1][:10]
        except Exception:
            pass

        # Gọi endpoint
        response = None
        status_code = 500
        exception = None
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            exception = e
            logger.error(f"Exception in request: {str(e)}", exc_info=True)
            status_code = 500

        # Tính toán response time
        process_time = time.time() - start_time
        
        # Ghi log
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "client_ip": client_ip,
            "method": method,
            "path": path,
            "query_string": query_string,
            "status_code": status_code,
            "response_time_ms": round(process_time * 1000, 2),
            "user_id": user_id,
        }
        
        # Xác định log level dựa vào status code
        if status_code >= 500:
            logger.error(f"Server Error: {json.dumps(log_data)}")
        elif status_code >= 400:
            logger.warning(f"Client Error: {json.dumps(log_data)}")
        elif status_code >= 200:
            logger.info(f"Request: {json.dumps(log_data)}")
        
        # Thêm custom headers
        if response:
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = f"{int(time.time() * 1000)}"
            return response
        
        if exception:
            raise exception
        
        # Fallback response nếu có lỗi
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )


def log_execution_time(func):
    """
    Decorator để log execution time của một function
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"Function {func.__name__} took {duration:.2f}s")
        return result
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"Function {func.__name__} took {duration:.2f}s")
        return result
    
    # Xác định wrapper phù hợp
    if hasattr(func, '__call__'):
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
    
    return sync_wrapper
