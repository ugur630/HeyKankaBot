import unittest
from datetime import datetime

from bot.scheduler import JobScheduler


class FakeJob:
    def __init__(
        self,
        name: str,
        *,
        should_run: bool = True,
        should_fail: bool = False,
    ) -> None:
        self.name = name
        self._should_run = should_run
        self._should_fail = should_fail
        self.executed = 0
        self.marked = 0

    def should_run(self, current_time: datetime) -> bool:
        del current_time
        return self._should_run

    def execute(self, current_time: datetime | None = None) -> None:
        del current_time
        self.executed += 1
        if self._should_fail:
            raise RuntimeError(f"{self.name} failed")

    def mark_ran(self, current_time: datetime) -> None:
        del current_time
        self.marked += 1


class SchedulerTests(unittest.TestCase):
    def test_scheduler_continues_when_a_job_fails(self) -> None:
        first_job = FakeJob("first", should_fail=True)
        second_job = FakeJob("second")
        scheduler = JobScheduler(jobs=[first_job, second_job])

        scheduler.run_pending(datetime(2026, 7, 4, 8, 0))

        self.assertEqual(first_job.executed, 1)
        self.assertEqual(first_job.marked, 1)
        self.assertEqual(second_job.executed, 1)
        self.assertEqual(second_job.marked, 1)

    def test_scheduler_skips_jobs_that_are_not_due(self) -> None:
        skipped_job = FakeJob("skipped", should_run=False)
        scheduler = JobScheduler(jobs=[skipped_job])

        scheduler.run_pending(datetime(2026, 7, 4, 8, 0))

        self.assertEqual(skipped_job.executed, 0)
        self.assertEqual(skipped_job.marked, 0)


if __name__ == "__main__":
    unittest.main()
