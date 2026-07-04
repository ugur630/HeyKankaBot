import unittest

from bot.utils.helpers import split_message


class SplitMessageTests(unittest.TestCase):
    def test_short_text_is_returned_as_single_chunk(self) -> None:
        chunks = split_message("hello kanka")
        self.assertEqual(chunks, ["hello kanka"])

    def test_long_text_without_newlines_splits_at_limit(self) -> None:
        text = "a" * 9000
        chunks = split_message(text, limit=4096)

        self.assertEqual(len(chunks), 3)
        self.assertEqual("".join(chunks), text)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 4096)

    def test_long_text_prefers_splitting_on_newline_boundary(self) -> None:
        first_line = "x" * 4090
        second_line = "y" * 20
        text = f"{first_line}\n{second_line}"

        chunks = split_message(text, limit=4096)

        self.assertEqual(chunks[0], first_line)
        self.assertEqual(chunks[1], second_line)

    def test_reconstructed_chunks_preserve_content_for_long_multiline_text(
        self,
    ) -> None:
        text = "\n".join(f"line {i} " + "z" * 50 for i in range(200))
        chunks = split_message(text, limit=500)

        self.assertTrue(all(len(chunk) <= 500 for chunk in chunks))
        self.assertEqual("\n".join(chunks), text)


if __name__ == "__main__":
    unittest.main()
