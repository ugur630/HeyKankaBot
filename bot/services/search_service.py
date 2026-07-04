import json
import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus, urlparse

import httpx

from bot.utils.logger import logger


SEARCH_PROVIDER = "bing_rss"
SEARCH_STOPWORDS = {
    "abi",
    "acaba",
    "ara",
    "arar",
    "arar misin",
    "bana",
    "bir",
    "bu",
    "bul",
    "dostum",
    "en",
    "gibi",
    "gore",
    "icin",
    "internette",
    "iyi",
    "kanka",
    "lazim",
    "lutfen",
    "misin",
    "mi",
    "mu",
    "musun",
    "oner",
    "oneri",
    "onerir",
    "onerir misin",
    "onerisi",
    "peki",
    "reis",
    "rica",
    "sence",
    "soyle",
    "simdi",
    "ve",
    "ya",
    "yardimci",
}

TOKEN_REPLACEMENTS = {
    "ayakkabi": "shoes",
    "haber": "news",
    "hava": "weather",
    "kripto": "crypto",
    "modeli": "model",
    "modelleri": "models",
    "oneri": "best",
    "oner": "best",
    "onerir": "best",
    "populer": "popular",
    "sneaker": "sneakers",
}

TRUSTED_DOMAINS = {
    "adidas.com": 6,
    "news.adidas.com": 6,
    "runnersworld.com": 5,
    "tomsguide.com": 4,
    "wirecutter.com": 5,
    "cnet.com": 4,
    "reuters.com": 5,
    "apnews.com": 5,
    "bbc.com": 4,
    "bbc.co.uk": 4,
    "cnbc.com": 4,
    "investopedia.com": 4,
    "weather.com": 5,
    "accuweather.com": 5,
}

BLOCKED_DOMAIN_KEYWORDS = (
    "adult",
    "bahis",
    "bet",
    "casino",
    "escort",
    "porn",
    "sex",
    "xxx",
)

BLOCKED_SNIPPET_KEYWORDS = (
    "adult",
    "bonus",
    "casino",
    "click here",
    "escort",
    "free spins",
    "porn",
    "xxx",
)

TURKISH_CHAR_MAP = str.maketrans(
    {
        "\u00e7": "c",
        "\u011f": "g",
        "\u0131": "i",
        "\u00f6": "o",
        "\u015f": "s",
        "\u00fc": "u",
        "\u0130": "I",
    }
)


