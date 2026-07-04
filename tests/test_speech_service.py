import unittest
from unittest.mock import MagicMock, patch

from bot.services.speech_service import SpeechService


class FakeSegment:
    def __init__(self, text: str) -> None:
        self.text = text


class SpeechServiceTests(unittest.TestCase):
    def test_transcribe_joins_segments_into_plain_text(self) -> None:
        fake_model = MagicMock()
        fake_model.transcribe.return_value = (
            [FakeSegment(" Merhaba "), FakeSegment("dunya ")],
            object(),
        )

        with patch(
            "bot.services.speech_service.WhisperModel",
            return_value=fake_model,
        ) as whisper_model_cls:
            service = SpeechService(model_size="small")
            self.assertEqual(whisper_model_cls.call_count, 0)

            transcript = service.transcribe("voice.ogg")

            self.assertEqual(transcript, "Merhaba dunya")
            whisper_model_cls.assert_called_once_with(
                "small", device="cpu", compute_type="int8"
            )
            fake_model.transcribe.assert_called_once_with(
                "voice.ogg", language="tr"
            )

    def test_model_is_loaded_lazily_and_cached(self) -> None:
        fake_model = MagicMock()
        fake_model.transcribe.return_value = ([], object())

        with patch(
            "bot.services.speech_service.WhisperModel",
            return_value=fake_model,
        ) as whisper_model_cls:
            service = SpeechService()
            service.transcribe("first.ogg")
            service.transcribe("second.ogg")

            whisper_model_cls.assert_called_once()


if __name__ == "__main__":
    unittest.main()
