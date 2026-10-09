import contextlib
import logging
import time
import uuid
from typing import Generator
import django_redis
from django.conf import settings

logger = logging.getLogger(__name__)

# Atomic Lua script: only delete the key if the value matches our unique token
LUA_RELEASE_LOCK = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


class DistributedLockException(Exception):
    """Raised when a distributed lock cannot be acquired or held."""
    pass


class RedisDistributedLock:
    """
    Production-grade Redis-backed Distributed Lock using atomic primitives:
    - Acquire: SET key token NX PX <ttl_ms>
    - Release: Lua script checking token before DEL (prevents releasing expired locks held by others)
    - Reliability: Strict fail-closed semantics by default in production.
    """

    def __init__(self, key: str, ttl_seconds: int = 60, connection_alias: str = "default"):
        self.key = f"lock:{key}"
        self.ttl_seconds = ttl_seconds
        self.ttl_ms = int(ttl_seconds * 1000)
        self.token = str(uuid.uuid4())
        self.connection_alias = connection_alias
        self.acquired = False

        # If testing/locmem cache is configured, allow permissive lock bypass
        self._allow_mock = getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False) or getattr(settings, "LOCK_PERMISSIVE_TEST_MODE", False)

        try:
            self.redis_client = django_redis.get_redis_connection(connection_alias)
        except Exception as exc:
            if self._allow_mock:
                self.redis_client = None
            else:
                logger.error(f"[DistributedLock] Failed to connect to Redis for lock '{self.key}': {exc}")
                raise DistributedLockException(f"Redis connection failed for lock '{self.key}': {exc}") from exc

    def acquire(self, blocking: bool = False, timeout_seconds: float = 5.0) -> bool:
        """
        Attempts to acquire the distributed lock.
        If blocking=True, retries until timeout_seconds is reached.
        """
        if self.redis_client is None:
            if self._allow_mock:
                self.acquired = True
                return True
            raise DistributedLockException(f"Cannot acquire lock '{self.key}': Redis client is unavailable.")

        start_time = time.monotonic()
        while True:
            try:
                result = self.redis_client.set(
                    self.key,
                    self.token,
                    nx=True,
                    px=self.ttl_ms,
                )
            except Exception as exc:
                logger.error(f"[DistributedLock] Error during SETNX for '{self.key}': {exc}")
                if self._allow_mock:
                    self.acquired = True
                    return True
                raise DistributedLockException(f"Redis SETNX failed for lock '{self.key}': {exc}") from exc

            if result:
                self.acquired = True
                logger.debug(f"[DistributedLock] Acquired lock '{self.key}' with token '{self.token}' (TTL: {self.ttl_seconds}s)")
                return True

            if not blocking or (time.monotonic() - start_time) >= timeout_seconds:
                logger.warning(f"[DistributedLock] Failed to acquire lock '{self.key}' (Held by another process)")
                return False

            time.sleep(0.1)

    def release(self) -> bool:
        """
        Releases the lock safely using the atomic Lua script.
        Returns True if the lock was owned and deleted; False otherwise.
        """
        if not self.acquired:
            return False

        if self.redis_client is None:
            self.acquired = False
            return True

        try:
            result = self.redis_client.eval(
                LUA_RELEASE_LOCK,
                1,
                self.key,
                self.token,
            )
            deleted = bool(result)
            if deleted:
                logger.debug(f"[DistributedLock] Successfully released lock '{self.key}'")
            else:
                logger.warning(f"[DistributedLock] Lock '{self.key}' was already expired or claimed by another worker")
            return deleted
        except Exception as exc:
            logger.error(f"[DistributedLock] Error during Lua release for '{self.key}': {exc}")
            return False
        finally:
            self.acquired = False

    def __enter__(self):
        if not self.acquire(blocking=False):
            raise DistributedLockException(f"Could not acquire lock for resource '{self.key}'")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


@contextlib.contextmanager
def distributed_lock(key: str, ttl_seconds: int = 60) -> Generator[RedisDistributedLock, None, None]:
    """Convenience context manager for distributed locking."""
    lock = RedisDistributedLock(key=key, ttl_seconds=ttl_seconds)
    lock_acquired = lock.acquire(blocking=False)
    if not lock_acquired:
        raise DistributedLockException(f"Lock '{lock.key}' is already held by another worker.")
    try:
        yield lock
    finally:
        lock.release()
