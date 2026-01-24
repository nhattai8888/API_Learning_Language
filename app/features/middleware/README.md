# Middleware Documentation

Tài liệu này mô tả các middleware được cài đặt cho ứng dụng FastAPI.

## Các Middleware Có Sẵn

### 1. Rate Limit Middleware
**Mục đích:** Giới hạn số lượng request từ một client trong một khoảng thời gian.

**Tính năng:**
- Giới hạn requests per minute theo IP address
- Sử dụng Redis để tracking
- Tự động expire tracking data sau 60 giây
- Thêm rate limit headers vào response
- Skip health check endpoints

**Cấu hình:**
```python
from app.features.middleware import setup_middlewares

setup_middlewares(
    app=app,
    redis_client=redis,
    rate_limit_requests_per_minute=60,  # Số request/phút
    enable_rate_limit=True,
)
```

**Response Headers:**
- `X-RateLimit-Limit`: Tổng số request cho phép
- `X-RateLimit-Remaining`: Số request còn lại
- `X-RateLimit-Reset`: Thời gian reset (Unix timestamp)

**Error Response (429):**
```json
{
    "detail": "Too many requests. Please try again later.",
    "retry_after": 60
}
```

---

### 2. Logging & Monitoring Middleware
**Mục đích:** Ghi log tất cả HTTP requests/responses và monitor performance.

**Tính năng:**
- Ghi log method, path, status code, response time
- Lấy thông tin client IP
- Extract user_id từ authorization header
- Phân loại log level dựa vào status code
- Skip logging cho healthcheck/docs endpoints
- Decorator `log_execution_time()` để log function execution

**Cấu hình:**
```python
from app.features.middleware import setup_middlewares

setup_middlewares(
    app=app,
    enable_logging=True,
)
```

**Log Format:**
```json
{
    "timestamp": "2025-01-24T10:30:45.123456",
    "client_ip": "192.168.1.100",
    "method": "GET",
    "path": "/api/vocabularies",
    "query_string": "page=1&limit=10",
    "status_code": 200,
    "response_time_ms": 45.23,
    "user_id": "user123"
}
```

**Response Headers:**
- `X-Process-Time`: Thời gian xử lý (seconds)
- `X-Request-ID`: Request ID duy nhất

**Sử dụng decorator:**
```python
from app.features.middleware import log_execution_time

@log_execution_time
async def slow_function():
    await asyncio.sleep(2)
    # Function took 2.00s
```

---

### 3. Security Middleware
**Mục đích:** Bảo vệ ứng dụng khỏi các cuộc tấn công phổ biến.

**Tính năng:**
- **SQL Injection Detection:** Phát hiện các pattern SQL injection cơ bản
- **CSRF Protection:** Kiểm tra CSRF token
- **Security Headers:** Thêm các headers bảo mật vào response
- **CORS Support:** Xử lý CORS requests
- **XSS Protection:** Prevent XSS attacks thông qua Content-Security-Policy

**Cấu hình:**
```python
from app.features.middleware import setup_middlewares

setup_middlewares(
    app=app,
    enable_security=True,
)
```

**Security Headers Được Thêm:**
- `X-Content-Type-Options: nosniff` - Prevent MIME type sniffing
- `X-Frame-Options: DENY` - Prevent clickjacking
- `X-XSS-Protection: 1; mode=block` - XSS protection
- `Strict-Transport-Security: max-age=31536000` - Force HTTPS
- `Content-Security-Policy: ...` - XSS & injection protection
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()` - Feature policies
- `Access-Control-Allow-Origin: ...` - CORS headers

**CSRF Token Usage:**
```bash
# Gửi request với CSRF token
curl -X POST http://localhost:8000/api/vocabularies \
  -H "X-CSRF-Token: your-token-here" \
  -H "Content-Type: application/json" \
  -d '{"word": "test"}'
