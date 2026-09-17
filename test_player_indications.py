import unittest
from unittest.mock import patch

import pandas as pd

from src.caption_zagueiros import generate_zagueiros_caption_plain
from src.engine import CartolaEngine
from src.player_indications import analyse_matchups, append_individual_section, _keeper_evidence


class PlayerIndicationsTests(unittest.TestCase):
    def setUp(self):
        self.games = pd.DataFrame({
            "TIME": ["ALFA"] * 5, "TEAM_KEY": ["ALFA"] * 5,
            "ADVERSARIO_KEY": ["OUTRO"] * 5,
            "NOME": ["JOAO"] * 5, "ROLE": ["ZAG"] * 5,
            "POSICAO": ["3"] * 5,
            "MATCH_ID": [f"j{i}" for i in range(5)],
            "DATA": pd.date_range("2026-08-01", periods=5),
            "DE": [2, 2, 2, 1, 1], "CHUTES": [0] * 5,
            "PG": [0] * 5, "GS": [0] * 5,
        })
        self.lineup = {"ALFA": {"ZAG": [{"nome": "Joao", "status": 7}]}}
        self.rows = [{"MANDANTE": "ALFA", "VISITANTE": "BETA"}]
        self.reference = {"own": {("ZAG", "DE"): {
            .75: 1.5, .80: 1.5, .85: 1.6, .90: 2.5}},
                          "conceded": {("ZAG", "DE"): 4.0}}

    def _analyse(self, opponent_values, reference=None):
        with (patch("src.player_indications._source", return_value=self.games),
              patch("src.player_indications._quantiles", return_value=reference or self.reference),
              patch("src.player_indications._opponent_games", return_value=opponent_values),
              patch("src.player_indications._keeper_evidence", return_value=None)):
            return analyse_matchups(None, self.lineup, self.rows, "ZAGUEIROS")

    def test_recurrent_individual_cross_survives_without_collective_highlight(self):
        chosen, audit = self._analyse([4, 5, 4, 4, 0])
        self.assertEqual(len(chosen), 1)
        self.assertTrue(chosen[0]["cruzamento"])
        self.assertTrue(chosen[0]["forte"])
        self.assertEqual(chosen[0]["ocorrencias"], 3)
        self.rows[0]["INDICACOES_ZAGUEIROS"] = chosen
        caption = generate_zagueiros_caption_plain(self.rows, 28)
        self.assertIn("JOAO", caption.upper())
        self.assertIn("4/5 jogos", caption)

    def test_two_opponent_concessions_do_not_make_cross(self):
        chosen, audit = self._analyse([4, 0, 0, 4, 0])
        self.assertEqual(len(chosen), 1)
        self.assertFalse(chosen[0]["cruzamento"])

    def test_cross_alone_does_not_promote_moderate_player(self):
        moderate_reference = {"own": {("ZAG", "DE"): {
            .75: 1.5, .80: 1.5, .85: 2.5, .90: 2.5}},
                              "conceded": {("ZAG", "DE"): 4.0}}
        chosen, audit = self._analyse([4, 5, 4, 4, 0], moderate_reference)
        self.assertFalse(chosen)
        self.assertTrue(audit[0]["cruzamento"])
        self.assertEqual(audit[0]["motivo"], "abaixo_dos_cortes")

    def test_goalkeeper_statement_requires_recent_individual_gs(self):
        keeper = self.games.copy()
        keeper["TIME"] = "BETA"
        keeper["TEAM_KEY"] = "BETA"
        keeper["NOME"] = "MARIO"
        keeper["POSICAO"] = "1"
        keeper["GS"] = [2, 2, 0, 3, 1]
        lineup = {"BETA": {"GOL": [{"nome": "Mario", "status": 7}]}}
        item = _keeper_evidence(keeper, lineup, "BETA")
        self.assertEqual(item, {"nome": "Mario", "hits": 3, "jogos": 5})

    def test_basic_average_has_no_team_share(self):
        engine = CartolaEngine.__new__(CartolaEngine)
        rows = []
        for game in range(3):
            for name, basic in (("A", 4), ("B", 2)):
                rows.append({"TIME": "ALFA", "POSICAO": "3", "NOME": name,
                             "MANDO": "CASA", "MATCH_ID": f"j{game}",
                             "DATA": pd.Timestamp("2026-08-01") + pd.Timedelta(days=game),
                             "DS": 0, "FF": 0, "FD": 0, "FT": 0,
                             "PONTOS": basic, "BASICA": basic})
        engine.df_pj = pd.DataFrame(rows)
        detail = engine.get_player_concentration("ALFA", "ZAGUEIROS", max_rank=None)
        basic = detail[detail.SCOUT.eq("BASICA")]
        self.assertEqual(set(basic.TOTAL), {2, 4})
        self.assertTrue(basic.PARTICIPACAO.isna().all())
        self.assertEqual(set(basic.CONCENTRACAO), {"NAO_APLICAVEL"})


if __name__ == "__main__":
    unittest.main()
