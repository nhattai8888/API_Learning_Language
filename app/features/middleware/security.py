import logging
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import re

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware để xử lý:
    - CORS headers
    - CSRF protection
    - Security headers
    - XSS protection
    - SQL injection detection (cơ bản)
    - Suspicious request patterns
    """

    # Các pattern nguy hiểm (cơ bản SQL injection detection)
    DANGEROUS_PATTERNS = [
        r"(?i)(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|SCRIPT)\b)",
        r"(?i)(--|#|;|\*|\/\*|\*\/)",
        r"(?i)(union\s+select)",
        r"(?i)(or\s+1\s*=\s*1)",
    ]

    # Whitelist các endpoints không cần check bảo mật
    SECURITY_WHITELIST = ["/health", "/docs", "/redoc", "/openapi.json"]

    def __init__(
        self,
        app,
        allowed_origins: list = None,
        check_sql_injection: bool = True,
        enable_csrf: bool = True,
    ):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
        self.check_sql_injection = check_sql_injection
        self.enable_csrf = enable_csrf

    async def dispatch(self, request: Request, call_next: Callable):
        # Bỏ qua check cho security whitelist
        if request.url.path in self.SECURITY_WHITELIST:
            return await call_next(request)

        # 1. Kiểm tra SQL injection
        if self.check_sql_injection:
            sql_injection_result = self._check_sql_injection(request)
            if sql_injection_result:
                logger.warning(
                    f"Suspicious SQL injection attempt from {request.client.host}: "
                    f"{request.url.path}"
                )
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Forbidden - Suspicious request pattern"}
                )

        # 2. Kiểm tra CSRF cho non-GET requests
        if self.enable_csrf and request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            if not self._verify_csrf(request):
                logger.warning(
                    f"CSRF validation failed for {request.method} {request.url.path}"
                )
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF validation failed"}
                )

        # 3. Gọi endpoint
        response = await call_next(request)

        # 4. Thêm security headers
        response = self._add_security_headers(response, request)

        return response

    def _check_sql_injection(self, request: Request) -> bool:
        """
        Kiểm tra các query string và path parameters cho SQL injection patterns
        """
        # Kiểm tra query string
        if request.url.query:
            for pattern in self.DANGEROUS_PATTERNS:
                if re.search(pattern, request.url.query):
                    return True

        # Kiểm tra path
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, request.url.path):
                return True

        return False

    def _verify_csrf(self, request: Request) -> bool:
        """
        Kiểm tra CSRF token (đơn giản)
        Có thể extend để kiểm tra token thực
        """
        # Bỏ qua CSRF check nếu có authorization header (JWT)
        if "authorization" in request.headers:
            return True

        # Kiểm tra CSRF token trong headers hoặc form data
        csrf_token = request.headers.get("x-csrf-token")
        if csrf_token:
            return True

        # Nếu là from khác origin, đòi hỏi CSRF token
        origin = request.headers.get("origin")
        referer = request.headers.get("referer")

        if origin or referer:
            if not csrf_token:
                return False

        return True

    def _add_security_headers(self, response, request: Request):
        """
        Thêm các security headers vào response
        """
        # X-Content-Type-Options: mencegah MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: mencegah clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection: proteksi XSS
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Strict-Transport-Security
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

        # Content-Security-Policy (permissive)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:"
        )

        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        # CORS headers
        origin = request.headers.get("origin")
        if origin in self.allowed_origins or "*" in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = (
                origin if origin else "*"
            )
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, PATCH, OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-CSRF-Token"
            )
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Max-Age"] = "3600"

        return response
