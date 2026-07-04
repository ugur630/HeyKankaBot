import importlib
import logging
import unittest
from unittest import mock

import bot.utils.logger as logger_module


class LoggerLevelTests(unittest.TestCase):
    def tearDown(self) -> None:
        importlib.reload(logger_module)

    def test_defaults_to_info_when_unset(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("LOG_LEVEL", None)
            importlib.reload(logger_module)

        self.assertEqual(logger_module.logger.level, logging.INFO)

    def test_reads_log_level_from_environment(self) -> None:
        with mock.patch.dict("os.environ", {"LOG_LEVEL": "WARNING"}):
            importlib.reload(logger_module)

        self.assertEqual(logger_module.logger.level, logging.WARNING)

    def test_falls_back_to_info_for_invalid_value(self) -> None:
        with mock.patch.dict("os.environ", {"LOG_LEVEL": "NOT_A_LEVEL"}):
            importlib.reload(logger_module)

        self.assertEqual(logger_module.logger.level, logging.INFO)


if __name__ == "__main__":
    unittest.main()
