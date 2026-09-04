import unittest

from src.caption_atacantes import generate_atacantes_caption_plain


def row(**updates):
    base = {
        "MANDANTE": "FLAMENGO", "VISITANTE": "VASCO",
        "COC_PG": 0, "CDF_PG": 0, "COF_PG": 0, "CDC_PG": 0,
        "COC_CHUTES": 0, "CDF_CHUTES": 0, "COF_CHUTES": 0, "CDC_CHUTES": 0,
        "COC_BASICA": 0, "CDF_BASICA": 0, "COF_BASICA": 0, "CDC_BASICA": 0,
    }
    base.update(updates)
    return base


class AtacantesCaptionTests(unittest.TestCase):
    def test_strong_goal_participation_is_not_ignored(self):
        text = generate_atacantes_caption_plain([row(COC_PG=8, COC_CHUTES=13)], 23, 3)
        self.assertIn("DESTAQUES ENTRE OS ATACANTES", text)
        self.assertIn("8 participações em gol", text)

    def test_exceptional_finishing_supports_offensive_participation(self):
        text = generate_atacantes_caption_plain([row(COC_PG=3, COC_CHUTES=22)], 23, 3)
        self.assertIn("3 participações em gol", text)
        self.assertIn("22 finalizações", text)

    def test_seventeen_shots_need_strong_conceded_context(self):
        weak = generate_atacantes_caption_plain([row(COC_CHUTES=17, CDF_CHUTES=16)], 23, 3)
        strong = generate_atacantes_caption_plain([row(COC_CHUTES=17, CDF_CHUTES=17)], 23, 3)
        self.assertNotIn("17 finalizações", weak)
        self.assertIn("17 finalizações", strong)


if __name__ == "__main__":
    unittest.main()
