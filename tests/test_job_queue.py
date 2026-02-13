import asyncio

from app.services.job_queue import JobQueue


def test_job_queue_runs_and_records_metrics():
    async def _run():
        queue = JobQueue(max_history=10)
        await queue.start()

        async def good_job():
            await asyncio.sleep(0.01)
            return 123

        enqueued = await queue.enqueue("sync_resources_task", good_job, dedupe_key="a", dedupe_window_s=1)
        assert enqueued is True

        await asyncio.sleep(0.05)
        status = queue.get_status()
        assert status["metrics"]["total_runs"] == 1
        assert status["metrics"]["success_count"] == 1
        assert status["metrics"]["failure_count"] == 0

        await queue.stop()

    asyncio.run(_run())


def test_job_queue_deduplicates_within_window():
    async def _run():
        queue = JobQueue(max_history=10)
        await queue.start()

        async def slow_job():
            await asyncio.sleep(0.05)

        enqueued_first = await queue.enqueue("review_pending_task", slow_job, dedupe_key="same", dedupe_window_s=60)
        enqueued_second = await queue.enqueue("review_pending_task", slow_job, dedupe_key="same", dedupe_window_s=60)

        assert enqueued_first is True
        assert enqueued_second is False

        await queue.stop()

    asyncio.run(_run())
