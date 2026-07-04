from importlib import import_module
import inspect
import pkgutil

import bot.jobs
from bot.jobs import BaseJob, JobContext
from bot.utils.logger import logger


class JobRegistry:
    def build_jobs(self, context: JobContext) -> list[BaseJob]:
        self._import_job_modules()
        jobs = [
            job_class(context)
            for job_class in sorted(
                self._iter_job_classes(),
                key=lambda item: item.__name__,
            )
        ]
        logger.info(
            "Scheduler discovered jobs: %s",
            [job.name for job in jobs],
        )
        return jobs

    def _import_job_modules(self) -> None:
        for module_info in pkgutil.iter_modules(bot.jobs.__path__):
            if module_info.name.startswith("_") or module_info.name == "registry":
                continue
            import_module(f"bot.jobs.{module_info.name}")

    def _iter_job_classes(self) -> list[type[BaseJob]]:
        job_classes: list[type[BaseJob]] = []
        for job_class in BaseJob.__subclasses__():
            if inspect.isabstract(job_class):
                continue
            job_classes.append(job_class)
        return job_classes
