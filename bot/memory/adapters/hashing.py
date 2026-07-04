import math
import re
from collections import Counter

from bot.memory.adapters.base import EmbeddingAdapter


TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


class HashingEmbeddingAdapter(EmbeddingAdapter):
    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * self.dimensions

        vector = [0.0] * self.dimensions
        counts = Counter(tokens)

        for token, weight in counts.items():
            vector[hash(token) % self.dimensions] += float(weight)

            for ngram in self._char_ngrams(token):
                vector[hash(ngram) % self.dimensions] += 0.35

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector

        return [value / norm for value in vector]

    def _tokenize(self, text: str) -> list[str]:
        return [token.lower() for token in TOKEN_PATTERN.findall(text)]

    def _char_ngrams(self, token: str) -> list[str]:
        if len(token) < 3:
            return [token]

        return [
            token[index : index + 3]
            for index in range(len(token) - 2)
        ]
