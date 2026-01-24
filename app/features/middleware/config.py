"""
Cấu hình cho Middleware
"""
from typing import List

class MiddlewareConfig:
    """
    Cấu hình cho tất cả middleware
    """
    
    # Rate Limit Middleware
    RATE_LIMIT_ENABLED = True
    REQUESTS_PER_MINUTE = 60
    RATE_LIMIT_EXCLUDE_PATHS = ["/health", "/docs", "/redoc", "/openapi.json"]
    
    # Logging & Monitoring Middleware
    LOGGING_ENABLED = True
    LOGGING_EXCLUDE_PATHS = ["/health", "/docs", "/redoc", "/openapi.json"]
    
    # Security Middleware
    SECURITY_ENABLED = True
    SECURITY_CHECK_SQL_INJECTION = True
    SECURITY_ENABLE_CSRF = True
    SECURITY_ALLOWED_ORIGINS = ["*"]  # Nên thay đổi trong production
    SECURITY_WHITELIST_PATHS = ["/health", "/docs", "/redoc", "/openapi.json"]
    
    # CORS
    CORS_ENABLED = True
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["*"]
    CORS_ALLOW_ORIGIN_REGEX = ".*"  # Regex pattern cho allowed origins
    
    @classmethod
    def get_rate_limit_config(cls):
        """Lấy cấu hình rate limit"""
        return {
            "enabled": cls.RATE_LIMIT_ENABLED,
            "requests_per_minute": cls.REQUESTS_PER_MINUTE,
            "exclude_paths": cls.RATE_LIMIT_EXCLUDE_PATHS,
        }
    
    @classmethod
    def get_logging_config(cls):
        """Lấy cấu hình logging"""
        return {
            "enabled": cls.LOGGING_ENABLED,
            "exclude_paths": cls.LOGGING_EXCLUDE_PATHS,
        }
    
    @classmethod
    def get_security_config(cls):
        """Lấy cấu hình security"""
        return {
            "enabled": cls.SECURITY_ENABLED,
            "check_sql_injection": cls.SECURITY_CHECK_SQL_INJECTION,
            "enable_csrf": cls.SECURITY_ENABLE_CSRF,
            "allowed_origins": cls.SECURITY_ALLOWED_ORIGINS,
            "whitelist_paths": cls.SECURITY_WHITELIST_PATHS,
        }
    
    @classmethod
    def get_cors_config(cls):
        """Lấy cấu hình CORS"""
        return {
            "enabled": cls.CORS_ENABLED,
            "allow_credentials": cls.CORS_ALLOW_CREDENTIALS,
            "allow_methods": cls.CORS_ALLOW_METHODS,
            "allow_headers": cls.CORS_ALLOW_HEADERS,
            "allow_origin_regex": cls.CORS_ALLOW_ORIGIN_REGEX,
        }
