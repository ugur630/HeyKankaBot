from faster_whisper import WhisperModel

from bot.utils.logger import logger


class SpeechService:
    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model: WhisperModel | None = None

    def _get_model(self) -> WhisperModel:
        if self._model is None:
            logger.info("Loading Whisper model: %s", self.model_size)
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._model

    def transcribe(self, file_path: str) -> str:
        model = self._get_model()
        segments, _ = model.transcribe(file_path, language="tr")
        return " ".join(segment.text.strip() for segment in segments).strip()
