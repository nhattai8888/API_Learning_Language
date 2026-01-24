import time
import logging
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware sử dụng Redis để giới hạn số lượng request
    Lazy initialize redis - chờ đến khi cần dùng
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute

    async def _get_redis_client(self):
        """Lazy load redis client from cache module"""
        from app.core.cache import redis
        return redis

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip rate limiting cho health check
        if request.url.path == "/health":
            return await call_next(request)

        try:
            # Get redis client dynamically
            redis_client = await self._get_redis_client()
            
            if not redis_client:
                logger.debug("Redis client not available, skipping rate limit")
                return await call_next(request)

            # Lấy client IP
            client_ip = request.client.host if request.client else "unknown"
            
            # Tạo key cho tracking
            rate_limit_key = f"rate_limit:{client_ip}:{int(time.time() // 60)}"
            
            # Kiểm tra số lượng request
            current_requests = await redis_client.incr(rate_limit_key)
            
            # Set TTL cho key (60 giây)
            if current_requests == 1:
                await redis_client.expire(rate_limit_key, 60)
            
            # Kiểm tra xem vượt quá giới hạn không
            if current_requests > self.requests_per_minute:
                logger.warning(
                    f"Rate limit exceeded for IP {client_ip}: "
                    f"{current_requests}/{self.requests_per_minute} requests"
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many requests. Please try again later.",
                        "retry_after": 60
                    }
                )
            
            # Thêm headers thông tin rate limit
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(
                self.requests_per_minute - current_requests
            )
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
            
            return response

        except Exception as e:
            logger.error(f"Rate limit middleware error: {str(e)}")
            return await call_next(request)
