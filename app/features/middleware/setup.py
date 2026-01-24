"""
Setup middleware cho FastAPI application
"""
from fastapi import FastAPI
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def setup_middlewares(
    app: FastAPI,
    rate_limit_requests_per_minute: int = 60,
    enable_rate_limit: bool = True,
    enable_logging: bool = True,
    enable_security: bool = True,
):
    """
    Setup tất cả middleware cho application
    NOTE: Middleware phải được add ở top level, trước app khởi động
    
    Args:
        app: FastAPI application instance
        rate_limit_requests_per_minute: Số request/phút cho rate limit
        enable_rate_limit: Enable/disable rate limit middleware
        enable_logging: Enable/disable logging middleware
        enable_security: Enable/disable security middleware
    """
    from .security import SecurityMiddleware
    from .logging_monitoring import LoggingMonitoringMiddleware
    from .rate_limit import RateLimitMiddleware
    
    # Order matters - middleware được thực thi từ dưới lên
    
    if enable_security:
        app.add_middleware(SecurityMiddleware)
        logger.info("✓ Security middleware enabled")
    
    if enable_logging:
        app.add_middleware(LoggingMonitoringMiddleware)
        logger.info("✓ Logging & Monitoring middleware enabled")
    
    if enable_rate_limit:
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=rate_limit_requests_per_minute
        )
        logger.info(
            f"✓ Rate limit middleware enabled ({rate_limit_requests_per_minute} requests/minute)"
        )
    
    return app


def setup_cors(app: FastAPI, allowed_origins: list = None):
    """
    Setup CORS middleware
    
    Args:
        app: FastAPI application instance
        allowed_origins: List of allowed origins
    """
    from fastapi.middleware.cors import CORSMiddleware
    
    if allowed_origins is None:
        allowed_origins = ["*"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"✓ CORS middleware enabled for origins: {allowed_origins}")
    
    return app