class SearchService:
    def __init__(
        self,
        max_results: int = 5,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.max_results = max_results
        self.timeout_seconds = timeout_seconds

    def search(self, query: str) -> dict[str, object]:
        original_query = query.strip()
        if not original_query:
            return self._empty_search_payload(query)

        rewritten_query = self.rewrite_query(original_query)
        logger.info("Search original query: %s", original_query)
        logger.info("Search rewritten query: %s", rewritten_query)
        logger.info("Search provider: %s", SEARCH_PROVIDER)

        url = (
            "https://www.bing.com/search?format=rss&q="
            f"{quote_plus(rewritten_query)}"
        )

        started_at = time.perf_counter()
        with httpx.Client(
            follow_redirects=True,
            timeout=self.timeout_seconds,
            headers={"User-Agent": "Mozilla/5.0"},
        ) as client:
            response = client.get(url)
        elapsed_ms = (time.perf_counter() - started_at) * 1000

        logger.info("Search HTTP status: %s", response.status_code)
        logger.info("Search response time: %.2f ms", elapsed_ms)
        response.raise_for_status()

        root = ET.fromstring(response.text)
        raw_results = self._parse_feed(root)
        selected_results = self._select_results(
            raw_results=raw_results,
            original_query=original_query,
            rewritten_query=rewritten_query,
        )

        logger.info("Search number of results: %s", len(selected_results))
        logger.info(
            "Search selected snippets: %s",
            [
                {
                    "title": item["title"],
                    "url": item["url"],
                }
                for item in selected_results
            ],
        )

        return {
            "query": original_query,
            "rewritten_query": rewritten_query,
            "provider": SEARCH_PROVIDER,
            "results": selected_results,
        }

    def format_results(self, query: str) -> str:
        try:
            payload = self.search(query)
        except (httpx.HTTPError, ET.ParseError, ValueError) as exc:
            return json.dumps(
                {
                    "query": query,
                    "rewritten_query": self.rewrite_query(query),
                    "provider": SEARCH_PROVIDER,
                    "error": f"Search failed: {exc}",
                    "results": [],
                }
            )

        return json.dumps(payload)

    def rewrite_query(self, query: str) -> str:
        normalized = self._normalize(query)
        tokens = re.findall(r"[a-z0-9]+", normalized)
        filtered_tokens = [
            TOKEN_REPLACEMENTS.get(token, token)
            for token in tokens
            if token not in SEARCH_STOPWORDS
        ]

        if self._is_adidas_shoe_query(filtered_tokens):
            return "most popular Adidas sneakers"

        if not filtered_tokens:
            return query.strip()

        return " ".join(self._deduplicate_tokens(filtered_tokens))

    def _parse_feed(self, root: ET.Element) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            description = (item.findtext("description") or "").strip()

            if not title or not link:
                continue

            results.append(
                {
                    "title": title,
                    "url": link,
                    "snippet": description,
                }
            )
        return results

    def _select_results(
        self,
        raw_results: list[dict[str, str]],
        original_query: str,
        rewritten_query: str,
    ) -> list[dict[str, str]]:
        scored_results: list[tuple[int, dict[str, str]]] = []
        for result in raw_results:
            if self._is_blocked_result(result):
                continue

            score = self._score_result(
                result=result,
                original_query=original_query,
                rewritten_query=rewritten_query,
            )
            if score <= 0:
                continue

            scored_results.append((score, result))

        scored_results.sort(
            key=lambda item: (
                -item[0],
                item[1]["title"].lower(),
            )
        )

        selected: list[dict[str, str]] = []
        seen_domains: set[str] = set()
        for _, result in scored_results:
            domain = self._extract_domain(result["url"])
            if domain in seen_domains and len(selected) >= 2:
                continue

            selected.append(result)
            seen_domains.add(domain)
            if len(selected) >= self.max_results:
                break

        return selected

    def _score_result(
        self,
        result: dict[str, str],
        original_query: str,
        rewritten_query: str,
    ) -> int:
        domain = self._extract_domain(result["url"])
        combined_text = self._normalize(
            " ".join(
                [
                    result.get("title", ""),
                    result.get("snippet", ""),
                    original_query,
                ]
            )
        )
        query_tokens = set(re.findall(r"[a-z0-9]+", self._normalize(rewritten_query)))
        overlap_score = sum(
            2 for token in query_tokens if token and token in combined_text
        )

        trust_score = 0
        for trusted_domain, value in TRUSTED_DOMAINS.items():
            if domain == trusted_domain or domain.endswith(f".{trusted_domain}"):
                trust_score = max(trust_score, value)

        brand_bonus = 0
        if "adidas" in rewritten_query.lower() and "adidas" in domain:
            brand_bonus = 4

        snippet_penalty = 0
        if len(result.get("snippet", "")) < 20:
            snippet_penalty = 2

        return trust_score + overlap_score + brand_bonus - snippet_penalty

    def _is_blocked_result(self, result: dict[str, str]) -> bool:
        domain = self._extract_domain(result["url"])
        if any(keyword in domain for keyword in BLOCKED_DOMAIN_KEYWORDS):
            return True

        combined_text = self._normalize(
            " ".join(
                [
                    result.get("title", ""),
                    result.get("snippet", ""),
                ]
            )
        )
        return any(keyword in combined_text for keyword in BLOCKED_SNIPPET_KEYWORDS)

    def _is_adidas_shoe_query(self, tokens: list[str]) -> bool:
        token_set = set(tokens)
        return (
            "adidas" in token_set
            and ("shoes" in token_set or "sneakers" in token_set)
            and (
                "popular" in token_set
                or "best" in token_set
                or "model" in token_set
            )
        )

    def _normalize(self, value: str) -> str:
        lowered = value.lower().translate(TURKISH_CHAR_MAP)
        return " ".join(lowered.split())

    def _deduplicate_tokens(self, tokens: list[str]) -> list[str]:
        deduplicated: list[str] = []
        seen: set[str] = set()
        for token in tokens:
            if token in seen:
                continue
            seen.add(token)
            deduplicated.append(token)
        return deduplicated

    def _extract_domain(self, url: str) -> str:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        return hostname.lower().removeprefix("www.")

    def _empty_search_payload(self, query: str) -> dict[str, object]:
        return {
            "query": query,
            "rewritten_query": "",
            "provider": SEARCH_PROVIDER,
            "results": [],
        }
