from fastapi import Request, HTTPException, status
from typing import Dict, Tuple
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self):
        # Store request counts per IP and endpoint category
        self._requests: Dict[Tuple[str, str], list] = defaultdict(list)
        
        # Define rate limits (requests, seconds)
        self.LIMITS = {
            "auth": (10, 60),      # 10 requests per minute
            "conversations": (100, 60),  # 100 requests per minute
            "messages": (50, 60),   # 50 requests per minute
            "voice": (5, 60),       # 5 requests per minute
            "profile": (20, 60),    # 20 requests per minute
        }

    def _get_category(self, path: str) -> str:
        if "/auth" in path:
            return "auth"
        elif "/conversations" in path and "/messages" not in path:
            return "conversations"
        elif "/messages" in path:
            return "messages"
        elif "/voice" in path:
            return "voice"
        elif "/profile" in path:
            return "profile"
        return "default"

    async def check_rate_limit(self, request: Request):
        # Get client IP
        client_ip = request.client.host
        path_category = self._get_category(request.url.path)
        key = (client_ip, path_category)

        # Get rate limit for category
        max_requests, window = self.LIMITS.get(path_category, (20, 60))  # Default: 20 requests per minute

        # Clean old requests
        now = time.time()
        self._requests[key] = [req_time for req_time in self._requests[key] 
                             if now - req_time < window]

        # Check if limit exceeded
        if len(self._requests[key]) >= max_requests:
            reset_time = self._requests[key][0] + window
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_time)),
                }
            )

        # Add current request
        self._requests[key].append(now)

        # Add rate limit headers
        remaining = max_requests - len(self._requests[key])
        reset_time = now + window

        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(max_requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(reset_time)),
        }
