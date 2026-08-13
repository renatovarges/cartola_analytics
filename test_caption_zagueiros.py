import unittest

from src.caption_zagueiros import generate_zagueiros_caption_plain


class ZagueirosCaptionTests(unittest.TestCase):
    def base_row(self, **updates):
        row = {
            "MANDANTE": "FLAMENGO", "VISITANTE": "VASCO",
            "COC_SG": 0, "CDF_SG": 0, "COF_SG": 0, "CDC_SG": 0,
            "COC_DE": 0, "CDF_DE": 0, "COF_DE": 0, "CDC_DE": 0,
            "COC_CHUTES_INDIV": 0, "CDF_CHUTES_INDIV": 0,
            "COF_CHUTES_INDIV": 0, "CDC_CHUTES_INDIV": 0,
            "COC_CHUTES_JOGADOR": "", "COF_CHUTES_JOGADOR": "",
            "COC_BASICA": 0, "CDF_BASICA": 0,
            "COF_BASICA": 0, "CDC_BASICA": 0,
        }
        row.update(updates)
        return row

    def test_individual_finishing_names_player(self):
        text = generate_zagueiros_caption_plain([
            self.base_row(COC_CHUTES_INDIV=5, COC_CHUTES_JOGADOR="JOÃO SILVA")
        ], 23, 3)
        self.assertIn("João Silva fez 5 FINALIZAÇÕES", text)
        self.assertNotIn("Os zagueiros do Flamengo somaram 5 FINALIZAÇÕES", text)

    def test_basic_only_enters_exceptional_band(self):
        ordinary = generate_zagueiros_caption_plain([self.base_row(COC_BASICA=2.6)], 23, 3)
        exceptional = generate_zagueiros_caption_plain([self.base_row(COC_BASICA=3.5)], 23, 3)
        self.assertNotIn("MÉDIA BÁSICA", ordinary)
        self.assertIn("MÉDIA BÁSICA", exceptional)

    def test_individual_threshold_scales_with_window(self):
        text = generate_zagueiros_caption_plain([
            self.base_row(COC_CHUTES_INDIV=4, COC_CHUTES_JOGADOR="JOÃO")
        ], 23, 5)
        self.assertNotIn("ZAGUEIROS PARA FINALIZAÇÕES", text)

    def test_sg_never_enters_defender_analysis(self):
        text = generate_zagueiros_caption_plain([
            self.base_row(COC_SG=3)
        ], 23, 3)
        self.assertNotIn("ZAGUEIROS PARA SG", text)
        self.assertNotIn("3 SG", text)


if __name__ == "__main__":
    unittest.main()