```

**SQL Injection Detection:**
```
Middleware sẽ block request nếu phát hiện:
- UNION SELECT
- DROP, DELETE statements
- OR 1=1 patterns
- SQL comments (--,#,/*,*/)
```

---

## Cách Sử Dụng Trong Main App

```python
from fastapi import FastAPI
from app.features.middleware import setup_middlewares, setup_cors
from app.core.cache import redis

# Tạo FastAPI app
app = FastAPI(...)

# Setup middleware
setup_middlewares(
    app=app,
    redis_client=redis,
    rate_limit_requests_per_minute=60,
    enable_rate_limit=True,
    enable_logging=True,
    enable_security=True,
)

# Setup CORS (optional)
setup_cors(app, allowed_origins=["http://localhost:3000", "http://example.com"])
```

---

## Cấu Hình Chi Tiết

### Middleware Config Class

```python
from app.features.middleware import MiddlewareConfig

# Xem cấu hình
rate_limit_config = MiddlewareConfig.get_rate_limit_config()
logging_config = MiddlewareConfig.get_logging_config()
security_config = MiddlewareConfig.get_security_config()
cors_config = MiddlewareConfig.get_cors_config()

# Sửa cấu hình
MiddlewareConfig.REQUESTS_PER_MINUTE = 100
MiddlewareConfig.SECURITY_CHECK_SQL_INJECTION = False
```

---

## Thứ Tự Middleware

Thứ tự thực thi middleware rất quan trọng:

```
Request
  ↓
[3] Rate Limit Middleware (Cuối cùng được add)
  ↓
[2] Logging & Monitoring Middleware
  ↓
[1] Security Middleware (Đầu tiên được add)
  ↓
Application Logic
  ↓
[1] Security Middleware (Response)
  ↓
[2] Logging & Monitoring Middleware (Response)
  ↓
[3] Rate Limit Middleware (Response)
  ↓
Response
```

---

## Troubleshooting

### 1. Rate Limit Không Hoạt Động
**Nguyên nhân:** Redis không khả dụng
**Giải pháp:** Đảm bảo Redis đang chạy
```bash
redis-cli ping  # Nên trả về PONG
```

### 2. CSRF Token Required Nhưng Không Biết Lấy Từ Đâu
**Giải pháp:** Nếu dùng JWT token, middleware sẽ tự động skip CSRF check

### 3. SQL Injection Detection Quá Khắt
**Giải pháp:** Tắt SQL injection detection
```python
MiddlewareConfig.SECURITY_CHECK_SQL_INJECTION = False
```

### 4. CORS Errors
**Giải pháp:** Thêm origin vào whitelist
```python
setup_cors(app, allowed_origins=["http://localhost:3000", "https://yourdomain.com"])
```

---

## Ví Dụ Thực Tế

### Test Rate Limiting
```bash
# Loop gửi 70 request trong 1 phút
for i in {1..70}; do
    curl -v http://localhost:8000/api/vocabularies
done
# Request thứ 61-70 sẽ nhận 429 Too Many Requests
```

### Test Logging
```bash
# Check logs
tail -f app.log

# Xem request được ghi
# INFO Request: {"timestamp": "...", "method": "GET", ...}
```

### Test Security Headers
```bash
curl -i http://localhost:8000/api/vocabularies
# Xem các security headers trong response
```

---

## Performance Impact

- **Rate Limit:** ~1-2ms per request (Redis lookup)
- **Logging:** ~2-5ms per request (JSON serialization + log write)
- **Security:** ~1-3ms per request (pattern matching)

**Tổng cộng:** ~5-10ms overhead cho request

---

## Recommendations

1. **Production:** Thay đổi CORS origins từ "*" sang danh sách cụ thể
2. **Performance:** Tắt SQL injection detection nếu không cần
3. **Logging:** Sử dụng centralized logging service (ELK, CloudWatch, etc.)
4. **Rate Limiting:** Điều chỉnh requests_per_minute dựa vào traffic
