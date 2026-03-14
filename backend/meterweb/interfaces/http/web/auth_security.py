from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class _AttemptBucket:
    attempts: deque[datetime] = field(default_factory=deque)
    lock_until: datetime | None = None


class LoginAttemptGuard:
    def __init__(self, max_attempts: int, window_seconds: int, lock_duration_seconds: int) -> None:
        self._max_attempts = max_attempts
        self._window = timedelta(seconds=window_seconds)
        self._lock_duration = timedelta(seconds=lock_duration_seconds)
        self._buckets: dict[str, _AttemptBucket] = {}

    def is_locked(self, key: str, now: datetime | None = None) -> bool:
        current = now or datetime.utcnow()
        bucket = self._buckets.get(key)
        if bucket is None:
            return False

        self._prune(bucket, current)
        if bucket.lock_until and bucket.lock_until > current:
            return True

        if bucket.lock_until and bucket.lock_until <= current:
            bucket.lock_until = None
            bucket.attempts.clear()

        return False

    def register_failure(self, key: str, now: datetime | None = None) -> None:
        current = now or datetime.utcnow()
        bucket = self._buckets.setdefault(key, _AttemptBucket())

        self._prune(bucket, current)
        if bucket.lock_until and bucket.lock_until > current:
            return

        bucket.attempts.append(current)
        if len(bucket.attempts) >= self._max_attempts:
            bucket.lock_until = current + self._lock_duration

    def register_success(self, key: str) -> None:
        bucket = self._buckets.get(key)
        if bucket is None:
            return
        bucket.attempts.clear()
        bucket.lock_until = None

    def _prune(self, bucket: _AttemptBucket, now: datetime) -> None:
        threshold = now - self._window
        while bucket.attempts and bucket.attempts[0] < threshold:
            bucket.attempts.popleft()
