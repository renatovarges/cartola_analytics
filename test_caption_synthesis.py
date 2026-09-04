import unittest

from src.caption_atacantes import generate_atacantes_caption_plain
from src.caption_meias import generate_meias_caption_plain
from src.caption_volantes import generate_volantes_caption_plain
from src.caption_laterais import generate_laterais_caption_plain


class CaptionSynthesisTests(unittest.TestCase):
    def test_attackers_merge_scouts_and_explain_each_name(self):
        row = {"MANDANTE": "FLAMENGO", "VISITANTE": "VASCO",
               "COC_G": 5, "COC_A": 2, "COC_PG": 7, "CDF_PG": 1,
               "COC_CHUTES": 21, "CDF_CHUTES": 18, "COC_BASICA": 4, "CDF_BASICA": 2,
               "DESTAQUES_MANDANTE_G": ["Pedro"],
               "DESTAQUES_MANDANTE_A": ["Cebolinha"],
               "DESTAQUES_MANDANTE_CHUTES": ["Pedro"]}
        text = generate_atacantes_caption_plain([row], 26, 3)
        self.assertEqual(text.count("Os atacantes do Flamengo"), 1)
        self.assertIn("gols — Pedro", text)
        self.assertIn("assistências — Cebolinha", text)
        self.assertIn("finalizações — Pedro", text)

    def test_window_is_never_hardcoded(self):
        row = {"MANDANTE": "FLAMENGO", "VISITANTE": "VASCO",
               "COC_AF": 25, "CDF_AF": 20, "COC_CHUTES": 0, "CDF_CHUTES": 0,
               "COC_PG": 0, "CDF_PG": 0, "COC_BASICA": 0, "CDF_BASICA": 0}
        text = generate_meias_caption_plain([row], 26, 5)
        self.assertIn("últimos 5 jogos", text)
        self.assertNotIn("últimos 3 jogos", text)

    def test_volante_appears_once_with_primary_scouts(self):
        row = {"MANDANTE": "MIRASSOL", "VISITANTE": "VASCO",
               "COC_DE": 20, "CDF_DE": 15, "COC_PG": 4, "CDF_PG": 3,
               "COC_BASICA": 6, "CDF_BASICA": 4,
               "DESTAQUES_MANDANTE_DE": ["Neto Moura"],
               "DESTAQUES_MANDANTE_BASICA": ["Neto Moura"]}
        text = generate_volantes_caption_plain([row], 26, 3)
        self.assertEqual(text.count("Os volantes do Mirassol"), 1)
        self.assertIn("20 desarmes", text)
        self.assertIn("média básica de 6,0 pontos", text)

    def test_lateral_team_is_not_repeated_for_left_and_right(self):
        row = {"MANDANTE": "FLAMENGO", "VISITANTE": "VASCO",
               "COC_LE_DE": 12, "CDF_LE_DE": 8, "COC_LE_PG": 0, "CDF_LE_PG": 0,
               "COC_LE_BASICA": 4.5, "CDF_LE_BASICA": 3,
               "COC_LD_DE": 11, "CDF_LD_DE": 8, "COC_LD_PG": 0, "CDF_LD_PG": 0,
               "COC_LD_BASICA": 4.3, "CDF_LD_BASICA": 3,
               "DESTAQUES_MANDANTE_LE_DE": float("nan"),
               "DESTAQUES_MANDANTE_LD_DE": float("nan")}
        text = generate_laterais_caption_plain([row], 26, 3)
        self.assertEqual(text.count("Os laterais do Flamengo"), 1)
        self.assertIn("pela esquerda", text)
        self.assertIn("pela direita", text)

    def test_single_lateral_side_is_named_directly(self):
        row = {"MANDANTE": "CORINTHIANS", "VISITANTE": "VASCO",
               "COC_LE_DE": 0, "CDF_LE_DE": 0, "COC_LE_PG": 0, "CDF_LE_PG": 0,
               "COC_LE_BAS": 0, "CDF_LE_BAS": 0,
               "COC_LD_DE": 13, "CDF_LD_DE": 8, "COC_LD_PG": 0, "CDF_LD_PG": 0,
               "COC_LD_BAS": 5.3, "CDF_LD_BAS": 4.0,
               "DESTAQUES_MANDANTE_LD_DE": ["Matheuzinho"],
               "DESTAQUES_MANDANTE_LD_BASICA": ["Matheuzinho"]}
        text = generate_laterais_caption_plain([row], 26, 3)
        self.assertIn("O lateral direito do Corinthians", text)
        self.assertNotIn("Os laterais do Corinthians", text)


if __name__ == "__main__":
    unittest.main()
