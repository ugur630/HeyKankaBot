import unittest

from bot.services.search_service import SearchService


class SearchServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = SearchService(max_results=3)

    def test_rewrites_conversational_adidas_query(self) -> None:
        rewritten = self.service.rewrite_query(
            "internette bana en populer adidas ayakkabi modeli onerir misin"
        )

        self.assertEqual(rewritten, "most popular Adidas sneakers")

    def test_filters_spam_results(self) -> None:
        raw_results = [
            {
                "title": "Adidas Bonus Casino",
                "url": "https://adidas-casino.example.com",
                "snippet": "free spins and bonus",
            },
            {
                "title": "Best Adidas Shoes 2026",
                "url": "https://www.runnersworld.com/gear/a/adidas-shoes",
                "snippet": "Editors pick the best Adidas running shoes.",
            },
            {
                "title": "Official Adidas Running Shoes",
                "url": "https://www.adidas.com/us/running-shoes",
                "snippet": "Shop official Adidas running shoe models.",
            },
        ]

        selected = self.service._select_results(
            raw_results=raw_results,
            original_query="En populer Adidas ayakkabi modeli oner.",
            rewritten_query="most popular Adidas sneakers",
        )

        self.assertEqual(len(selected), 2)
        self.assertTrue(
            all("casino" not in result["url"] for result in selected)
        )

    def test_prefers_trusted_sources(self) -> None:
        raw_results = [
            {
                "title": "Adidas shoe roundup",
                "url": "https://randomblog.example.com/adidas-roundup",
                "snippet": "A quick post about Adidas shoes.",
            },
            {
                "title": "Official Adidas Running Shoes",
                "url": "https://www.adidas.com/us/running-shoes",
                "snippet": "Shop official Adidas running shoe models.",
            },
            {
                "title": "Best Adidas Shoes 2026",
                "url": "https://www.runnersworld.com/gear/a/adidas-shoes",
                "snippet": "Editors pick the best Adidas running shoes.",
            },
        ]

        selected = self.service._select_results(
            raw_results=raw_results,
            original_query="En populer Adidas ayakkabi modeli oner.",
            rewritten_query="most popular Adidas sneakers",
        )

        self.assertEqual(selected[0]["url"], "https://www.adidas.com/us/running-shoes")
        self.assertEqual(
            selected[1]["url"],
            "https://www.runnersworld.com/gear/a/adidas-shoes",
        )


if __name__ == "__main__":
    unittest.main()
