from bot.jobs import BaseJob, JobContext


class EveningSummaryJob(BaseJob):
    name = "evening_summary"

    def __init__(self, context: JobContext) -> None:
        super().__init__(context, enabled=False)

    def run(self) -> None:
        return None
