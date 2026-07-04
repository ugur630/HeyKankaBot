from bot.jobs import BaseJob, JobContext


class AINewsJob(BaseJob):
    name = "ai_news"

    def __init__(self, context: JobContext) -> None:
        super().__init__(context, enabled=False)

    def run(self) -> None:
        return None
