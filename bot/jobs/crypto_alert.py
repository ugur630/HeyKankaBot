from bot.jobs import BaseJob, JobContext


class CryptoAlertJob(BaseJob):
    name = "crypto_alert"

    def __init__(self, context: JobContext) -> None:
        super().__init__(context, enabled=False)

    def run(self) -> None:
        return None
