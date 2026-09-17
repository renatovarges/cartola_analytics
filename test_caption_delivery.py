import unittest

from src.caption_delivery import split_caption


class CaptionDeliveryTests(unittest.TestCase):
    def test_long_caption_keeps_every_character_in_order(self):
        caption = "Título\n" + ("Jogador: scout e cruzamento.\n" * 200)
        parts = split_caption(caption, 3500)
        self.assertGreater(len(parts), 1)
        self.assertTrue(all(len(part) <= 3500 for part in parts))
        self.assertEqual("".join(parts), caption)

    def test_single_long_line_is_preserved(self):
        caption = "x" * 20
        self.assertEqual("".join(split_caption(caption, 7)), caption)


if __name__ == "__main__":
    unittest.main()
