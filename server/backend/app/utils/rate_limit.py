import threading
import time
from dataclasses import dataclass

from fastapi import HTTPException, Request, status
from redis import Redis
from redis.exceptions import RedisError

from app.config import get_settings


@dataclass
class MemoryCounter:
    count: int
    expires_at: float


class RateLimiter:
    def __init__(self) -> None:
        settings = get_settings()
        self.storage_uri = settings.RATE_LIMIT_STORAGE_URI
        self.fail_open = settings.RATE_LIMIT_FAIL_OPEN
        self.redis = (
            Redis.from_url(self.storage_uri, decode_responses=True)
            if self.storage_uri.startswith(("redis://", "rediss://"))
            else None
        )
        self._memory: dict[str, MemoryCounter] = {}
        self._lock = threading.Lock()

    def _hit_memory(self, key: str, limit: int, window_seconds: int) -> int:
        now = time.monotonic()
        with self._lock:
            current = self._memory.get(key)
            if current is None or current.expires_at <= now:
                current = MemoryCounter(count=0, expires_at=now + window_seconds)
                self._memory[key] = current
            current.count += 1
            retry_after = max(1, int(current.expires_at - now))
            return retry_after if current.count > limit else 0

    def _hit_redis(self, key: str, limit: int, window_seconds: int) -> int:
        assert self.redis is not None
        redis_key = f"forest-wellness:rate-limit:{key}"
        with self.redis.pipeline(transaction=True) as pipeline:
            pipeline.incr(redis_key)
            pipeline.ttl(redis_key)
            count, ttl = pipeline.execute()
        if count == 1 or ttl < 0:
            self.redis.expire(redis_key, window_seconds)
            ttl = window_seconds
        return max(1, ttl) if count > limit else 0

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        try:
            retry_after = (
                self._hit_redis(key, limit, window_seconds)
                if self.redis is not None
                else self._hit_memory(key, limit, window_seconds)
            )
        except RedisError as exc:
            if self.fail_open:
                return
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="认证保护服务暂不可用",
            ) from exc
        if retry_after:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后重试",
                headers={"Retry-After": str(retry_after)},
            )


rate_limiter = RateLimiter()


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"
