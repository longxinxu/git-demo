from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, TypeVar


T = TypeVar("T")


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 0.2


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.opened_at: float | None = None

    def before_call(self) -> None:
        if self.opened_at is None:
            return
        if (time.time() - self.opened_at) >= self.recovery_timeout:
            self.failure_count = 0
            self.opened_at = None
            return
        raise RuntimeError("circuit_open")

    def on_success(self) -> None:
        self.failure_count = 0
        self.opened_at = None

    def on_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.opened_at = time.time()


def call_with_retry_and_circuit(
    func: Callable[[], T],
    retry: RetryConfig,
    circuit: CircuitBreaker,
) -> T:
    last_error: Exception | None = None
    for attempt in range(retry.max_retries + 1):
        circuit.before_call()
        try:
            result = func()
            circuit.on_success()
            return result
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            circuit.on_failure()
            if attempt >= retry.max_retries:
                break
            sleep_seconds = retry.base_delay * (2**attempt)
            time.sleep(sleep_seconds)
    assert last_error is not None
    raise last_error
