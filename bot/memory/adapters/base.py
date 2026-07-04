from collections.abc import Sequence
from typing import Protocol


class EmbeddingAdapter(Protocol):
    def embed(self, text: str) -> Sequence[float]:
        ...
