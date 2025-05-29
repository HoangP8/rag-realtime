from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from .rate_limiter import RateLimiter

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = RateLimiter()

    async def dispatch(self, request: Request, call_next):
        await self.rate_limiter.check_rate_limit(request)
        response = await call_next(request)

        # Add rate limit headers from request state
        if hasattr(request.state, "rate_limit_headers"):
            for key, value in request.state.rate_limit_headers.items():
                response.headers[key] = value

        return response
