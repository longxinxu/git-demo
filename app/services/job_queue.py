from __future__ import annotations

import asyncio
import json
import logging
import time
import traceback
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

logger = logging.getLogger("app.jobs")


@dataclass
class JobRunRecord:
    job_name: str
    dedupe_key: str
    status: str
    started_at: str
    finished_at: str
    duration_ms: float
    result: Any | None = None
    error: str | None = None
    traceback: str | None = None


class JobQueue:
    def __init__(self, max_history: int = 50) -> None:
        self._queue: asyncio.Queue[tuple[str, str, Callable[[], Awaitable[Any]]]] = asyncio.Queue()
        self._history: deque[JobRunRecord] = deque(maxlen=max_history)
        self._dedupe_seen_at: dict[str, float] = {}
        self._running_keys: set[str] = set()
        self._worker_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._worker_task and not self._worker_task.done():
            return
        self._worker_task = asyncio.create_task(self._worker_loop())

    async def stop(self) -> None:
        if not self._worker_task:
            return
        self._worker_task.cancel()
        try:
            await self._worker_task
        except asyncio.CancelledError:
            pass

    async def enqueue(
        self,
        job_name: str,
        fn: Callable[[], Awaitable[Any]] | Callable[[], Any],
        dedupe_key: str,
        dedupe_window_s: int = 60,
    ) -> bool:
        now = time.time()
        last_seen_at = self._dedupe_seen_at.get(dedupe_key)
        if dedupe_key in self._running_keys:
            return False
        if last_seen_at and now - last_seen_at < dedupe_window_s:
            return False

        self._dedupe_seen_at[dedupe_key] = now

        async def _runner() -> Any:
            result = fn()
            if asyncio.iscoroutine(result):
                return await result
            return result

        await self._queue.put((job_name, dedupe_key, _runner))
        return True

    async def _worker_loop(self) -> None:
        while True:
            job_name, dedupe_key, fn = await self._queue.get()
            self._running_keys.add(dedupe_key)
            started = time.perf_counter()
            started_at = datetime.now(timezone.utc).isoformat()
            try:
                result = await fn()
                duration_ms = (time.perf_counter() - started) * 1000
                finished_at = datetime.now(timezone.utc).isoformat()
                self._history.append(
                    JobRunRecord(
                        job_name=job_name,
                        dedupe_key=dedupe_key,
                        status="success",
                        started_at=started_at,
                        finished_at=finished_at,
                        duration_ms=duration_ms,
                        result=result,
                    )
                )
                logger.info(
                    json.dumps(
                        {
                            "event": "job_completed",
                            "job_name": job_name,
                            "dedupe_key": dedupe_key,
                            "status": "success",
                            "duration_ms": round(duration_ms, 2),
                            "result": result,
                        },
                        ensure_ascii=False,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                duration_ms = (time.perf_counter() - started) * 1000
                finished_at = datetime.now(timezone.utc).isoformat()
                tb = traceback.format_exc()
                self._history.append(
                    JobRunRecord(
                        job_name=job_name,
                        dedupe_key=dedupe_key,
                        status="failed",
                        started_at=started_at,
                        finished_at=finished_at,
                        duration_ms=duration_ms,
                        error=str(exc),
                        traceback=tb,
                    )
                )
                logger.error(
                    json.dumps(
                        {
                            "event": "job_completed",
                            "job_name": job_name,
                            "dedupe_key": dedupe_key,
                            "status": "failed",
                            "duration_ms": round(duration_ms, 2),
                            "error": str(exc),
                        },
                        ensure_ascii=False,
                    )
                )
            finally:
                self._running_keys.discard(dedupe_key)
                self._queue.task_done()

    def get_status(self) -> dict[str, Any]:
        runs = list(self._history)
        total = len(runs)
        success = len([r for r in runs if r.status == "success"])
        failed = total - success
        avg_duration = sum(r.duration_ms for r in runs) / total if total else 0.0

        return {
            "queue_size": self._queue.qsize(),
            "running_jobs": sorted(self._running_keys),
            "metrics": {
                "total_runs": total,
                "success_count": success,
                "failure_count": failed,
                "success_rate": round((success / total) * 100, 2) if total else 0.0,
                "failure_rate": round((failed / total) * 100, 2) if total else 0.0,
                "avg_duration_ms": round(avg_duration, 2),
            },
            "recent_runs": [run.__dict__ for run in reversed(runs)],
        }


class PeriodicJobScheduler:
    def __init__(self) -> None:
        self._handles: list[asyncio.TimerHandle] = []
        self._running = False

    def start(self) -> None:
        self._running = True

    def schedule(self, interval_seconds: int, trigger: Callable[[], Awaitable[None]]) -> None:
        loop = asyncio.get_running_loop()

        def _tick() -> None:
            if not self._running:
                return
            asyncio.create_task(trigger())
            handle = loop.call_later(interval_seconds, _tick)
            self._handles.append(handle)

        handle = loop.call_later(interval_seconds, _tick)
        self._handles.append(handle)

    def stop(self) -> None:
        self._running = False
        for handle in self._handles:
            handle.cancel()
        self._handles.clear()
